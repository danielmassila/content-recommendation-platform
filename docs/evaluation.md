# Offline evaluation

The repository includes a deterministic offline comparison between the hybrid recommender and its Bayesian popularity
baseline. Metrics are computed with a fixed seed and should be read as regression signals, not as proof of production
recommendation quality.

## Current benchmark

MovieLens latest-small, seed 42, top-10 evaluation:

| Split | Model | Precision@10 | Recall@10 | MAP@10 |
| --- | --- | ---: | ---: | ---: |
| Leave-one-out | Popularity | 0.0044 | 0.0443 | 0.0131 |
| Leave-one-out | Hybrid UserCF + popularity | 0.0030 | 0.0295 | 0.0073 |
| 80/20, relevant rating >= 4 | Popularity | 0.0860 | 0.0649 | 0.0315 |
| 80/20, relevant rating >= 4 | Hybrid UserCF + popularity | 0.0317 | 0.0447 | 0.0190 |

The current hybrid implementation does **not** outperform the popularity baseline. This is a known model-quality
limitation, not hidden behind the product interface. The likely causes to investigate are the raw cosine similarity on
explicit ratings, sparse neighbor overlap, candidate generation, and the dynamic blend weight.

## Reproduce

With the local dataset imported:

```bash
make py-eval
```

For the ratio split:

```bash
docker compose run --rm reco-job python -m jobs.evaluate_offline \
  --split ratio --test-ratio 0.2 --liked-threshold 4.0 --k 10 --n 50 --neighbors 50
```

## Next model iteration

A future iteration should be accepted only if it improves the recorded baseline on both protocols. Candidate
experiments include mean-centered or significance-weighted similarity, item-based collaborative filtering, matrix
factorization, and systematic blend-weight tuning.

