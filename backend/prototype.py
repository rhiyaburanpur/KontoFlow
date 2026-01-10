import pdfplumber as pdfp
import pandas as pd 
import os
from dotenv import load_dotenv
from sqlmodel import Session, select
from models import Transaction, engine, create_db_and_tables

load_dotenv()
pdf_path = os.getenv("PDF_PATH")
pdf_password = os.getenv("PDF_PASSWORD")

if not pdf_path or not pdf_password:
    print("Error: Could not find PDF_PATH or PDF_PASSWORD in .env file.")
    print("Make sure you created the .env file in the same folder as your script or project root.")
    exit()

try:
    with pdfp.open(pdf_path, password=pdf_password) as pdf:
        first_page = pdf.pages[0]
        table = first_page.extract_table()
        
        if not table:
            print("Error: No table found")
            exit()

    df = pd.DataFrame(table[1:], columns=table[0])
    if 'Details' in df.columns:
        df['Details'] = df['Details'].str.replace('\n', ' ', regex=False)

    df.fillna("-", inplace=True)

    df['Date'] = pd.to_datetime(df["Date"], format="mixed")

    numeric_cols = ["Debit", "Credit", "Balance"]
    for col in numeric_cols:
         df[col] = df[col].astype(str).str.replace(',', '')

    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0).round(2)
    print(df.head())

    print("Intializing Database")
    create_db_and_tables()
    with Session(engine) as session:
        count = 0 
        for index, row in df.iterrows():
            txn = Transaction(
                transaction_date=row["Date"].date(),
                description=row["Details"],
                reference=row["Ref No./Cheque\nNo"] if row["Ref No./Cheque\nNo"] != '-' else None,
                debit_amount=row["Debit"],
                credit_amount=row["Credit"],
                balance=row["Balance"]
            )
            session.add(txn)
            count+=1

        session.commit()
    print(f"Saved {count} transactions to database.db successfully.")

except Exception as e:
    import traceback
    traceback.print_exc()
    
df.to_csv("c:/dev/KontoFow/backend/cleaned_statement.csv", index=False)
print("Saved cleaned data to cleaned_statement.csv")