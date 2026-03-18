import sys
import os
from datetime import date

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, backend_path)

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


@pytest.fixture(autouse=True)
def clean_db(test_engine):
    """Wipe all rows before each test so tests don't interfere with each other."""
    from models import Transaction
    from sqlmodel import delete
    with Session(test_engine) as session:
        session.exec(delete(Transaction))
        session.commit()


@pytest.fixture
def client(test_engine):
    from main import app, get_session

    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(test_engine):
    from main import app, get_session
    from models import Transaction

    with Session(test_engine) as session:
        session.add(Transaction(transaction_date=date(2025, 10, 1), description="UPI/DR/petro payment", debit_amount=170.0, credit_amount=0.0, balance=193881.76, category="Transport"))
        session.add(Transaction(transaction_date=date(2025, 10, 4), description="NEFT SHIVAM ASSOCIATE", debit_amount=0.0, credit_amount=5000.0, balance=198881.76, category="Income"))
        session.add(Transaction(transaction_date=date(2025, 10, 4), description="UPI/DR/AMART groceries", debit_amount=22.0, credit_amount=0.0, balance=198839.76, category="Groceries"))
        session.add(Transaction(transaction_date=date(2025, 10, 6), description="UPI/DR/MANTHAN/contr", debit_amount=213.0, credit_amount=0.0, balance=198626.76, category="Utilities"))
        session.add(Transaction(transaction_date=date(2025, 10, 7), description="UPI/DR/petro second", debit_amount=50.0, credit_amount=0.0, balance=198576.76, category="Transport"))
        session.commit()

    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_transactions_returns_empty_list(client):
    response = client.get("/transactions")
    assert response.status_code == 200
    assert response.json() == []


def test_get_transactions_returns_all_rows(seeded_client):
    response = seeded_client.get("/transactions")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_get_transactions_min_amount_filter(seeded_client):
    response = seeded_client.get("/transactions?min_amount=200")
    assert response.status_code == 200
    results = response.json()
    for txn in results:
        assert txn["debit_amount"] >= 200 or txn["credit_amount"] >= 200


def test_by_category_returns_all_categories(seeded_client):
    response = seeded_client.get("/transactions/by-category")
    assert response.status_code == 200
    categories = [row["category"] for row in response.json()]
    assert "Transport" in categories
    assert "Income" in categories
    assert "Groceries" in categories
    assert "Utilities" in categories


def test_by_category_aggregates_totals_correctly(seeded_client):
    response = seeded_client.get("/transactions/by-category")
    assert response.status_code == 200
    rows = response.json()
    transport = next(r for r in rows if r["category"] == "Transport")
    assert transport["total_debit"] == 220.0
    assert transport["transaction_count"] == 2


def test_by_category_filter_by_category_name(seeded_client):
    response = seeded_client.get("/transactions/by-category?category=Income")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["category"] == "Income"
    assert rows[0]["total_credit"] == 5000.0


def test_by_category_filter_by_start_date(seeded_client):
    response = seeded_client.get("/transactions/by-category?start_date=2025-10-04")
    assert response.status_code == 200
    rows = response.json()
    categories = [r["category"] for r in rows]
    assert "Transport" in categories
    assert "Income" in categories


def test_by_category_filter_by_date_range(seeded_client):
    response = seeded_client.get(
        "/transactions/by-category?start_date=2025-10-01&end_date=2025-10-01"
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["category"] == "Transport"
    assert rows[0]["transaction_count"] == 1


def test_by_category_returns_correct_response_shape(seeded_client):
    response = seeded_client.get("/transactions/by-category?category=Groceries")
    assert response.status_code == 200
    row = response.json()[0]
    assert "category" in row
    assert "total_debit" in row
    assert "total_credit" in row
    assert "transaction_count" in row