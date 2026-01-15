from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from typing import List
from models import Transaction, engine

app = FastAPI(title="KontoFlow API", version="1.0")

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/transactions", response_model=List[Transaction])
def read_transactions(session: Session = Depends(get_session)):
    """
    Fetch all transactions from the database.
    """
    statement = select(Transaction)
    results = session.exec(statement).all()
    return results

@app.get("/")
def read_root():
    return {"message": "Welcome to KontoFlow API. Visit /docs for the menu."}