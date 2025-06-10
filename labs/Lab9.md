## Lab 9: Reliable Replicated State Using DynamoDB, Route 53 Private DNS, and Multi-AZ EC2

### Objective
Design a highly available key-value service using DynamoDB, EC2 in multiple AZs, Route 53 failover, and health checks—without buying a public domain.

---

### AWS Services Used
* EC2 (Amazon Linux 2)
* DynamoDB
* Route 53 Private Hosted Zone
* CloudWatch (optional)

---

### Prerequisite: Create an EC2 IAM Role for DynamoDB Access

1. In the AWS console go to **IAM → Roles → Create role**.  
2. Select **EC2** as the trusted entity, click **Next**.  
3. Attach the policy **AmazonDynamoDBFullAccess** (or a narrower custom policy).  
4. Name the role `EC2_DynamoDB_Access`, finish creation.

---

### 1. Launch Two EC2 Web Servers in Different AZs

1.1.  In the EC2 console, **Launch instances** → **Amazon Linux 2 AMI** → **t2.micro**.  
1.2.  Edit **Network settings**, choose VPC `<your-VPC>` and **Subnet** AZ-a, and under **IAM role** select `EC2_DynamoDB_Access`.    
1.3.  Select or create a key pair, open port 22 (SSH) and 80 (HTTP) from your IP.  
1.4.  Under **Advanced Details**, in **User data** paste:
```bash
#!/bin/bash
yum update -y
yum install -y python3-pip
pip3 install flask boto3

cat <<'EOF' > /home/ec2-user/app.py
from flask import Flask, request
import boto3, json

app = Flask(__name__)
# specify your AWS region here:
ddb = boto3.resource('dynamodb', region_name='replace-with-your-region')
table = ddb.Table('SREKeyValue')

@app.route('/write')
def write():
    key = request.args.get('key')
    value = request.args.get('value')
    table.put_item(Item={'key': key, 'value': value})
    return json.dumps({'status':'written'}), 200

@app.route('/read')
def read():
    key = request.args.get('key')
    resp = table.get_item(Key={'key': key})
    return json.dumps(resp.get('Item', {})), 200

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
EOF

sudo python3 /home/ec2-user/app.py &
```
1.5. Click on **Launch instance**
1.6. Repeat steps 1.1–1.5 but choose a different subnet in AZ-b. You now have **two** web servers.

---

### 2. Create a DynamoDB Table

2.1. In the DynamoDB console, **Create table**  
• Table name: `SREKeyValue`  
• Partition key: `key` (String)  
• Leave defaults (auto-scaling and multi-AZ are on by default)  
2.2. Click **Create**.

---

### 3. Configure Route 53 Private Hosted Zone & Health Checks

#### 3.1. Private Hosted Zone

3.1.1. In Route 53 console, **Get started** → **Create hosted zone**  
• Domain name: `sre-test.local`  
• Type: **Private hosted zone**  
• Region: select same region as your EC2s
• VPCs: select the VPC where your EC2s live → **Create hosted zone**

#### 3.2. Health Checks

3.2.1. In Route 53 console, **Health checks** → **Create health check**  
• Name: `hc-az1`  
• Endpoint: Public IPv4 of AZ-a instance  
• Protocol: HTTP, Port: 80, Path: `/health`  
• Request interval/Threshold: defaults → **Create**  

3.2.2. Repeat for AZ-b instance as `hc-az2`.

#### 3.3. Failover DNS Records

3.3.1. In your `sre-test.local` zone, **Create record**  
• Record name: `svc`  
• Record type: **A – IPv4 address**  
• Value/Route traffic to: Public IP of AZ-a instance  
• Routing policy: **Failover** → **Primary**  
• Associate health check: `hc-az1`  
→ **Create records**

3.3.2. **Create record** again with same name `svc`, value → public IP AZ-b, Routing policy → **Secondary**, attach `hc-az2`.

---

### 4. Test High Availability

4.1. SSH into **either** instance and install `bind-utils`:
```bash
sudo yum install -y bind-utils
```

4.2. From one instance, resolve your service name using the VPC DNS resolver at `.2`:
```bash
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
MAC=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/network/interfaces/macs/ | head -1 | tr -d '/')
CIDR=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/network/interfaces/macs/$MAC/vpc-ipv4-cidr-block)
IP=$(echo $CIDR | sed 's#/.*##; s/$/.2/')
dig +short svc.sre-test.local $IP
```
You should get the AZ-a IP first.

4.3. Write & read via DNS name:
```bash
curl "http://svc.sre-test.local/write?key=foo&value=bar"
curl "http://svc.sre-test.local/read?key=foo"
```
**Important:** if the API is not reachable, ssh into both EC2 instances and run `sudo python3 /home/ec2-user/app.py &` to start the APIs

4.4. Simulate failure: stop the AZ-a instance in the EC2 console, wait ~30 s, then rerun the `write/read`—traffic should now go to AZ-b.

---

### Cleanup

* Terminate both EC2 instances  
* Delete DynamoDB table `SREKeyValue`  
* In Route 53 console: delete records, health checks, and hosted zone `sre-test.local`