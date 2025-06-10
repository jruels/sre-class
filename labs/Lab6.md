# Lab 6: Distributed Tracing and Log Correlation with AWS X-Ray and CloudWatch Logs Insights

### Objective

Deploy a multi-service app with X-Ray enabled. Inject delays and failures, then diagnose them via **service maps**, **traces**, and **log queries**.

---


## What Students Will Learn

* Enable distributed tracing with X-Ray
* View trace maps and performance breakdown
* Correlate traces with CloudWatch logs

---

## Step 0: Prerequisites

1. Install EB CLI:

```bash
pip install awsebcli --upgrade
```

---

## Step 1: Deploy Sample Flask App with X-Ray

### 1.1 Create App Files

#### `application.py`

```python
from flask import Flask
import time
import aws_xray_sdk.core as xray

xray.patch_all()

application = Flask(__name__)

@application.route("/")
def home():
    return "✅ Home endpoint OK!"

@application.route("/slow")
def slow():
    time.sleep(2)
    return "⏱️ Slow endpoint complete"
```

#### `requirements.txt`

```
flask
aws-xray-sdk
```

#### `.ebextensions/01_xray.config`

```yaml
option_settings:
  aws:elasticbeanstalk:application:
    Application Healthcheck URL: "/"
  aws:elasticbeanstalk:xray:
    XRayEnabled: true
```

---

### 1.2 Deploy with EB CLI

```bash
eb init -p python-3.13 xray-app
# — Configure SSH keypair "sre-lab-key" —
# 1) In AWS Console > EC2 > Key Pairs, create or confirm "sre-lab-key"
# 2) Download sre-lab-key.pem and place in your ~/.ssh/ directory:
#      Windows PowerShell: Move-Item C:\Downloads\sre-lab-key.pem $HOME\.ssh\
#      Linux/macOS: mv ~/Downloads/sre-lab-key.pem ~/.ssh/
# 3) Secure the key: chmod 400 ~/.ssh/sre-lab-key.pem
eb create xray-env --keyname sre-lab-key
```

> Note: This creates the environment and enables X-Ray by default.

---

## Step 2: Generate Traffic

```bash
while true; do curl https://<your-env-url>/slow; sleep 1; done
```

Wait 5–10 minutes.

---

## Step 3: View Traces in X-Ray

1. Go to **AWS X-Ray > Service Map**
2. Look for `ElasticBeanstalk -> EC2`
3. Drill into `slow()` traces to view latency spikes
4. If no traces appear:
   - SSH into the instance and verify the daemon is running
   ```bash
   eb ssh
   sudo systemctl status xray-daemon
   ```
   - Check the daemon log for errors:
   ```bash
   sudo tail -n 50 /var/log/xray/xray.log
   ```
   - Ensure the EC2 instance role includes the AWSXRayDaemonWriteAccess policy.

---

## Step 4: Use CloudWatch Logs Insights

```sql
fields @timestamp, @message
| filter @message like /slow/
| sort @timestamp desc
```

Or trace errors:

```sql
fields @timestamp, @message, @logStream
| filter @message like /Exception/
```

---

## Step 5: Remove Delay and Compare Traces

* Remove `time.sleep(2)` from `slow()`
* Redeploy:

```bash
eb deploy
```

* Observe trace latency drop in X-Ray

---

## Step 6: Cleanup

```bash
eb terminate xray-env
```

---

## Reflection

* What causes cold starts in Lambda-based systems?
* How would you detect a partial failure across microservices?

