from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select
from datetime import date

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_date: date
    description: str
    reference: Optional[str] = None
    debit_amount: float = 0.0
    credit_amount: float = 0.0
    balance: float

sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=True) 

def create_db_and_tables():
        SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    print("Creating database and tables...")
    create_db_and_tables()
    print("Done!")