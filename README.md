
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
  - [10. Infrastructure as Code](#10-infrastructure-as-code)
    - [🏗️ **CDK Architecture:**](#️-cdk-architecture)
    - [📦 **Infrastructure Components:**](#-infrastructure-components)
    - [🚀 **Deploy Infrastructure:**](#-deploy-infrastructure)
    - [🔄 **CDK Project Structure:**](#-cdk-project-structure)
    - [📋 **CDK Configuration Files:**](#-cdk-configuration-files)
    - [🎯 **Migration from Terraform:**](#-migration-from-terraform)
  - [11. Current Implementation Status](#11-current-implementation-status)
    - [✅ **Completed:**](#-completed)
    - [🚧 **In Progress:**](#-in-progress)
    - [📋 **Planned:**](#-planned)
  - [12. Getting Started](#12-getting-started)
    - [🔧 **Prerequisites:**](#-prerequisites)
    - [🚀 **Quick Setup:**](#-quick-setup)
    - [📊 **Verify Deployment:**](#-verify-deployment)

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
  - `lambdas/[indicator]/monitor`: checks SGS API and verifies if there was a change
  - `lambdas/[indicator]/bronze2silver`: validates and transforms raw data
  - `lambdas/[indicator]/silver2gold`: calculates final indicators

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
economic-indicators-monitor/
├── README.md
├── DEVELOPMENT.md
├── lambdas/                        # Lambda Functions
│   ├── usdbrl/                     # USD-BRL Pipeline (Implemented)
│   │   ├── monitor/                # Monitors SGS API for changes
│   │   ├── bronze2silver/          # Data quality and validation
│   │   └── silver2gold/            # Financial indicators calculation
│   ├── selic/                      # Selic Pipeline (Future)
│   │   ├── monitor/
│   │   ├── bronze2silver/
│   │   └── silver2gold/
│   ├── ipca/                       # IPCA Pipeline (Future)
│   │   ├── monitor/
│   │   ├── bronze2silver/
│   │   └── silver2gold/
│   └── shared/                     # Shared utilities and libraries
├── infra-aws-cdk/                  # AWS CDK Infrastructure
│   ├── app.py                      # CDK Application entry point
│   ├── economic_indicators_stack.py # Main stack (S3, DynamoDB, IAM)
│   └── usdbrl_lambdas.py          # USD-BRL Lambda functions module
├── configs/                        # Configuration Files
│   ├── indicators.json
│   └── dq-rules.yaml
├── notebooks/                      # Jupyter Notebooks
│   └── analysis-athena.ipynb
├── docs/                          # Documentation
│   └── Economic-Indicators.excalidraw
├── tests/                         # Test Files
│   └── unit/
├── cdk.json                       # CDK Configuration
├── cdk.context.json              # CDK Context Cache
└── cdk.out/                      # CDK Output (ignored)
```

## 10. Infrastructure as Code

The project uses **AWS CDK (Cloud Development Kit)** for infrastructure management, providing a modern, programmatic approach to cloud resources:

### 🏗️ **CDK Architecture:**
- **AWS CDK v2**: Infrastructure defined in Python for better integration with Lambda code
- **Hybrid Modular Design**: Core resources in main stack, Lambda functions in separate modules
- **Environment Isolation**: Configurable for Dev/Prod environments

### 📦 **Infrastructure Components:**
- **S3 Data Lake**: `dl-economic-indicators-prod` with Intelligent Tiering for cost optimization
- **DynamoDB State Table**: `sgs-indicators-state` for tracking indicator processing state
- **Lambda Functions**: Automated deployment with proper IAM roles and environment variables
- **IAM Roles**: Least-privilege access policies for S3 and DynamoDB operations
- **CloudWatch Logs**: 2-week retention for cost optimization

### 🚀 **Deploy Infrastructure:**

**Prerequisites:**
```bash
# Install Node.js and AWS CDK CLI
npm install -g aws-cdk

# Configure AWS credentials
aws configure

# Install Python dependencies
pip install aws-cdk-lib constructs
```

**Deployment Commands:**
```bash
# Bootstrap CDK (one-time setup per account/region)
cdk bootstrap

# Preview changes
cdk synth

# Deploy infrastructure
cdk deploy

# Destroy infrastructure (if needed)
cdk destroy
```

### 🔄 **CDK Project Structure:**
```
infra-aws-cdk/
├── app.py                          # CDK Application entry point
├── economic_indicators_stack.py    # Main stack definition
└── usdbrl_lambdas.py              # Lambda functions module
```

### 📋 **CDK Configuration Files:**
- `cdk.json`: CDK CLI configuration and feature flags
- `cdk.context.json`: Cached AWS account/region information
- `cdk.out/`: Generated CloudFormation templates (ignored in Git)

### 🎯 **Migration from Terraform:**
This project originally used Terraform but was migrated to AWS CDK for:
- **Better Python Integration**: Same language as Lambda functions
- **Type Safety**: IDE support and compile-time error checking
- **AWS Native**: Direct support for latest AWS features
- **Simplified Deployment**: Single tool for infrastructure and application code

---

## 11. Current Implementation Status

### ✅ **Completed:**
- **USD-BRL Pipeline**: Complete medallion architecture implementation
- **AWS CDK Infrastructure**: S3, DynamoDB, Lambda functions, and IAM roles
- **Hybrid Modular Design**: Core infrastructure with separated Lambda modules
- **Data Lake Setup**: Bronze/Silver/Gold layers with proper partitioning

### 🚧 **In Progress:**
- **Lambda Function Testing**: Validating deployed functions with real SGS API data
- **Data Quality Rules**: Implementing comprehensive validation logic

### 📋 **Planned:**
- **Additional Indicators**: Selic, IPCA, GDP pipelines
- **EventBridge Integration**: Event-driven orchestration
- **SQS Queues**: Reliable message processing between layers
- **Athena/Iceberg**: Analytics-ready data consumption
- **Monitoring & Alerts**: CloudWatch dashboards and SNS notifications

---

## 12. Getting Started

### 🔧 **Prerequisites:**
1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Node.js** (for AWS CDK CLI)
4. **Python 3.12+** with virtual environment

### 🚀 **Quick Setup:**

1. **Clone the repository:**
```bash
git clone https://github.com/VictorMsilva/economic-indicators-monitor.git
cd economic-indicators-monitor
```

2. **Set up Python environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install aws-cdk-lib constructs
```

3. **Install CDK CLI:**
```bash
npm install -g aws-cdk
```

4. **Deploy infrastructure:**
```bash
cdk bootstrap  # One-time setup
cdk deploy     # Deploy all resources
```

5. **Test Lambda functions:**
```bash
# Test monitor function
aws lambda invoke --function-name usdbrl-monitor response.json

# Test bronze2silver function  
aws lambda invoke --function-name usdbrl-bronze2silver response.json

# Test silver2gold function
aws lambda invoke --function-name usdbrl-silver2gold response.json
```

### 📊 **Verify Deployment:**
- **S3 Bucket**: `dl-economic-indicators-prod`
- **DynamoDB**: `sgs-indicators-state`
- **Lambda Functions**: `usdbrl-monitor`, `usdbrl-bronze2silver`, `usdbrl-silver2gold`

For detailed development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).
