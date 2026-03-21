import pdfplumber as pdfp
import pandas as pd
from sqlmodel import Session, select
from models import Transaction, engine
from categorizer import categorize
import hashlib

def compute_hash(transaction_date, description, debit_amount, credit_amount):
    raw = f"{transaction_date}|{description}|{debit_amount}|{credit_amount}"
    return hashlib.sha256(raw.encode()).hexdigest()

def process_bank_statement(pdf_path: str, pdf_password: str = None):
    # extraction
    try:
        with pdfp.open(pdf_path, password=pdf_password) as pdf:
            if not pdf.pages:
                raise ValueError("PDF is empty")
            table = pdf.pages[0].extract_table()
            if not table:
                raise ValueError("No table found on the first page")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to read the PDF: {e}")

    # transformation
    df = pd.DataFrame(table[1:], columns=table[0])

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

   # load
    count = 0
    with Session(engine) as session:
        for _, row in df.iterrows():
            txn_hash = compute_hash(
                row['Date'].date(),
                row['Details'],
                row['Debit'],
                row['Credit']
            )

            existing = session.exec(
                select(Transaction).where(Transaction.transaction_hash == txn_hash)
            ).first()

            if existing:
                continue

            txn = Transaction(
                transaction_date=row['Date'].date(),
                description=row['Details'],
                reference=row["Ref No./Cheque\nNo"] if row['Ref No./Cheque\nNo'] != '-' else None,
                debit_amount=row["Debit"],
                credit_amount=row['Credit'],
                balance=row["Balance"],
                category=categorize(row['Details']),
                transaction_hash=txn_hash
            )
            session.add(txn)
            count += 1

        session.commit()
    return count