from pathlib import Path

import pandas as pd
import pytest

from src import MovieStorage
import main


def test_movies_persist(client, test_storage, uploaded_movies):
    reopened = MovieStorage(test_storage.db_path)
    df = reopened.get()

    assert reopened.count_movies() == 20
    assert len(df) == 20
    assert df.columns.tolist() == ["title", "release_year", "rating", "genre"]

    original = pd.read_csv(Path("fixtures") / "sample_movies.csv")
    assert df["title"].tolist() == original["title"].tolist()

    storage_ids = [row["id"] for row in reopened.select_columns(["title"], limit=100)]
    response = client.get("/movies", params={"limit": 100})
    assert response.status_code == 200
    api_ids = [movie["id"] for movie in response.json()["data"]]

    assert storage_ids == list(range(1, 21))
    assert api_ids == storage_ids


def test_cache_and_processing(client, uploaded_movies, processing_body):
    first = client.get("/movies", params={"limit": 100})
    small = client.get("/movies", params={"limit": 1})
    assert first.status_code == 200
    assert small.status_code == 200
    assert main.cache.get(100) == first.json()
    assert main.cache.get(1) == small.json()

    repeat = client.get("/movies", params={"limit": 100})
    assert repeat.status_code == 200
    assert repeat.json() == first.json()

    processed = client.post("/movies/process", json=processing_body)
    assert processed.status_code == 200
    body = processed.json()
    assert body["validation_rows_removed"] == 0
    assert body["cleaning_report"]["rows_before"] == 20
    assert body["cleaning_report"]["rows_after"] == 16
    assert body["cleaning_report"]["rows_removed"] == 4
    assert main.cache.get(100) is None
    assert main.cache.get(1) is None

    after = client.get("/movies", params={"limit": 100})
    assert after.status_code == 200
    data = after.json()["data"]
    expected_titles = [
        "Movie A", "Movie B", "Movie C", "Movie D", "Movie E", "Movie F",
        "Movie G", "Movie H", "Movie I", "Movie J", "Movie K", "Movie L",
        "Movie M", "Movie N", "Movie O", "Movie P",
    ]
    assert after.json()["total_rows"] == 16
    assert [movie["title"] for movie in data] == expected_titles
    assert [movie["id"] for movie in data] == list(range(1, 17))
    assert main.cache.get(100) == after.json()


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    first = client.get("/movies", params={"limit": 100})
    assert first.status_code == 200

    def fail_if_called(*args, **kwargs):
        pytest.fail("A cache hit should not query the database")

    monkeypatch.setattr(main.storage, "select_columns", fail_if_called)
    monkeypatch.setattr(main.storage, "count_movies", fail_if_called)

    second = client.get("/movies", params={"limit": 100})
    assert second.status_code == 200
    assert second.json() == first.json()
