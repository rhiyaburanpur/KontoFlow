import pdfplumber as pdfp
import pandas as pd 
import os
from dotenv import load_dotenv

load_dotenv()

import pdfplumber as pdfp
import pandas as pd
import os
from dotenv import load_dotenv

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
        
        if table:
            print("\n Extracted Data Preview: \n")
            for row in table[:3]:
                print(row)
        else:
            print('No table data found on the first page.')

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

except Exception as e:
    print(f"An error occurred: {e}")

df.rename(columns={
    "Ref No./Cheque\nNo": "Reference",
    "Date": "transaction_date",
    "Details": "description",
    "Debit": "debit_amount",
    "Credit": "credit_amount",
    "Balance": "balance"
}, inplace=True)

df.to_csv("c:/dev/KontoFow/backend/cleaned_statement.csv", index=False)
print("Saved cleaned data to cleaned_statement.csv")