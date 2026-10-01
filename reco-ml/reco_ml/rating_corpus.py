"""Explicit snapshot selection and disjoint identities for the existing engine."""

from collections import defaultdict

from reco_ml import repositories


def load_corpus(conn, dataset_version):
    """Positive IDs are application users; negative IDs are external neighbors.

    This reversible encoding is internal to the calculation, never persisted.
    Requires positive source IDs, as enforced for MovieLens by V8.
    Currently loads the corpus in memory; not intended for the full dataset yet.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM staging.movielens_imports WHERE dataset_version=%s AND status='ready')", (dataset_version,))
        if not cur.fetchone()[0]:
            raise ValueError('Selected MovieLens snapshot is not published (ready)')
    app = repositories.fetch_all_ratings(conn)
    if any(user <= 0 for user, _, _ in app):
        raise ValueError('Application user IDs must be positive')
    with conn.cursor() as cur:
        cur.execute('SELECT movielens_user_id,item_id,rating FROM movielens_ratings WHERE dataset_version=%s', (dataset_version,))
        external = cur.fetchall()
    if not external:
        raise ValueError('Selected MovieLens snapshot has no ratings')
    if any(user <= 0 for user, _, _ in external):
        raise ValueError('MovieLens user IDs must be positive')
    ratings = app + [(-user, item, float(rating)) for user, item, rating in external]
    values = defaultdict(list)
    for _, item, rating in ratings:
        values[item].append(rating)
    stats = {item: (len(scores), sum(scores) / len(scores)) for item, scores in values.items()}
    mean = sum(rating for _, _, rating in ratings) / len(ratings)
    return ratings, stats, mean
