# Serverless

This is a template for Serverless backup of all repositories in our Organization to AWS Code Commit - Below is a brief explanation of what we have generated for you:

```bash
.
├── README.md                   <-- This instructions file
├── backup                     <-- Source code for a lambda function
│   ├── app.py                  <-- Lambda function code
│   ├── requirements.txt        <-- Lambda function code
├── template.yaml               <-- SAM Template
└── tests                       <-- Unit tests
    └── unit
        ├── __init__.py
        └── test_handler.py
```

## Requirements

* AWS CLI already configured with Administrator permission
* [Python 3 installed](https://www.python.org/downloads/)
* `pip3 install aws-sam-cli`

## Setup process

**SAM CLI** is used to emulate Lambda uses our `template.yaml` to understand how to bootstrap this environment (runtime, where the source code is, etc.) - The Lambda Function will get triggered automatically on a daily basis:

```yaml
...
 Events:
        TriggerScheduledEvent:
          Type: Schedule
          Properties:
            Schedule: rate(1 Day)
```

## Packaging and deployment

AWS Lambda Python runtime requires a flat folder with all dependencies including the application. SAM will use `CodeUri` property to know where to look up for both application and dependencies:

```yaml
...
    ServerlessFunction:
    Properties:
      CodeUri: backup/
            ...
```

# SAM CLI commands

## Building the project

[AWS Lambda requires a flat folder](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html) with the application as well as its dependencies in  deployment package. When you make changes to your source code or dependency manifest.

```bash
sam build --base-dir <Absolute path with suffix /backup>
```

## Create S3 bucket

```bash
aws s3 mb s3://BUCKET_NAME
```

## Package Lambda function defined locally and upload to S3 as an artifact

```bash
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket REPLACE_THIS_WITH_YOUR_S3_BUCKET_NAME
```

## Deploy SAM template as a CloudFormation stack

```bash
sam deploy \
    --template-file packaged.yaml \
    --stack-name Serverless \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides NotificationEmail="<your email>"
```

## Describe Output section of CloudFormation stack previously created

```bash
aws cloudformation describe-stacks \
    --stack-name Serverless-Pramodh \
    --query 'Stacks[].Outputs[?OutputKey==`ServerlessApi`]' \
    --output table
```
