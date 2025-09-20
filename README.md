
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

## 4. Data Layers

### **Bronze Layer** (Raw Data)
**Location:** `s3://bucket/bronze/[indicator]/`
**Format:** JSON with original SGS API response
**Purpose:** Historical data preservation and lineage tracking

### **Silver Layer** (Curated Data)
**Location:** `s3://bucket/silver/[indicator]/`
**Format:** Structured JSON with data quality validation
**Purpose:** Clean, validated data ready for analytics

### **Gold Layer** (Business Intelligence)
**Location:** `s3://bucket/gold/[indicator]/`
**Format:** Multiple specialized JSON artifacts optimized for consumption
**Purpose:** Advanced financial analysis, business metrics, and decision support

#### 🎯 **Gold Layer Architecture - 7 Artifact Types:**

**Structure:**
```
gold/
├── metadata/                       # Data catalog and quality metrics
│   └── usdbrl.json                # Comprehensive dataset metadata
├── technical/                      # Technical analysis indicators
│   └── usdbrl_indicators.json     # 17 financial indicators
├── seasonal/                       # Seasonal and cyclical patterns
│   └── usdbrl_patterns.json       # Weekday/monthly patterns
├── aggregations/                   # Time-based aggregations
│   ├── usdbrl_monthly.json        # Monthly OHLC + statistics
│   └── usdbrl_yearly.json         # Yearly performance metrics
└── usdbrl/                        # Indicator-specific summaries
    └── summary/
        ├── latest_summary.json    # Business intelligence summary
        └── summary.json           # Dataset overview
```

**1. Technical Indicators** (`technical/usdbrl_indicators.json`)
```json
{
  "ma_7": 5.3305,                    // Simple Moving Average 7 days
  "ma_30": 5.4080,                   // Simple Moving Average 30 days  
  "ma_90": 5.5072,                   // Simple Moving Average 90 days
  "avg_daily_return": 0.0239,        // Average daily return %
  "daily_volatility": 0.9261,        // Daily price volatility
  "annualized_volatility": 7.904,    // Annualized volatility (252 trading days)
  "max_daily_gain": 4.48,            // Maximum single-day gain %
  "max_daily_loss": -4.51,           // Maximum single-day loss %
  "rolling_volatility_30d": 0.498,   // 30-day rolling volatility
  "momentum_7d": -1.08,              // 7-day price momentum %
  "momentum_30d": -2.20,             // 30-day price momentum %
  "max_drawdown_pct": 22.23,         // Maximum peak-to-trough decline %
  "resistance_level": 5.4828,        // Technical resistance level
  "support_level": 5.301,            // Technical support level
  "trend_slope": 0.0003,             // Linear regression slope
  "trend_direction": "bullish",      // Trend classification
  "rsi_14": 45.67                    // RSI indicator (14-period, if applicable)
}
```

**2. Seasonal Patterns** (`seasonal/usdbrl_patterns.json`)
```json
{
  "weekday_patterns": {
    "Monday": { "average": 5.2134, "count": 264, "volatility": 1.23 },
    "Tuesday": { "average": 5.2087, "count": 265, "volatility": 1.18 }
  },
  "monthly_patterns": {
    "January": { "average": 5.1845, "count": 154, "volatility": 1.67 },
    "February": { "average": 5.2134, "count": 142, "volatility": 1.34 }
  }
}
```

**3. Monthly Aggregations** (`aggregations/usdbrl_monthly.json`)
```json
[
  {
    "period": "2023-01",
    "count": 22,
    "avg_value": 5.1234,
    "min_value": 4.9876,
    "max_value": 5.2567,
    "volatility": 0.0234
  }
]
```

**4. Yearly Aggregations** (`aggregations/usdbrl_yearly.json`)
```json
{
  "2023": {
    "open": 5.1234, "high": 5.6789, "low": 4.7654, "close": 5.3456,
    "average": 5.1987, "median": 5.2087, "yearly_return": 4.34
  }
}
```

**5. Enhanced Summary** (`usdbrl/summary/latest_summary.json`)
```json
{
  "indicator": "usdbrl",
  "latest_value": 5.2890,
  "trend": "bullish",
  "momentum_7d": 2.34,
  "volatility": 1.2456,
  "risk_metrics": {
    "max_drawdown": 8.45,
    "volatility_30d": 1.1234
  }
}
```

