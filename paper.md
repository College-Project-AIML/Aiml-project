# Models of the Scheme Discovery Platform: Architecture, Function, and Accuracy

**Document type:** Technical paper / model card compendium
**Date:** October 20, 2026
**Scope:** Every learning and similarity model currently used in this repository — the XGBoost eligibility ranker, the heuristic scoring fallback, the sentence-transformer embedding model, the FAQ matcher, the scheme retriever, the grounded LLM answer generator, and the MinHash-LSH deduplication engine.

---

## 1. Abstract

This platform helps Indian citizens discover government welfare schemes. Several distinct models cooperate to make that possible: an embedding model converts free-text questions into vectors; cosine-similarity matchers retrieve the right schemes and FAQs; a supervised XGBoost classifier personalises the ranking of schemes against a user's profile; a local LLM composes grounded answers; and a statistical string-similarity engine keeps the dataset clean during ingestion.

The centrepiece — and the model with the most room to grow — is the **XGBoost ranker**. It is trainable end-to-end from user telemetry (the `user_events` table → `ml_training_data` materialized view → `train_real.py`), which means its accuracy is not a fixed number but **a function of accumulated user interaction data**. Right now its real-world accuracy is limited, because the shipped artifact (`models/ranker.json`) was trained on **synthetic labels derived from the same heuristic rules it is meant to replace**. This paper explains why that number must be read with caution, why the model will genuinely improve over time as the feedback flywheel spins, and what engineering steps accelerate that improvement.

---

## 2. System overview: where each model sits

```
                          ┌─────────────────────────────────────────────┐
 User query ─────────────▶│ all-MiniLM-L6-v2 embedder (chatbot/)        │
                          │  ├─▶ FAQ matcher (cosine ≥ 0.35)            │
                          │  └─▶ Scheme retriever (cosine over npz      │
                          │        embedding index)                     │
                          └──────────────┬──────────────────────────────┘
                                         │ top-N candidate schemes
                                         ▼
   User profile ─────────▶┌─────────────────────────────────────────────┐
                          │ Feature extractor (ml/features.py)          │
                          │   14 normalised features                    │
                          └──────────────┬──────────────────────────────┘
                                         ▼
                          ┌─────────────────────────────────────────────┐
                          │ XGBoost ranker (models/ranker.json)         │
                          │   fallback: heuristic weighted scorer       │
                          └──────────────┬──────────────────────────────┘
                                         │ ranked schemes
                                         ▼
                          ┌─────────────────────────────────────────────┐
                          │ Ollama qwen2.5:1.5b grounded generator      │
                          │   (strict context-only answer)              │
                          └─────────────────────────────────────────────┘

 Ingestion pipeline ─────▶ MinHash-LSH + SequenceMatcher dedup engine
```

| # | Model | Technologies | Location | Role |
|---|-------|-------------|----------|------|
| 1 | **XGBoost eligibility ranker** ★ | XGBoost (`binary:logistic`), NumPy | `services/api/ml/scorer.py`, `train.py`, `train_real.py`, `ranker.py`, `features.py`; artifact `models/ranker.json` | Personalised relevance scoring of each (user, scheme) pair |
| 2 | Heuristic scorer (fallback) | Pure Python weights | `scorer.py` | Scores schemes when no ML artifact is loadable |
| 3 | Sentence embedder | `sentence-transformers/all-MiniLM-L6-v2` (22 MB, 384-dim) | `services/api/chatbot/embeddings.py` | Encodes queries, FAQ questions, scheme blurbs |
| 4 | FAQ matcher | Cosine similarity over cached FAQ embeddings | `services/api/chatbot/matcher.py` | Matches a question to a stored FAQ (threshold 0.35) |
| 5 | Scheme retriever | Cosine similarity over persisted `.npz` embedding index | `services/api/chatbot/scheme_retriever.py` | Retrieves top-N schemes for the chatbot |
| 6 | Grounded answer generator | Ollama, `qwen2.5:1.5b` (temperature 0.2) | `services/api/chatbot/generator.py` | Writes the final chatbot response, strictly from provided context |
| 7 | Dedup engine | MinHash LSH (120 hashes, 40 bands × 3) + `difflib.SequenceMatcher` | `ingestion/dedup/dedup_engine.py` | Removes exact and near-duplicate schemes at ingestion |

---

## 3. The XGBoost Ranker ★ (primary model)

