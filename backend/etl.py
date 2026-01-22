import pdfplumber as pdfp
import pandas as pd
from sqlmodel import Session
from models import Transaction,engine

def process_bank_statement(pdf_path: str, pdf_password: str = None):
    #extraction of the pdf content
    try:
        with pdfp.open(pdf_path, password=pdf_password) as pdf:
            if not pdf.pages:
                raise ValueError("PDF is empty")
            table = pdf.pages[0].extract_table()

            if not table:
                raise ValueError("No table found on the first page")
    except Exception as e:
        raise ValueError(f"Failed to read the PDF: {e}")

    # transformation
    df = pd.DataFrame(table[1:], columns= table[0])
    
    # data cleaning
    if "Details" in df.columns:
        df['Details'] = df["Details"].str.replace("\n"," ",regex=False)

    df.fillna('-',inplace=True)

    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    df.dropna(subset=["Date"], inplace=True)   #drop rows when data failed to parse

    numeric_cols = ["Debit","Credit","Balance"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", "")
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).round(2)

    # load
    count = 0
    with Session(engine) as session:
        for index, row in df.iterrows():
            txn= Transaction(
                transaction_date=row['Date'].date(),
                description=row['Details'],
                reference=row["Ref No./Cheque\nNo"] if row['Ref No./Cheque\nNo'] != '-' else None,
                debit_amount=row["Debit"],
                credit_amount=row['Credit'],
                balance=row["Balance"]
            )
            session.add(txn)
            count+=1
        
        session.commit()
    
    return count