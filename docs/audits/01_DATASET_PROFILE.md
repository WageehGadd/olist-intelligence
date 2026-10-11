# T-00 — 01 DATASET PROFILE

All files were fully loaded and profiled. Numeric summaries use pandas sample standard deviation and 1.5×IQR flags. Flags are screening indicators, not proof of errors; monetary floating-point residuals near zero must use cent tolerances. Identifier/ZIP numerical distributions have no business interpretation. Category summaries are limited to 15 values; review text and raw IDs are never exported. CSV blank fields are parsed as missing by pandas; whitespace-only nonnull values are separately counted. Candidate keys are hypotheses tested below, not declared constraints.

## customers

File `99,441` rows × `5` columns; 9,033,957 bytes. Full duplicate excess: 0. Candidate key ['customer_id']; duplicate key excess 0; null key rows 0.

- `customer_city`: object; missing 0 (0.0000%); whitespace 0; unique 4,119. Top categories: {"belo horizonte": 2773, "brasilia": 2131, "campinas": 1444, "curitiba": 1521, "goiania": 692, "guarulhos": 1189, "niteroi": 849, "osasco": 746, "porto alegre": 1379, "rio de janeiro": 6882, "salvador": 1245, "santo andre": 797, "santos": 713, "sao bernardo do campo": 938, "sao paulo": 15540}.
- `customer_id`: object; missing 0 (0.0000%); whitespace 0; unique 99,441.
- `customer_state`: object; missing 0 (0.0000%); whitespace 0; unique 27. Top categories: {"BA": 3380, "CE": 1336, "DF": 2140, "ES": 2033, "GO": 2020, "MA": 747, "MG": 11635, "MT": 907, "PA": 975, "PE": 1652, "PR": 5045, "RJ": 12852, "RS": 5466, "SC": 3637, "SP": 41746}.
- `customer_unique_id`: object; missing 0 (0.0000%); whitespace 0; unique 96,096.
- `customer_zip_code_prefix`: int64; missing 0 (0.0000%); whitespace 0; unique 14,994. Numeric summary: {"count": 99441, "iqr_outliers": 0, "mean": 35137.47458291851, "negative": 0, "quantiles": {"0.0": 1003.0, "0.01": 1327.0, "0.25": 11347.0, "0.5": 24416.0, "0.75": 58900.0, "0.95": 90550.0, "0.99": 97513.0, "1.0": 99990.0}, "std": 29797.938996206118, "zero": 0}.

## geolocation

File `1,000,163` rows × `5` columns; 61,273,883 bytes. Full duplicate excess: 261,831. Candidate key ['geolocation_zip_code_prefix']; duplicate key excess 981,148; null key rows 0.

- `geolocation_city`: object; missing 0 (0.0000%); whitespace 0; unique 8,011. Top categories: {"belo horizonte": 27805, "brasilia": 10470, "curitiba": 16593, "goiania": 5661, "guarulhos": 11340, "niteroi": 6534, "osasco": 7658, "porto alegre": 13521, "recife": 6168, "rio de janeiro": 62151, "salvador": 11865, "santo andre": 6863, "sao bernardo do campo": 8112, "sao paulo": 135800, "são paulo": 24918}.
- `geolocation_lat`: float64; missing 0 (0.0000%); whitespace 0; unique 717,363. Numeric summary: {"count": 1000163, "iqr_outliers": 168240, "mean": -21.17615291038396, "negative": 998827, "quantiles": {"0.0": -36.6053744107061, "0.01": -30.104535674977235, "0.25": -23.60354554038031, "0.5": -22.91937749486411, "0.75": -19.97962033957529, "0.95": -7.673935632134225, "0.99": -2.501042206708081, "1.0": 45.06593318269697}, "std": 5.715866308822852, "zero": 0}.
- `geolocation_lng`: float64; missing 0 (0.0000%); whitespace 0; unique 717,615. Numeric summary: {"count": 1000163, "iqr_outliers": 42348, "mean": -46.39054132093579, "negative": 1000160, "quantiles": {"0.0": -101.46676644931476, "0.01": -57.65070011329355, "0.25": -48.573172180526896, "0.5": -46.63787866960149, "0.75": -43.7677088028139, "0.95": -38.50438614872029, "0.99": -34.93864131076286, "1.0": 121.10539381057764}, "std": 4.269748306619603, "zero": 0}.
- `geolocation_state`: object; missing 0 (0.0000%); whitespace 0; unique 27. Top categories: {"BA": 36045, "CE": 11674, "DF": 12986, "ES": 16748, "GO": 20139, "MG": 126336, "MS": 10431, "MT": 12031, "PA": 10853, "PE": 16432, "PR": 57859, "RJ": 121169, "RS": 61851, "SC": 38328, "SP": 404268}.
- `geolocation_zip_code_prefix`: int64; missing 0 (0.0000%); whitespace 0; unique 19,015. Numeric summary: {"count": 1000163, "iqr_outliers": 0, "mean": 36574.16646586607, "negative": 0, "quantiles": {"0.0": 1001.0, "0.01": 1318.0, "0.25": 11075.0, "0.5": 26530.0, "0.75": 63504.0, "0.95": 91750.0, "0.99": 98010.0, "1.0": 99990.0}, "std": 30549.335710319865, "zero": 0}.

