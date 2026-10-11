"""Synthetic mutation tests: critical inconsistencies fail both API and CLI."""
import copy,csv,importlib.util,json,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];DIR=ROOT/'docs/planning';SCRIPT=ROOT/'scripts/planning/validate_master_plan_v2_2.py'
spec=importlib.util.spec_from_file_location('master_validator',SCRIPT);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

@pytest.fixture
def package():
    rows=list(csv.DictReader((DIR/'OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv').open()))
    text=(DIR/'OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md').read_text()
    configs=[json.loads((DIR/name).read_text()) for name in ['schedule_config_v2_2.json','approval_state_v2_2.json','delivery_contract_v2_2.json']]
    return rows,text,*configs

def execute(package):return v.validate_documents(*package)

def mutate(name,package):
    rows,text,schedule,approval,contract=copy.deepcopy(package)
    if name=='incorrect_owner_hours':
        line=next(line for line in text.splitlines() if line.startswith('| T-01 | Concept Brief'))
        replacement=line.replace('| 6 | T-00 |','| 7 | T-00 |');assert replacement!=line;text=text.replace(line,replacement,1)
    elif name=='missing_dag_edge':
        assert '    T39 --> T40\n' in text;text=text.replace('    T39 --> T40\n','',1)
    elif name=='phantom_route':text+='\nActive mock request: POST /api/v1/predict/unregistered-forecast\n'
    elif name=='missing_task':rows=[r for r in rows if r['Task ID']!='T-12']
    elif name=='duplicate_task':rows.append(copy.deepcopy(rows[1]))
    elif name=='mandatory_optional_dependency':next(r for r in rows if r['Task ID']=='T-04')['Dependencies']+=' , T-12'
    elif name=='contradictory_owner':
        line=next(line for line in text.splitlines() if line.startswith('| T-01 | Concept Brief'));text=text.replace(line,line.replace('| Wageeh |','| Rana |'),1)
    elif name=='invalid_status':rows[1]['Status']='Magically finished'
    elif name=='incorrect_schedule_total':
        line=next(line for line in text.splitlines() if line.startswith('| 6-week mandatory |'));text=text.replace(line,line.replace('| 460.80 |','| 461.80 |'),1)
    elif name=='missing_registry_entry':
        text='\n'.join(line for line in text.splitlines() if not line.startswith('| 7 | GET | `/api/v1/analytics/sellers`'))+'\n'
    elif name=='extra_dag_edge':text=text.replace('    T39 --> T40','    T39 --> T40\n    T00 --> T40',1)
    elif name=='cycle':rows[0]['Dependencies']='T-40'
    elif name=='bad_summary_total':text=text.replace('| Owner implementation hours | 358 |','| Owner implementation hours | 359 |',1)
    elif name=='bad_member_scope':text=text.replace('| Wageeh | 68 | 10 | 8 | 14 |','| Wageeh | 69 | 10 | 8 | 14 |',1)
    elif name=='bad_detailed_dependency':text=text.replace('| **Dependencies** | T-01(approval_gate_passed), T-02 |','| **Dependencies** | T-01, T-02 |',1)
    elif name=='bad_method':text+='\nDELETE /api/v1/analytics/summary\n'
    elif name=='approval_bypass':approval.update(current_state='Rejected',administrative_workflow_closed=True,approval_gate_passed=True,approval_evidence='Rejected response')
    elif name=='nonfinite_hours':rows[1]['Estimated Owner Hours']='nan'
    else:raise AssertionError(name)
    return rows,text,schedule,approval,contract

MUTATIONS=[('incorrect_owner_hours','V-02'),('missing_dag_edge','V-03'),('phantom_route','V-06'),('missing_task','V-01'),('duplicate_task','V-01'),('mandatory_optional_dependency','V-03'),('contradictory_owner','V-02'),('invalid_status','V-01'),('incorrect_schedule_total','V-05'),('missing_registry_entry','V-06'),('extra_dag_edge','V-03'),('cycle','V-03'),('bad_summary_total','V-04'),('bad_member_scope','V-04'),('bad_detailed_dependency','V-02'),('bad_method','V-06'),('approval_bypass','V-07'),('nonfinite_hours','V-01')]

