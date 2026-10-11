"""Bounded feasibility baselines; no model files are saved."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import average_precision_score,roc_auc_score,precision_score,recall_score,f1_score,brier_score_loss
from core import load,safe_order_frame,delivery_eligible,calendar_late
ROOT=Path(__file__).resolve().parents[2]

def metrics(y,p):
    pred=p>=.5; k=max(1,int(np.ceil(len(y)*.1))); top=np.argsort(-p,kind='stable')[:k]
    return {'n':len(y),'positive':int(y.sum()),'average_precision':float(average_precision_score(y,p)),'roc_auc':float(roc_auc_score(y,p)),'precision_05':float(precision_score(y,pred,zero_division=0)),'recall_05':float(recall_score(y,pred,zero_division=0)),'f1_05':float(f1_score(y,pred,zero_division=0)),'brier':float(brier_score_loss(y,p)),'top_10pct_recall':float(np.asarray(y)[top].sum()/y.sum())}

def partitions(time,known,cfg):
    a=pd.Timestamp(cfg['train_end']);b=pd.Timestamp(cfg['validation_end']);c=pd.Timestamp(cfg['test_end'])
    return {'train':time.lt(a)&known.lt(a),'validation':time.ge(a)&time.lt(b)&known.lt(b),'test':time.ge(b)&time.lt(c)&known.lt(c)}

def run():
    cfg=json.loads((ROOT/'scripts/audit/config.json').read_text()); t=load(ROOT/cfg['raw_dir']);o=safe_order_frame(t)
    reports={}
    for task in ['delivery','review']:
        eligible=delivery_eligible(o,'purchase') if task=='delivery' else o.low_score.notna()&o.review_creation.gt(o.order_purchase_timestamp)
        d=o.loc[eligible].copy(); y=calendar_late(d.order_delivered_customer_date,d.order_estimated_delivery_date).astype(int) if task=='delivery' else d.low_score.astype(int)
        d['purchase_hour']=d.order_purchase_timestamp.dt.hour;d['purchase_weekday']=d.order_purchase_timestamp.dt.dayofweek;d['purchase_month']=d.order_purchase_timestamp.dt.month
        d['promise_days']=(d.order_estimated_delivery_date-d.order_purchase_timestamp).dt.total_seconds()/86400
        # Final payment/installment records deliberately excluded: no availability timestamps.
        numeric=['item_count','item_price','freight','seller_count','product_count','purchase_hour','purchase_weekday','purchase_month','promise_days']
        categorical=['customer_state']
        pre=ColumnTransformer([('num',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),numeric),('cat',OneHotEncoder(handle_unknown='ignore'),categorical)])
        model=Pipeline([('pre',pre),('lr',LogisticRegression(max_iter=1000,random_state=cfg['seed']))])
        known=d.order_delivered_customer_date if task=='delivery' else d.review_answer
        masks=partitions(d.order_purchase_timestamp,known,cfg); train=masks['train']
        model.fit(d.loc[train,numeric+categorical],y[train]);dummy=DummyClassifier(strategy='prior').fit(d.loc[train,numeric],y[train])
        reports[task]={'scenario':'purchase-time retrospective proxy; static catalog and cart features assumed available','features':numeric+categorical,'label_available_before_partition_end':True,'split_counts':{k:int(v.sum()) for k,v in masks.items()},'metrics':{}}
        for split in ['validation','test']:
            m=masks[split]; reports[task]['metrics'][split]={'logistic':metrics(y[m],model.predict_proba(d.loc[m,numeric+categorical])[:,1]),'dummy':metrics(y[m],dummy.predict_proba(d.loc[m,numeric])[:,1])}
    r=t['order_reviews'].merge(t['orders'][['order_id','order_purchase_timestamp']],on='order_id',validate='many_to_one')
    r['text']=r.review_comment_message.fillna('').str.strip().str.casefold().str.replace(r'\s+',' ',regex=True)
    # Unanimous order ratings; remove all repeated normalized texts and repeated
    # orders conservatively, preventing template and duplicate-order contamination.
    unanimous=r.groupby('order_id').review_score.nunique().eq(1)
    r=r[r.text.ne('') & ~r.text.duplicated(keep=False) & ~r.order_id.duplicated(keep=False) & r.order_id.map(unanimous)].copy()
    masks=partitions(r.review_answer_timestamp,r.review_answer_timestamp,cfg); y=r.review_score.le(2).astype(int)
    model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),min_df=3,max_features=20000,sublinear_tf=True)),('lr',LogisticRegression(max_iter=1000,random_state=cfg['seed']))])
    train=masks['train'];model.fit(r.loc[train,'text'],y[train]); dummy=DummyClassifier(strategy='prior').fit(np.zeros((train.sum(),1)),y[train])
    reports['nlp']={'task':'post-review low-score detection, 1–2 versus 3–5; rating proxy not gold sentiment','split_counts':{k:int(v.sum()) for k,v in masks.items()},'excluded_all_repeated_text_and_multireview_orders':True,'metrics':{}}
    for split in ['validation','test']:
        m=masks[split];reports['nlp']['metrics'][split]={'tfidf_logistic':metrics(y[m],model.predict_proba(r.loc[m,'text'])[:,1]),'dummy':metrics(y[m],dummy.predict_proba(np.zeros((m.sum(),1)))[:,1])}
    (ROOT/cfg['output_dir']/'baselines.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))
if __name__=='__main__':run()