**6. Comprehensive Metadata** (`metadata/usdbrl.json`)
```json
{
  "indicator": "usdbrl",
  "name": "USD-BRL Exchange Rate",
  "source": "Banco Central do Brasil",
  "data_range": {
    "start_date": "2020-01-02",
    "end_date": "2025-09-20",
    "total_records": 1847
  },
  "quality_metrics": {
    "completeness": 1.0,
    "consistency": 1.0,
    "timeliness": 1.0
  }
}
```

---

## 🧮 Technical Indicators & Financial Analysis

The Silver2Gold transformation implements **17 advanced technical indicators** for comprehensive financial analysis:

### **📊 Moving Averages & Trend Analysis**
- **Simple Moving Averages**: 7, 30, and 90-day periods for trend identification
- **Trend Slope**: Linear regression coefficient for directional strength
- **Trend Direction**: Algorithmic classification (bullish/bearish/sideways)

### **📈 Volatility & Risk Metrics**
- **Daily Volatility**: Standard deviation of daily returns
- **Annualized Volatility**: Scaled to 252 trading days
- **Rolling Volatility (30d)**: Time-varying volatility measure
- **Maximum Drawdown**: Peak-to-trough decline percentage
- **Max Daily Gain/Loss**: Extreme single-day movements

### **⚡ Momentum Indicators**
- **7-Day Momentum**: Short-term price velocity
- **30-Day Momentum**: Medium-term trend strength
- **Average Daily Return**: Mean return percentage

### **🎯 Support & Resistance Levels**
- **Support Level**: Key downside price level (recent low)
- **Resistance Level**: Key upside price level (recent high)
- **Technical Analysis**: Algorithmic level identification

### **📅 Seasonal Pattern Analysis**
- **Weekday Effects**: Performance by day of week
- **Monthly Seasonality**: Historical patterns by calendar month
- **Volatility Clustering**: Time-based volatility patterns

### **🔢 Statistical Aggregations**
- **Monthly OHLC**: Open, High, Low, Close by month
- **Yearly Performance**: Annual returns and statistics
- **Count & Coverage**: Data completeness metrics

### **Implementation Details**
- **Window Periods**: Configurable lookback periods for all indicators
- **Data Quality**: Handles missing data and outliers
- **Performance**: Optimized for large time series (1400+ data points)
- **Accuracy**: Uses industry-standard financial calculation methods

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
  - `lambdas/[indicator]/silver2gold`: calculates advanced financial indicators and business intelligence

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

### **Advanced Financial Analysis**
The Gold layer provides comprehensive financial intelligence through multiple specialized artifacts:

- **Technical Analysis**: 17+ indicators including moving averages, volatility, momentum, drawdown analysis
- **Trend Analysis**: Linear regression with bullish/bearish/sideways classification  
- **Seasonal Patterns**: Day-of-week and monthly behavioral analysis
- **Risk Metrics**: Drawdown analysis, volatility measurements, support/resistance levels
- **Time-based Aggregations**: Monthly and yearly OHLC data with performance metrics

### **Query Interfaces**
- **Athena**: Direct SQL queries on Silver and Gold layers. Iceberg support: MERGE, time travel, schema evolution. Used for exploratory analysis, dashboards, and BI tool integration.
- **RDS (optional)**: Replication of Gold data to PostgreSQL or MySQL. Ideal for REST APIs or integration with external systems.
- **REST API**: AWS API Gateway endpoints for programmatic access to indicators and analytics
- **EC2 (optional)**: Hosts visual interfaces (e.g., Streamlit, Dash). Can query Athena or RDS.
- **CloudFront**: CDN to distribute interfaces hosted on EC2 or S3.

### **REST API Endpoints**

Base URL: `https://j2a31q0ubd.execute-api.us-east-2.amazonaws.com/prod/`

#### **Available Endpoints**

**1. Individual Indicator Data**
```bash
GET /indicators/{indicator}?mode={mode}&limit={limit}
```

**2. All Indicators Summary**
```bash
GET /indicators/all?mode={mode}
```

#### **Query Parameters**

