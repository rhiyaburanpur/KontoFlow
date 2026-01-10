from sqlmodel import Session, select
from models import Transaction, engine

with Session(engine) as session:
    statement = select(Transaction)
    results = session.exec(statement).all()

    print(f"\nFound {len(results)} transactions in the database: \n")

    for txn in results:
        print(f"ID: {txn.id} | Date: {txn.transaction_date} | Amount: {txn.debit_amount} | Ref: {txn.reference}")
        