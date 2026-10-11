#!/usr/bin/env python3
"""Strict V2.2 document consistency validator (Python stdlib only).

Default exit 0 means planning consistency, never academic approval. Use
--require-approval for an implementation gate (exit 2 while approval is OPEN).
No Git mutations, raw-data reads or product implementation occur here.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / 'docs/planning'
TASK_IDS = {f'T-{n:02}' for n in range(41)} | {'T-22B'}
MEMBERS = {'Wageeh','Hamza','Hasnaa','Rana'}
SCOPES = {'MVP','Governance','Advanced','Optional'}
MANDATORY = {'MVP','Governance'}
STATUSES = {'Planned','In Progress','Completed','Completed locally','Blocked'}
COLUMNS = ['Task ID','Phase','Title','Owner','Reviewer','Collaborators','Dependencies','Priority','Scope','Estimated Owner Hours','Estimated Collaborator Hours','Estimated Reviewer Hours','Status','Gate','Deliverable']
HOURS = ['Estimated Owner Hours','Estimated Collaborator Hours','Estimated Reviewer Hours']
SUMMARY_MAP = {'Task ID':'Task ID','Title':'Title','Owner':'Owner','Phase':'Phase','Scope':'Scope','Priority':'Priority','Owner Hours':'Estimated Owner Hours','Deps':'Dependencies','Status':'Status','Collaborators':'Collaborators','Reviewer':'Reviewer','Collaborator Hours':'Estimated Collaborator Hours','Reviewer Hours':'Estimated Reviewer Hours'}
ENDPOINTS = {('GET','/api/v1/health'),('GET','/api/v1/analytics/summary'),('GET','/api/v1/analytics/trends'),('GET','/api/v1/analytics/geographic'),('GET','/api/v1/analytics/categories'),('GET','/api/v1/analytics/customers'),('GET','/api/v1/analytics/sellers'),('POST','/api/v1/predict/delivery-risk'),('POST','/api/v1/predict/review-sentiment'),('GET','/api/v1/models/metadata')}
STATES = {'Proposal prepared','Proposal submitted','Awaiting instructor response','Approved','Approved with conditions','Rejected'}


def plain(value: str) -> str:
    return value.replace('**','').replace('`','').strip()


def number(value: str) -> float:
    # Accept presentation emphasis, approximation prefix and explicit hour suffix.
    match=re.fullmatch(r'~?(-?\d+(?:\.\d+)?)(?:h|%| \(done\)| \(completed\))?',plain(value))
    if not match: raise ValueError(f'Not an unambiguous displayed number: {value!r}')
    val=float(match.group(1))
    if not math.isfinite(val): raise ValueError('Nonfinite hours')
    return val


def deps(value: str) -> set[str]:
    return set(re.findall(r'T-\d+[A-Z]*',value))


def normalized(value: str, column: str) -> Any:
    value=plain(value)
    if column in HOURS: return number(value)
    if column=='Dependencies':
        if value in {'','—','None'}: return ''
        return ','.join(sorted(re.sub(r'\s+','',v) for v in value.split(',')))
    if value in {'','—'}: return ''
    return value


def section(text: str, heading: str) -> str:
    match=re.search(r'^'+re.escape(heading)+r'\s*\n',text,re.M)
    if not match: raise ValueError(f'Missing heading {heading}')
    depth=len(heading)-len(heading.lstrip('#'))
    following=re.search(r'^#{1,'+str(depth)+r'} ',text[match.end():],re.M)
    return text[match.end():match.end()+following.start()] if following else text[match.end():]


def tables(text: str) -> list[list[list[str]]]:
    groups=[];current=[]
    for line in text.splitlines()+['']:
        if line.strip().startswith('|'):
            row=[plain(c) for c in line.strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?',c.strip()) for c in row):current.append(row)
        elif current:
            groups.append(current);current=[]
    return groups


def table(text: str, first_header: str) -> list[dict[str,str]]:
    matches=[t for t in tables(text) if t[0][0]==first_header]
    if len(matches)!=1:raise ValueError(f'Expected one {first_header!r} table, got {len(matches)}')
    t=matches[0]
    if len(set(t[0]))!=len(t[0]):raise ValueError('Duplicate table columns')
    if any(len(r)!=len(t[0]) for r in t[1:]):raise ValueError('Malformed Markdown table width')
    return [dict(zip(t[0],r)) for r in t[1:]]


def specs(text: str) -> list[tuple[str,dict[str,str]]]:
    content=section(text,'## Part 11 — Detailed Task Specifications')
    matches=list(re.finditer(r'^### (T-\d+[A-Z]*) — ([^\n]+)',content,re.M));result=[]
    for idx,m in enumerate(matches):
        block=content[m.end():matches[idx+1].start() if idx+1<len(matches) else len(content)]
        rows=table(block,'Field')
        if len({r['Field'] for r in rows})!=len(rows):raise ValueError(f'Duplicate spec field {m[1]}')
        result.append((m[1],{r['Field']:r['Value'] for r in rows}))
    return result


def approval_passed(state: dict[str,Any]) -> bool:
    evidence=state.get('approval_evidence')
    return bool(evidence) and (state.get('current_state')=='Approved' or (state.get('current_state')=='Approved with conditions' and state.get('conditions_incorporated') is True and state.get('conditions_accepted') is True))


def workload(rows: list[dict[str,str]], selected: set[str]|None=None) -> list[float]:
    return [sum(number(r[c]) for r in rows if selected is None or r['Scope'] in selected) for c in HOURS]


def validate_documents(rows: list[dict[str,str]], text: str, schedule: dict, approval: dict, contract: dict, columns: list[str]|None=None) -> dict:
    checks=[]
    def check(cid: str, title: str, fn):
        try:
            evidence=fn()
            checks.append({'id':cid,'title':title,'status':'PASS','evidence':evidence})
        except (ValueError,KeyError,TypeError,IndexError,AssertionError) as exc:
            checks.append({'id':cid,'title':title,'status':'FAIL','evidence':str(exc) or 'Condition failed'})
    def require(ok,reason):
        if not ok:raise ValueError(reason)
    ids=[r.get('Task ID','') for r in rows];by_id={r.get('Task ID',''):r for r in rows}
    def ledger_structure():
        require(set(columns or COLUMNS)==set(COLUMNS),'CSV columns differ from canonical 15 columns')
        require(len(columns or COLUMNS)==15,'Duplicate CSV columns')
        require(not [k for k,n in Counter(ids).items() if n>1],f'Duplicate task IDs: {dict(Counter(ids))}')
        require(set(ids)==TASK_IDS,f'Missing IDs {sorted(TASK_IDS-set(ids))}; extra {sorted(set(ids)-TASK_IDS)}')
        for r in rows:
            require(set(r)==set(COLUMNS),'Malformed/extra CSV fields')
            require(r['Owner'] in MEMBERS,f'Invalid single owner: {r["Task ID"]}')
            require(r['Reviewer'] in MEMBERS|{'Instructor','N/A'},f'Invalid reviewer {r["Task ID"]}')
            require(r['Owner']!=r['Reviewer'],f'Owner equals reviewer {r["Task ID"]}')
            require(r['Scope'] in SCOPES,f'Invalid scope {r["Task ID"]}')
            require(r['Status'] in STATUSES,f'Invalid status {r["Task ID"]}')
            require(r['Priority'] in {'P0','P1','P2',''},f'Invalid priority {r["Task ID"]}')
            require(r['Deliverable'].strip(),f'Missing deliverable {r["Task ID"]}')
            for c in HOURS:require(number(r[c])>=0,f'Negative hours {r["Task ID"]}')
            tokens=re.findall(r'T-\d+[A-Z]*(?:\(approval_gate_passed\))?',r['Dependencies'])
            require(len(tokens)==len(set(tokens)),f'Duplicate dependencies {r["Task ID"]}')
            remainder=re.sub(r'T-\d+[A-Z]*(?:\(approval_gate_passed\))?|[,\s]+','',r['Dependencies'])
            require(not remainder,f'Unsupported dependency annotation {r["Task ID"]}: {remainder}')
            coll=set(v.strip() for v in r['Collaborators'].split(',') if v.strip())
            require(coll<=MEMBERS-{r['Owner']},f'Invalid nonowner collaborators {r["Task ID"]}')
        require(by_id['T-00']['Status']=='Completed locally' and number(by_id['T-00'][HOURS[0]])==0,'T-00 must be completed locally, zero remaining hours')
        return '42 exact IDs, valid roles/scopes/statuses/priorities and finite nonnegative hours'
    check('V-01','Ledger schema, identity and value constraints',ledger_structure)
    def task_agreement():
        summ=table(section(text,'### 10.1 Task Summary Table'),'Task ID');sp=specs(text)
        require(set(summ[0])==set(SUMMARY_MAP),'Task summary columns incomplete or extra')
        require(Counter(r['Task ID'] for r in summ)==Counter(ids),'Summary missing/duplicate/extra task IDs')
        require(Counter(k for k,v in sp)==Counter(ids),'Specs missing/duplicate/extra task IDs')
        errors=[]
        for r in summ:
            for display,canonical in SUMMARY_MAP.items():
                if normalized(r[display],canonical)!=normalized(by_id[r['Task ID']][canonical],canonical):errors.append(f'{r["Task ID"]} summary {canonical}: {r[display]!r} != {by_id[r["Task ID"]][canonical]!r}')
        smap={'Estimated Hours':'Estimated Owner Hours','Estimated Collaborator Hours':'Estimated Collaborator Hours','Estimated Reviewer Hours':'Estimated Reviewer Hours'}
        for tid,s in sp:
            for col in ['Task ID','Title','Phase','Priority','Scope','Owner','Reviewer','Collaborators','Dependencies','Status']:
                if normalized(s[col],col)!=normalized(by_id[tid][col],col):errors.append(f'{tid} spec {col}')
            for label,col in smap.items():
                if number(s[label])!=number(by_id[tid][col]):errors.append(f'{tid} spec {col}')
        require(not errors,'; '.join(errors))
        return 'Every summary and detailed spec reconciles fields, role metadata, dependencies including gate annotation, status and three hour budgets'
    check('V-02','Exact task-by-task plan/ledger agreement',task_agreement)
    def graph_check():
        edges={(d,r['Task ID']) for r in rows for d in deps(r['Dependencies'])}
        require(all(a in by_id and b in by_id for a,b in edges),'Unknown dependency ID')
        for a,b in edges:require(not(by_id[b]['Scope'] in MANDATORY and by_id[a]['Scope'] not in MANDATORY),f'Mandatory {b} depends on expansion {a}')
        pending={tid:deps(r['Dependencies']) for tid,r in by_id.items()};order=[]
        while pending:
            ready=sorted(n for n,d in pending.items() if not d)
            require(ready,'Cycle detected in canonical graph')
            for n in ready:
                order.append(n);del pending[n]
            for d in pending.values():d.difference_update(ready)
        dag=section(text,'### 6.4 Task Dependency DAG');blocks=re.findall(r'```mermaid\n(.*?)```',dag,re.S)
        require(len(blocks)==1,'Expected one complete Task Dependency DAG')
        # Narrow supported grammar: declarations separate; explicit single edges.
        diagram=set()
        for line in blocks[0].splitlines():
            if '-->' in line:
                m=re.fullmatch(r'\s*T(\d+[A-Z]*)\s*-->\s*T(\d+[A-Z]*)\s*',line)
                require(m is not None,f'Unsupported edge grammar: {line}')
                diagram.add((f'T-{m[1]}',f'T-{m[2]}'))
        missing=edges-diagram;extra=diagram-edges
        require(not missing and not extra,f'Missing DAG edges {sorted(missing)}; extra DAG edges {sorted(extra)}')
        declared=set('T-'+v for v in re.findall(r'^\s*T(\d+[A-Z]*)\[',blocks[0],re.M));require(declared==set(ids),'Missing/extra DAG node declarations')
        sp=dict(specs(text));spec_edges={(d,tid) for tid,v in sp.items() for d in deps(v['Dependencies'])}
        require(spec_edges==edges,f'Spec edges differ: missing {sorted(edges-spec_edges)}, extra {sorted(spec_edges-edges)}')
        dist={};paths={}
        for tid in order:
            predecessors=deps(by_id[tid]['Dependencies']);best=max(sorted(predecessors),key=lambda k:dist[k]) if predecessors else None
            dist[tid]=number(by_id[tid][HOURS[0]])+(dist[best] if best else 0);paths[tid]=(paths[best] if best else [])+[tid]
        end=max(sorted(dist),key=lambda k:dist[k]);claimed=re.search(r'\*\*Critical path total:\*\* (\d+) owner hours',text)
        require(claimed and int(claimed[1])==dist[end],'Critical path hour claim differs')
        chain=section(text,'### 16.4 Critical Path Analysis');listed=re.findall(r'(T-\d+[A-Z]*)\(\d+h\)',chain)
        require(listed==[n for n in paths[end] if number(by_id[n][HOURS[0]])>0],'Displayed critical path chain differs')
        return {'edges':len(edges),'missing_edges':[],'extra_edges':[],'cycle':False,'critical_path_hours':dist[end],'critical_path':paths[end]}
    check('V-03','Full DAG/spec dependency equality and acyclicity',graph_check)
    def workload_claims():
        a=section(text,'### 10.2 Workload Summary');owners=table(a,'Member');scope_rows=table(a,'Scope');effort=table(a,'Category')
        errors=[];tot=workload(rows);byowner={n:workload([r for r in rows if r['Owner']==n])[0] for n in sorted(MEMBERS)}
        def equal(actual,expected,where):
            if abs(number(actual)-expected)>1e-6:errors.append(f'{where}: {actual} != {expected}')
        require(Counter(r['Member'] for r in owners)==Counter(list(MEMBERS)+['TOTAL']),'Owner summary missing/extra/duplicate rows')
        for r in owners:
            selected=rows if r['Member']=='TOTAL' else [x for x in rows if x['Owner']==r['Member']]
            for sc in SCOPES:equal(r[sc],workload(selected,{sc})[0],f'{r["Member"]}/{sc}')
            total=workload(selected)[0];equal(r['Total'],total,f'{r["Member"]}/total');equal(r['Percentage'],round(total/tot[0]*100,1),'owner percentage')
        require(Counter(r['Scope'] for r in scope_rows)==Counter(list(SCOPES)+['Total Owner']),'Scope summary rows differ')
        for r in scope_rows:equal(r['Hours'],tot[0] if r['Scope']=='Total Owner' else workload(rows,{r['Scope']})[0],r['Scope'])
        must=workload(rows,MANDATORY);optional=workload(rows,SCOPES-MANDATORY)
        expected={'Owner implementation hours':tot[0],'Collaborator hours':tot[1],'Reviewer hours':tot[2],'Total assigned effort':sum(tot),'Estimated shared activities (meetings, syncs, ~5h/person)':schedule['team_size']*schedule['shared_hours_per_person'],'Required academic delivery (MVP + Governance owner hours)':must[0],'Optional expansion (Advanced + Optional owner hours)':optional[0]}
        require({r['Category'] for r in effort}==set(expected),'Effort category rows differ')
        for r in effort:equal(r['Hours'],expected[r['Category']],r['Category'])
        # Part16 detailed owner task tables and their displayed totals/subtotals.
        w=section(text,'### 16.1 Detailed Workload by Member')
        for member in sorted(MEMBERS):
            m=re.search(r'^#### '+member+r'(?: Gadd)? — (\d+) hours total\n(.*?)(?=^#### |\Z)',w,re.M|re.S);require(m is not None,f'Missing member detail {member}')
            equal(m[1],byowner[member],f'{member} heading hours')
            detail=table(m[2],'Task');listed={}
            for r in detail:
                tid=re.match(r'(T-\d+[A-Z]*)\b',r['Task'])
                if tid:
                    require(tid[1] not in listed,f'Duplicate member task {tid[1]}');listed[tid[1]]=r
                elif r['Task']=='Subtotals':
                    equal(r['Hours'],byowner[member],f'{member} subtotal')
                    short={'MVP':'MVP','Gov':'Governance','Adv':'Advanced','Opt':'Optional'}
                    displays={short[k]:float(v) for k,v in re.findall(r'(MVP|Gov|Adv|Opt): (\d+)',r['Scope'])}
                    actual={sc:workload([q for q in rows if q['Owner']==member],{sc})[0] for sc in SCOPES}
                    require(displays=={k:v for k,v in actual.items() if v},f'{member} scope subtotals differ')
                else:raise ValueError('Unknown member detail row')
            actual={r['Task ID']:r for r in rows if r['Owner']==member and number(r[HOURS[0]])>0}
            require(set(listed)==set(actual),f'{member} detailed task coverage differs')
            for tid,r in listed.items():equal(r['Hours'],number(actual[tid][HOURS[0]]),tid);require(r['Scope']==actual[tid]['Scope'],f'{tid} detailed scope mismatch')
        summary=table(section(text,'### 16.2 Summary Quantities'),'Category')
        values=[workload(rows,{'MVP'})[0],workload(rows,{'Governance'})[0],must[0],workload(rows,{'Advanced'})[0],workload(rows,{'Optional'})[0],*tot,sum(tot),schedule['team_size']*schedule['shared_hours_per_person'],must[0]*schedule['contingency_rate'],must[1],must[2],sum(must)+20+must[0]*schedule['contingency_rate'],sum(tot)+20+tot[0]*schedule['contingency_rate']]
        require(len(summary)==len(values),'Part16 summary count differs')
        for r,value in zip(summary,values):equal(r['Hours'],value,r['Category'])
        friendly=table(section(text,'## Part 19 — Team-Friendly Summary'),'Member')
        require({r['Member'] for r in friendly}==MEMBERS,'Team summary coverage differs')
        for r in friendly:
            m=re.fullmatch(r'(\d+) \((\d+\.\d+)%\)',r['Hours']);require(m is not None,'Ambiguous team summary hours')
            equal(m[1],byowner[r['Member']],'friendly hours');equal(m[2],round(byowner[r['Member']]/tot[0]*100,1),'friendly percentage')
        require(not errors,'; '.join(errors))
        review_by_person={person:sum(number(r[HOURS[2]]) for r in rows if r['Reviewer']==person) for person in sorted(MEMBERS|{'Instructor'})}
        return {'owner':byowner,'reviewer_hours_by_person':review_by_person,'collaborator_budget':'53 task-pooled hours; no per-person distribution is claimed','scope':{sc:workload(rows,{sc})[0] for sc in sorted(SCOPES)},'collaboration':tot[1],'review':tot[2],'assigned_total':sum(tot),'mandatory':must,'optional':optional}
    check('V-04','Displayed owner/scope/role totals and member task hours',workload_claims)
    def schedules():
        require(schedule['team_size']==len(MEMBERS),'Schedule team size differs')
        require(all(isinstance(schedule[k],(int,float)) and math.isfinite(schedule[k]) and schedule[k]>=0 for k in ['hours_per_person_week','shared_hours_per_person','contingency_rate']),'Invalid schedule numeric assumptions')
        require(schedule['contingency_basis']=='selected scope owner hours','Unknown contingency basis')
        displayed_assumptions=table(section(text,'### 16.3 Schedule Scenarios — checked capacity arithmetic, not a resource schedule'),'Assumption')
        assumptions={r['Assumption']:r['Value'] for r in displayed_assumptions}
        expected_assumptions={'Team size':schedule['team_size'],'Hours/person/week':schedule['hours_per_person_week'],'Shared hours/person':schedule['shared_hours_per_person'],'Contingency rate':schedule['contingency_rate'],'Contingency basis':schedule['contingency_basis']}
        require(set(assumptions)==set(expected_assumptions),'Schedule assumption coverage differs')
        for k,value in expected_assumptions.items():require((assumptions[k]==value if isinstance(value,str) else number(assumptions[k])==value),f'Schedule assumption mismatch {k}')
        scs=schedule['scenarios'];require([(v['weeks'],set(v['scopes'])) for v in scs]==[(6,MANDATORY),(8,MANDATORY),(10,MANDATORY),(10,SCOPES)],'Required 6/8/10-week scenarios missing or changed')
        displayed=table(section(text,'### 16.3 Schedule Scenarios — checked capacity arithmetic, not a resource schedule'),'Scenario')
        require(len(displayed)==len(scs),'Schedule row count differs')
        results=[]
        for sc,r in zip(scs,displayed):
            owner,coll,rev=workload(rows,set(sc['scopes']));capacity=schedule['team_size']*schedule['hours_per_person_week']*sc['weeks'];shared=schedule['team_size']*schedule['shared_hours_per_person'];cont=owner*schedule['contingency_rate'];required=owner+coll+rev+shared+cont
            expected={'Weeks':sc['weeks'],'Capacity':capacity,'Owner':owner,'Collaboration':coll,'Review':rev,'Shared':shared,'Contingency':cont,'Required':required,'Balance':capacity-required,'Hours/person/week needed':round(required/(schedule['team_size']*sc['weeks']),4)}
            for k,v in expected.items():require(abs(number(r[k])-v)<1e-6,f'Schedule {r["Scenario"]}/{k}: {r[k]} != {v}')
            require(set(v.strip() for v in r['Scopes'].split(','))==set(sc['scopes']),'Scenario scopes differ')
            require(r['Capacity verdict']==('CAPACITY ONLY' if capacity>=required else 'EXCEEDS CAPACITY'),'Capacity verdict incorrect')
            results.append({'scenario':r['Scenario'],'capacity':capacity,'required':required,'balance':capacity-required})
        return results
    check('V-05','Schedule configuration, arithmetic and displayed verdicts',schedules)
    def api():
        content=section(text,'### 8.1 Canonical Endpoint Registry');reg=table(content,'#')
        pairs=[(r['Method'],r['Path']) for r in reg];require(len(pairs)==len(set(pairs)),'Duplicate registry routes');require(set(pairs)==ENDPOINTS,f'Registry missing {sorted(ENDPOINTS-set(pairs))}, extra {sorted(set(pairs)-ENDPOINTS)}')
        # Only explicit historical delimiters, never keyword heuristics.
        starts=text.count('<!-- historical-routes:start -->');ends=text.count('<!-- historical-routes:end -->');require(starts==ends,'Unbalanced historical route delimiters')
        active=re.sub(r'<!-- historical-routes:start -->.*?<!-- historical-routes:end -->','',text,flags=re.S)
        paths=set(re.findall(r'/api/v1/[A-Za-z0-9_./{}-]+',active));allowed={p for m,p in pairs}
        require(paths<=allowed,f'Undefined active paths: {sorted(paths-allowed)}')
        short=re.findall(r'(?<![A-Za-z0-9_/])(/(?:analytics|predict|models)/[a-z-]+)',active);require(not short,f'Unqualified API references: {short}')
        explicit=set(re.findall(r'\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[A-Za-z0-9_./{}-]+)',active));require(explicit<=set(pairs),f'Undefined active method/path {sorted(explicit-set(pairs))}')
        contracts=section(text,'### 8.3 Endpoint Contracts');defined=[]
        for block in re.split(r'^#### Endpoint \d+:',contracts,flags=re.M)[1:]:
            route=re.search(r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/api/v1/[A-Za-z0-9_./{}-]+)',block)
            require(route is not None,'Endpoint definition missing route');defined.append(route.groups())
        require(Counter(defined)==Counter(pairs),'Endpoint definitions missing/extra/duplicate registry routes')
        screens=table(section(text,'### 8.2 Screen-to-Endpoint Coverage Matrix'),'Frontend Screen');ui=table(section(text,'### 9.1 Screen Inventory'),'#')
        require(len(screens)==7 and len(ui)==7,'Missing frontend screen mappings')
        for r in screens:
            refs=set(re.findall(r'/api/v1/[\w/-]+',r['Primary Endpoint(s)']+' '+r['Secondary']));require(refs and refs<=allowed,'Screen uses undefined/no endpoint')
        # Match each screen's full endpoint set in Part9 to its canonical Part8 mapping.
        sm={r['Frontend Screen']:set(re.findall(r'/api/v1/[\w/-]+',r['Primary Endpoint(s)']+' '+r['Secondary'])) for r in screens}
        require({r['Screen'] for r in ui}==set(sm),'Screen names differ')
        for r in ui:require(set(re.findall(r'/api/v1/[\w/-]+',r['API Dependencies']))==sm[r['Screen']],f'Screen route mapping mismatch {r["Screen"]}')
        return {'registry_entries':len(pairs),'active_paths':sorted(paths),'definitions':len(defined),'screens':len(ui),'historical_blocks':starts,'mock_contracts':'Part8 JSON fixtures; separate implementation mock files do not yet exist'}
    check('V-06','All active API references, methods, definitions and screens',api)
    def approval_check():
        require(approval['current_state'] in STATES,'Invalid approval state')
        for k in ['administrative_workflow_closed','conditions_incorporated','conditions_accepted','approval_gate_passed']:require(type(approval[k]) is bool,f'Invalid approval flag {k}')
        closed=approval['current_state'] in {'Approved','Approved with conditions','Rejected'}
        require(approval['administrative_workflow_closed']==closed,'Administrative closure contradicts state')
        require(approval['approval_evidence'] is None or (isinstance(approval['approval_evidence'],str) and bool(approval['approval_evidence'].strip())),'Evidence must be a nonempty reference or null')
        require(approval['approval_gate_passed']==approval_passed(approval),'Approval gate contradicts evidence/state/accepted conditions')
        if not approval_passed(approval):
            require(all(r['Status'] in {'Planned','Blocked'} for r in rows if r['Task ID'] not in {'T-00','T-01','T-02'}),'Formal implementation task started before approval gate')
        require(normalized(by_id['T-03']['Dependencies'],'Dependencies')=='T-01(approval_gate_passed),T-02','T-03 depends on task closure instead of approval_gate_passed')
        sp=dict(specs(text));pre=sp['T-03']['Preconditions'];require('approval_gate_passed=true' in pre and 'never unlocks T-03' in pre,'T-03 precondition fails to prohibit rejected closure')
        require('Rejection closes administration but NEVER' in sp['T-01']['Definition of Done'],'T-01 DoD does not separate rejected closure from milestone success')
        require('incorporated AND accepted' in sp['T-01']['Definition of Done'],'Conditional acceptance missing from T-01 DoD')
        require('approval_gate_passed MUST be true' in text,'Release gate missing')
        require('After approval_gate_passed=true' in text,'First sprint lacks gate')
        return {'gate_logic':'consistent','runtime_gate':approval['approval_gate_passed'],'external_evidence_authenticated':False,'limitation':'Task DAG and syntax cannot prove instructor approval or enforce future execution behavior'}
    check('V-07','Separate approval-state predicate and task-unlocking contract',approval_check)
    def inference_contract():
        baseline=['item_count','item_price','freight','seller_count','product_count','purchase_hour','purchase_weekday','purchase_month','promise_days','customer_state']
        require(contract['snapshot']=='purchase_creation','Primary snapshot changed')
        require([f['name'] for f in contract['features']]==baseline,'Canonical ten-feature list/order changed')
        require(set(contract['raw_fields'])=={'purchase_timestamp','estimated_delivery_date','customer_state','items'},'Raw schema changed/missing timestamp')
        require(all(v['required'] is True for v in contract['raw_fields'].values()),'Raw mandatory flag missing')
        require(contract['lookups_required']==[],'Unexpected lookup dependency')
        require(contract['extra_fields']=='reject 422','Unknown field policy not rejecting')
        require('never server time' in contract['timestamp_policy'],'Server-time substitution allowed')
        require(set(contract['fixture'])==set(contract['raw_fields']),'Fixture field coverage differs')
        require(set(contract['fixture_expected_features'])==set(baseline),'Fixture expected vector incomplete')
        # Verify fixture arithmetic only; no product feature pipeline implemented.
        from datetime import datetime,date
        fixture=contract['fixture'];purchase=datetime.fromisoformat(fixture['purchase_timestamp']);promise=datetime.combine(date.fromisoformat(fixture['estimated_delivery_date']),datetime.min.time());items=fixture['items']
        expected={'item_count':len(items),'item_price':sum(i['price_brl'] for i in items),'freight':sum(i['freight_value_brl'] for i in items),'seller_count':len({i['seller_key'] for i in items}),'product_count':len({i['product_key'] for i in items}),'purchase_hour':purchase.hour,'purchase_weekday':purchase.weekday(),'purchase_month':purchase.month,'promise_days':(promise-purchase).total_seconds()/86400,'customer_state':fixture['customer_state']}
        require(expected==contract['fixture_expected_features'],'Frozen fixture arithmetic differs')
        endpoint=section(text,'#### Endpoint 8: Delivery Risk Prediction — purchase-v1 canonical contract')
        for n in baseline:require('`'+n+'`' in endpoint,f'Feature {n} absent from plan contract')
        require('Frozen parity tests' in endpoint,'Missing future parity acceptance criteria')
        spec=dict(specs(text))
        for tid in ['T-11','T-19','T-26','T-28','T-31']:require('purchase-v1' in spec[tid]['Acceptance Criteria'],f'{tid} contract acceptance absent')
        require('no server-time default' in text,'Frontend permits server timestamp default')
        return {'feature_count':10,'fixture_arithmetic':'verified','training_serving_pipeline_parity':'NOT IMPLEMENTED; future T-11/T-19/T-28 tests required','availability':'cart and promise snapshot assumptions, not historical proof'}
    check('V-08','Planning input/feature contract and frozen fixture arithmetic',inference_contract)
    def structure():
        parts=[int(n) for n in re.findall(r'^## Part (\d+) —',text,re.M)];require(parts==list(range(1,20)),'19-part structure missing/duplicated')
        require('docs/audits/FINAL_DATASET_AUDIT_REPORT.md' in text,'Real audit report path absent')
        require(not re.search(r't00_reports/|scripts/0[1-5]_|scripts/01-05',text),'Invented audit paths remain')
        require('Completed locally' in text and 'untracked' in text,'Local completion/merge distinction missing')
        require('Procedure A' in text and 'Procedure B' in text,'Evaluation protocols absent')
        return '19 parts, actual audit paths and retained Procedure A/B; semantics also require manual review'
    check('V-09','Preserved plan structure and real audit path references',structure)
    passed=all(c['status']=='PASS' for c in checks)
    return {'checks':checks,'consistent':passed,'approval_status':'PASSED (evidence authentication still manual)' if approval_passed(approval) else 'OPEN — pending or blocked; formal implementation not unlocked','exit_code':0 if passed else 1}


def validate(csv_path: Path, plan_path: Path, schedule_path: Path, approval_path: Path, contract_path: Path) -> dict:
    try:
        with csv_path.open(newline='',encoding='utf-8') as stream:
            reader=csv.DictReader(stream);rows=list(reader);columns=reader.fieldnames
        return validate_documents(rows,plan_path.read_text(),json.loads(schedule_path.read_text()),json.loads(approval_path.read_text()),json.loads(contract_path.read_text()),columns)
    except (OSError,ValueError,TypeError) as exc:
        return {'consistent':False,'exit_code':1,'checks':[{'id':'INPUT','status':'FAIL','title':'Input availability/parsing','evidence':str(exc)}],'approval_status':'NOT VERIFIED'}


def main(argv: list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',type=Path,default=DEFAULT_DIR/'OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv')
    parser.add_argument('--plan',type=Path,default=DEFAULT_DIR/'OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md')
    parser.add_argument('--schedule',type=Path,default=DEFAULT_DIR/'schedule_config_v2_2.json')
    parser.add_argument('--approval',type=Path,default=DEFAULT_DIR/'approval_state_v2_2.json')
    parser.add_argument('--contract',type=Path,default=DEFAULT_DIR/'delivery_contract_v2_2.json')
    parser.add_argument('--require-approval',action='store_true',help='Exit 2 if consistent but external approval gate is not passed')
    args=parser.parse_args(argv);result=validate(args.csv,args.plan,args.schedule,args.approval,args.contract)
    if result['consistent'] and args.require_approval and not approval_passed(json.loads(args.approval.read_text())):result['exit_code']=2
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result['exit_code']

if __name__=='__main__':raise SystemExit(main())
