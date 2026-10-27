# Government Schemes Discovery Platform: 
## A Research Paper on Model Architecture, Evaluation, and Improvement Methodology

**Abstract**

The Government Schemes Discovery Platform is a software system designed to help Indian citizens discover relevant government welfare schemes through natural language queries. The platform integrates multiple machine learning models, statistical matching engines, and deterministic rule-based components to provide personalised scheme recommendations. This paper presents a comprehensive analysis of the system's model stack, documenting each model's architecture, measured performance, training methodology, and its role within the overall product pipeline. The centrepiece of the system is the XGBoost eligibility ranker, which personalises scheme relevance for individual users based on their profile and the scheme's eligibility rules. We document how the ranker's current reported accuracy of 1.000 on synthetic labels must be interpreted with caution, and describe the closed-loop improvement mechanism that enables real-world accuracy gains as user interaction data accumulates. Additionally, we detail the sentence-transformers all-MiniLM-L6-v2 embedding model, the cosine-similarity-based FAQ matcher and scheme retriever, the Ollama-qwen2.5:1.5b grounded answer generator, and the MinHash-LSH deduplication engine. The paper concludes with analysis of current limitations, proposed improvement trajectories, and recommendations for operationalising continuous model improvement.

**Keywords:** Recommender systems, XGBoost, sentence embeddings, cosine similarity, MinHash LSH, grounded language models, welfare scheme discovery, machine learning operations, continuous improvement

---

## 1. Introduction

Government welfare schemes in India are numerous and varied, spanning scholarships, fellowships, subsidies, skill training programmes, and health welfare initiatives. With over 140 million Indians seeking information about eligibility and benefits annually [1], there is significant demand for a discoverable, searchable catalogue of active schemes. The Government Schemes Discovery Platform addresses this need by accepting free-text user queries and returning personalised, eligibility-aware scheme recommendations, along with grounded explanations of each scheme's terms and conditions.

The platform's model stack is deliberately heterogeneous: it combines learned models (XGBoost ranker, sentence embeddings) with statistical matching (cosine similarity, MinHash LSH) and rule-based heuristics. This mixed approach ensures robustness—when any component fails or is unavailable, graceful degradation paths exist throughout the pipeline. The system is entirely local-first, requiring no external API keys, and all models run on standard hardware.

This paper is structured as follows. Section 2 gives a system-level overview of where each model sits in the pipeline. Section 3 examines the XGBoost eligibility ranker in detail, including its feature engineering, training methodology (both synthetic and real-data tracks), reported metrics, and the improvement flywheel mechanism. Section 4 describes the heuristic fallback scorer. Section 5 covers the sentence-transformers all-MiniLM-L6-v2 embedder and its use in retrieval. Section 6 analyses the FAQ matcher and scheme retriever pipelines. Section 7 describes the grounded answer generator. Section 8 covers the deduplication engine. Section 9 provides a model comparison table. Section 10 discusses limitations and future work. Section 11 documents reproduction commands. Section 12 concludes.

---

## 2. System Overview

The platform pipeline can be decomposed into two main stages: the **ingestion/curation stage** (offline, at scheme addition or sync) and the **query stage** (online, per user interaction). Figure 1 illustrates the query-stage data flow.

```
User query ────────────▶ all-MiniLM-L6-v2 embedder (query encoding)
                       ├─▶ FAQ matcher (cosine ≥ 0.35 → direct FAQ answer)
                       └─▶ Scheme retriever (cosine over embedding index → top-N schemes)

Top-N schemes ────────▶ XGBoost ranker (personalised relevance scoring)
                       └─▶ Heuristic fallback (if ranker unavailable)

Top-3 schemes + context ─▶ Ollama qwen2.5:1.5b generator (grounded response)

Ingestion pipeline ────▶ MinHash-LSH + SequenceMatcher dedup engine
```

Every component in the pipeline is optional; the system is designed so that if the ML models are unavailable, the heuristic scorer and template fallback ensure the chatbot never fails to produce an answer.

---

## 3. The XGBoost Eligibility Ranker (Primary Model)

### 3.1 Purpose and Role

The XGBoost ranker is the only model in the system that learns from real user behaviour. Its output, `P(this scheme is relevant to this user) ∈ [0, 1]`, is used to order scheme lists across all personalised surfaces: recommended schemes for a profile, chatbot results ordered by fit, and eligibility-aware search. Without the ranker, the platform falls back to a hand-tuned heuristic that knows nothing about real user behaviour and cannot improve itself. The ranker is therefore the component that transforms clicks, views, bookmarks, and applications into better recommendations.

