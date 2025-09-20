# Development Guide

## Getting Started

This project uses Python 3.9+ for Lambda functions and Terraform for infrastructure management.

### Prerequisites

1. **Terraform**: Install from [terraform.io](https://terraform.io)
2. **AWS CLI**: Configured with appropriate credentials
3. **Python 3.9+**: For Lambda development

### Setup Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install pytest boto3 moto requests python-dateutil
   ```

3. Install specific function dependencies:
   ```bash
   cd lambdas/usdbrl/monitor
   pip install -r requirements.txt
   ```

### Infrastructure Setup

1. **Initialize Terraform backend** (one-time setup):
   ```bash
   cd infrastructure/terraform
   ./setup-backend.sh
   ```

2. **Deploy infrastructure**:
   ```bash
   terraform init
   terraform plan    # Review changes
   terraform apply   # Deploy
   ```

3. **Manage infrastructure**:
   ```bash
   terraform plan    # Preview changes
   terraform apply   # Apply changes
   terraform destroy # Clean up (careful!)
   ```

### Testing Locally

Each Lambda function folder has a `test_local.py` script to test the function locally:

```bash
cd lambdas/usdbrl/monitor
python test_local.py
```

### Infrastructure Overview

- **S3 Bucket**: `dl-economic-indicators-prod` (data lake)
- **DynamoDB**: `sgs-indicators-state` (Lambda state management)
- **Terraform Backend**: 
  - S3: `economic-indicators-terraform-state`
  - DynamoDB: `economic-indicators-terraform-locks`

### Folder Structure

The project is organized by indicator first, then by processing stage:

```
lambdas/
├── usdbrl/               # USD-BRL Exchange Rate
│   ├── monitor/          # Monitors API for changes
│   ├── bronze2silver/    # Processes raw data
│   └── silver2gold/      # Creates refined metrics
├── selic/                # Selic Rate
│   ├── monitor/
│   ├── bronze2silver/
│   └── silver2gold/
└── shared/               # Shared utility functions
```

### Configuration

- `configs/indicators.json`: Contains API endpoints and parameters for each indicator

### Infrastructure as Code

The project uses **Terraform modules** for infrastructure:

```
infrastructure/terraform/
├── modules/
│   ├── s3/           # S3 bucket with cost optimization
│   └── lambda/       # Lambda functions with IAM roles
├── main.tf           # Main infrastructure
├── variables.tf      # Configuration variables
└── outputs.tf        # Infrastructure outputs
```

**Key Resources:**
- S3 bucket with Intelligent Tiering (cost optimization)
- DynamoDB for Lambda state management
- IAM roles with least privilege access
- Remote state with locking mechanism

### Contributing

1. Create a branch for your feature
2. Implement your changes
3. Update infrastructure via Terraform
4. Write/update tests
5. Submit a PR
