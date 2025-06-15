## Lab 7: Chaos Testing with AWS Fault Injection Simulator (FIS)

### Objective

Test system resilience by simulating an EC2 instance failure using AWS FIS, and verify auto recovery via Auto Scaling.

---

### AWS Services Used

* EC2
* Auto Scaling
* CloudWatch
* Fault Injection Simulator
* IAM

---

### Step-by-Step Instructions

### 1. Launch a Sample Web App

1. Go to **EC2 > Launch Instance**
2. Name: `resilience-test-instance`
3. AMI: Amazon Linux 2023 AMI
4. Instance type: `t2.micro`
5. Under Advanced Details> User data (basic web app):

```bash
#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "✅ Resilience Lab Homepage" > /var/www/html/index.html
```

6. Enable Auto-assign public IP
7. Reuse the security group from Lab 1:

   * Allow HTTP (80) and SSH (22)
8. Create a new key pair if needed

---

### 2. Create Launch Template

* EC2 > Launch Templates > Create
* Name: `FISLaunchTemplate`
* Use same settings as above
* Add the same user data and security group

---

### 3. Create Auto Scaling Group

* EC2 > Auto Scaling > Create Auto Scaling Group
* Name: `ResilienceASG`
* Use `FISLaunchTemplate`
* Select 2 AZs under `Choose instance launch options`
* Desired = Min = Max = 1 under `Configure group size and scaling`
* Click Next and then select `Create Auto Scaling group`


---

### 4. Create an IAM Role for FIS

#### 1. Create a trust policy so FIS can assume the role. Save as `trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "fis.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

#### 2. Create the role and attach the trust policy:

```bash
aws iam create-role \
  --role-name FISExecutionRole \
  --assume-role-policy-document file://trust-policy.json
```

---

#### 3. Attach the permissions policy inline:

```bash
aws iam put-role-policy \
  --role-name FISExecutionRole \
  --policy-name FISPermissions \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ec2:TerminateInstances",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:UpdateAutoScalingGroup"
        ],
        "Resource": "*"
      }
    ]
  }'
```

---

#### 4. Confirm the role exists:

```bash
aws iam get-role --role-name FISExecutionRole
```
---

### 5. Create and Start FIS Experiment

1. Go to **AWS FIS > Create experiment template**
2. Target: EC2 instances in Auto Scaling group `ResilienceASG` by selecting `aws:ec2:instance` under Resource type and selecting the ec2 instances as the targets.
3. Action: Terminate instance
4. IAM Role: `FISExecutionRole`. Make sure to add log writing permissions to the IAM Role.
5. To enable logging, select `Send to CloudWatch Logs`. 
6. Create or select an existing log group
7. Save and run

---

### 6. Observe Auto Scaling Behavior

* Watch the instance terminate and get replaced
* View logs and metrics in **CloudWatch**

---

### Cleanup

* Delete Auto Scaling group
* Delete launch template
* Delete FIS experiment

---
