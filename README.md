# llm-embedding-sample

LLM Embedding Sample App using Flask and PostgreSQL with pgvector extension.

### Install Python 3.11 and dependencies

```
pip install openai numpy flask jinja2 psycopg2 pgvector
```

### Run PostgreSQL with pgvector

```
docker run -d \
       --rm \
       --name pgvector \
       -p 5432:5432 \
       -e POSTGRES_PASSWORD=password \
       -e POSTGRES_USER=postgres \
       -e POSTGRES_DB=postgres \
       -e PGDATA=/var/lib/postgresql/data/pgdata \
       -v /path/to/llm-embedding-sample/pg-data:/var/lib/postgresql/data \
       -v /path/to/llm-embedding-sample/pg-init-script:/docker-entrypoint-initdb.d \
       ankane/pgvector:latest
```

NOTE: replace `/path/to/...` with real path.

The initial script is in `pg-init-script` and it is only executed once when container started.

The db files are stores at `pg-data`.

### Run Flask app

```
$ python3 app.py
```

When app starts:

- load all `.md` files from `docs`;
- create embedding and save into db if record is not exist.

### Ask

Open `http://localhost:5000`:
