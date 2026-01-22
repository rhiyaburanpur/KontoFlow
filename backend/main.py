import os
import shutil
from fastapi import FastAPI, Depends, Query, UploadFile, File, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from models import Transaction, engine
from etl import process_bank_statement

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