"""Run only against an explicitly supplied disposable PostgreSQL database."""

import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest

from reco_ml.movie_catalog import upsert_tmdb_movie
from reco_ml.movie_mapping import MappingConflict

DSN = os.getenv("CATALOG_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="CATALOG_TEST_DSN must point to a disposable database")


@pytest.fixture(scope="module", autouse=True)
def schema():
    if not DSN:
        return
    migrations = Path(__file__).resolve().parents[3] / "backend/src/main/resources/db/migration"
    with psycopg.connect(DSN) as conn:
        for migration in sorted(migrations.glob("V*__*.sql"), key=lambda path: int(path.name.split("__")[0][1:])):
            conn.execute(migration.read_text())


def payload(tmdb_id):
    return {"id": tmdb_id, "title": "Example", "imdb_id": "tt0133093",
            "genres": [{"name": "Science Fiction"}], "poster_path": None}


def test_create_update_and_keep_application_references():
    with psycopg.connect(DSN) as conn:
        item_id = upsert_tmdb_movie(conn, payload(603))
        row = conn.execute("SELECT movielens_id, metadata, tmdb_last_synced_at FROM items WHERE id=%s", (item_id,)).fetchone()
        assert row[0] is None
        assert row[1]["source"] == "tmdb"
        assert row[1]["tmdb"]["posterPath"] is None
        assert row[2] is not None
        user_id = conn.execute("INSERT INTO users(email) VALUES ('app@example.com') RETURNING id").fetchone()[0]
        conn.execute("INSERT INTO ratings(user_id,item_id,rating) VALUES (%s,%s,4)", (user_id, item_id))
        conn.execute("UPDATE items SET movielens_id=2571, metadata=metadata || '{\"custom\":true}' WHERE id=%s", (item_id,))
        assert upsert_tmdb_movie(conn, {**payload(603), "title": "Updated", "imdb_id": None}) == item_id
        row = conn.execute("SELECT title, imdb_id, movielens_id, metadata FROM items WHERE id=%s", (item_id,)).fetchone()
        assert row[:3] == ("Updated", "tt0133093", 2571)
        assert row[3]["custom"] is True
        assert row[3]["source"] == "movielens+tmdb"
        assert conn.execute("SELECT item_id FROM ratings WHERE user_id=%s", (user_id,)).fetchone()[0] == item_id
        with pytest.raises(MappingConflict):
            upsert_tmdb_movie(conn, {**payload(603), "imdb_id": "tt9999999"})


def test_legacy_json_identity_blocks_duplicate_creation():
    with psycopg.connect(DSN) as conn:
        conn.execute("INSERT INTO items(title,type,metadata) VALUES ('Legacy','MOVIE','{\"tmdbId\":604}')")
        with pytest.raises(MappingConflict):
            upsert_tmdb_movie(conn, payload(604))
        assert conn.execute("SELECT count(*) FROM items WHERE tmdb_id=604").fetchone()[0] == 0


def test_concurrent_upserts_return_same_internal_id():
    def sync(_):
        with psycopg.connect(DSN) as conn:
            return upsert_tmdb_movie(conn, payload(605))
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(sync, range(2)))
    assert ids[0] == ids[1]


def test_movielens_import_is_replayable_and_preserves_app_data(tmp_path):
    from reco_ml.movielens_import import import_snapshot
    from unittest.mock import Mock
    import io
    from urllib.error import HTTPError

    (tmp_path / 'links.csv').write_text('movieId,imdbId,tmdbId\n8001,0133093,8001\n8002,,\n8003,,8003\n8004,,8004\n')
    (tmp_path / 'ratings.csv').write_text('userId,movieId,rating,timestamp\n42,8001,4.5,1000000000\n42,8002,4,1000000000\n42,8003,3,1000000000\n42,8004,2,1000000000\n42,8999,5,1000000000\n')
    client = Mock()
    client.get_movie.side_effect = [payload(8003), HTTPError('test',404,'missing',{},io.BytesIO())]
    with psycopg.connect(DSN) as conn:
        item_id = upsert_tmdb_movie(conn, payload(8001))
        before = conn.execute('SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM ratings)').fetchone()
        report = import_snapshot(conn, tmp_path, client)
        assert report['inserted'] == 2
        assert report['rejected_ratings'] == {'missing_tmdb_id': 1, 'tmdb_not_found': 1, 'missing_link': 1}
        assert client.get_movie.call_count == 2
        assert conn.execute('SELECT item_id FROM movielens_ratings WHERE dataset_version=%s AND item_id=%s', (report['dataset_version'],item_id)).fetchone()[0] == item_id
        replay = import_snapshot(conn, tmp_path)
        assert replay['inserted'] == 0
        assert replay['already_present'] == 2
        assert conn.execute('SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM ratings)').fetchone() == before


