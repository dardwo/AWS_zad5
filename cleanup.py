#!/usr/bin/env python3
import boto3

REGION = "us-east-1"
PROJECT_NAME = "invoice-ocr-z52"

lambda_client = boto3.client('lambda', region_name=REGION)
apigateway = boto3.client('apigatewayv2', region_name=REGION)

lambda_client.delete_function(FunctionName=f"{PROJECT_NAME}-function")

print("Usuń API ręcznie w konsoli (HTTP API).")
print("Cleanup Lambda zakończony.")