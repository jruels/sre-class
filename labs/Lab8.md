## Lab 8: Load Testing at Scale with JMeter and CloudWatch Insights

### Objective

Simulate 50,000 concurrent users using Apache JMeter and analyze system performance under load using CloudWatch.

---

### AWS Services Used

* EC2
* CloudWatch
* Amazon Linux 2
* S3 (optional)

---

### Step-by-Step Instructions

### 1. Launch Target Web App on EC2
1.1 Login to AWS Console:
- Open https://console.aws.amazon.com/ and sign in with your AWS credentials.

1.2 Navigate to EC2 Dashboard:
- In the Services menu, select **EC2** under Compute.

1.3 Launch a new instance:
- Click **Launch instance**.
- **Step 1: Choose an AMI** – select **Amazon Linux 2 AMI (HVM), SSD Volume Type**.
- **Step 2: Choose an Instance Type** – select **t2.micro** (free tier).
- **Step 3: Configure Instance Details** – leave defaults.
- **Step 4: Key pair (login)** - select an existing key pair or create a new one. Download the `.pem` file and save it (you will use it to SSH). Restrict the permissions using `chmod 400 {replace-with-key-pair-name}.pem`
- **Step 4: Configure Storage** – leave defaults.
- **Step 6: Network Settings**:
  - Create a new security group
  - Add rule **SSH** (port 22) from your IP.
  - Add rule **HTTP** (port 80) from 0.0.0.0/0.
- **Step 7: Review and Launch** – click **Launch instance**.


1.4 (Optional) Install a simple web server via user data:
```bash
#!/bin/bash
sudo yum update -y
sudo yum install -y httpd
sudo systemctl start httpd
sudo systemctl enable httpd
echo "<h1>Test Page</h1>" > /var/www/html/index.html
```
- Paste this as **User data** in **Step 3: Configure Instance Details** if you want the server to auto-install.

1.5 Find the public IP:
- Wait until the instance state is **running**.
- Select the instance and copy **Public IPv4 address** – note this value as `TARGET_IP`.

---

### 2. Launch a JMeter EC2 Instance
2.1 In the EC2 Dashboard, click **Launch instance** again.
- **Name** – `Name=jmeter-load-generator`.
- **AMI** – choose **Amazon Linux 2**.
- **Instance Type** – select **t2.medium** for sufficient load capacity.
- **Security Group** – create `sg-jmeter` allowing:
  - **SSH** (port 22) from your IP.
  - **Outbound** – allow all traffic (default).
- **Review and Launch** – select the same key pair you used earlier.

2.2 Wait for the JMeter instance to be **running**. Copy its **Public IPv4 address** as `JMETER_IP`.

2.3 SSH into the JMeter instance:
- On Linux/macOS:
  ```bash
  ssh -i ~/.ssh/your-key.pem ec2-user@${JMETER_IP}
  ```
- On Windows (PowerShell):
  ```powershell
  ssh -i C:\Users\<YourUser>\.ssh\your-key.pem ec2-user@${JMETER_IP}
  ```

2.4 Install Java and JMeter:
```bash
sudo yum update -y
sudo yum install -y java-1.8.0
wget https://dlcdn.apache.org/jmeter/binaries/apache-jmeter-5.6.3.tgz
tar -xvzf apache-jmeter-5.6.3.tgz
cd apache-jmeter-5.6.3/bin
```

---

### 3. Create a JMeter Test Plan

```bash
cat > test-plan.jmx <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Load Test Plan" enabled="true">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Concurrency" enabled="true">
        <stringProp name="ThreadGroup.num_threads">50000</stringProp>
        <stringProp name="ThreadGroup.ramp_time">60</stringProp>
        <stringProp name="ThreadGroup.duration">120</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
    <boolProp name="LoopController.continue_forever">false</boolProp>
    <stringProp name="LoopController.loops">10</stringProp>
  </elementProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="HTTP GET" enabled="true">
          <stringProp name="HTTPSampler.domain">34.220.107.74</stringProp>
          <stringProp name="HTTPSampler.path">/</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
EOF
```

> Replace `your-app-public-ip` with your app instance's IP.

---

### 4. Run JMeter Headlessly

```bash
./jmeter -n -t test-plan.jmx -l results.jtl
```

---

### 5. Monitor in CloudWatch

* Go to the app instance's monitoring tab to monitor the instance metrics
* Go to CPU utilization (%) visual > Select view in metrics > Select the bell (alarm) icon under actions > Give the alarm a name and threshold for high CPU usage
* Use Insights to query logs if logging enabled 

---

### Cleanup

* Terminate JMeter and target EC2 instances

---