def test_movielens_temporary_api_failure_rolls_back_import(tmp_path):
    from reco_ml.movielens_import import import_snapshot
    from unittest.mock import Mock
    (tmp_path / 'links.csv').write_text('movieId,imdbId,tmdbId\n9001,,9001\n9002,,9002\n')
    (tmp_path / 'ratings.csv').write_text('userId,movieId,rating,timestamp\n42,9001,4,1\n42,9002,5,1\n')
    client = Mock()
    client.get_movie.side_effect = [payload(9001), TimeoutError()]
    with pytest.raises(TimeoutError):
        with psycopg.connect(DSN) as conn:
            import_snapshot(conn, tmp_path, client)
    with psycopg.connect(DSN) as conn:
        assert conn.execute('SELECT count(*) FROM items WHERE tmdb_id=9001').fetchone()[0] == 0


def test_import_skips_ambiguous_links_without_calling_tmdb_for_them(tmp_path):
    from reco_ml.movielens_import import import_snapshot
    from unittest.mock import Mock
    (tmp_path / 'links.csv').write_text('movieId,imdbId,tmdbId\n9601,0000001,9600\n9602,0000002,9600\n9603,0133093,9603\n')
    (tmp_path / 'ratings.csv').write_text('userId,movieId,rating,timestamp\n42,9601,4,1\n42,9602,5,1\n42,9603,4,1\n')
    client = Mock()
    client.get_movie.return_value = payload(9603)
    with psycopg.connect(DSN) as conn:
        report = import_snapshot(conn, tmp_path, client)
        assert report['inserted'] == 1
        assert report['rejected_ratings'] == {'ambiguous_link': 2}
        assert set(report['rejected_links']) == {9601, 9602}
        client.get_movie.assert_called_once_with(9603)
        assert conn.execute('SELECT count(*) FROM items WHERE tmdb_id=9600').fetchone()[0] == 0


def test_staging_is_separate_and_preserves_duplicates_for_validation():
    import uuid
    run_id = uuid.uuid4()
    with psycopg.connect(DSN) as conn:
        before = conn.execute('SELECT count(*) FROM public.movielens_ratings').fetchone()[0]
        conn.execute("INSERT INTO staging.movielens_imports(id,dataset_version,source_hashes) VALUES (%s,'staging-test','{}')", (run_id,))
        for line, value in [(2,4),(3,5)]:
            conn.execute('''INSERT INTO staging.movielens_ratings
                VALUES (%s,%s,42,2571,%s,CURRENT_TIMESTAMP)''', (run_id,line,value))
        assert conn.execute('SELECT count(*) FROM staging.movielens_ratings WHERE import_id=%s',(run_id,)).fetchone()[0] == 2
        assert conn.execute('SELECT count(*) FROM public.movielens_ratings').fetchone()[0] == before
        conn.execute('DELETE FROM staging.movielens_imports WHERE id=%s',(run_id,))
        assert conn.execute('SELECT count(*) FROM staging.movielens_ratings WHERE import_id=%s',(run_id,)).fetchone()[0] == 0
        assert conn.execute('SELECT count(*) FROM public.movielens_ratings').fetchone()[0] == before


def test_staging_tracks_attempts_and_validates_completion():
    import uuid
    run_id = uuid.uuid4()
    with psycopg.connect(DSN) as conn:
        conn.execute("INSERT INTO staging.movielens_imports(id,dataset_version,source_hashes) VALUES (%s,'retry-test','{}')",(run_id,))
        with pytest.raises(psycopg.errors.UniqueViolation):
            with conn.transaction():
                conn.execute("INSERT INTO staging.movielens_imports(id,dataset_version,source_hashes) VALUES (%s,'retry-test','{}')",(uuid.uuid4(),))
        with pytest.raises(psycopg.errors.CheckViolation):
            with conn.transaction():
                conn.execute("UPDATE staging.movielens_imports SET status='ready' WHERE id=%s",(run_id,))
        with pytest.raises(psycopg.errors.CheckViolation):
            with conn.transaction():
                conn.execute("UPDATE staging.movielens_imports SET status='ready',finished_at=now(),rows_read=2,rows_accepted=1 WHERE id=%s",(run_id,))
        conn.execute("UPDATE staging.movielens_imports SET status='failed',finished_at=now() WHERE id=%s",(run_id,))
        conn.execute("INSERT INTO staging.movielens_imports(id,dataset_version,source_hashes) VALUES (%s,'retry-test','{}')",(uuid.uuid4(),))