| Parameter | Values | Description | Default |
|-----------|--------|-------------|---------|
| `mode` | `data`, `summary`, `aggregations` | Response format type | `data` |
| `limit` | Integer | Number of records (data mode only) | `10` |

#### **Response Modes**

**📊 Data Mode** (`?mode=data`)
```bash
curl "/indicators/usdbrl?mode=data&limit=5"
```
Returns paginated historical data with metadata:
```json
{
  "indicator": "usdbrl",
  "data": [
    {
      "indicator": "usdbrl",
      "name": "USD-BRL Exchange Rate",
      "statistics": {
        "count": 1436,
        "min": 4.0213,
        "max": 6.2086,
        "mean": 5.2774,
        "latest_value": 5.3276
      },
      "data_quality": "valid",
      "s3_key": "gold/usdbrl/summary.json"
    }
  ]
}
```

**💡 Summary Mode** (`?mode=summary`)
```bash
curl "/indicators/usdbrl?mode=summary"
```
Returns business intelligence summary with technical analysis:
```json
{
  "indicator": "usdbrl",
  "latest_value": 5.3276,
  "latest_date": "2025-09-19",
  "trend": "bullish",
  "momentum_7d": -1.08,
  "volatility": 0.926,
  "support_level": 5.301,
  "resistance_level": 5.4828,
  "data_quality_score": 1.0,
  "statistics": {
    "count": 1436,
    "min": 4.0213,
    "max": 6.2086,
    "mean": 5.2774
  },
  "risk_metrics": {
    "max_drawdown": 22.23,
    "volatility_30d": 0.498
  }
}
```

**📈 Aggregations Mode** (`?mode=aggregations`)
```bash
curl "/indicators/usdbrl?mode=aggregations"
```
Returns comprehensive financial analysis with 4 data types:
```json
{
  "indicator": "usdbrl",
  "aggregations": {
    "monthly": [
      {
        "period": "2025-09",
        "count": 15,
        "avg_value": 5.3861,
        "min_value": 5.301,
        "max_value": 5.468,
        "volatility": 0.0605
      }
    ],
    "yearly": {
      "2024": {
        "open": 4.8916,
        "high": 6.1991,
        "low": 4.8543,
        "close": 6.1923,
        "yearly_return": 26.59
      }
    },
    "technical_indicators": {
      "ma_7": 5.3305,
      "ma_30": 5.4080,
      "ma_90": 5.5072,
      "daily_volatility": 0.9261,
      "annualized_volatility": 7.904,
      "momentum_7d": -1.08,
      "momentum_30d": -2.20,
      "max_drawdown_pct": 22.23,
      "resistance_level": 5.4828,
      "support_level": 5.301,
      "trend_direction": "bullish"
    },
    "seasonal_patterns": {
      "weekday_patterns": {
        "Monday": { "average": 5.281, "volatility": 0.358 }
      },
      "monthly_patterns": {
        "September": { "average": 5.295, "volatility": 0.209 }
      }
    }
  }
}
```

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
│   ├── usdbrl/                     # USD-BRL Pipeline (Fully Implemented)
│   │   ├── monitor/                # Monitors SGS API for changes
│   │   ├── bronze2silver/          # Data quality and validation
│   │   └── silver2gold/            # Advanced financial analysis (17+ indicators)
│   ├── api/                        # REST API Gateway Function
│   │   └── lambda_function.py      # Multi-mode endpoint handler
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
│   └── indicators.json
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
- **USD-BRL Pipeline**: Complete medallion architecture with advanced financial analysis
- **AWS CDK Infrastructure**: S3, DynamoDB, Lambda functions, IAM roles, and API Gateway
- **Data Lake Setup**: Bronze/Silver/Gold layers with proper partitioning
- **Advanced Analytics**: 17 technical indicators including MA, volatility, momentum, drawdown analysis
- **REST API**: Fully functional with 3 consumption modes (data/summary/aggregations)
- **Gold Layer Intelligence**: 7 specialized artifacts with comprehensive financial analysis
- **Risk Metrics**: Maximum drawdown, volatility clustering, support/resistance identification
- **Seasonal Analysis**: Weekday and monthly pattern recognition with statistical validation
- **Technical Indicators**: Moving averages, trend analysis, momentum indicators, risk assessment
- **Data Quality**: Comprehensive validation and metadata tracking with 100% data quality scores

