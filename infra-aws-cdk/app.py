#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import aws_cdk as cdk
from economic_indicators_stack import EconomicIndicatorsStack

app = cdk.App()

# Stack principal com todos os recursos
EconomicIndicatorsStack(
    app, 
    "EconomicIndicatorsStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region="us-east-2"
    )
)

app.synth()