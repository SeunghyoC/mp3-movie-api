# MP3 Movie API

This API stores a movie collection in SQLite and caches movie lookups with fakeredis. Uploading a CSV to `POST /upload` replaces all stored movies. `GET /movies` returns the stored movies, and `GET /movies/search` filters them by minimum rating with SQL. `POST /movies/process` cleans the stored movies using the MP1 pipeline and saves the result. `GET /movies` responses are cached for 90 seconds, and the cache is cleared after every upload or processing request. The main modules are `main.py` (endpoints), `src/database.py` (table setup), `src/storage.py` (SQL queries), and `src/cache.py` (caching).

## Run the API

```bash
python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs

## Run the tests

```bash
python -m pytest tests -v
```

## Sample processing request

After uploading `fixtures/sample_movies.csv`, send this to `POST /movies/process`:

```json
{
  "validation": {
    "required_columns": ["title", "release_year", "rating", "genre"],
    "numeric_columns": ["release_year", "rating"]
  },
  "processing": {
    "remove_duplicates": true,
    "missing": {"enabled": true, "axis": "rows"},
    "outliers": {"enabled": true, "columns": ["rating"], "method": "iqr", "threshold": 1.5}
  }
}
```

Expected result: 20 rows before, 16 rows after (2 duplicates and 2 rating outliers removed).

```json
{
  "validation_rows_removed": 0,
  "cleaning_report": {
    "rows_before": 20,
    "rows_after": 16,
    "rows_removed": 4,
    "columns_before": 4,
    "columns_after": 4,
    "columns_removed": 0
  }
}
```
