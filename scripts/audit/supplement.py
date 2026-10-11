"""Additional catalog, geographic and label-sensitivity evidence."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from core import load,safe_order_frame,distribution,FILES,digest
ROOT=Path(__file__).resolve().parents[2]
def run():
 t=load(ROOT/'data/raw');o=safe_order_frame(t);i=t['order_items'];p=t['products'];g=t['geolocation'];r=t['order_reviews']
 geo=g[g.geolocation_lat.between(-34,6)&g.geolocation_lng.between(-74,-34)].drop_duplicates().groupby('geolocation_zip_code_prefix')[['geolocation_lat','geolocation_lng']].median()
 item=i.merge(p,on='product_id',validate='many_to_one').merge(t['sellers'],on='seller_id',validate='many_to_one').merge(o[['order_id','customer_zip_code_prefix']],on='order_id',validate='many_to_one')
 item=item.merge(geo.add_prefix('seller_'),left_on='seller_zip_code_prefix',right_index=True,how='left',validate='many_to_one').merge(geo.add_prefix('customer_'),left_on='customer_zip_code_prefix',right_index=True,how='left',validate='many_to_one')
 lat1=np.radians(item.seller_geolocation_lat);lat2=np.radians(item.customer_geolocation_lat);dlat=lat2-lat1;dlon=np.radians(item.customer_geolocation_lng-item.seller_geolocation_lng)
 item['distance_km']=6371*2*np.arcsin(np.sqrt((np.sin(dlat/2)**2+np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2).clip(0,1)))
 feature_missing={c:{'item_missing':int(item[c].isna().sum()),'orders_any_missing':int(item.groupby('order_id')[c].apply(lambda s:s.isna().any()).sum())} for c in ['product_category_name','product_weight_g','product_length_cm','product_height_cm','product_width_cm','distance_km']}
 data={'item_feature_missingness':feature_missing,'distance_km':distribution(item.distance_km),'product_nonpositive':{c:int(p[c].le(0).sum()) for c in ['product_weight_g','product_length_cm','product_height_cm','product_width_cm']},'payment_installments':t['order_payments'].payment_installments.value_counts().sort_index().to_dict(),'payment_types':t['order_payments'].payment_type.value_counts().to_dict(),'multi_seller_orders':int(o.seller_count.gt(1).sum()),'review_latest_answer_sensitivity':r.sort_values(['review_answer_timestamp','review_creation_date','review_id'],kind='stable').drop_duplicates('order_id',keep='last').review_score.le(2).value_counts().to_dict(),'review_creation_equal_delivery_calendar_day':int(o.review_creation.dt.normalize().eq(o.order_delivered_customer_date.dt.normalize()).sum()),'review_answer_after_delivery':int((o.review_answer>o.order_delivered_customer_date).sum()),'source_hashes':{f:digest(ROOT/'data/raw'/f) for f in FILES.values()}}
 (ROOT/'data/processed/t00/supplement.json').write_text(json.dumps(data,indent=2,default=lambda x:int(x))+'\n')
 print(json.dumps(data,indent=2,default=lambda x:int(x)))
if __name__=='__main__':run()
