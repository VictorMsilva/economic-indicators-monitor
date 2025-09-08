
# 📄 Real-Time Economic Indicators Monitor

Automated data pipeline for Brazilian economic indicators (Selic, IPCA, exchange rates, GDP) from the Central Bank of Brazil (SGS API).

---

## 📚 Table of Contents

- [📄 Real-Time Economic Indicators Monitor](#-real-time-economic-indicators-monitor)
  - [📚 Table of Contents](#-table-of-contents)
  - [1. Project Description](#1-project-description)
  - [2. Key Features](#2-key-features)
  - [3. Architecture](#3-architecture)
    - [Objective](#objective)
  - [4. Data Layers](#4-data-layers)
  - [5. Orchestration \& Triggers](#5-orchestration--triggers)
  - [6. Data Quality \& Quarantine](#6-data-quality--quarantine)
  - [7. Consumption \& Analytics](#7-consumption--analytics)
  - [8. Observability \& Monitoring](#8-observability--monitoring)
  - [9. Folder Structure](#9-folder-structure)

---

## 1. Project Description

**Real‑Time Economic Indicators Monitor** is a data engineering project designed to automate the ingestion, processing, and delivery of official Brazilian economic indicators — such as **Selic**, **IPCA**, **exchange rates**, and **GDP** — from the Central Bank of Brazil (SGS API).

The goal is to replace manual, spreadsheet-based workflows with a fully automated, reliable, and scalable data pipeline that supports:

- Market intelligence dashboards for internal teams
- Automated alerts on critical variations (e.g., Selic hikes, inflation surges)
- Data feeds for forecasting models in demand, credit, and churn analysis

---

## 2. Key Features

- Automated ingestion from the Bacen SGS API with incremental loads and revision handling
- Medallion architecture (Bronze → Silver → Gold) for clean separation of raw, curated, and business-ready data
- Data quality checks & quarantine to ensure accuracy and prevent bad data propagation
- Historical versioning using Parquet + Delta Lake for ACID transactions, upserts, and time travel
- Metadata & lineage tracking for full traceability from source to dashboard
- Environment isolation (Dev/Prod) for safe testing and deployment
- Scalable orchestration with Prefect/Airflow and cloud-ready storage (S3/MinIO)

---

## 3. Architecture

The pipeline is reactive and scalable for ingesting, transforming, and delivering economic indicators such as USD-BRL, IPCA, Selic, and others. The pipeline is triggered only when there is a real update in the data, ensuring efficiency and resource savings.

### Objective
Update data only when there is a change in the indicators, processing them in three layers (Bronze, Silver, Gold) and making them available for consumption via dashboards, APIs, or analytics.

---

## 4. Data Layers

- **Bronze Layer**  
  Raw data from the Bacen SGS API.  
  Format: JSON  
  Location: `s3://dl-prod/bronze/[indicator]/`

- **Silver Layer**  
  Cleaned, typed, and validated data.  
  Format: Parquet + Iceberg  
  Location: `s3://dl-prod/silver/[indicator]/`

- **Gold Layer**  
  Aggregated and enriched indicators.  
  Format: Parquet + Iceberg  
  Location: `s3://dl-prod/gold/indicators/`

---

## 5. Orchestration & Triggers

- **EventBridge**
  - Rule 1: Detects new file in Bronze → triggers Lambda Bronze → Silver
  - Rule 2: Detects new file in Silver → sends message to SQS Silver → Gold
- **SQS**
  - Queue per indicator and stage (e.g., `sqs-usdbrl-silver2gold`)
  - Ensures reliable delivery and decoupling between transformations
- **Lambda Functions**
  - `lambda-monitor-[indicator]`: checks SGS API and verifies if there was a change
  - `lambda-bronze2silver-[indicator]`: validates and transforms raw data
  - `lambda-silver2gold-[indicator]`: calculates final indicators

---

## 6. Data Quality & Quarantine

Invalid records are stored in S3 with error metadata:

```json
{
  "series_id": 1,
  "ref_date": "2025-09-07",
  "value": "N/A",
  "raw_payload": { "data": "07/09/2025", "valor": "N/A" },
  "dq_status": "invalid",
  "dq_reason": "Missing value",
  "ingest_ts": "2025-09-07T14:22:00Z"
}
```
Location: `s3://dl-prod/quarantine/[indicator]/`

---

## 7. Consumption & Analytics

- **Athena**: Direct SQL queries on Silver and Gold layers. Iceberg support: MERGE, time travel, schema evolution. Used for exploratory analysis, dashboards, and BI tool integration.
- **RDS (optional)**: Replication of Gold data to PostgreSQL or MySQL. Ideal for REST APIs or integration with external systems.
- **EC2 (optional)**: Hosts visual interfaces (e.g., Streamlit, Dash). Can query Athena or RDS.
- **CloudFront**: CDN to distribute interfaces hosted on EC2 or S3.

---

## 8. Observability & Monitoring

- **CloudWatch**: Logs and metrics for all Lambdas
- **Alarms**: For errors, latency, queue backlogs
- **SNS**: Email alerts or automations

**Monitored Metrics:**
  - Errors, Duration, Invocations (Lambda)
  - ApproximateNumberOfMessagesVisible (SQS)
  - FailedInvocations (EventBridge)

**Dashboards:** Centralized health view in CloudWatch

**SGS API Monitoring Strategy:**
  - Lambda scheduled via EventBridge Scheduler (e.g., daily at 9am)
  - Checks the Bacen SGS API
  - Compares with the last saved value (in DynamoDB or Iceberg)
  - If there is a change: writes to Bronze, triggers the pipeline via EventBridge or SQS
  - Avoids unnecessary reprocessing and reduces cost

---

## 9. Folder Structure

```
sgs-indicators-pipeline/
├── README.md
├── lambdas/
│   ├── monitor-usdbrl/
│   ├── bronze2silver-usdbrl/
│   ├── silver2gold-usdbrl/
│   └── shared/
├── infrastructure/
│   ├── eventbridge/
│   ├── sqs/
│   ├── cloudwatch/
│   └── s3-buckets/
├── configs/
│   ├── indicators.json
│   └── dq-rules.yaml
├── notebooks/
│   └── analysis-athena.ipynb
├── docs/
│   └── architecture-diagram.md
└── tests/
    └── unit/
```
