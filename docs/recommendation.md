# Recommendation Algorithm

The recommendation system combines three complementary techniques, in order to balance statistical robustness,
personalization, computational efficiency and offline evaluability.
The goal is not to reproduce Netflix like black-box recommendations,
but to ensure interpretability, and engineering control.

---

## 1 - Popularity-Based Baseline

The popularity score uses a **Bayesian weighted average** in order to avoid
overvaluing items with very few ratings.

Formula:

score = (v / (v + m)) * R + (m / (v + m)) * C

Where:

- v = number of ratings for the item
- R = average rating for the item
- C = global mean rating across all the items
- m = reliability threshold

The threshold `m` is not arbitrarily fixed, but rather inferred from the dataset using a quantile of rating counts,
ensuring data-driven robustness : `m = quantile_q({v_i})`

All popularity scores are min-max normalized to [0,1]
before being blended with collaborative filtering.

---

## 2 - User-Based Collaborative Filtering (Cosine + Bias Model)

### 2.1 Similarity

User similarity is computed using **cosine similarity**
over commonly rated items.

sim(u,v) = cosine similarity on shared items

To avoid recomputing the same similarities multiple times,
a similarity cache is used during recommendation generation.

Additionally, in order to enhance performance,

- Similarities are computed only for a limited neighbor pool
- Not all user pairs are evaluated

---

### 2.2 Bias baseline model

Before applying collaborative filtering,
a baseline prediction model is computed:

baseline(u,i) = μ + b_u(u) + b_i(i)

Where:

- μ = global average rating
- b_i = item bias (regularized)
- b_u = user bias (regularized)

Regularization prevents overfitting on users or items
with very few ratings.

---

### 2.3 Neighborhood Prediction with Bias

The collaborative filtering prediction is computed on residuals:

r̂(u,i) = baseline(u,i) + ( Σ sim(u,v) * ( r(v,i) − baseline(v,i) ) )/ ( Σ sim(u,v) )

If no neighbors are available,
the fallback prediction is simply:

r̂(u,i) = baseline(u,i)

This formulation ensures:

- Robustness for sparse users
- Correction of systematic rating tendencies
- Better numerical stability

Predicted CF scores are normalized to [0,1]
before blending.
___

### 2.4 Neighbor Pool Strategy

To reduce computational cost:

- A fixed neighbor pool is built once per user.
- The pool is derived from:
    - The user’s highest-rated items (seed items)
    - The top raters of those seed items

Similarities are computed only for this limited pool.
This avoids recomputing neighbors for every candidate item
and keeps runtime bounded.

---

## 3 - Hybrid Blending Strategy

The final recommendation score combines
Collaborative Filtering and Popularity:

score = α * CF + (1 − α) * Popularity

The blending factor α depends on user profile maturity:

α = n_ratings / (n_ratings + threshold)

Where:

- n_ratings = number of ratings given by the user
- threshold = median number of ratings across users

This ensures:

- for cold start users → popularity dominates
- for mature users → personalization dominates

Both CF predictions and popularity scores
are normalized to [0,1] before blending.

---

## 4 - Complexity Control

We avoid scoring the entire item catalog. Instead, candidates are built from:

1. Top popularity items (pop_p)
2. Items liked by top neighbors (rating threshold applied)

Additional constraints:

- Limit number of seed items per user
- Limit number of raters inspected per seed item
- Limit total neighbor pool size
- Limit maximum CF candidate size

These constraints reduce complexity from:

O(users × items) to approximately O(users × candidate_subset)

This makes the system suitable for demo-scale environments
while remaining structurally extensible.

---

## 5 - Offline Evaluation Strategy

Evaluation is implemented as a separate job
to ensure strict separation between, model training, recommendation generation and evaluation metrics computation.

### 5.1 - Data Splitting

Supported strategies:

- Leave-One-Out (LOO)
- Train/Test split (e.g., 80/20)

### 5.2 - Metrics:

For each evaluated user, recommendations are generated and compared
against held-out test items. We used the following metrics:

- Precision@K
- Recall@K
- MAP@K

### 5.3 Evaluation Results and Observations

Under a Leave-One-Out evaluation setting (MovieLens 100K–scale dataset):

Popularity baseline:
- Precision@10: 0.0044
- Recall@10: 0.0443
- MAP@10: 0.0131

Hybrid (UserCF + Popularity):
- Precision@10: 0.0030
- Recall@10: 0.0295
- MAP@10: 0.0073

Relative to the popularity baseline:

Recall@10: −33.3%

MAP@10: −44.2%

#### Interpretation

The hybrid model currently underperforms the popularity baseline, which is not unexepected given the moderate size of the dataset used. Given the limited user histories, popularity is a very strong basline. Collaborative filtering requires sufficient user overlap to outperform global trends. In addition, the candidate pruning and neighbor caps (introduced for performance control) may reduce personalization strength.

In short:

- Popularity is statistically robust and stable.
- The hybrid model introduces personalization but currently does not extract enough signal to beat the strong baseline.

However, the result is valuable because it
- Validates the evaluation pipeline
- Confirms the robustness of the popularity component
- Highlights clear improvement directions for next versions (neighbor tuning, similarity weighting, bias calibration, ...)