@pytest.mark.parametrize('name,expected',MUTATIONS)
def test_mutation_fails_expected_check_and_cli(name,expected,package,tmp_path):
    mutated=mutate(name,package);result=execute(mutated)
    assert not result['consistent'] and result['exit_code']==1
    assert any(c['id']==expected and c['status']=='FAIL' for c in result['checks'])
    rows,text,schedule,approval,contract=mutated
    ledger=tmp_path/'ledger.csv'
    with ledger.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=v.COLUMNS);writer.writeheader();writer.writerows(rows)
    plan=tmp_path/'plan.md';plan.write_text(text)
    paths=[]
    for name,obj in [('schedule',schedule),('approval',approval),('contract',contract)]:
        path=tmp_path/(name+'.json');path.write_text(json.dumps(obj));paths.extend(['--'+name,str(path)])
    process=subprocess.run([sys.executable,'-B',str(SCRIPT),'--csv',str(ledger),'--plan',str(plan),*paths],capture_output=True,text=True)
    assert process.returncode==1,process.stdout+process.stderr
    assert json.loads(process.stdout)['exit_code']==1

def test_final_package_consistent_but_approval_open(package):
    result=execute(package)
    assert result['consistent']
    assert all(c['status']=='PASS' for c in result['checks'])
    assert result['approval_status'].startswith('OPEN')

@pytest.mark.parametrize('state,closed,incorporated,accepted,evidence,expected',[
    ('Proposal prepared',False,False,False,None,False),
    ('Proposal submitted',False,False,False,None,False),
    ('Awaiting instructor response',False,False,False,None,False),
    ('Rejected',True,True,True,'response',False),
    ('Approved',True,False,False,None,False),
    ('Approved',True,False,False,'approval reference',True),
    ('Approved with conditions',True,True,False,'response',False),
    ('Approved with conditions',True,False,True,'response',False),
    ('Approved with conditions',True,True,True,None,False),
    ('Approved with conditions',True,True,True,'accepted changes reference',True),
])
def test_approval_predicate_requires_evidence_and_accepted_conditions(state,closed,incorporated,accepted,evidence,expected):
    assert v.approval_passed({'current_state':state,'administrative_workflow_closed':closed,'conditions_incorporated':incorporated,'conditions_accepted':accepted,'approval_evidence':evidence}) is expected

def test_rejected_administrative_closure_never_unlocks_implementation(package):
    rows,text,schedule,approval,contract=package
    approval.update(current_state='Rejected',administrative_workflow_closed=True,approval_gate_passed=False)
    result=v.validate_documents(rows,text,schedule,approval,contract)
    assert result['consistent'] and result['approval_status'].startswith('OPEN')

def test_require_approval_cli_exits_two():
    result=subprocess.run([sys.executable,'-B',str(SCRIPT),'--require-approval'],capture_output=True,text=True)
    assert result.returncode==2
    assert json.loads(result.stdout)['consistent'] is True

def test_unavailable_files_fail_nonzero(tmp_path):
    result=subprocess.run([sys.executable,'-B',str(SCRIPT),'--csv',str(tmp_path/'missing.csv')],capture_output=True,text=True)
    assert result.returncode==1
    assert json.loads(result.stdout)['checks'][0]['status']=='FAIL'

def test_schedule_assumption_mutation_detected(package):
    rows,text,schedule,approval,contract=package
    text=text.replace('| Hours/person/week | 12 |','| Hours/person/week | 13 |',1)
    result=v.validate_documents(rows,text,schedule,approval,contract)
    assert any(c['id']=='V-05' and c['status']=='FAIL' for c in result['checks'])

def test_arbitrary_unqualified_method_route_is_detected(package):
    rows,text,schedule,approval,contract=package
    result=v.validate_documents(rows,text+'\nPOST /brand-new-route\n',schedule,approval,contract)
    assert any(c['id']=='V-06' and c['status']=='FAIL' for c in result['checks'])

def test_missing_source_field_breaks_inference_contract(package):
    rows,text,schedule,approval,contract=package
    del contract['raw_fields']['purchase_timestamp']
    result=v.validate_documents(rows,text,schedule,approval,contract)
    assert any(c['id']=='V-08' and c['status']=='FAIL' for c in result['checks'])

def test_historical_routes_are_explicitly_excluded_not_keyword_skipped(package):
    rows,text,schedule,approval,contract=package
    # Ordinary words like "phantom" do not exempt an active route.
    result=v.validate_documents(rows,text+'\nphantom mock POST /api/v1/not-registered\n',schedule,approval,contract)
    assert any(c['id']=='V-06' and c['status']=='FAIL' for c in result['checks'])