## order_items

File `112,650` rows × `7` columns; 15,438,671 bytes. Full duplicate excess: 0. Candidate key ['order_id', 'order_item_id']; duplicate key excess 0; null key rows 0.

- `freight_value`: float64; missing 0 (0.0000%); whitespace 0; unique 6,999. Numeric summary: {"count": 112650, "iqr_outliers": 12134, "mean": 19.990319928983578, "negative": 0, "quantiles": {"0.0": 0.0, "0.01": 4.4198, "0.25": 13.08, "0.5": 16.26, "0.75": 21.15, "0.95": 45.12, "0.99": 84.52, "1.0": 409.68}, "std": 15.806405412297083, "zero": 383}.
- `order_id`: object; missing 0 (0.0000%); whitespace 0; unique 98,666.
- `order_item_id`: int64; missing 0 (0.0000%); whitespace 0; unique 21. Numeric summary: {"count": 112650, "iqr_outliers": 13984, "mean": 1.1978339991122948, "negative": 0, "quantiles": {"0.0": 1.0, "0.01": 1.0, "0.25": 1.0, "0.5": 1.0, "0.75": 1.0, "0.95": 2.0, "0.99": 4.0, "1.0": 21.0}, "std": 0.7051240313951733, "zero": 0}.
- `price`: float64; missing 0 (0.0000%); whitespace 0; unique 5,968. Numeric summary: {"count": 112650, "iqr_outliers": 8427, "mean": 120.65373901464716, "negative": 0, "quantiles": {"0.0": 0.85, "0.01": 9.99, "0.25": 39.9, "0.5": 74.99, "0.75": 134.9, "0.95": 349.9, "0.99": 890.0, "1.0": 6735.0}, "std": 183.63392805025939, "zero": 0}.
- `product_id`: object; missing 0 (0.0000%); whitespace 0; unique 32,951.
- `seller_id`: object; missing 0 (0.0000%); whitespace 0; unique 3,095.
- `shipping_limit_date`: datetime64[ns]; missing 0 (0.0000%); whitespace 0; unique 93,318. Range 2016-09-19 00:15:34 → 2020-04-09 22:35:08.

## order_payments

File `103,886` rows × `5` columns; 5,777,138 bytes. Full duplicate excess: 0. Candidate key ['order_id', 'payment_sequential']; duplicate key excess 0; null key rows 0.

- `order_id`: object; missing 0 (0.0000%); whitespace 0; unique 99,440.
- `payment_installments`: int64; missing 0 (0.0000%); whitespace 0; unique 24. Numeric summary: {"count": 103886, "iqr_outliers": 6313, "mean": 2.853348863176944, "negative": 0, "quantiles": {"0.0": 0.0, "0.01": 1.0, "0.25": 1.0, "0.5": 1.0, "0.75": 4.0, "0.95": 10.0, "0.99": 10.0, "1.0": 24.0}, "std": 2.6870506738564797, "zero": 2}.
- `payment_sequential`: int64; missing 0 (0.0000%); whitespace 0; unique 29. Numeric summary: {"count": 103886, "iqr_outliers": 4526, "mean": 1.0926785129853878, "negative": 0, "quantiles": {"0.0": 1.0, "0.01": 1.0, "0.25": 1.0, "0.5": 1.0, "0.75": 1.0, "0.95": 1.0, "0.99": 3.0, "1.0": 29.0}, "std": 0.7065837791949956, "zero": 0}.
- `payment_type`: object; missing 0 (0.0000%); whitespace 0; unique 5. Top categories: {"boleto": 19784, "credit_card": 76795, "debit_card": 1529, "not_defined": 3, "voucher": 5775}.
- `payment_value`: float64; missing 0 (0.0000%); whitespace 0; unique 29,077. Numeric summary: {"count": 103886, "iqr_outliers": 7981, "mean": 154.10038041699553, "negative": 0, "quantiles": {"0.0": 0.0, "0.01": 6.69, "0.25": 56.79, "0.5": 100.0, "0.75": 171.8375, "0.95": 437.635, "0.99": 1039.9164999999994, "1.0": 13664.08}, "std": 217.49406386472435, "zero": 9}.

