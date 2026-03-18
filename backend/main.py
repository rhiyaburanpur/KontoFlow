import os
import shutil
from fastapi import FastAPI, Depends, Query, UploadFile, File, HTTPException
from sqlmodel import SQLModel, Session, select, func
from typing import List, Optional
from models import Transaction, engine
from etl import process_bank_statement

class CategorySummary(SQLModel):
    category: str
    total_debit: float
    total_credit: float
    transaction_count: int

app = FastAPI(title="KontoFlow API", version="1.0")

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/upload-statement")
def upload_statement(
    file: UploadFile = File(...),
    password: Optional[str] = None
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    temp_filename = f"temp_{file.filename}"
    try:
        with open(temp_filename,"wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        count = process_bank_statement(temp_filename, password) # running the ETL pipeline
        return {"message":"Success", "transactions_added": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.get("/transactions", response_model=List[Transaction])
def read_transactions(
    session: Session = Depends(get_session), 
    min_amount: Optional[float] = Query(None)
):
    statement = select(Transaction)
    if min_amount:
        statement = statement.where(
            (Transaction.debit_amount >= min_amount) | 
            (Transaction.credit_amount >= min_amount)
        )
    results = session.exec(statement).all()
    return results

@app.get("/transactions/by-category", response_model=List[CategorySummary])
def transactions_by_category(
    session: Session = Depends(get_session),
    category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    statement = select(
        Transaction.category,
        func.round(func.sum(Transaction.debit_amount), 2).label("total_debit"),
        func.round(func.sum(Transaction.credit_amount), 2).label("total_credit"),
        func.count(Transaction.id).label("transaction_count")
    ).group_by(Transaction.category)

    if category:
        statement = statement.where(Transaction.category == category)
    if start_date:
        statement = statement.where(Transaction.transaction_date >= start_date)
    if end_date:
        statement = statement.where(Transaction.transaction_date <= end_date)

    rows = session.exec(statement).all()

    return [
        CategorySummary(
            category=row[0],
            total_debit=row[1],
            total_credit=row[2],
            transaction_count=row[3]
        )
        for row in rows
    ]