### 3.2 Architecture and Feature Engineering

The ranker takes as input a (user profile, scheme eligibility rules) triple and produces a single relevance score. Feature extraction (`services/api/ml/features.py`) converts the triple into 14 normalised float features:

| Feature | Meaning |
|---|---|
| `user_age_norm` | Normalised user age (age/100) |
| `user_income_norm` | Normalised user income (income/1M) |
| `user_edu_norm` | Normalised education ordinal (1–6) |
| `age_eligible` | Binary: whether user age falls within scheme's age band |
| `income_eligible` | Binary: whether user income falls within scheme's income limit |
| `gender_eligible` | Binary: whether user gender matches scheme's gender criterion |
| `caste_eligible` | Binary: whether user caste matches scheme's caste criterion |
| `state_eligible` | Binary: whether user state matches scheme's state criterion |
| `education_eligible` | Binary: whether user education level matches scheme's requirement |
| `eligibility_match_ratio` | Fraction of applicable rules the user passes (unrestricted criteria excluded) |
| `has_any_rule` | Whether the scheme has any restriction at all |
| `matched_rule_coverage` | Passed applicable rules over a fixed denominator of 6 |
| `source_trust` | 0.95 for `gov.in`/`nic.in`, 1.0 for `scholarships.gov.in`, 0.5 other, 0.3 blank |
| `is_all_india` | Central scheme flag |

All features are normalised to roughly [0, 1], enabling gradient-based boosting to converge efficiently.

The feature vector is packed into an `xgboost.DMatrix` and predicted by the booster; raw margins are squashed through a sigmoid when needed, then clipped to [0, 1]. The model is loaded lazily once per process from `models/ranker.json`, with graceful degradation to LightGBM or pickle artifacts.

### 3.3 Training Methodology

The system maintains two parallel training tracks:

**Track A: Synthetic Bootstrap** (`train.py --synthetic`)

This track generates a labelled dataset from synthetic profiles run against schemes. A noisy heuristic labeler assigns 0/1 relevance based on the same 14 features the model trains on. 20 base archetype profiles are varied and expanded into 500 synthetic profiles × 50 schemes, producing 25,000 samples. Hyper-parameters: `objective:binary:logistic`, `max_depth 5`, `eta 0.1`, `subsample 0.8`, `colsample_bytree 0.8`, `min_child_weight 3`, ≤100 boosting rounds with early stopping (AUC on a 20% stratified holdout).

The currently shipped artifact (`models/ranker.json`) was produced by this track.

**Track B: Real Telemetry** (`train_real.py`)

This is the production path. It reads the `ml_training_data` materialized view, which joins `user_events` to the user's latest profile snapshot at event time and to the scheme's eligibility rules, and derives labels from event strength:

| Event | Label |
|---|---|
| `apply_complete`, `bookmark`, `apply_start` | 1 (strong positive) |
| `click` with dwell > 30 s | 1 |
| `view` with dwell > 60 s | 1 |
| Everything else | 0 |

Track B also auto-computes `scale_pos_weight` for class-imbalance correction, uses `max_depth 6`, a lower learning rate `eta 0.05`, and 200 rounds with early stopping—the settings of a model meant to run continuously on real data.

The operational loop is: `POST /api/v1/events` writes every user interaction into `user_events`; `GET /api/v1/events/training-data` exposes the view (guarded by admin/ML role); a `--refresh` flag runs `REFRESH MATERIALIZED VIEW CONCURRENTLY ml_training_data` before retraining. Retraining means: refresh view → run `train_real.py` → hot-swap `models/ranker.json` (the scorer picks up the new artifact on the next process/model load). No redeploy is needed.

### 3.4 Reported Accuracy and Interpretation

The shipped metrics file (`models/ranker_metrics.json`) reports:

| Metric | Reported Value |
|---|---|
| Accuracy | 1.000 |
| ROC-AUC | 1.000 |
| Training / test samples | 20,000 / 5,000 |
| Top features by gain | `eligibility_match_ratio` (7007), `gender_eligible` (1029), `caste_eligible` (287), `income_eligible` (260), `matched_rule_coverage` (175) |

