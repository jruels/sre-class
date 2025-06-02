# 🧪 Lab 4: Proactive Alerting & Automated Remediation with CloudWatch and Systems Manager

### 🧭 Objective

Create a system that monitors an EC2 instance for high CPU usage, triggers an alarm, and automatically remediates the issue by rebooting the instance using **AWS Systems Manager Automation**.

---

### ⏱️ Duration

\~90 minutes

---

## ✅ What Students Will Learn

* Launch an EC2 instance with SSM access
* Simulate high CPU usage on an EC2 instance
* Create CloudWatch metrics, alarms, and dashboards
* Create and execute Systems Manager Automation runbooks
* Automatically respond to alerts using EventBridge

---

## 🔧 AWS Services Used

* **EC2**
* **CloudWatch (Metrics, Alarms)**
* **SNS (Notifications)**
* **Systems Manager (SSM & Automation)**
* **EventBridge**

---

## 🔐 Step 0: Create IAM Roles

### 🛡 0.1 Create an IAM Role for EC2 with SSM and CloudWatch Access

1. Go to **IAM > Roles > Create role**
2. **Service or use case**: Select `EC2`
3. **Permissions**: Attach these policies:

   * `AmazonSSMManagedInstanceCore`
   * `CloudWatchAgentServerPolicy`
   * `AmazonEC2RoleforSSM`
4. **Role Name**: `EC2MonitoringSSMRole`
5. Click **Create role**

---

## 💻 Step 1: Launch a Managed EC2 Instance

### 🖥 1.1 Launch an EC2 Instance with SSM Access

1. Go to **EC2 > Instances > Launch instance**
2. Name: `Lab1-SSM-EC2`
3. AMI: `Amazon Linux 2` or `Amazon Linux 2023`
4. Instance type: `t3.micro`
5. Key pair: Create or choose one (for SSH fallback)
6. **Network settings**:
   * Allow **SSH**
7. **Advanced Details**:

   * IAM Instance Profile: Select `EC2MonitoringSSMRole`
8. Click **Launch Instance**

---

## ✅ Step 2: Verify Systems Manager Connectivity

1. Go to **Systems Manager > Fleet Manager**
2. Confirm your instance appears as **Managed**
   (Status: `Online`)

If not, verify:

* IAM role is correct
* SSM Agent is installed (Amazon Linux includes it)
* Instance is in public subnet with internet

---

## 🧪 Step 3: Simulate High CPU Usage

### ⚡ 3.1 Use SSM to Simulate CPU Stress

1. Go to **Systems Manager > Run Command**
2. Click **Run a command**
3. Command document: `AWS-RunShellScript`
4. Target: `Lab1-SSM-EC2`
5. Command:

   ```bash
   yes > /dev/null &
   ```
6. Click **Run**

This command runs an infinite loop to stress the CPU.

---

## 📈 Step 4: Monitor Metrics with CloudWatch

### 📊 4.1 View the CPU Metric

1. Go to **CloudWatch > Metrics > EC2 > Per-Instance Metrics**
2. Locate the `CPUUtilization` metric for your instance
3. Add to a new **Dashboard** (optional)

---

## 🚨 Step 5: Create a CloudWatch Alarm

### 🔔 5.1 Alarm Setup

1. Go to **CloudWatch > Alarms > Create Alarm**
2. Select Metric: `EC2 > Per-Instance Metrics > CPUUtilization`
3. Conditions:

   * Threshold: `Greater than 80%`
   * Period: `5 minutes`
4. Actions:

   * Create new **SNS topic**: `HighCPU-Alert`
   * Add your **email** as a subscriber (don’t forget to **confirm** it)
5. Alarm Name: `HighCPUAlarm-Lab1`
6. Click **Create Alarm**

---

## 🤖 Step 6: Create a Remediation Automation (SSM Runbook)

### 🛠 6.1 Create a Custom SSM Automation Runbook

1. Go to **Systems Manager > Automation > Create Runbook**
2. Type: `Automation`
3. Name: `RebootOnHighCPU`
4. Content (YAML):

```yaml
description: "Reboot an EC2 instance on high CPU"
schemaVersion: '0.3'
assumeRole: "{{ AutomationAssumeRole }}"
parameters:
  InstanceId:
    type: String
  AutomationAssumeRole:
    type: String
mainSteps:
  - name: rebootInstance
    action: aws:executeAwsApi
    inputs:
      Service: ec2
      Api: RebootInstances
      InstanceIds:
        - "{{ InstanceId }}"

```

5. Click **Create Runbook**

---

### 🧾 6.2 Create an IAM Role for Automation

1. Go to **IAM > Roles > Create Role**
2. Service or use case: `Systems Manager`
3. Permissions:

   * `AmazonEC2FullAccess`
   * `AmazonSSMFullAccess`
4. Name: `SSMAutomationRole`

---

## 📡 Step 7: Connect the Alarm to the Automation via EventBridge

### 🔁 7.1 Create an EventBridge Rule

1. Go to **EventBridge > Rules > Create Rule**

2. Name: `TriggerRebootOnHighCPU`

3. Event Pattern:

   ```json
   {
     "source": ["aws.cloudwatch"],
     "detail-type": ["CloudWatch Alarm State Change"],
     "detail": {
       "alarmName": ["HighCPUAlarm-Lab1"],
       "state": {
         "value": ["ALARM"]
       }
     }
   }
   ```

4. Target: **Systems Manager Automation**

   * Document: `RebootOnHighCPU`
   * Input:

     ```json
     {
       "InstanceId": "i-xxxxxxxxxxxxxxx",
       "AutomationAssumeRole": "arn:aws:iam::<account-id>:role/SSMAutomationRole"
     }
     ```

5. Click **Create**

---

## 🔁 Step 8: Validate Everything

1. Use **SSM RunCommand** to stress CPU again:

   ```bash
   yes > /dev/null &
   ```

2. Wait 5–7 minutes.

You should observe:

* CloudWatch alarm enters `ALARM` state
* SNS sends email
* EventBridge triggers SSM Automation
* EC2 instance reboots automatically

---

## 🧹 Step 9: Cleanup

1. Terminate the EC2 instance
2. Delete:

   * Alarm
   * EventBridge rule
   * SSM document
   * IAM roles (optional)
   * SNS topic

---

## 💬 Reflection

* What are the pros/cons of rebooting vs scaling?
* How could you escalate to PagerDuty or Slack instead of email?
* What if the automation fails?
