import sys
import os
import tempfile

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, backend_path)

import pytest
from sqlmodel import SQLModel, create_engine, Session

@pytest.fixture(scope="session")
def test_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    try:
        os.unlink(path)
    except PermissionError:
        pass

@pytest.fixture(scope="session")
def test_engine(test_db_path):
    import models
    import etl
    import main

    engine = create_engine(f"sqlite:///{test_db_path}")
    SQLModel.metadata.create_all(engine)

    models.engine = engine
    etl.engine = engine
    main.engine = engine

    return engine

@pytest.fixture(autouse=True)
def clean_db(test_engine):
    yield
    with Session(test_engine) as session:
        from models import Transaction
        from sqlalchemy import text
        session.exec(text('DELETE FROM "transaction"'))
        session.commit()