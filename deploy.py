#!/usr/bin/env python3
import os
import sys
import json
import time
import zipfile
import io
import boto3

REGION = "us-east-1"
PROJECT_NAME = "invoice-ocr-z52"

# Load .env
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

for lower_key in ['aws_access_key_id', 'aws_secret_access_key', 'aws_session_token']:
    val = os.getenv(lower_key)
    if val:
        os.environ[lower_key.upper()] = val

if not os.getenv("AWS_ACCESS_KEY_ID"):
    print("ERROR: Brak AWS credentials w .env!")
    sys.exit(1)

sts = boto3.client('sts', region_name=REGION)
account_id = sts.get_caller_identity()['Account']
LAMBDA_ROLE_ARN = f"arn:aws:iam::{account_id}:role/LabRole"

lambda_client = boto3.client('lambda', region_name=REGION)
apigateway = boto3.client('apigatewayv2', region_name=REGION)

print("Tworzę pakiet Lambda...")
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write('lambda_function.py', 'lambda_function.py')
zip_bytes = zip_buffer.getvalue()

function_name = f"{PROJECT_NAME}-function"

try:
    func = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.12',
        Role=LAMBDA_ROLE_ARN,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_bytes},
        Timeout=60,
        MemorySize=256
    )
    function_arn = func['FunctionArn']
except lambda_client.exceptions.ResourceConflictException:
    print("Funkcja istnieje — aktualizuję kod...")
    lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_bytes
    )
    function_arn = lambda_client.get_function(
        FunctionName=function_name
    )['Configuration']['FunctionArn']

waiter = lambda_client.get_waiter('function_active_v2')
waiter.wait(FunctionName=function_name)

print("Tworzę API Gateway...")
api = apigateway.create_api(
    Name=f"{PROJECT_NAME}-api",
    ProtocolType='HTTP'
)

api_id = api['ApiId']
endpoint = api['ApiEndpoint']

integration = apigateway.create_integration(
    ApiId=api_id,
    IntegrationType='AWS_PROXY',
    IntegrationUri=function_arn,
    PayloadFormatVersion='2.0'
)

apigateway.create_route(
    ApiId=api_id,
    RouteKey='POST /invoice',
    Target=f"integrations/{integration['IntegrationId']}"
)

apigateway.create_stage(
    ApiId=api_id,
    StageName='$default',
    AutoDeploy=True
)

lambda_client.add_permission(
    FunctionName=function_name,
    StatementId='apigateway-invoke',
    Action='lambda:InvokeFunction',
    Principal='apigateway.amazonaws.com',
    SourceArn=f"arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*"
)

print("\nDeployment zakończony!")
print(f"Endpoint: {endpoint}/invoice")