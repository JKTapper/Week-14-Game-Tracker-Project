#pylint: skip-file
import pytest
import pandas as pd
from form import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_get_form_page(monkeypatch, client):
    class FakeConn:
        def begin(self):
            class DummyCtx:
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb): pass
            return DummyCtx()
    
    monkeypatch.setattr("form.connect_to_rds", lambda: FakeConn())

    def fake_read_sql(query, conn):
        return pd.DataFrame({"genre_name": ["Romance", "Thriller"]})

    monkeypatch.setattr("pandas.read_sql", fake_read_sql)

    response = client.get("/")
    assert response.status_code == 200
    assert b"Romance" in response.data
    assert b"Thriller" in response.data



def test_submit_form_success(monkeypatch, client):
    class FakeConn:
        def begin(self):
            class DummyCtx:
                def __enter__(inner_self): return inner_self
                def __exit__(inner_self, exc_type, exc_val, exc_tb): pass
            return DummyCtx()

        def execute(self, query, params=None):
            class Result:
                def fetchone(inner_self):
                    return [42]
            return Result()

    monkeypatch.setattr("form.connect_to_rds", lambda: FakeConn())

    monkeypatch.setattr("pandas.read_sql", lambda q, c: pd.DataFrame({"genre_name": ["Sci-Fi", "Fantasy"]}))

    response = client.post("/", data={
        "email": "test@example.com",
        "genre": ["Sci-Fi"],
        "notifications": "on",
        "summary": "on"
    })

    assert response.status_code == 200


def test_submit_form_duplicate_email(monkeypatch, client):
    class FakeConn:
        def begin(self):
            class DummyCtx:
                def __enter__(inner_self): return inner_self
                def __exit__(inner_self, exc_type, exc_val, exc_tb): pass
            return DummyCtx()

        def execute(self, query, params=None):
            raise Exception("duplicate email")

    monkeypatch.setattr("form.connect_to_rds", lambda: FakeConn())

    monkeypatch.setattr("pandas.read_sql", lambda q, c: pd.DataFrame({"genre_name": ["Horror", "Mystery"]}))

    response = client.post("/", data={
        "email": "duplicate@example.com",
        "genre": ["Horror"]
    })

    assert response.status_code == 200
    assert b"There was an error with your request" in response.data
