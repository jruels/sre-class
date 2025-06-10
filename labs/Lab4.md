# Lab 4: Blue/Green Deployment with GitHub, CodePipeline, and CodeDeploy

### Objective

Implement a **zero-downtime deployment** using **GitHub as the source**, and AWS **CodePipeline + CodeDeploy** to perform **canary and blue/green rollouts** on EC2 Auto Scaling groups.

---

## Learning Outcomes

* Integrate GitHub with AWS CodePipeline
* Set up a simple web app and deploy it to EC2
* Perform Blue/Green deployments using CodeDeploy
* Understand traffic shifting and rollback mechanisms

---

## AWS Services Used

* GitHub (Source)
* S3 (Artifact store)
* CodePipeline (CI/CD orchestrator)
* CodeDeploy (Deployment strategy)
* EC2 (Web app hosts)
* Auto Scaling
* IAM

---

## Step 0: Setup Prerequisites

### 0.1 IAM Roles to Create

#### a) CodePipeline Role

* **IAM > Roles > Create Role**
* Service or use case: `CodePipeline`
* Permissions: `AWSCodePipelineFullAccess`, `AmazonS3FullAccess`
* Name: `CodePipelineServiceRole`

#### b) CodeDeploy Role

* Service or use case: `CodeDeploy`
* Permissions: `AWSCodeDeployRole`
* Name: `CodeDeployServiceRole`

#### c) EC2 Instance Role

* Service or use case: `EC2`
* Permissions: `AmazonEC2RoleforAWSCodeDeploy`, `AmazonSSMManagedInstanceCore`
* Name: `EC2CodeDeployRole`

---

## Step 1: Create Your GitHub Repository

### 1.1 Create a new GitHub repo (e.g., `sre-bluegreen-app`)

### 1.2 Clone and add files

```bash
git clone https://github.com/<your-username>/sre-bluegreen-app.git
cd sre-bluegreen-app
```

#### a) `app.py`

```python
from flask import Flask
application = Flask(__name__)

@application.route("/")
def home():
    return "✅ Version 1 deployed via CodeDeploy!"
```

#### b) `requirements.txt`

```
flask
```

#### c) `appspec.yml`

```yaml
version: 0.0
os: linux
files:
  - source: .
    destination: /home/ec2-user/app
hooks:
  AfterInstall:
    - location: scripts/install.sh
      timeout: 180
  ApplicationStart:
    - location: scripts/start.sh
      timeout: 180
```

#### d) `scripts/install.sh`

```bash
#!/bin/bash
cd /home/ec2-user/app
pip3 install -r requirements.txt
```

#### e) `scripts/start.sh`

```bash
#!/bin/bash
cd /home/ec2-user/app
nohup python3 app.py &
```

Make the scripts executable:

```bash
chmod +x scripts/*.sh
```

Push changes:

```bash
git add .
git commit -m "Initial commit for Blue/Green lab"
git push origin main
```

---

## Step 2: Create Launch Template & Auto Scaling Group

### 2.1 Launch Template

1. **EC2 > Launch Templates > Create**
2. Name: `BlueGreenTemplate`
3. AMI: Amazon Linux 2 (x86\_64)
4. Instance type: `t3.micro`
5. IAM instance profile: `EC2CodeDeployRole`
6. User data:

```bash
#!/bin/bash
yum update -y
yum install -y ruby wget python3
cd /home/ec2-user
wget https://aws-codedeploy-us-west-2.s3.us-west-2.amazonaws.com/latest/install
chmod +x ./install
./install auto
systemctl start codedeploy-agent
```

---

### 2.2 Auto Scaling Group

* Go to **EC2 > Auto Scaling Groups**
* Create ASG using `BlueGreenTemplate`
* VPC: default
* Subnet: public subnets
* Size: 1 desired, 1 min, 2 max

---

## Step 3: Create CodeDeploy App & Deployment Group

### 3.1 Create CodeDeploy Application

* **CodeDeploy > Applications > Create**
* Name: `BlueGreenApp`
* Platform: EC2/On-premises

### 3.2 Create Deployment Group

* Name: `BlueGreenDG`
* Service role: `CodeDeployServiceRole`
* Deployment type: **Blue/Green**
* Load balancer: Configure with Target Group (create one via EC2 → Target Groups)
* Choose Auto Scaling group: `BlueGreenASG`
* Deployment config: `Canary10Percent5Minutes`

---

## Step 4: Create CodePipeline with GitHub Source

### 4.1 Create a New S3 Bucket for Artifacts

```bash
aws s3 mb s3://<your-unique-bucket-name> --region <same-region-as-pipeline>
```

### 4.2 Create Pipeline

* Go to **CodePipeline > Create pipeline**
* Select `Build custom pipeline`
* Name: `BlueGreenPipeline`
* Service role > Existing service role: `CodePipelineServiceRole`
* Artifact store > custom location: `s3://<your-bucket>`

#### Source Stage:

* Provider: **GitHub (Version 2)**
* Connect to GitHub → `sre-bluegreen-app` repo
* Branch: `main`

#### Deploy Stage:

* Provider: **CodeDeploy**
* Application: `BlueGreenApp`
* Deployment Group: `BlueGreenDG`

---

## Step 5: Test the Deployment

1. Open your browser and visit the public DNS of an instance (or use the load balancer DNS).
2. You should see:

   ```
   ✅ Version 1 deployed via CodeDeploy!
   ```

---

## Step 6: Simulate a New Version

1. Change `app.py` to:

```python
return "🚀 Version 2 deployed via GitHub!"
```

2. Push the change:

```bash
git commit -am "Deploy version 2"
git push origin main
```

3. Watch:

   * CodePipeline runs
   * CodeDeploy executes canary deployment (10%)
   * After 5 minutes → shifts to remaining 90%

---

## Step 7: Cleanup

* Delete:

  * CodePipeline
  * CodeDeploy app & group
  * Auto Scaling group
  * Launch template
  * GitHub repo (optional)

---

## Reflection

* What if the canary fails? How can you roll back automatically?
* How would you add a manual approval step before 90% rollout?