### 3.1 What it is required for

Every "personalised" surface in the product — recommended schemes for a profile, chatbot results ordered by fit, eligibility-aware search — depends on this model. Its job is defined precisely:

> Given a user profile (age, income, gender, caste, state, education level) and a scheme with its parsed eligibility rules, output **P(this scheme is relevant to this user)** ∈ [0, 1], used to order the scheme list.

Without it, the platform falls back to a hand-tuned heuristic (§4) that knows nothing about real user behaviour and cannot improve itself. The ranker is therefore the model that turns *clicks, views, bookmarks and applications* into *better recommendations*, i.e. the only component that learns.

### 3.2 How it works

**Pipeline.**

1. **Feature extraction** (`features.py`) — a (profile, rules, scheme) triple is converted into 14 floats, all normalised to roughly [0, 1]:

   | Feature | Meaning |
   |---|---|
   | `user_age_norm`, `user_income_norm`, `user_edu_norm` | Normalised user attributes (age/100, income/1M, education ordinal/6) |
   | `age_eligible`, `income_eligible`, `gender_eligible`, `caste_eligible`, `state_eligible`, `education_eligible` | Per-criterion fit. Near-misses degrade gracefully (e.g. age 1 yr outside a 20-yr band still scores ≈0.95) |
   | `eligibility_match_ratio` | Fraction of *applicable* rules the user passes (unrestricted criteria are excluded, so the ratio cannot exceed 1) |
   | `has_any_rule` | Whether the scheme has any restriction at all |
   | `matched_rule_coverage` | Passed applicable rules over a fixed denominator of 6 — favours schemes *specifically* targeted at the user over schemes open to everyone |
   | `source_trust` | 0.95 for `gov.in`/`nic.in`, 1.0 for `scholarships.gov.in`, 0.5 other, 0.3 blank |
   | `is_all_india` | Central scheme flag |

2. **Scoring** (`scorer.py`) — the feature vector is packed into an `xgboost.DMatrix` and predicted by the booster; raw margins are squashed through a sigmoid when needed, then clipped to [0, 1]. The model is loaded lazily once per process from `RANKER_MODEL_PATH` (default `models/ranker.json`), with graceful degradation to LightGBM or pickle artifacts.

3. **Ranking** (`ranker.py`) — every candidate scheme is scored, annotated with `relevance_score` and human-readable `match_details` for the UI, then sorted by score (with `confidence_score` as a tiebreaker).

**Training — two tracks.**

*Track A: synthetic bootstrap (`train.py --synthetic`).* Simulated profiles are run against schemes; a noisy heuristic labeler assigns 0/1 relevance. 20 base archetype profiles are varied and expanded into 500 synthetic profiles × 50 schemes to produce the 25,000-sample dataset. Hyper-parameters: `objective:binary:logistic`, `max_depth 5`, `eta 0.1`, `subsample 0.8`, `colsample_bytree 0.8`, `min_child_weight 3`, ≤100 boosting rounds with early stopping (AUC on a 20 % stratified holdout).

*Track B: real telemetry (`train_real.py`).* The production path. It reads the `ml_training_data` materialized view, which joins `user_events` to the user's **latest profile snapshot at event time** and to the scheme's eligibility rules, and derives labels from event strength:

| Event | Label |
|---|---|
| `apply_complete`, `bookmark`, `apply_start` | 1 (strong positive) |
| `click` with dwell > 30 s | 1 |
| `view` with dwell > 60 s | 1 |
| everything else | 0 |

Track B also adds `scale_pos_weight` (automatic class-imbalance correction), a deeper `max_depth 6`, a lower learning rate `eta 0.05` and 200 rounds with early stopping — the settings of a model meant to run continuously on real data.

**Operational loop.** `POST /api/v1/events` writes every user interaction into `user_events`; `GET /api/v1/events/training-data` exposes the view (guarded by admin/ML role); a `--refresh` flag runs `REFRESH MATERIALIZED VIEW CONCURRENTLY ml_training_data` before retraining. Retraining means: refresh view → run `train_real.py` → hot-swap `models/ranker.json` (the scorer picks the new artifact up on the next process/model load).

### 3.3 Measured accuracy — and why it must be read with caution

The shipped metrics file (`models/ranker_metrics.json`) reports:

| Metric | Reported value |
|---|---|
| Accuracy | **1.000** |
| ROC-AUC | **1.000** |
| Training / test samples | 20,000 / 5,000 |
| Top features by gain | `eligibility_match_ratio` (7007), `gender_eligible` (1029), `caste_eligible` (287), `income_eligible` (260), `matched_rule_coverage` (175) |

**These numbers are not the model's real-world accuracy.** They are an artifact of Track A: the synthetic labels are generated by a deterministic rule applied to *the same 14 features the model trains on*. The model simply re-learned the labeling function, and on a 20 % random split of a dataset generated from a fixed rule set that is trivially easy. A 100 % accuracy on this split tells us the training pipeline is sound — and nothing about how well the model predicts what a *real* human finds relevant.

Three honest consequences:

1. **Today's true accuracy is lower.** Real relevance is subjective, contextual, and partially unobservable. A user may bookmark a scheme for a relative; dwell time is noisy; negative examples are mostly "scroll-past" rather than explicit rejections. On real telemetry, expect materially lower accuracy and AUC than the artifact suggests, at least initially.
2. **The heuristic fallback is currently competitive.** The scorer silently falls back to the hand-tuned rule score (§4), which was itself the source of the synthetic labels. Until the model is retrained on real events, the ML layer adds little beyond the heuristic.
3. **This is expected and by design** — the synthetic phase is the documented "starting dataset until real user interaction data becomes available."

### 3.4 Why it will get better over time

Unlike every other model in this system, the XGBoost ranker has a built-in improvement flywheel:

```
users browse ──▶ user_events (click/view/bookmark/apply)
                    │
                    ▼
       ml_training_data materialized view  (refresh: REFRESH MATERIALIZED VIEW CONCURRENTLY)
                    │
                    ▼
       train_real.py  →  models/ranker.json (+ updated _metrics.json)
                    │
                    ▼
       every profile personalised with a progressively smarter ranking
```

Concretely, accuracy should improve over time because:

- **Label quality compounds.** Real engagement events are ground truth the heuristic will never have. Every bookmark and completed application is a labelled preference the synthetic data could only imitate.
- **Coverage compounds.** The synthetic dataset covered 20 archetype profiles against 50 synthetic schemes. Real traffic covers the actual scheme catalogue (a full MyScheme catalog is ≈4,800 records) and the actual demographic distribution of users, including regions and rule combinations the simulators never generated.
- **Imbalance handling is already in place.** Track B auto-computes `scale_pos_weight`, so as positives remain rare (most events are views/clicks, few are applications), training stays stable instead of degrading to a trivial classifier.
- **The snapshot join keeps labels honest.** The `LATERAL` join in `ml_training_data` attaches the profile the user had *at event time*, so a user who updates their income does not poison older labels.
- **Hot-swappable artifact.** No redeploy is needed to ship an improved model — the scorer reloads from disk, so the flywheel can spin as often as retraining is scheduled (e.g. weekly once telemetry accumulates).

**Recommended trajectory for accuracy gains** (in rough order of payoff):

