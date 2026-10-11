# T-00 — 07 DEEP LEARNING NLP FEASIBILITY

**Primary DL recommendation: Portuguese post-review low-rating text classification, benchmarked against TF-IDF + logistic regression.** Text is submitted evidence available after the review; it cannot predict that same review at purchase. Labels 1–2 versus 3–5 are rating proxies; 3-star exclusion and human sentiment annotation are needed for a sentiment claim. Five-star classification is harder, ordinal and optional; topic discovery/clustering are exploratory and need human Portuguese validation rather than invented complaint labels.

Measured lengths are Unicode characters and regex words, not transformer tokens. Preserve accents and negation; spelling, informal Portuguese and sarcasm need error analysis. Language proportions were not measured by a validated detector. Repeated template texts and conflicting ratings demonstrate weak supervision noise. Public reports export no review messages; deployed demos should mask names/contact patterns and manually inspect examples.

Classical baseline: train-only TF-IDF vocabulary and logistic regression. Small embedding + CNN is the fallback DL experiment, suitable for short texts; train-only vocabulary, padding and regularization, compare macro-F1/AP, do not claim improvement. LSTM/BiLSTM is possible but sequential cost and short messages give little reason to prioritize it. BERTimbau is a stronger pretrained Portuguese candidate with a 110M-parameter base model; fine-tune a classification head with short maximum length after token profiling, early stopping and GPU budget approval. A multilingual encoder is useful only if validated language diversity requires it. Parameter-efficient fine-tuning can reduce trainable weights but still requires backbone memory and a measured deployment budget. No pretrained weights or DL framework was downloaded.

Resource estimates (not measured): 110M float32 parameters are ~440 MB for weights alone; training gradients/optimizer/activations require substantially more. GPU training is preferred; CPU inference may be feasible after latency benchmarks. Small CNN may train on CPU, but actual timing remains unknown. Tabular MLP is optional: standardized numeric features and train-only categorical embeddings/one-hot, missing indicators, early stopping and fair boosted-tree comparisons. No evidence here establishes a tabular neural advantage.

Sources checked 2026-10-10: [BERTimbau model card](https://huggingface.co/neuralmind/bert-base-portuguese-cased), [authors' repository](https://github.com/neuralmind-ai/portuguese-bert). These support model identity and architecture, not performance on Olist.

```json
{
  "char_length": {
    "count": 40950,
    "iqr_outliers": 1833,
    "mean": 68.39836385836387,
    "negative": 0,
    "quantiles": {
      "0.0": 1.0,
      "0.01": 3.0,
      "0.25": 28.0,
      "0.5": 53.0,
      "0.75": 94.0,
      "0.95": 192.0,
      "0.99": 200.0,
      "1.0": 208.0
    },
    "std": 53.833227413849755,
    "zero": 0
  },
  "missing_messages": 58247,
  "no_alphabetic_character": 159,
  "nonempty_messages": 40950,
  "nonempty_titles": 11566,
  "normalized_duplicate_excess": 5952,
  "normalized_text_conflicting_scores": 487,
  "normalized_unique_messages": 34998,
  "one_or_two_word_messages": 5675,
  "text_score_distribution": {
    "1": 8744,
    "2": 2145,
    "3": 3556,
    "4": 5970,
    "5": 20535
  },
  "whitespace_only_nonnull": 27,
  "word_count_regex_not_model_tokens": {
    "count": 40950,
    "iqr_outliers": 1454,
    "mean": 11.742783882783883,
    "negative": 0,
    "quantiles": {
      "0.0": 0.0,
      "0.01": 1.0,
      "0.25": 4.0,
      "0.5": 9.0,
      "0.75": 16.0,
      "0.95": 33.0,
      "0.99": 38.0,
      "1.0": 45.0
    },
    "std": 9.656211328334217,
    "zero": 123
  }
}
```
