"""Run: .venv/bin/python -B scripts/audit/run.py; never writes raw data."""
from __future__ import annotations
import json,sys,platform
from pathlib import Path
import numpy as np
import pandas as pd
from core import *
ROOT=Path(__file__).resolve().parents[2]

def clean(x):
    if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    if isinstance(x,(np.integer,)): return int(x)
    if isinstance(x,(np.floating,float)): return float(x) if np.isfinite(x) else None
    if isinstance(x,(np.bool_,)): return bool(x)
    return x

def compute(t,cfg):
    o=safe_order_frame(t); r=t['order_reviews']; i=t['order_items']; g=t['geolocation']; result={}
    fk=[]
    for child,col,parent,pcol in [('orders','customer_id','customers','customer_id'),('order_items','order_id','orders','order_id'),('order_items','product_id','products','product_id'),('order_items','seller_id','sellers','seller_id'),('order_payments','order_id','orders','order_id'),('order_reviews','order_id','orders','order_id'),('products','product_category_name','translation','product_category_name'),('customers','customer_zip_code_prefix','geolocation','geolocation_zip_code_prefix'),('sellers','seller_zip_code_prefix','geolocation','geolocation_zip_code_prefix')]:
        s=t[child][col]; fk.append({'child':child,'column':col,'parent':parent,'null':int(s.isna().sum()),'unmatched_nonnull_rows':int((s.notna() & ~s.isin(t[parent][pcol])).sum()),'unmatched_unique':int(s[s.notna() & ~s.isin(t[parent][pcol])].nunique())})
    counts={n:t[n].groupby('order_id').size() for n in ['order_items','order_payments','order_reviews']}
    amplification=pd.DataFrame(counts).fillna(0).clip(lower=1).prod(axis=1).sum()
    discrep=(o.payment-o.item_price-o.freight).dropna()
    rg=review_labels(r)
    result['relational']={'foreign_keys':fk,'order_children':{n:{'orders_present':len(s),'multi_record_orders':int((s>1).sum()),'records_per_order':distribution(s)} for n,s in counts.items()},'naive_inner_common_order_join_rows':int(pd.DataFrame(counts).dropna().prod(axis=1).sum()),'naive_left_children_present_join_rows':int(amplification),'duplicate_order_product_excess':int(i.duplicated(['order_id','product_id']).sum()),'missing_items':int(o.item_count.isna().sum()),'missing_payments':int(o.payment.isna().sum()),'missing_reviews':int(o.score.isna().sum()),'conflicting_score_orders':int(rg.score_count.gt(1).sum()),'conflicting_binary_orders':int(r.assign(low=r.review_score.le(2)).groupby('order_id').low.nunique().gt(1).sum()),'financial_difference_brl':distribution(discrep),'financial_abs_difference_gt_1_brl':int(discrep.abs().gt(1).sum()),'financial_abs_difference_gt_001_brl':int(discrep.abs().gt(.01+1e-8).sum()),'geo_zip_count':g.geolocation_zip_code_prefix.nunique(),'geo_multiple_coordinate_zips':int(g.groupby('geolocation_zip_code_prefix')[['geolocation_lat','geolocation_lng']].nunique().max(axis=1).gt(1).sum()),'geo_invalid_global_coordinates':int((~g.geolocation_lat.between(-90,90)|~g.geolocation_lng.between(-180,180)).sum()),'geo_outside_brazil_approx_box':int((~g.geolocation_lat.between(-34,6)|~g.geolocation_lng.between(-74,-34)).sum())}
    temporal={}
    pairs=[('purchase_to_approval','order_purchase_timestamp','order_approved_at'),('approval_to_carrier','order_approved_at','order_delivered_carrier_date'),('carrier_to_delivery','order_delivered_carrier_date','order_delivered_customer_date'),('purchase_to_delivery','order_purchase_timestamp','order_delivered_customer_date'),('estimate_to_delivery','order_estimated_delivery_date','order_delivered_customer_date'),('purchase_to_review','order_purchase_timestamp','review_creation'),('review_to_answer','review_creation','review_answer')]
    for name,a,b in pairs: temporal[name]=distribution((o[b]-o[a]).dt.total_seconds()/86400)
    temporal['missing_timestamps']={c:int(o[c].isna().sum()) for c in o if pd.api.types.is_datetime64_any_dtype(o[c])}
    temporal['order_status']=o.order_status.value_counts().to_dict()
    temporal['status_actual_delivery']=pd.crosstab(o.order_status,o.order_delivered_customer_date.notna()).to_dict()
    temporal['review_row_creation_to_answer']=distribution((r.review_answer_timestamp-r.review_creation_date).dt.total_seconds()/86400)
    temporal['review_before_delivery_orders']=int((o.review_creation<o.order_delivered_customer_date).sum())
    temporal['monthly']=o.groupby(o.order_purchase_timestamp.dt.to_period('M')).agg(orders=('order_id','size'),delivered=('order_status',lambda s:s.eq('delivered').sum()),actual_delivery_known=('order_delivered_customer_date','count')).reset_index().astype({'order_purchase_timestamp':str}).to_dict('records')
    temporal['max_purchase']=str(o.order_purchase_timestamp.max()); temporal['max_delivery']=str(o.order_delivered_customer_date.max()); temporal['max_review_answer']=str(r.review_answer_timestamp.max())
    result['temporal']=temporal
    late=calendar_late(o.order_delivered_customer_date,o.order_estimated_delivery_date)
    duration=(o.order_delivered_customer_date-o.order_purchase_timestamp).dt.total_seconds()/86400
    targets={'delivery':{},'review':{}}
    for stage in ['purchase','approval','carrier']:
        mask=delivery_eligible(o,stage)
        targets['delivery'][stage]={'calendar_lateness':target_summary(late[mask]),'literal_timestamp_lateness':target_summary(o.loc[mask,'order_delivered_customer_date'].gt(o.loc[mask,'order_estimated_delivery_date'])),'over_30_days':target_summary(duration[mask].gt(cfg['duration_threshold_days']))}
    for stage,col in [('purchase','order_purchase_timestamp'),('carrier','order_delivered_carrier_date'),('post_delivery','order_delivered_customer_date')]:
        mask=o.low_score.notna() & o[col].notna() & o.review_creation.gt(o[col]) & o[col].ge(o.order_purchase_timestamp)
        targets['review'][stage]=target_summary(o.loc[mask,'low_score'])
    targets['review']['score_rows']=r.review_score.value_counts().sort_index().to_dict()
    targets['review']['score_by_status_rows']=pd.crosstab(r.merge(t['orders'][['order_id','order_status']],on='order_id',validate='many_to_one').order_status,r.review_score).to_dict()
    targets['review']['unanimous_orders']=target_summary(o.low_score)
    targets['delivery']['monthly_purchase_labels']=o.loc[delivery_eligible(o,'purchase')].assign(late=late).groupby(o.order_purchase_timestamp.dt.to_period('M')).late.agg(['size','sum','mean']).reset_index().astype({'order_purchase_timestamp':str}).to_dict('records')
    result['targets']=targets
    customer=o.groupby('customer_unique_id').agg(orders=('order_id','size'),first=('order_purchase_timestamp','min'),last=('order_purchase_timestamp','max'),monetary=('payment','sum'))
    delivered=o[o.order_status.eq('delivered')].groupby('customer_unique_id').agg(frequency=('order_id','size'),last=('order_purchase_timestamp','max'),monetary=('payment','sum'))
    anchor=pd.Timestamp('2018-09-01'); delivered['recency']=(anchor-delivered['last']).dt.total_seconds()/86400
    futures=[]
    for cutoff in cfg['customer_cutoffs']:
        cut=pd.Timestamp(cutoff); end=cut+pd.Timedelta(days=cfg['customer_horizon_days']); start=cut-pd.Timedelta(days=cfg['customer_observation_days'])
        before=o[o.order_purchase_timestamp.lt(cut)&o.order_purchase_timestamp.ge(start)]
        ids=set(before.customer_unique_id); future=o[o.order_purchase_timestamp.ge(cut)&o.order_purchase_timestamp.lt(end)&o.customer_unique_id.isin(ids)]
        spending=future.groupby('customer_unique_id').payment.sum().reindex(sorted(ids),fill_value=0)
        futures.append({'cutoff':cutoff,'observation_start':str(start.date()),'horizon_end':str(end.date()),'eligible_customers':len(ids),'future_buyers':future.customer_unique_id.nunique(),'positive_pct':100*future.customer_unique_id.nunique()/len(ids),'future_order_count':len(future),'future_recorded_payment_brl':distribution(spending),'fully_inside_conservative_purchase_coverage':end<=anchor})
    result['customers']={'unique_customers':len(customer),'repeat_customers':int(customer.orders.gt(1).sum()),'repeat_pct':float(customer.orders.gt(1).mean()*100),'orders_per_customer':distribution(customer.orders),'recorded_payment_per_customer':distribution(customer.monetary),'activity_span_days':distribution((customer['last']-customer['first']).dt.total_seconds()/86400),'delivered_customer_rfm':{c:distribution(delivered[c]) for c in ['frequency','monetary','recency']},'recency_anchor':str(anchor.date()),'cohort_sizes':customer['first'].dt.to_period('M').astype(str).value_counts().sort_index().to_dict(),'geographic_state':o.groupby('customer_state').agg(orders=('order_id','size'),customers=('customer_unique_id','nunique'),recorded_payment=('payment','sum')).to_dict('index'),'future_windows':futures}
    text=r.review_comment_message.fillna('').str.strip(); valid=text.ne(''); normalized=text.str.casefold().str.replace(r'\s+',' ',regex=True)
    words=text.str.findall(r'\b\w+\b').str.len(); chars=text.str.len()
    result['nlp']={'nonempty_messages':int(valid.sum()),'missing_messages':int(r.review_comment_message.isna().sum()),'whitespace_only_nonnull':int((r.review_comment_message.notna() & ~valid).sum()),'nonempty_titles':int(r.review_comment_title.fillna('').str.strip().ne('').sum()),'char_length':distribution(chars[valid]),'word_count_regex_not_model_tokens':distribution(words[valid]),'one_or_two_word_messages':int((valid & words.le(2)).sum()),'no_alphabetic_character':int((valid & ~text.str.contains(r'[^\W\d_]',regex=True)).sum()),'normalized_unique_messages':int(normalized[valid].nunique()),'normalized_duplicate_excess':int(normalized[valid].duplicated().sum()),'normalized_text_conflicting_scores':int(r.loc[valid].assign(text=normalized[valid]).groupby('text').review_score.nunique().gt(1).sum()),'text_score_distribution':r.loc[valid].review_score.value_counts().sort_index().to_dict()}
    return result,o