## order_reviews

File `99,224` rows × `7` columns; 14,451,670 bytes. Full duplicate excess: 0. Candidate key ['review_id']; duplicate key excess 814; null key rows 0.

- `order_id`: object; missing 0 (0.0000%); whitespace 0; unique 98,673.
- `review_answer_timestamp`: datetime64[ns]; missing 0 (0.0000%); whitespace 0; unique 98,248. Range 2016-10-07 18:32:28 → 2018-10-29 12:27:35.
- `review_comment_message`: object; missing 58,247 (58.7025%); whitespace 27; unique 36,159.
- `review_comment_title`: object; missing 87,656 (88.3415%); whitespace 2; unique 4,527.
- `review_creation_date`: datetime64[ns]; missing 0 (0.0000%); whitespace 0; unique 636. Range 2016-10-02 00:00:00 → 2018-08-31 00:00:00.
- `review_id`: object; missing 0 (0.0000%); whitespace 0; unique 98,410.
- `review_score`: int64; missing 0 (0.0000%); whitespace 0; unique 5. Numeric summary: {"count": 99224, "iqr_outliers": 14575, "mean": 4.08642062404257, "negative": 0, "quantiles": {"0.0": 1.0, "0.01": 1.0, "0.25": 4.0, "0.5": 5.0, "0.75": 5.0, "0.95": 5.0, "0.99": 5.0, "1.0": 5.0}, "std": 1.3475791311150982, "zero": 0}.

## orders

File `99,441` rows × `8` columns; 17,654,914 bytes. Full duplicate excess: 0. Candidate key ['order_id']; duplicate key excess 0; null key rows 0.

- `customer_id`: object; missing 0 (0.0000%); whitespace 0; unique 99,441.
- `order_approved_at`: datetime64[ns]; missing 160 (0.1609%); whitespace 0; unique 90,733. Range 2016-09-15 12:16:38 → 2018-09-03 17:40:06.
- `order_delivered_carrier_date`: datetime64[ns]; missing 1,783 (1.7930%); whitespace 0; unique 81,018. Range 2016-10-08 10:34:01 → 2018-09-11 19:48:28.
- `order_delivered_customer_date`: datetime64[ns]; missing 2,965 (2.9817%); whitespace 0; unique 95,664. Range 2016-10-11 13:46:32 → 2018-10-17 13:22:46.
- `order_estimated_delivery_date`: datetime64[ns]; missing 0 (0.0000%); whitespace 0; unique 459. Range 2016-09-30 00:00:00 → 2018-11-12 00:00:00.
- `order_id`: object; missing 0 (0.0000%); whitespace 0; unique 99,441.
- `order_purchase_timestamp`: datetime64[ns]; missing 0 (0.0000%); whitespace 0; unique 98,875. Range 2016-09-04 21:15:19 → 2018-10-17 17:30:18.
- `order_status`: object; missing 0 (0.0000%); whitespace 0; unique 8. Top categories: {"approved": 2, "canceled": 625, "created": 5, "delivered": 96478, "invoiced": 314, "processing": 301, "shipped": 1107, "unavailable": 609}.

## products

File `32,951` rows × `9` columns; 2,379,446 bytes. Full duplicate excess: 0. Candidate key ['product_id']; duplicate key excess 0; null key rows 0.

