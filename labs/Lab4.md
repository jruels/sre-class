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

### 0.0 Create a GitHub account

* If required, create a [GitHub account](http://github.com/signup)

* After creating a GitHub account, [create a new repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories) named `sre-bluegreen-app`

### 0.1 IAM Roles to Create

#### a) CodePipeline Role

* **IAM > Roles > Create Role**
* Service or use case: `Codedeploy`
* Permissions: `AWSCodePipelineFullAccess`, `AmazonS3FullAccess`
* Name: `CodePipelineServiceRole`
* Select the role from the list 
* Navigate to the trust policy tab
  * Edit and replace `codedeploy` with `codepipeline`


#### b) CodeDeploy Role

* Service or use case: `CodeDeploy`
* Permissions: `AWSCodeDeployRole`
* Name: `CodeDeployServiceRole`

#### c) EC2 Instance Role

* Service or use case: `EC2`
* Permissions: `AmazonEC2RoleforAWSCodeDeploy`, `AmazonSSMManagedInstanceCore`
* Name: `EC2CodeDeployRole`

---

## Step 1: Clone your new repository

**Run the following commands in Visual Studio Code's Bash terminal.**

### 1.1 Clone your new GitHub repo (e.g., `sre-bluegreen-app`)

**NOTE**: Replace `<your-username>` with your GitHub username

```bash
git clone https://github.com/<your-username>/sre-bluegreen-app.git
cd sre-bluegreen-app
```

### 1.2 Add files

In Visual Studio Code, create the following folders and files.

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

In VS Code Bash terminal, run: 

```bash
git add .
git commit -m "Initial commit for Blue/Green lab"
git push origin main
```

If you receive an error, run the following commands, providing your info: 

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Attempt the `git commit` and `git push` commands again.

---

## Step 2: Create Launch Template & Auto Scaling Group

### 2.1 Launch Template

1. **EC2 > Launch Templates > Create**
2. Name: `BlueGreenTemplate`
3. AMI: Amazon Linux 2 AMI (HVM)
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
* Subnet: public subnets (select one)
* Step 3: Leave default (click next)
* Size: 1 desired, 1 min, 2 max
* Click on skip to review and create the Auto Scaling Group

---

## Step 3: Create CodeDeploy App & Deployment Group

### 3.1 Create CodeDeploy Application

* **CodeDeploy > Applications > Create**
* Name: `BlueGreenApp`
* Platform: EC2/On-premises

### 3.2 Create Target Group

* **EC2 > Target Groups**
* Create new target group
  * Name: ASGtarget
  * Leave the rest default and create the group.

### 3.3 Create Deployment Group

* Name: `BlueGreenDG`
* Service role: `CodeDeployServiceRole`
* Deployment type: **Blue/Green**
* Load balancer: Configure with Target Group (create one via EC2 → Target Groups)
* Choose Auto Scaling group: `BlueGreenASG`
* Deployment config: `Canary10Percent5Minutes`

---

## Step 4: Create CodePipeline with GitHub Source

### 4.1 Create a New S3 Bucket for Artifacts

Run the command below in Visual Studio Code Bash terminal, or AWS CloudShell.

NOTE: replace `<your-unique-bucket-name>` with an actual unique string (DNS compliant)

```bash
aws s3 mb s3://<your-unique-bucket-name> --region <same-region-as-pipeline>
```

### 4.2 Create Pipeline

* Go to **CodePipeline > Create pipeline**
* Select `Build custom pipeline`
* Name: `BlueGreenPipeline`
* Service role > Existing service role: `CodePipelineServiceRole`
* Expand the Additional Settings
* Artifact store > choose custom location and specify your newly created S3 bucket: `s3://<your-bucket>`

#### Source Stage:

* Provider: **GitHub (via OAuth)**
* Click Connect to GitHub
  * In the pop-up window, authorize AWS Code Pipeline to access your GitHub account. 

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

Run the following in VS Code:

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
   * CodeDeploy executes a canary deployment (10%)
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