### 🚧 **In Progress:**
- **Documentation**: Technical specification updates and API examples (current task)
- **Performance Optimization**: Lambda function memory and timeout tuning
- **Enhanced Monitoring**: CloudWatch dashboard for pipeline health metrics

### 📋 **Planned:**
- **Additional Indicators**: Selic, IPCA, GDP pipelines with similar financial analysis
- **EventBridge Integration**: Event-driven orchestration for real-time processing
- **SQS Queues**: Reliable message processing between layers
- **Athena/Iceberg**: Analytics-ready data consumption with time travel capabilities
- **Monitoring & Alerts**: SNS notifications for anomaly detection and threshold breaches
- **Machine Learning**: Forecasting models based on technical indicators and seasonal patterns
- **Authentication**: API key management and rate limiting implementation

---

## 📈 Financial Analysis Capabilities

The Gold layer implements advanced financial analysis for comprehensive market intelligence:

### **Technical Indicators (17+ Metrics)**
- **Moving Averages**: 7, 30, and 90-day periods for trend identification
- **Volatility Analysis**: Daily and annualized volatility (252 trading days)
- **Momentum Indicators**: 7-day and 30-day momentum calculations
- **Risk Metrics**: Maximum drawdown analysis from peak values
- **Support/Resistance**: Dynamic price levels based on recent data
- **Trend Analysis**: Linear regression with directional classification

### **Seasonal Pattern Analysis**
- **Weekday Effects**: Statistical analysis of Monday-Friday performance patterns
- **Monthly Seasonality**: Historical monthly averages with volatility measurements
- **Behavioral Insights**: Trading patterns and market tendencies by time period

### **Time-Based Aggregations**
- **Monthly Summaries**: OHLC data, averages, volatility, and first/last values
- **Annual Performance**: Yearly returns, median values, and comprehensive statistics
- **Historical Analysis**: Complete time series with statistical measures

### **Business Intelligence Features**
- **Data Quality Scoring**: Completeness, consistency, and timeliness metrics
- **Metadata Management**: Comprehensive indicator information and lineage
- **Real-time Updates**: Latest values with trend direction and momentum
- **Risk Assessment**: Drawdown percentages and volatility regime classification

### **API Integration**
All financial analysis is available through RESTful endpoints:
```bash
# Technical indicators and risk metrics
GET /indicators/usdbrl?mode=aggregations

# Latest market intelligence summary  
GET /indicators/usdbrl?mode=summary

# Raw time series data
GET /indicators/usdbrl?limit=100
```

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

**Infrastructure Components:**
- **S3 Bucket**: `dl-economic-indicators-prod` with Bronze/Silver/Gold structure
- **DynamoDB**: `sgs-indicators-state` for indicator state management
- **API Gateway**: REST API with CORS-enabled endpoints
- **Lambda Functions**: Complete USD-BRL pipeline with financial analysis

**Test API Endpoints:**
```bash
# Get latest USD-BRL data
curl -X GET "https://your-api-id.execute-api.region.amazonaws.com/prod/indicators/usdbrl?limit=5"

# Get technical analysis summary
curl -X GET "https://your-api-id.execute-api.region.amazonaws.com/prod/indicators/usdbrl?mode=summary"

# Get aggregations and indicators  
curl -X GET "https://your-api-id.execute-api.region.amazonaws.com/prod/indicators/usdbrl?mode=aggregations"
```

**Expected S3 Gold Layer Structure:**
```
gold/
├── metadata/usdbrl.json              # Comprehensive metadata
├── aggregations/
│   ├── usdbrl_monthly.json          # Monthly OHLC data
│   └── usdbrl_yearly.json           # Annual performance
├── technical/usdbrl_indicators.json  # 17+ technical indicators
├── seasonal/usdbrl_patterns.json    # Weekday/monthly patterns  
├── usdbrl/summary/latest_summary.json # Business intelligence
└── usdbrl/summary.json              # Legacy compatibility
```

**Lambda Function Testing:**
```bash
# Test complete pipeline
aws lambda invoke --function-name usdbrl-monitor response.json
aws lambda invoke --function-name usdbrl-bronze2silver response.json  
aws lambda invoke --function-name usdbrl-silver2gold response.json
```

For detailed development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).