- `product_category_name`: object; missing 610 (1.8512%); whitespace 0; unique 73. Top categories: {"automotivo": 1900, "bebes": 919, "beleza_saude": 2444, "brinquedos": 1411, "cama_mesa_banho": 3029, "cool_stuff": 789, "esporte_lazer": 2867, "fashion_bolsas_e_acessorios": 849, "informatica_acessorios": 1639, "moveis_decoracao": 2657, "papelaria": 849, "perfumaria": 868, "relogios_presentes": 1329, "telefonia": 1134, "utilidades_domesticas": 2335}.
- `product_description_lenght`: float64; missing 610 (1.8512%); whitespace 0; unique 2,960. Numeric summary: {"count": 32341, "iqr_outliers": 2078, "mean": 771.4952846232337, "negative": 0, "quantiles": {"0.0": 4.0, "0.01": 84.0, "0.25": 339.0, "0.5": 595.0, "0.75": 972.0, "0.95": 2063.0, "0.99": 3286.199999999997, "1.0": 3992.0}, "std": 635.1152246349538, "zero": 0}.
- `product_height_cm`: float64; missing 2 (0.0061%); whitespace 0; unique 102. Numeric summary: {"count": 32949, "iqr_outliers": 1892, "mean": 16.937661234028347, "negative": 0, "quantiles": {"0.0": 2.0, "0.01": 2.0, "0.25": 8.0, "0.5": 13.0, "0.75": 21.0, "0.95": 44.0, "0.99": 69.0, "1.0": 105.0}, "std": 13.637554061749494, "zero": 0}.
- `product_id`: object; missing 0 (0.0000%); whitespace 0; unique 32,951.
- `product_length_cm`: float64; missing 2 (0.0061%); whitespace 0; unique 99. Numeric summary: {"count": 32949, "iqr_outliers": 1380, "mean": 30.81507784758263, "negative": 0, "quantiles": {"0.0": 7.0, "0.01": 16.0, "0.25": 18.0, "0.5": 25.0, "0.75": 38.0, "0.95": 65.0, "0.99": 100.0, "1.0": 105.0}, "std": 16.914458054065967, "zero": 0}.
- `product_name_lenght`: float64; missing 610 (1.8512%); whitespace 0; unique 66. Numeric summary: {"count": 32341, "iqr_outliers": 290, "mean": 48.47694876472589, "negative": 0, "quantiles": {"0.0": 5.0, "0.01": 20.0, "0.25": 42.0, "0.5": 51.0, "0.75": 57.0, "0.95": 60.0, "0.99": 63.0, "1.0": 76.0}, "std": 10.245740725237239, "zero": 0}.
- `product_photos_qty`: float64; missing 610 (1.8512%); whitespace 0; unique 19. Numeric summary: {"count": 32341, "iqr_outliers": 849, "mean": 2.1889861166939797, "negative": 0, "quantiles": {"0.0": 1.0, "0.01": 1.0, "0.25": 1.0, "0.5": 1.0, "0.75": 3.0, "0.95": 6.0, "0.99": 8.0, "1.0": 20.0}, "std": 1.7367656379315446, "zero": 0}.
- `product_weight_g`: float64; missing 2 (0.0061%); whitespace 0; unique 2,204. Numeric summary: {"count": 32949, "iqr_outliers": 4551, "mean": 2276.4724877841513, "negative": 0, "quantiles": {"0.0": 0.0, "0.01": 60.0, "0.25": 300.0, "0.5": 700.0, "0.75": 1900.0, "0.95": 10850.0, "0.99": 22538.00000000001, "1.0": 40425.0}, "std": 4282.038730977007, "zero": 4}.
- `product_width_cm`: float64; missing 2 (0.0061%); whitespace 0; unique 95. Numeric summary: {"count": 32949, "iqr_outliers": 912, "mean": 23.196728277034204, "negative": 0, "quantiles": {"0.0": 6.0, "0.01": 11.0, "0.25": 15.0, "0.5": 20.0, "0.75": 30.0, "0.95": 47.0, "0.99": 63.0, "1.0": 118.0}, "std": 12.079047453227835, "zero": 0}.

## sellers

File `3,095` rows × `4` columns; 174,703 bytes. Full duplicate excess: 0. Candidate key ['seller_id']; duplicate key excess 0; null key rows 0.

- `seller_city`: object; missing 0 (0.0000%); whitespace 0; unique 611. Top categories: {"belo horizonte": 68, "campinas": 41, "curitiba": 127, "guarulhos": 50, "ibitinga": 49, "maringa": 40, "osasco": 32, "porto alegre": 28, "ribeirao preto": 52, "rio de janeiro": 96, "santo andre": 45, "sao bernardo do campo": 32, "sao jose do rio preto": 33, "sao paulo": 694, "sorocaba": 32}.
- `seller_id`: object; missing 0 (0.0000%); whitespace 0; unique 3,095.
- `seller_state`: object; missing 0 (0.0000%); whitespace 0; unique 23. Top categories: {"BA": 19, "CE": 13, "DF": 30, "ES": 23, "GO": 40, "MG": 244, "MS": 5, "PB": 6, "PE": 9, "PR": 349, "RJ": 171, "RN": 5, "RS": 129, "SC": 190, "SP": 1849}.
- `seller_zip_code_prefix`: int64; missing 0 (0.0000%); whitespace 0; unique 2,246. Numeric summary: {"count": 3095, "iqr_outliers": 0, "mean": 32291.059450726978, "negative": 0, "quantiles": {"0.0": 1001.0, "0.01": 1139.94, "0.25": 7093.5, "0.5": 14940.0, "0.75": 64552.5, "0.95": 89290.09999999999, "0.99": 95900.0, "1.0": 99730.0}, "std": 32713.453829509002, "zero": 0}.

