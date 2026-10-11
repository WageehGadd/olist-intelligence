"""Read-only Olist computations; outputs contain aggregates only."""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

FILES = {n: f'olist_{n}_dataset.csv' for n in ['customers','geolocation','order_items','order_payments','order_reviews','orders','products','sellers']}
FILES['translation'] = 'product_category_name_translation.csv'
KEYS = {'customers':['customer_id'],'orders':['order_id'],'products':['product_id'],'sellers':['seller_id'],'order_items':['order_id','order_item_id'],'order_payments':['order_id','payment_sequential'],'order_reviews':['review_id'],'translation':['product_category_name'],'geolocation':['geolocation_zip_code_prefix']}

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def load(raw: Path) -> dict[str,pd.DataFrame]:
    missing = [f for f in FILES.values() if not (raw/f).is_file()]
    if missing: raise FileNotFoundError(f'Missing required datasets: {missing}')
    tables = {}
    for name,file in FILES.items():
        df = pd.read_csv(raw/file)
        for c in df.columns:
            if 'timestamp' in c or c.endswith('_date') or c == 'shipping_limit_date' or c == 'order_approved_at':
                df[c] = pd.to_datetime(df[c], errors='raise')
        tables[name] = df
    return tables

def distribution(s: pd.Series) -> dict:
    x=s.dropna()
    if not len(x): return {'count':0}
    q=x.quantile([0,.01,.25,.5,.75,.95,.99,1])
    iqr=q.loc[.75]-q.loc[.25]
    return {'count':len(x),'mean':float(x.mean()),'std':float(x.std()),'quantiles':{str(k):float(v) for k,v in q.items()},'negative':int((x<0).sum()),'zero':int((x==0).sum()),'iqr_outliers':int(((x<q.loc[.25]-1.5*iqr)|(x>q.loc[.75]+1.5*iqr)).sum())}

def profile(name: str, df: pd.DataFrame, path: Path) -> dict:
    cols={}
    for c in df:
        s=df[c]; text=s.astype('string'); blank=text.str.fullmatch(r'\s*',na=False)
        p={'dtype':str(s.dtype),'missing':int(s.isna().sum()),'missing_pct':float(s.isna().mean()*100),'whitespace_only':int(blank.sum()),'unique':int(s.nunique())}
        if pd.api.types.is_datetime64_any_dtype(s): p.update(min=str(s.min()),max=str(s.max()))
        elif pd.api.types.is_numeric_dtype(s): p['numeric']=distribution(s)
        elif not c.endswith('_id') and 'comment' not in c:
            p['top_categories']={str(k):int(v) for k,v in s.value_counts().head(15).items()}
        cols[c]=p
    key=KEYS[name]
    return {'rows':len(df),'columns':len(df.columns),'bytes':path.stat().st_size,'sha256':digest(path),'full_duplicates':int(df.duplicated().sum()),'candidate_key':key,'key_null_rows':int(df[key].isna().any(axis=1).sum()),'duplicate_key_excess':int(df.duplicated(key).sum()),'column_profile':cols}

def review_labels(reviews: pd.DataFrame) -> pd.DataFrame:
    """Conservative label: retain only orders with unanimous observed score.

    No arbitrary latest/mean score tie-breaking. First review creation is the
    conservative label-availability boundary; score becomes known at answer.
    """
    g=reviews.groupby('order_id')
    r=g.agg(review_count=('review_score','size'),score_count=('review_score','nunique'),score=('review_score','first'),review_creation=('review_creation_date','min'),review_answer=('review_answer_timestamp','max'))
    r['low_score']=r['score'].le(2).where(r['score_count'].eq(1))
    return r

def safe_order_frame(t: dict) -> pd.DataFrame:
    i=t['order_items'].groupby('order_id').agg(item_count=('order_item_id','size'),item_price=('price','sum'),freight=('freight_value','sum'),seller_count=('seller_id','nunique'),product_count=('product_id','nunique'))
    p=t['order_payments'].groupby('order_id').agg(payment=('payment_value','sum'),payment_records=('payment_value','size'),installments_max=('payment_installments','max'))
    o=t['orders'].merge(t['customers'],on='customer_id',validate='one_to_one')
    return o.merge(i,on='order_id',how='left',validate='one_to_one').merge(p,on='order_id',how='left',validate='one_to_one').merge(review_labels(t['order_reviews']),on='order_id',how='left',validate='one_to_one')

def target_summary(y: pd.Series) -> dict:
    y=y.dropna().astype(bool)
    return {'n':len(y),'positive':int(y.sum()),'negative':int((~y).sum()),'positive_pct':float(y.mean()*100) if len(y) else None}

def delivery_eligible(o: pd.DataFrame, stage: str) -> pd.Series:
    purchase=o.order_purchase_timestamp; actual=o.order_delivered_customer_date
    valid=o.order_status.eq('delivered') & actual.notna() & o.order_estimated_delivery_date.notna() & actual.ge(purchase)
    if stage in ['approval','carrier']:
        valid &= o.order_approved_at.notna() & o.order_approved_at.ge(purchase) & o.order_approved_at.le(actual)
    if stage == 'carrier': valid &= o.order_delivered_carrier_date.notna() & o.order_delivered_carrier_date.ge(o.order_approved_at) & o.order_delivered_carrier_date.le(actual)
    return valid

def calendar_late(actual: pd.Series, estimate: pd.Series) -> pd.Series:
    return actual.dt.normalize().gt(estimate.dt.normalize())