def main():
    cfg=json.loads((ROOT/'scripts/audit/config.json').read_text()); raw=ROOT/cfg['raw_dir']; out=ROOT/cfg['output_dir']; out.mkdir(parents=True,exist_ok=True)
    before={f:digest(raw/f) for f in FILES.values()}; t=load(raw)
    profiles={n:profile(n,df,raw/FILES[n]) for n,df in t.items()}
    results,o=compute(t,cfg)
    results['environment']={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'pandas':pd.__version__,'numpy':np.__version__}
    assert before=={f:digest(raw/f) for f in FILES.values()},'Raw data changed during audit!'
    for name,obj in [('profiles',profiles),('statistics',results),('raw_hashes',before)]: (out/f'{name}.json').write_text(json.dumps(clean(obj),indent=2,sort_keys=True,allow_nan=False)+'\n')
    pd.DataFrame(results['temporal']['monthly']).to_csv(out/'monthly_orders.csv',index=False)
    pd.DataFrame(results['relational']['foreign_keys']).to_csv(out/'foreign_keys.csv',index=False)
    print(json.dumps(clean({'targets':results['targets'],'customers':{k:v for k,v in results['customers'].items() if k in ['unique_customers','repeat_customers','repeat_pct','future_windows']},'nlp':results['nlp']}),indent=2))
if __name__=='__main__': main()