## translation

File `71` rows × `2` columns; 2,613 bytes. Full duplicate excess: 0. Candidate key ['product_category_name']; duplicate key excess 0; null key rows 0.

- `product_category_name`: object; missing 0 (0.0000%); whitespace 0; unique 71. Top categories: {"alimentos": 1, "artes": 1, "beleza_saude": 1, "casa_construcao": 1, "construcao_ferramentas_iluminacao": 1, "construcao_ferramentas_seguranca": 1, "fashion_esporte": 1, "fashion_underwear_e_moda_praia": 1, "industria_comercio_e_negocios": 1, "instrumentos_musicais": 1, "livros_interesse_geral": 1, "livros_tecnicos": 1, "moveis_quarto": 1, "moveis_sala": 1, "pcs": 1}.
- `product_category_name_english`: object; missing 0 (0.0000%); whitespace 0; unique 71. Top categories: {"art": 1, "books_general_interest": 1, "books_technical": 1, "computers": 1, "construction_tools_lights": 1, "construction_tools_safety": 1, "fashion_sport": 1, "fashion_underwear_beach": 1, "food": 1, "furniture_bedroom": 1, "furniture_living_room": 1, "health_beauty": 1, "home_construction": 1, "industry_commerce_and_business": 1, "musical_instruments": 1}.

## Catalog and financial screening

```json
{
  "product_nonpositive": {
    "product_weight_g": 4,
    "product_length_cm": 0,
    "product_height_cm": 0,
    "product_width_cm": 0
  },
  "payment_installments": {
    "0": 2,
    "1": 52546,
    "2": 12413,
    "3": 10461,
    "4": 7098,
    "5": 5239,
    "6": 3920,
    "7": 1626,
    "8": 4268,
    "9": 644,
    "10": 5328,
    "11": 23,
    "12": 133,
    "13": 16,
    "14": 15,
    "15": 74,
    "16": 5,
    "17": 8,
    "18": 27,
    "20": 17,
    "21": 3,
    "22": 1,
    "23": 1,
    "24": 18
  },
  "payment_types": {
    "credit_card": 76795,
    "boleto": 19784,
    "voucher": 5775,
    "debit_card": 1529,
    "not_defined": 3
  },
  "item_feature_missingness": {
    "product_category_name": {
      "item_missing": 1603,
      "orders_any_missing": 1451
    },
    "product_weight_g": {
      "item_missing": 18,
      "orders_any_missing": 16
    },
    "product_length_cm": {
      "item_missing": 18,
      "orders_any_missing": 16
    },
    "product_height_cm": {
      "item_missing": 18,
      "orders_any_missing": 16
    },
    "product_width_cm": {
      "item_missing": 18,
      "orders_any_missing": 16
    },
    "distance_km": {
      "item_missing": 555,
      "orders_any_missing": 494
    }
  },
  "distance_km": {
    "count": 112095,
    "mean": 596.6828471753226,
    "std": 588.864635434508,
    "quantiles": {
      "0.0": 0.0,
      "0.01": 5.712493518220994,
      "0.25": 183.07750339063978,
      "0.5": 431.7097257224985,
      "0.75": 791.8789380771076,
      "0.95": 2089.847006799731,
      "0.99": 2478.7491983217933,
      "1.0": 3579.262050348394
    },
    "negative": 0,
    "zero": 26,
    "iqr_outliers": 8610
  }
}
```
## Provenance and license

Source: [Olist Kaggle dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), checked 2026-10-10. Local file SHA-256 hashes identify this audit snapshot; they do not prove it is an unmodified publisher release, and download/version metadata was not supplied. Publisher page was accessible but its dynamic license field did not render in the browsing tool. CC BY-NC-SA 4.0 is the reported dataset license in available search metadata/independent references, but primary publisher metadata confirmation remains an explicit release gate. Do not treat this audit as a definitive licensing determination.

If confirmed, [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) requires credit, license link, indication of changes, noncommercial use and compatible sharing of adaptations. Public access does not mean unrestricted redistribution. Keep raw data and generated derivatives out of Git, link the publisher, and verify terms before publishing data, review examples or commercial services. Model-card licensing does not override dataset obligations.
