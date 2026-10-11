"""Synthetic checks of label boundaries, integrity, and immutable source data."""
import sys,json
from pathlib import Path
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/audit'))
from core import calendar_late,review_labels,delivery_eligible,load,digest,FILES

def test_same_day_delivery_is_not_late():
    a=pd.Series(pd.to_datetime(['2018-01-01 20:00','2018-01-02 00:00']))
    b=pd.Series(pd.to_datetime(['2018-01-01','2018-01-01']))
    assert calendar_late(a,b).tolist()==[False,True]

def test_conflicting_reviews_are_not_arbitrarily_resolved():
    r=pd.DataFrame({'order_id':['a','a','b','b'],'review_score':[1,5,2,2],'review_creation_date':pd.to_datetime(['2018-01-01']*4),'review_answer_timestamp':pd.to_datetime(['2018-01-02']*4)})
    labels=review_labels(r)
    assert pd.isna(labels.loc['a','low_score'])
    assert labels.loc['b','low_score']==True

def test_impossible_stage_sequence_is_excluded():
    o=pd.DataFrame({'order_status':['delivered'],'order_purchase_timestamp':pd.to_datetime(['2018-01-02']),'order_approved_at':pd.to_datetime(['2018-01-01']),'order_delivered_carrier_date':pd.to_datetime(['2018-01-03']),'order_delivered_customer_date':pd.to_datetime(['2018-01-04']),'order_estimated_delivery_date':pd.to_datetime(['2018-01-05'])})
    assert delivery_eligible(o,'purchase').iloc[0]
    assert not delivery_eligible(o,'approval').iloc[0]

def test_missing_input_gives_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError,match='Missing required datasets'): load(tmp_path)

def test_raw_files_match_manifest():
    manifest=json.loads((ROOT/'data/processed/t00/raw_hashes.json').read_text())
    assert {f:digest(ROOT/'data/raw'/f) for f in FILES.values()}==manifest

def test_reported_counts_and_label_totals():
    p=json.loads((ROOT/'data/processed/t00/profiles.json').read_text())
    s=json.loads((ROOT/'data/processed/t00/statistics.json').read_text())
    assert len(p)==9
    for task in s['targets']['delivery'].values():
        if isinstance(task,dict):
            for label in task.values():
                assert label['n']==label['positive']+label['negative']
    assert s['customers']['unique_customers']<=p['customers']['rows']

def test_maturity_partitions_purge_future_labels():
    from baselines import partitions
    cfg={'train_end':'2018-01-01','validation_end':'2018-04-01','test_end':'2018-09-01'}
    time=pd.Series(pd.to_datetime(['2017-12-01','2018-02-01','2018-05-01']))
    known=pd.Series(pd.to_datetime(['2018-01-03','2018-03-01','2018-10-01']))
    masks=partitions(time,known,cfg)
    assert masks['train'].sum()==0
    assert masks['validation'].tolist()==[False,True,False]
    assert masks['test'].sum()==0

def test_safe_join_does_not_multiply_child_money():
    from core import safe_order_frame
    t={'orders':pd.DataFrame({'order_id':['a'],'customer_id':['c']}),'customers':pd.DataFrame({'customer_id':['c'],'customer_unique_id':['u']}),'order_items':pd.DataFrame({'order_id':['a','a'],'order_item_id':[1,2],'price':[10,20],'freight_value':[2,3],'seller_id':['s','s'],'product_id':['p','p']}),'order_payments':pd.DataFrame({'order_id':['a','a'],'payment_value':[15,20],'payment_installments':[1,1]}),'order_reviews':pd.DataFrame({'order_id':['a','a'],'review_score':[5,5],'review_creation_date':pd.to_datetime(['2018-01-01']*2),'review_answer_timestamp':pd.to_datetime(['2018-01-02']*2)})}
    o=safe_order_frame(t)
    assert len(o)==1
    assert o.payment.iloc[0]==35
    assert o.item_price.iloc[0]==30

def test_required_reports_and_no_raw_identifiers_exported():
    reports=list((ROOT/'docs/audits').glob('*.md'))
    assert len(reports)>=12
    import re
    for report in reports:
        assert not re.search(r'\b[a-f0-9]{32}\b',report.read_text())
    final=(ROOT/'docs/audits/FINAL_DATASET_AUDIT_REPORT.md').read_text()
    for section in ['A. Executive','B. Dataset','C. Data','D. Data','E. Predictive','F. Customer','G. Deep','H. Architecture','I. Proposed','J. Risk','K. Open','L. Master']:
        assert section in final