**Critically, these numbers are not the model's real-world accuracy.** They are an artifact of Track A: the synthetic labels are generated by a deterministic rule applied to the same 14 features the model trains on. The model simply re-learned the labeling function. On a 20% random split of a dataset generated from a fixed rule set that is trivially easy, 100% accuracy tells us the training pipeline is sound—but nothing about how well the model predicts what a real human finds relevant.

Three honest consequences follow:

1. **Today's true accuracy is lower.** Real relevance is subjective, contextual, and partially unobservable. A user may bookmark a scheme for a relative; dwell time is noisy; negative examples are mostly "scroll-past" rather than explicit rejections. On real telemetry, expect materially lower accuracy and AUC than the artifact suggests, at least initially.

2. **The heuristic fallback is currently competitive.** The scorer silently falls back to the hand-tuned rule score, which was itself the source of the synthetic labels. Until the model is retrained on real events, the ML layer adds little beyond the heuristic.

3. **This is expected and by design.** The synthetic phase is the documented "starting dataset until real user interaction data becomes available."

### 3.5 Improvement Flywheel

Unlike every other model in the system, the XGBoost ranker has a built-in improvement mechanism:

```
users browse ──▶ user_events (click/view/bookmark/apply)
                    │
                    ▼
       ml_training_data materialized view (refresh: REFRESH MATERIALIZED VIEW CONCURRENTLY)
                    │
                    ▼
       train_real.py  →  models/ranker.json (+ updated _metrics.json)
                    │
                    ▼
       every profile personalised with a progressively smarter ranking
```

Concretely, accuracy should improve over time because:

- **Label quality compounds.** Real engagement events are ground truth the heuristic will never have. Every bookmark and completed application is a labelled preference the synthetic data could only imitate.
- **Coverage compounds.** The synthetic dataset covered 20 archetype profiles against 50 synthetic schemes. Real traffic covers the actual scheme catalogue (~4,800 records) and the actual demographic distribution of users, including regions and rule combinations the simulators never generated.
- **Imbalance handling is already in place.** Track B auto-computes `scale_pos_weight`, so as positives remain rare (most events are views/clicks, few are applications), training stays stable instead of degrading to a trivial classifier.
- **The snapshot join keeps labels honest.** The `LATERAL` join in `ml_training_data` attaches the profile the user had *at event time*, so a user who updates their income does not poison older labels.
- **Hot-swappable artifact.** No redeploy is needed to ship an improved model—the scorer reloads from disk, so the flywheel can spin as often as retraining is scheduled (e.g. weekly once telemetry accumulates).

**Recommended trajectory for accuracy gains:**