def test_streaming_staging_batches_and_failure_are_isolated(tmp_path):
    from reco_ml.staging_import import stage_snapshot
    from reco_ml.movielens_import import read_snapshot
    (tmp_path / 'links.csv').write_text('movieId,imdbId,tmdbId\n1,,862\n')
    path = tmp_path / 'ratings.csv'
    path.write_text('userId,movieId,rating,timestamp\n1,1,4,1\n2,1,5,2\n3,1,3,3\n')
    expected = read_snapshot(tmp_path)[0]
    with psycopg.connect(DSN) as conn:
        before = conn.execute('SELECT count(*) FROM public.movielens_ratings').fetchone()[0]
        report = stage_snapshot(conn, tmp_path, batch_size=2)
        assert report['rows_staged'] == 3
        assert report['dataset_version'] == expected
        assert conn.execute('SELECT status,rows_read,rows_accepted,staged_at IS NOT NULL FROM staging.movielens_imports WHERE id=%s',(report['import_id'],)).fetchone() == ('loading',3,0,True)
        assert conn.execute('SELECT count(*) FROM public.movielens_ratings').fetchone()[0] == before
    path.write_text('userId,movieId,rating,timestamp\n1,1,4,1\n2,1,5,2\n3,1,NaN,3\n')
    with psycopg.connect(DSN) as conn:
        with pytest.raises(ValueError):
            stage_snapshot(conn,tmp_path,batch_size=2)
        row=conn.execute("SELECT id,rows_read FROM staging.movielens_imports WHERE status='failed' AND error_message='ValueError' ORDER BY started_at DESC LIMIT 1").fetchone()
        assert row[1] == 2
        assert conn.execute('SELECT count(*) FROM staging.movielens_ratings WHERE import_id=%s',(row[0],)).fetchone()[0] == 2


def test_publication_is_atomic_deduplicated_and_replayable(tmp_path):
    from reco_ml.staging_import import stage_snapshot
    from reco_ml.staging_publish import publish_snapshot
    links = tmp_path / 'links.csv'
    links.write_text('movieId,imdbId,tmdbId\n9700,,9700\n9701,,\n')
    (tmp_path / 'ratings.csv').write_text('userId,movieId,rating,timestamp\n42,9700,4,1\n42,9700,4,1\n42,9701,3,1\n')
    with psycopg.connect(DSN) as conn:
        upsert_tmdb_movie(conn,payload(9700))
    with psycopg.connect(DSN) as conn:
        staged=stage_snapshot(conn,tmp_path,batch_size=1)
    with psycopg.connect(DSN) as conn:
        report=publish_snapshot(conn,staged['import_id'],links)
        assert report['published']==1
        assert report['duplicate_rows']==1
        assert report['rejected_ratings']=={'missing_tmdb_id':1}
        conn.rollback()
    with psycopg.connect(DSN) as conn:
        assert conn.execute('SELECT count(*) FROM public.movielens_ratings WHERE dataset_version=%s',(staged['dataset_version'],)).fetchone()[0]==0
        assert conn.execute('SELECT status FROM staging.movielens_imports WHERE id=%s',(staged['import_id'],)).fetchone()[0]=='loading'
        publish_snapshot(conn,staged['import_id'],links)
    with psycopg.connect(DSN) as conn:
        assert publish_snapshot(conn,staged['import_id'],links)['already_published']


def test_publication_rejects_changed_links_and_conflicting_notes(tmp_path):
    from reco_ml.staging_import import stage_snapshot
    from reco_ml.staging_publish import publish_snapshot
    links=tmp_path/'links.csv'
    original='movieId,imdbId,tmdbId\n9800,,9800\n'
    links.write_text(original)
    (tmp_path/'ratings.csv').write_text('userId,movieId,rating,timestamp\n42,9800,4,1\n42,9800,5,1\n')
    with psycopg.connect(DSN) as conn:
        staged=stage_snapshot(conn,tmp_path)
    links.write_text(original+'9801,,9801\n')
    with psycopg.connect(DSN) as conn:
        with pytest.raises(ValueError,match='differs'):
            publish_snapshot(conn,staged['import_id'],links)
    links.write_text(original)
    with psycopg.connect(DSN) as conn:
        with pytest.raises(MappingConflict):
            publish_snapshot(conn,staged['import_id'],links)
        assert conn.execute('SELECT count(*) FROM public.movielens_ratings WHERE dataset_version=%s',(staged['dataset_version'],)).fetchone()[0]==0


def test_recommender_requires_publication_and_direct_import_cannot_modify_it(tmp_path):
    from reco_ml.staging_import import stage_snapshot
    from reco_ml.staging_publish import publish_snapshot
    from reco_ml.rating_corpus import load_corpus
    from reco_ml.movielens_import import import_snapshot
    (tmp_path/'links.csv').write_text('movieId,imdbId,tmdbId\n9900,,9900\n')
    (tmp_path/'ratings.csv').write_text('userId,movieId,rating,timestamp\n42,9900,4,1\n')
    with psycopg.connect(DSN) as conn:
        upsert_tmdb_movie(conn,payload(9900))
    with psycopg.connect(DSN) as conn:
        staged=stage_snapshot(conn,tmp_path)
    with psycopg.connect(DSN) as conn:
        with pytest.raises(ValueError,match='not published'):
            load_corpus(conn,staged['dataset_version'])
        publish_snapshot(conn,staged['import_id'],tmp_path/'links.csv')
    with psycopg.connect(DSN) as conn:
        ratings,_,_=load_corpus(conn,staged['dataset_version'])
        assert any(user == -42 for user,_,_ in ratings)
        with pytest.raises(ValueError,match='already published'):
            import_snapshot(conn,tmp_path)
