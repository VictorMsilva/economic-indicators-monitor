## 📄 Project Description

**Real‑Time Economic Indicators Monitor** is a data engineering project designed to automate the ingestion, processing, and delivery of official Brazilian economic indicators — such as **Selic**, **IPCA**, **exchange rates**, and **GDP** — from the **Banco Central do Brasil (SGS API)**.

The goal is to replace manual, spreadsheet‑based workflows with a **fully automated, reliable, and scalable data pipeline** that supports:
- **Market intelligence dashboards** for internal teams
- **Automated alerts** on critical variations (e.g., Selic hikes, inflation surges)
- **Data feeds** for forecasting models in demand, credit, and churn analysis

### 🔍 Key Features
- Automated ingestion from the Bacen SGS API with incremental loads and revision handling  
- Medallion architecture (Bronze → Silver → Gold) for clean separation of raw, curated, and business‑ready data  
- Data Quality checks & quarantine to ensure accuracy and prevent bad data propagation  
- Historical versioning using Parquet + Delta Lake for ACID transactions, upserts, and time travel  
- Metadata & lineage tracking for full traceability from source to dashboard  
- Environment isolation (Dev/Prod) for safe testing and deployment  
- Scalable orchestration with Prefect/Airflow and cloud‑ready storage (S3/MinIO)
