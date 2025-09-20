# Development Guide

## Getting Started

This project uses Python 3.9+ for Lambda functions and AWS CDK v2 for infrastructure management.

### Prerequisites

1. **AWS CDK**: Install from [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
   ```bash
   npm install -g aws-cdk
   ```
2. **AWS CLI**: Configured with appropriate credentials
3. **Python 3.9+**: For Lambda development
4. **Node.js**: Required for CDK operations

### Setup Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install CDK dependencies:
   ```bash
   pip install aws-cdk-lib constructs
   ```

3. Install development dependencies:
   ```bash
   pip install pytest boto3 moto requests python-dateutil
   ```

4. Install specific function dependencies:
   ```bash
   cd lambdas/usdbrl/monitor
   pip install -r requirements.txt
   ```

### Infrastructure Setup

1. **Bootstrap CDK** (one-time setup):
   ```bash
   cdk bootstrap
   ```

2. **Deploy infrastructure**:
   ```bash
   cdk deploy                    # Deploy all resources
   cdk deploy --hotswap         # Fast deployment for development
   cdk diff                     # Show changes before deploy
   ```

3. **Manage infrastructure**:
   ```bash
   cdk synth                    # Generate CloudFormation template
   cdk destroy                  # Clean up (careful!)
   ```

### Testing Locally

Each Lambda function folder has a `test_local.py` script to test the function locally:

```bash
cd lambdas/usdbrl/monitor
python test_local.py
```

### Infrastructure Overview

- **S3 Bucket**: Data lake with Bronze/Silver/Gold layers
- **DynamoDB**: State management for Lambda functions
- **API Gateway**: REST API endpoints for data consumption
- **Lambda Functions**: Processing pipeline (monitor, bronze2silver, silver2gold, api)
- **CDK Configuration**: Infrastructure as Code with TypeScript/Python constructs

### Folder Structure

The project is organized by indicator first, then by processing stage:

```
lambdas/
├── usdbrl/               # USD-BRL Exchange Rate (COMPLETE)
│   ├── monitor/          # Monitors API for changes
│   ├── bronze2silver/    # Processes raw data
│   └── silver2gold/      # Creates 17 technical indicators + analytics
├── selic/                # Selic Rate (PLANNED)
│   ├── monitor/
│   ├── bronze2silver/
│   └── silver2gold/
├── api/                  # REST API Gateway Function (COMPLETE)
└── shared/               # Shared utility functions
```

### Configuration

- `configs/indicators.json`: Contains API endpoints and parameters for each indicator

### Infrastructure as Code

The project uses **AWS CDK v2** for infrastructure:

```
infra-aws-cdk/
├── app.py                # CDK app entry point
├── stacks/              
│   └── economic_indicators_stack.py    # Main infrastructure stack
├── constructs/           # Reusable CDK constructs
├── cdk.json             # CDK configuration
└── requirements.txt     # CDK dependencies
```

### API Testing

Test the deployed API with different modes:

```bash
# Base URL (replace with your deployed endpoint)
API_URL="https://j2a31q0ubd.execute-api.us-east-2.amazonaws.com/prod"

# Test summary mode - business intelligence
curl "$API_URL/indicators/usdbrl?mode=summary"

# Test aggregations mode - technical analysis
curl "$API_URL/indicators/usdbrl?mode=aggregations"

# Test data mode - historical data
curl "$API_URL/indicators/usdbrl?mode=data&limit=5"
```

### Contributing

1. Create a branch for your feature
2. Implement your changes
3. Update infrastructure via Terraform
4. Write/update tests
5. Submit a PR