1. Start regular `--refresh` + retraining runs as soon as real event volume exists, and track accuracy/AUC **on a time-ordered holdout** (never a random split on real interactions, to avoid leakage across a user's own events).
2. Add negative-weighted features over time (e.g. time-since-event decay) and richer scheme metadata (category, benefit amount parsed into ranges) as new input features — the feature dict in `features.py` is designed to extend by appending to `FEATURE_NAMES`.
3. Graduate the objective from binary relevance to a learning-to-rank objective (`rank:pairwise` / `rank:ndcg` per user session) once per-user query groups are plentiful — that optimises the actual product metric (ordering quality), not just pointwise classification.

### 3.5 Interpretation of current feature importance

The gain importances of the shipped artifact confirm the intended inductive bias: `eligibility_match_ratio` dominates (≈7,007 gain), followed by `gender_eligible` (1,029) and `caste_eligible` (287). That is exactly right for a scheme-eligibility domain — hard demographic gates should be the first splits. Notably `source_trust` (151) and `is_all_india` (38) contribute little, as they should; metadata was never meant to outweigh eligibility fit. When the model retrains on real data, watching these importances shift (e.g. `state_eligible` and `income_eligible` rising) will be an easy sanity check that it is learning real preferences rather than memorising the heuristic.

---

## 4. The Heuristic Scorer (fallback model)

**Required for:** guaranteeing a *working* relevance score when the ML artifact is missing, unsupported, or fails to load — the scorer always produces a number.

**How it works:** a two-component linear score: `0.80 × eligibility_match_ratio + 0.20 × matched_rule_coverage`. These two features are normalised over *applicable* rules only, so unrestricted schemes cannot inflate to a perfect score (the weighting was explicitly corrected for this after the raw weighted sum made unrelated profiles look like near-perfect matches). A legacy set of 9 tuned weights (`HEURISTIC_WEIGHTS`, with `state_eligible` 0.15, `caste_eligible` 0.12, etc.) plus hard-rule penalties is retained for reference.

**Accuracy:** no formal metric — it is deterministic shorthand for a hand-crafted ranking policy. It is, however, the model that labelled the synthetic data, so the XGBoost artifact currently ≈ emulates it. It will not improve over time; the ranker will.

---

## 5. Sentence Embedder — `all-MiniLM-L6-v2`

**Required for:** everything semantic. All three retrieval surfaces (FAQ matching, scheme retrieval, query understanding) share this single embedding model.

**How it works:** `sentence-transformers` loads the 22 MB MiniLM model lazily once per process; `encode()` returns L2-normalised 384-dimensional float32 vectors. Normalisation means cosine similarity degenerates to a plain dot product everywhere downstream — the matchers literally compute `embeddings @ q_emb`.

**Accuracy:** MiniLM-L6-v2 classically measures ≈59–63 % Spearman correlation on STS-style benchmarks; on this project's retrieval task the *end-to-end* numbers in §6 are what matter. Fully local, no API keys, deterministic; quality scales up trivially by swapping in a larger model since the interface (`encode`/`encode_single`) is one function.

---

## 6. FAQ Matcher and Scheme Retriever (cosine retrieval)

**Required for:** routing chatbot traffic — first to a canned FAQ answer when one exists (cheap, exact, upvoted by editors), otherwise to a semantic scheme search that feeds the LLM generator.

**How they work (`matcher.py`, `scheme_retriever.py`):**

- FAQ questions are embedded on demand and cached for 300 s; scheme embeddings are precomputed into a persistent `data/scheme_embedding_index.npz` (built by `scripts/build_scheme_embedding_index.py`) and cached in-process at start-up (`app.py` warms it).
- Both rank by cosine similarity; the FAQ matcher applies a **0.35 threshold** (tuned so short FAQ-style paraphrases pass while unrelated phrasing falls through to scheme search), the retriever returns top-N with a perScheme `similarity` rounded to 4 dp.

**Measured accuracy (retrieval eval, 100 queries via `scripts/eval_retrieval_10.py --benchmark scripts/eval_benchmark_100.json`):**

| Metric | Value |
|---|---|
| Hit rate | **1.00** (100/100) |
| Recall@5 | **1.00** |
| MRR | **0.971** |
| Precision@5 | 0.20 |

Read: when a query targets a known scheme, the retriever *always* finds it, and it is essentially always near rank 1 (MRR 0.97). Precision@5 of 0.20 simply reflects that the ground truth lists one relevant scheme while retrieval returns five — a property of the evaluation, not a model failure, and improvable by tuning `limit`.

---

## 7. Grounded Answer Generator — Ollama `qwen2.5:1.5b`

**Required for:** composing the final chatbot response from retrieved schemes without hallucinating.

**How it works:** a strict prompt template forces the model to answer **only** from the top-3 retrieved scheme blocks (name, status, state, category, truncated 500-char description and eligibility, link), with hard output rules: ≤3 schemes, ≤2 bullets each, no invented facts, no links or similarity scores echoed back. Sampling is conservative (`temperature 0.2`, `num_predict 120`, `num_ctx 2048`, `keep_alive 30 m`) and `warm_generator()` preloads the model at start-up to eliminate first-query latency. If Ollama is unreachable, a template fallback renders the same context as plain bullets — the chatbot never fails to answer.

**Accuracy:** there is no automated factuality benchmark yet; grounding is enforced structurally (context-only prompt + post-trim), and the generator is deliberately capped at restating provided context rather than reasoning beyond it. Latency is the material risk (local inference on small hardware), mitigated by `keep_alive`, low `num_ctx`, and the 60 s timeout with fallback.

---

## 8. Deduplication Engine — MinHash LSH + SequenceMatcher

**Required for:** data quality at ingestion — preventing duplicate schemes from repeated syncs from polluting the catalogue (a full MyScheme catalog is ~4,800 records; ~1,600 pairs would naively need comparing).

**How it works:** two stages. (1) *Exact dedup* by `scheme_id`. (2) *Near-dup detection*: each lowercased name is shingled into character trigrams and fingerprinted into a **120-hash min-hash signature split into 40 bands of 3 rows**; records sharing any band are candidate pairs, and only those are verified with the exact `SequenceMatcher` ratio ≥ **0.95** (env-tunable), guarded by an exact length-compatible prefilter. Two names with trigram-Jaccard ~0.7 collide in a band with p ≈ 1 − (1 − 0.34)⁴⁰ ≈ 1.0. Signatures are deterministic (SHA-256 of seed + shingle), immune to hash randomisation. Conservative safeguards: names are only merged within the *same state*, and records with differ **official links are never merged** (MyScheme links are unique per slug), so e.g. "Marriage Assistance Scheme" legitimately surviving in several states stays intact.

**Accuracy:** the LSH stage is probabilistic *candidate generation*, but the final decision is exact — by construction the decision matches a naive pairwise scan given its parameters. No separate accuracy metric exists because the output is a boolean gate, not a score.

---

## 9. Model comparison at a glance

| Model | Learns from data? | Current measured performance | Improves over time? |
|---|---|---|---|
| **XGBoost ranker** ★ | Yes — user ✅ telemetry | Reported 1.00 acc/1.00 AUC on **synthetic** labels; true real-world accuracy lower until retrained on events | **Yes — designed to**, via events → materialized view → retrain loop |
| Heuristic scorer | No | Deterministic rules; currently ≈ equivalent to what the ranker has learned | No |
| all-MiniLM-L6-v2 | No (frozen, pretrained) | 384-dim vectors; effective (see retrieval metrics) | Only by swapping the model |
| FAQ matcher | No (similarity threshold 0.35) | Threshold-based; precision governed by FAQ quality | Via FAQ curation only |
| Scheme retriever | No (similarity over index) | Recall@5 1.00, MRR 0.971, hit rate 1.00 on 100-query eval | Via index rebuilds with better blurbs/models |
| qwen2.5:1.5b generator | No (frozen, local) | Grounded by prompt structure; no benchmark yet | Via prompt/prompt-model upgrades |
| Dedup engine | No (statistical) | Exact decision quality by construction | No (threshold tunable) |

---

## 10. Limitations and future work

1. **The ranker's headline metric is synthetic** and should be relabelled in ops dashboards as *pipeline health*, not real-world accuracy. First real-data retraining should ship together with a time-ordered holdout evaluation and the `pos_weight` check already implemented in `train_real.py`.
2. **Retraining cadence is manual.** The loop (refresh view → train → swap artifact) exists but nothing schedules it; a cron job plus an automated AUC/accuracy regression gate would be the single highest-leverage addition.
3. **Relevance labels are engagement proxies.** Dwell and clicks carry selection bias (users only see what the ranker already surfaced). An explicit thumbs-down/irrelevant event type would de-bias negatives cheaply.
4. **Pointwise classification ≠ ranking quality.** Moving to a rank objective once sessions produce enough per-user groups aligns training with the product metric.
5. **Generator factuality is unmeasured.** A small labelled set of grounded-answer checks (name/eligibility/benefit extraction from the same context) would give the last unmeasured model a number.
6. **Embedding staleness.** The scheme index must be rebuilt when scheme text changes; a fingerprint (already computed at ingestion, `ingestion/sync/fingerprint.py`) could trigger selective re-embedding.

---

## 11. Reproduction commands

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

The platform's model stack is deliberately simple, local-first, and mostly deterministic — every component degrades gracefully, and none requires external API keys. The one model that embodies the product's ambitions is the XGBoost ranker: it is currently seeded by synthetic data, so its **real accuracy is admittedly lower today than the metrics file implies**, and the heuristic fallback remains competitive. But it is the only model with a closed learning loop wired through real user behaviour, `scale_pos_weight`-protected training, a hot-swappable artifact, and a materialized view that turns every click and application into a fresh labelled example. Its accuracy lower bound is bounded by the heuristic it imitates, and its upper bound — reached only with accumulated telemetry — is a ranking that genuinely knows its users.
