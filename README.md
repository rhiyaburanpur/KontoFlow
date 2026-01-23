# KontoFlow 

> **⚠️ Project Status: Phase 1 (Active Development)**
> Currently establishing the Backend Architecture, ETL Pipeline, and Database Persistence layers.
> _Last Updated: January 2026_

**KontoFlow** is a modern financial data engine designed to automate the extraction, cleaning, and storage of bank transactions. It transforms unstructured PDF bank statements into structured, queryable data via a RESTful API.

---

## Architecture (Phase 1)

This phase focuses on the **Data Engineering** and **Backend** foundations:



1.  **ETL Pipeline:** Extracts raw tables from PDF statements using `pdfplumber`, cleans data with `pandas`, and normalizes formats.
2.  **Persistence Layer:** Stores structured transaction data in a relational database (`SQLite`) using `SQLModel` (ORM).
3.  **REST API:** Exposes data via `FastAPI` for external consumption.

---

## Tech Stack

* **Language:** Python 3.13
* **API Framework:** FastAPI
* **Database / ORM:** SQLite / SQLModel
* **Data Processing:** Pandas
* **PDF Extraction:** PDFPlumber

---

## Getting Started

### 1. Prerequisites
* Python 3.10+
* Git

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone [https://github.com/rhiyaburanpur/KontoFlow.git](https://github.com/rhiyaburanpur/KontoFlow.git)
cd KontoFlow
pip install fastapi uvicorn sqlmodel pandas pdfplumber python-multipart python-dotenv
