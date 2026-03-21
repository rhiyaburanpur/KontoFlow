import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from sqlmodel import SQLModel, create_engine, Session
import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.insert(0, backend_path)

# Fixtures

@pytest.fixture
def raw_table():
    """
    A realistic raw table as pdfplumber would return it.
    Row 0 is the header. Rows 1-4 are data.
    Row 4 has a None date to test the drop logic.
    """
    return [
        ["Date", "Details", "Ref No./Cheque\nNo", "Debit", "Credit", "Balance"],
        ["01/01/2025", "UPI/DR/petro\npayment", "REF001", "1,500.00", "",        "10,000.00"],
        ["02/01/2025", "SALARY CREDIT",         "REF002", "",         "50,000.00","60,000.00"],
        ["03/01/2025", "UPI/DR/zomato\nfood",   "REF003", "350.75",   "",        "59,649.25"],
        ["04/01/2025", "ATM WITHDRAWAL",         "-",      "2,000.00", "",        "57,649.25"],
        [None,         "MISSING DATE ROW",       "REF005", "100.00",   "",        "57,549.25"],
    ]


@pytest.fixture
def in_memory_engine():
    """
    Creates a temporary SQLite database in memory.
    This replaces the real database.db so tests never touch the filesystem.
    """
    from models import Transaction
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


# --- Transform Logic Tests ---
# These tests do not need a PDF or a database.
# They test the cleaning logic in isolation by replicating the transform step.

def apply_transform(raw_table):
    """
    A helper that runs the exact same transform logic as etl.py.
    Kept here so tests don't import the function directly and hit the DB import.
    """
    df = pd.DataFrame(raw_table[1:], columns=raw_table[0])

    if "Details" in df.columns:
        df['Details'] = df["Details"].str.replace("\n", " ", regex=False)

    df.fillna('-', inplace=True)

    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    df.dropna(subset=["Date"], inplace=True)

    numeric_cols = ["Debit", "Credit", "Balance"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", "")
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).round(2)

    return df


def test_environment_setup():
    assert True


def test_newline_removed_from_description(raw_table):
    df = apply_transform(raw_table)
    assert "\n" not in df.iloc[0]["Details"]
    assert df.iloc[0]["Details"] == "UPI/DR/petro payment"


def test_row_with_missing_date_is_dropped(raw_table):
    df = apply_transform(raw_table)
    # raw_table has 5 data rows. The last one has None as date.
    # After dropping, we expect exactly 4 rows.
    assert len(df) == 4


def test_commas_removed_from_numeric_columns(raw_table):
    df = apply_transform(raw_table)
    assert df.iloc[0]["Debit"] == 1500.00
    assert df.iloc[1]["Credit"] == 50000.00
    assert df.iloc[0]["Balance"] == 10000.00


def test_empty_debit_becomes_zero(raw_table):
    # Row 1 (SALARY CREDIT) has an empty string for Debit
    df = apply_transform(raw_table)
    assert df.iloc[1]["Debit"] == 0.0


def test_empty_credit_becomes_zero(raw_table):
    # Row 0 (petro payment) has an empty string for Credit
    df = apply_transform(raw_table)
    assert df.iloc[0]["Credit"] == 0.0


def test_numeric_columns_are_float_type(raw_table):
    df = apply_transform(raw_table)
    assert df["Debit"].dtype == float
    assert df["Credit"].dtype == float
    assert df["Balance"].dtype == float


def test_amounts_are_rounded_to_two_decimal_places(raw_table):
    df = apply_transform(raw_table)
    assert df.iloc[2]["Debit"] == 350.75
    assert df.iloc[2]["Balance"] == 59649.25


# --- Extract Tests (PDF reading is mocked) ---
# We do not open a real PDF. We replace pdfplumber.open with a fake
# that returns our known raw_table. This isolates the test from the filesystem.

def make_pdf_context_mock(mock_pdf):
    """
    Returns a mock for pdfplumber.open() that works correctly as a context manager.
    __exit__ must return False so exceptions raised inside the with block propagate.
    """
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_pdf)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def test_raises_value_error_when_pdf_has_no_pages(in_memory_engine):
    mock_pdf = MagicMock()
    mock_pdf.pages = []

    with patch("pdfplumber.open", return_value=make_pdf_context_mock(mock_pdf)):
        with patch("etl.engine", in_memory_engine):
            from etl import process_bank_statement
            with pytest.raises(ValueError, match="PDF is empty"):
                process_bank_statement("fake_path.pdf")


def test_raises_value_error_when_page_has_no_table(in_memory_engine):
    mock_page = MagicMock()
    mock_page.extract_table.return_value = None

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=make_pdf_context_mock(mock_pdf)):
        with patch("etl.engine", in_memory_engine):
            from etl import process_bank_statement
            with pytest.raises(ValueError, match="No table found"):
                process_bank_statement("fake_path.pdf")


# --- Load Tests (database is in-memory) ---

def test_correct_row_count_is_returned(raw_table, in_memory_engine):
    """
    Mocks the PDF to return our known raw_table and uses an in-memory DB.
    Asserts the function returns the correct count of inserted rows.
    raw_table has 5 data rows, 1 with a None date → expect 4 inserted.
    """
    mock_page = MagicMock()
    mock_page.extract_table.return_value = raw_table

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=make_pdf_context_mock(mock_pdf)):
        with patch("etl.engine", in_memory_engine):
            from etl import process_bank_statement
            count = process_bank_statement("fake_path.pdf")
            assert count == 4


def test_transactions_are_persisted_to_database(raw_table, in_memory_engine):
    """
    After process_bank_statement runs, queries the in-memory DB
    and confirms the rows were actually written.
    """
    from models import Transaction

    mock_page = MagicMock()
    mock_page.extract_table.return_value = raw_table

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=make_pdf_context_mock(mock_pdf)):
        with patch("etl.engine", in_memory_engine):
            from etl import process_bank_statement
            process_bank_statement("fake_path.pdf")

    with Session(in_memory_engine) as session:
        results = session.exec(__import__("sqlmodel").select(Transaction)).all()
        assert len(results) == 4
        assert results[0].description == "UPI/DR/petro payment"
        assert results[1].credit_amount == 50000.00

def test_duplicate_upload_does_not_insert_extra_rows(raw_table, in_memory_engine):
    """
    Calls process_bank_statement twice with the same PDF.
    The second call should insert 0 new rows because all hashes already exist.
    Total rows in DB must still be 4, not 8.
    """
    from models import Transaction

    mock_page = MagicMock()
    mock_page.extract_table.return_value = raw_table

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=make_pdf_context_mock(mock_pdf)):
        with patch("etl.engine", in_memory_engine):
            from etl import process_bank_statement
            first_count = process_bank_statement("fake_path.pdf")
            second_count = process_bank_statement("fake_path.pdf")

    assert first_count == 4
    assert second_count == 0

    with Session(in_memory_engine) as session:
        results = session.exec(__import__("sqlmodel").select(Transaction)).all()
        assert len(results) == 4


def test_transaction_hash_is_stored_on_each_row(raw_table, in_memory_engine):
    """
    After inserting, every row in the DB must have a non-null transaction_hash.
    """
    from models import Transaction

    mock_page = MagicMock()
    mock_page.extract_table.return_value = raw_table

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=make_pdf_context_mock(mock_pdf)):
        with patch("etl.engine", in_memory_engine):
            from etl import process_bank_statement
            process_bank_statement("fake_path.pdf")

    with Session(in_memory_engine) as session:
        results = session.exec(__import__("sqlmodel").select(Transaction)).all()
        for row in results:
            assert row.transaction_hash is not None