# Lab 3: Monitoring a Distributed Application on AWS

**Objective:**
Build and monitor a production-like **distributed system** using AWS-managed services. You will instrument the system with **CloudWatch**, **X-Ray**, and **SNS** to observe behavior and receive alerts in case of failures.

**Estimated Time:** 90 minutes
**Prerequisites:** AWS admin access, basic CLI/Git knowledge, CloudWatch and Lambda fundamentals.

---

## Architecture Overview

```text
User Request
    │
    ▼
Elastic Beanstalk (Frontend Python App)
    │
    ▼
API Gateway (REST API)
    │
    ▼
Lambda Function (Processes request)
    │
    ▼
DynamoDB (Stores record)
```

* Each layer is independently managed, fault-isolated, and instrumented.
* X-Ray traces from Beanstalk → API Gateway → Lambda → DynamoDB.
* CloudWatch alarms monitor request volume and latency.

---

## Step-by-Step Instructions

---

### 1. Set Up Elastic Beanstalk (Frontend App)

#### 1.1 Create Beanstalk Environment

1. In Visual Studio Code Bash terminal, create a new file named `application.py` with the sample code below.

```python
# app.py
import os
import requests
from flask import Flask

application = Flask(__name__)

API_URL = os.environ.get("BACKEND_API_URL")

@application.route("/")
def index():
    try:
        res = requests.post(f"{API_URL}/record", json={"user": "sre-student"})
        return f"Backend Response: {res.text}"
    except Exception as e:
        return f"Error contacting backend: {e}", 500
```

2. Create a `requirements.txt`:

```txt
flask
requests
```

3. Zip the files.
4. In the AWS Console, go to **Elastic Beanstalk** → **Create Application**

   * Name: `sre-distapp`
   * Platform: **Python 3.13**
   * Application Code: Select **Upload your code** and choose the zip file from step 3.
7. In **Configure service access**, create a service role and EC2 instance profile with the defaults
8. In **Configure updates, monitoring, and logging - optional**, set:

   * Add a new environment property `BACKEND_API_URL`: Leave it blank for now. We'll update this after deploying API Gateway.
9. In **Platform -> Software**, enable:

   * **AWS X-Ray - X-Ray daemon** tracing
   * **CloudWatch Logs -> Log streaming**
11. Deploy and note the application **URL**.
12. **NOTE:** If you get a `CREATE_FAILED` error, click on **Actions -> Rebuild environment** then try again.

---

### 2. Set Up Backend API (API Gateway + Lambda + DynamoDB)

#### 2.0 Create IAM role

1. In **IAM** -> **Roles** create an IAM role for the Lambda service with the following: 
   1. Name: **EC2_DynamoDB_Access**
   2. Policies: **AmazonDynamoDBFullAccess**, **AWSLambda_FullAccess**, **AWSXrayFullAccess**

#### 2.1 Create DynamoDB Table

In VS Code, open a Bash terminal window and run the following command:
```bash
aws dynamodb create-table \
  --table-name UserRecords \
  --attribute-definitions AttributeName=RecordId,AttributeType=S \
  --key-schema AttributeName=RecordId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

#### 2.2 Create Lambda Function

Use this Python code for `lambda_function.py`:

```python
import json
import boto3
import uuid
import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UserRecords')

def lambda_handler(event, context):
    record_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat()
    table.put_item(Item={"RecordId": record_id, "Timestamp": timestamp})
    return {
        'statusCode': 200,
        'body': f'Record saved with ID: {record_id}'
    }
```

Deploy it:

```bash
zip function.zip lambda_function.py
aws lambda create-function \
  --function-name SaveUserRecord \
  --runtime python3.9 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --role <LAMBDA_EXECUTION_ROLE_ARN> \
  --tracing-config Mode=Active
```

> Replace `<LAMBDA_EXECUTION_ROLE_ARN>` with an IAM role ARN that has access to Lambda, DynamoDB, and X-Ray with the IAM role you created. In **IAM**, choose the role you created, and at the top, copy the ARN. Example ARN: `arn:aws:iam::327632770096:role/EC2_DynamoDB_Access`

#### 2.3 Create API Gateway

1. Go to **API Gateway** → Create API > Rest API > Build > New API
2. Enter `UserRecords` for API Name and create it
3. Create a new resource `/record`
4. Create a **POST** method for `/record` → Integrate it with the Lambda function.
5. Enable **X-Ray tracing** in stage settings.
6. Click `Deploy API`, enter `prod` for the stage and click `Deploy` 
7. Copy the Invoke URL (e.g., `https://abc123.execute-api.us-west-2.amazonaws.com/prod`).

---

### 3. Update Beanstalk Environment

1. Go back to **Elastic Beanstalk > Environments > [YOUR_ENVIRONMENT] > Configuration **
2. Under **Updates, monitoring, and logging**, scroll to the bottom of the page.
3. Set `BACKEND_API_URL` to your API Gateway base URL.
4. Save and deploy.

Now, Beanstalk forwards requests to API Gateway → Lambda → DynamoDB.

---

### 4. Generate Traffic

From your VS Code Bash terminal:

```bash
while true; do curl http://<your-beanstalk-url>; sleep 1; done
```

Let this run to build up metrics and traces.

---

### 5. Add Monitoring and Alerting

#### 5.1 CloudWatch Metrics and Dashboards

1. Go to **CloudWatch > Dashboards > Create Dashboard > `Lab3_Dashboard`**.
2. Add widgets (Choose a suitable widget type for each of the metrics below):

   * `API Gateway - 5xxError`, `Latency`, `Count`
   * `Lambda - Duration`, `Errors`
   * `DynamoDB - SuccessfulRequestLatency`

#### 5.2 Create Alarms

Example: Alert on high API latency

1. Go to **Alarms > Create Alarm**.

2. Select API Gateway latency metric:

   * Condition: `> 1000ms` for `2` out of `5` minutes
   * Action: Create SNS topic, subscribe with your email

3. Create a similar alarm for Lambda function error count > 1.

---

### 6. Explore Tracing with AWS X-Ray

1. Open **CloudWatch > X-Ray traces**.
2. View the **Trace Map**:
3. Drill into traces to analyze bottlenecks, errors, and latency.

---

### 7. Simulate Failure

1. Delete the Lambda function.
2. Run traffic for 5 minutes.
3. Watch for:

   * Alarms firing in **CloudWatch**
   * Alerts in your **email** from SNS

---

### 8. Cleanup Resources

```bash
aws dynamodb delete-table --table-name UserRecords
aws lambda delete-function --function-name SaveUserRecord
# Delete API Gateway manually or with CloudFormation if used
# Terminate Beanstalk environment in AWS Console
# Delete CloudWatch alarms and dashboard
# Delete SNS topic and unsubscribe
```

---

## Reflection & Challenge

* How would you extend this architecture to include a **messaging layer** like SQS or EventBridge?
* What kinds of **custom application metrics** could enhance observability?
* How would you apply **chaos engineering** principles to test this system?

---