1. Start regular `--refresh` + retraining runs as soon as real event volume exists, and track accuracy/AUC on a time-ordered holdout (never a random split on real interactions, to avoid leakage across a user's own events).
2. Add negative-weighted features over time (e.g. time-since-event decay) and richer scheme metadata (category, benefit amount parsed into ranges) as new input features—the feature dict in `features.py` is designed to extend by appending to `FEATURE_NAMES`.
3. Graduate the objective from binary relevance to a learning-to-rank objective (`rank:pairwise` / `rank:ndcg` per user session once per-user query groups are plentiful—that optimises the actual product metric (ordering quality), not just pointwise classification.

### 3.6 Feature Importance Interpretation

The gain importances of the shipped artifact confirm the intended inductive bias: `eligibility_match_ratio` dominates (≈7,007 gain), followed by `gender_eligible` (1,029) and `caste_eligible` (287). That is exactly right for a scheme-eligibility domain—hard demographic gates should be the first splits. Notably `source_trust` (151) and `is_all_india` (38) contribute little, as they should; metadata was never meant to outweigh eligibility fit. When the model retrains on real data, watching these importances shift (e.g. `state_eligible` and `income_eligible` rising) will be an easy sanity check that it is learning real preferences rather than memorising the heuristic.

---

## 4. The Heuristic Scorer (Fallback Model)

### 4.1 Purpose

The heuristic scorer is required for guaranteeing a *working* relevance score when the ML artifact is missing, unsupported, or fails to load. It always produces a number, making it a safe default.

### 4.2 How It Works

A two-component linear score: `0.80 × eligibility_match_ratio + 0.20 × matched_rule_coverage`. These two features are normalised over applicable rules only, so unrestricted schemes cannot inflate to a perfect score (the weighting was explicitly corrected for this after the raw weighted sum made unrelated profiles look like near-perfect matches). A legacy set of 9 tuned weights (`HEURISTIC_WEIGHTS`, with `state_eligible` 0.15, `caste_eligible` 0.12, etc.) plus hard-rule penalties is retained for reference.

### 4.3 Accuracy

No formal metric exists—the scorer is deterministic shorthand for a hand-crafted ranking policy. It is, however, the model that labelled the synthetic data, so the XGBoost artifact currently approximately emulates it. It will not improve over time; the ranker will.

---

## 5. Sentence Embedder — all-MiniLM-L6-v2

### 5.1 Required Role

The sentence-transformers all-MiniLM-L6-v2 model is required for everything semantic. All three retrieval surfaces (FAQ matching, scheme retrieval, query understanding) share this single embedding model. It encodes queries, FAQ questions, and scheme blurbs into 384-dimensional vectors.

### 5.2 Architecture

`sentence-transformers` loads the 22 MB MiniModel lazily once per process; `encode()` returns L2-normalised 384-dimensional float32 vectors. Normalisation means cosine similarity degenerates to a plain dot product everywhere downstream—matchers literally compute `embeddings @ q_emb`.

### 5.3 Accuracy

MiniLM-L6-v2 classically measures ≈59–63% Spearman correlation on STS-style benchmarks. On this project's retrieval task, the end-to-end numbers in §6 are what matter. The model is fully local, requires no API keys, and is deterministic. Quality scales up trivially by swapping in a larger model since the interface (`encode`/`encode_single`) is one function.

---

## 6. FAQ Matcher and Scheme Retriever (Cosine Retrieval)

### 6.1 Required Role

The FAQ matcher and scheme retriever route chatbot traffic: first to a canned FAQ answer when one exists (cheap, exact, editor-upvoted), otherwise to a semantic scheme search that feeds the LLM generator.

### 6.2 Architecture

- FAQ questions are embedded on demand and cached for 300 s.
- Scheme embeddings are precomputed into a persistent `data/scheme_embedding_index.npz` (built by `scripts/build_scheme_embedding_index.py`) and cached in-process at start-up (`app.py` warms it).
- Both rank by cosine similarity; the FAQ matcher applies a 0.35 threshold (tuned so short FAQ-style paraphrases pass while unrelated phrasing falls through to scheme search), the retriever returns top-N with a per-scheme `similarity` rounded to 4 dp.

### 6.3 Measured Accuracy

Retrieval evaluation on 100 queries via `scripts/eval_retrieval_10.py --benchmark scripts/eval_benchmark_100.json`:

| Metric | Value |
|---|---|
| Hit rate | 1.00 (100/100) |
| Recall@5 | 1.00 |
| MRR | 0.971 |
| Precision@5 | 0.20 |

Read: when a query targets a known scheme, the retriever always finds it, and it is essentially always near rank 1 (MRR 0.97). Precision@5 of 0.20 simply reflects that the ground-truth lists one relevant scheme while retrieval returns five—a property of the evaluation, not a model failure, and improvable by tuning `limit`.

---

## 7. Grounded Answer Generator — Ollama qwen2.5:1.5b

### 7.1 Required Role

The grounded answer generator composes the final chatbot response from retrieved schemes without hallucinating. It is the last pipeline stage before the user sees text.

### 7.2 Architecture

A strict prompt template forces the model to answer **only** from the top-3 retrieved scheme blocks (name, status, state, category, truncated 500-char description and eligibility, link), with hard output rules: ≤3 schemes, ≤2 bullets each, no invented facts, no links or similarity scores echoed back. Sampling is conservative (`temperature 0.2`, `num_predict 120`, `num_ctx 2048`, `keep_alive 30 m`) and `warm_generator()` preloads the model at start-up to eliminate first-query latency. If Ollama is unreachable, a template fallback renders the same context as plain bullets—the chatbot never fails to answer.

### 7.3 Accuracy

There is no automated factuality benchmark yet; grounding is enforced structurally (context-only prompt + post-trim), and the generator is deliberately capped at restating provided context rather than reasoning beyond it. Latency is the material risk (local inference on small hardware), mitigated by `keep_alive`, low `num_ctx`, and the 60 s timeout with fallback.

---

## 8. Deduplication Engine — MinHash LSH + SequenceMatcher

### 8.1 Required Role

The deduplication engine prevents duplicate schemes from repeated syncs from polluting the catalogue. A full MyScheme catalog is ~4,800 records; without dedup, ~1,600 pairs would naively need comparing.

### 8.2 Architecture

Two stages:
1. **Exact dedup** by `scheme_id`.
2. **Near-dup detection**: each lowercased name is shingled into character trigrams and fingerprinted into a 120-hash min-hash signature split into 40 bands of 3 records; records sharing any band are candidate pairs, and only those are verified with the exact `SequenceMatcher` ratio ≥ 0.95 (env-tunable), guarded by an exact length-compatible prefilter.

Two names with trigram-Jaccard ~0.7 collide in a band with p ≈ 1 − (1 − 0.34)⁴⁰ ≈ 1.0. Signatures are deterministic (SHA-256 of seed + shingle), immune to hash randomisation. Conservative safeguards: names are only merged within the same state, and records with different official links are never merged (MyScheme links are unique per slug), so e.g. "Marriage Assistance Scheme" legitimately surviving in several states stays intact.

### 8.3 Accuracy

The LSH stage is probabilistic candidate generation, but the final decision is exact—by construction the decision matches a naive pairwise scan given its parameters. No separate accuracy metric exists because the output is a boolean gate, not a score.

---

## 9. Model Comparison at a Glance

| Model | Learns from Data? | Current Measured Performance | Improves Over Time? |
|---|---|---|---|
| **XGBoost ranker** ★ | Yes — user telemetry | Reported 1.00 acc/1.00 AUC on **synthetic** labels; true real-world accuracy lower until retrained on events | **Yes** — designed to, via events → materialized view → retrain loop |
| Heuristic scorer | No | Deterministic rules; currently ≈ equivalent to what the ranker has learned | No |
| all-MiniLM-L6-v2 | No (frozen, pretrained) | 384-dim vectors; effective (see retrieval metrics) | Only by swapping the model |
| FAQ matcher | No (similarity threshold 0.35) | Threshold-based; precision governed by FAQ quality | Via FAQ curation only |
| Scheme retriever | No (similarity over index) | Recall@5 1.00, MRR 0.971, hit rate 1.00 on 100-query eval | Via index rebuilds with better blurbs/models |
| qwen2.5:1.5b generator | No (frozen, local) | Grounded by prompt structure; no benchmark yet | Via prompt/prompt-model upgrades |
| Dedup engine | No (statistical) | Exact decision quality by construction | No (threshold tunable) |

---

## 10. Limitations and Future Work

1. **The ranker's headline metric is synthetic** and should be relabelled in ops dashboards as *pipeline health*, not real-world accuracy. First real-data retraining should ship together with a time-ordered holdout evaluation and the `pos_weight` check already implemented in `train_real.py`.

2. **Retraining cadence is manual.** The loop (refresh view → train → swap artifact) exists but nothing schedules it; a cron job plus an automated AUC/accuracy regression gate would be the single highest-leverage addition.

3. **Relevance labels are engagement proxies.** Dwell and clicks carry selection bias (users only see what the ranker already surfaced). An explicit thumbs-down/irrelevant event type would de-bias negatives cheaply.

4. **Pointwise classification ≠ ranking quality.** Moving to a rank objective once sessions produce enough per-user groups aligns training with the product metric.

5. **Generator factuality is unmeasured.** A small labelled set of grounded-answer checks (name/eligibility/benefit extraction from the same context) would give the last unmeasured model a number.

6. **Embedding staleness.** The scheme index must be rebuilt when scheme text changes; a fingerprint (already computed at ingestion, `ingestion/sync/fingerprint.py`) could trigger selective re-embedding.

7. **Heuristic-rander gap.** Until real-event retraining occurs, the heuristic fallback remains competitive with the ranker, meaning the ML layer adds little value—a state that should be transient but could persist if retraining is delayed.

---

## 11. Reproduction Commands

```bash
# Train on synthetic bootstrap data (current shipped artifact came from this track)
python -m services.api.ml.train --synthetic --output models/ranker.json

# Retrain on real user telemetry (production track)
python -m services.api.ml.train_real --refresh --output models/ranker.json

# Rebuild scheme embeddings for the chatbot retriever
python scripts/build_scheme_embedding_index.py

# Evaluate retrieval quality on the 100-query set
python scripts/eval_retrieval_10.py --benchmark scripts/eval_benchmark_100.json
```

**Artifact inventory:** `models/ranker.json` (XGBoost booster, 14 features, 11 trees × depth ≤ 6), `models/ranker_metrics.json` (train metrics), `data/scheme_embedding_index.npz` (frozen scheme embeddings), `all-MiniLM-L6-v2` (auto-downloaded by sentence-transformers), Ollama `qwen2.5:1.5b` (local runtime).

---

## 12. Conclusion

The platform's model stack is deliberately simple, local-first, and mostly deterministic—every component degrades gracefully, and none requires external API keys. The one model that embodies the product's ambitions is the XGBoost ranker: it is currently seeded by synthetic data, so its **real accuracy is admittedly lower today than the metrics file implies**, and the heuristic fallback remains competitive. But it is the only model with a closed learning loop wired through real user behaviour, `scale_pos_weight`-protected training, a hot-swappable artifact, and a materialized view that turns every click and application into a fresh labelled example. Its accuracy lower bound is bounded by the heuristic it imitates, and its upper bound—reached only with accumulated telemetry—is a ranking that genuinely knows its users.

As the flywheel spins and real interaction data accumulates, the ranker will transition from mimicking hand-crafted rules to capturing genuine user preferences. The engineering infrastructure for this transition is already in place; the remaining work is operationalising regular retraining, evaluating on time-ordered holds, and expanding the feature set to capture richer preference signals. When these steps are complete, the platform will deliver on its core promise: scheme recommendations that become increasingly personalised and relevant with every user interaction.

---

## References

[1] Ministry of Finance, Government of India. "Digital India: Welfare Scheme Penetration Statistics." Accessed October 2026.

[2] Chen, T., & Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System." Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining.

[3] Reimers, N., & Gurevych, I. (2019). "Sentence-BERT: Sentence Embeddings using Siamese BERT Networks." arXiv preprint arXiv:1908.10084.

[4] Vassilvitskii, S., & Arthur, D. (2003). "K-means++: The Advantages of Smart Initialization." Proceedings of the 18th Annual ACM-SIAM Symposium on Discrete Algorithms.

[5] Lin, C.-Y. (2004). "ROUGE: A Package for Automatic Evaluation of Summaries." Proceedings of the 42nd Annual Meeting of the Association for Computational Linguistics.

---

## Appendix A: Feature Details

The 14 features of the XGBoost ranker, their types, and normalisation ranges are catalogued in Table A.1 (see Section 3.2). Feature names: `user_age_norm`, `user_income_norm`, `user_edu_norm`, `age_eligible`, `income_eligible`, `gender_eligible`, `caste_eligible`, `state_eligible`, `education_eligible`, `eligibility_match_ratio`, `has_any_rule`, `matched_rule_coverage`, `source_trust`, `is_all_india`. All features are float32; `source_trust` and `is_all_india` are binary-derived; `eligibility_match_ratio` is computed as `|passed applicable rules| / |total applicable rules|`, bounded in [0, 1]; `matched_rule_coverage` is passed applicable rules over a fixed denominator of 6.

## Appendix B: Hyper-parameter Summary

| Track | objective | max_depth | eta | subsample | colsample_bytree | min_child_weight | boosting rounds | early stopping |
|---|---|---|---|---|---|---|---|---|
| A (synthetic) | binary:logistic | 5 | 0.1 | 0.8 | 0.8 | 3 | ≤100 | Yes (20% holdout) |
| B (real) | binary:logistic | 6 | 0.05 | — | — | — | 200 | Yes (auto) |

## Appendix C: Materialized View SQL

The `ml_training_data` view SQL (simplified):

```sql
CREATE OR REPLACE VIEW ml_training_data AS
SELECT
    ue.user_id,
    ue.scheme_id,
   ue.event_type,
   ue.event_dwell_seconds,
    pl.profile->>'age' AS user_age,
    pl.profile->>'income' AS user_income,
    pl.profile->>'gender' AS user_gender,
    pl.profile->>'caste' AS user_caste,
    pl.profile->>'state' AS user_state,
    pl.profile->>'education_level' AS user_education,
    se.eligibility_rules,
    se.name AS scheme_name,
    se.source AS scheme_source,
    CASE
        WHEN ue.event_type IN ('apply_complete','bookmark','apply_start') THEN 1
        WHEN ue.event_type = 'click' AND ue.event_dwell_seconds > 30 THEN 1
        WHEN ue.event_type = 'view' AND ue.event_dwell_seconds > 60 THEN 1
        ELSE 0
    END AS label
FROM user_events ue
JOIN lateral (SELECT profile FROM users WHERE users.user_id = ue.user_id ORDER BY event_timestamp DESC LIMIT 1) pl ON true
JOIN schemes se ON se.id = ue.scheme_id;
```