
### Lab 2: Automating Toil with AWS Services

**Objective:**  
Reduce operational toil by automating EC2 patching and snapshot cleanup using AWS Systems Manager and Lambda.

**Duration:** ~1 hour  
**Prerequisites:** Familiarity with Systems Manager, Lambda, and toil concepts.

#### Instructions

1. **Create EC2 Instances**
   - Launch two `t2.micro` instances with **Amazon Linux 2 AMI**.
   - Use the same security group from Lab 1.
   - Note their instance IDs.

2. **Create EBS Snapshots**
   - In the EC2 console, go to **Volumes**.
   - Select the root volume of each instance and click **Create Snapshot**.

3. **Set Up Systems Manager for Patching**
   - Create an IAM role:
     - In IAM, create a role with `AmazonSSMManagedInstanceCore` policy.
     - Attach it to both instances via **EC2** > **Actions** > **Security** > **Modify IAM Role**.
   - Create an automation document:
     - Go to **Systems Manager** > **Documents** > **Create Document** > **Automation**.
     - Use this JSON (replace INSTANCE_IDS with your instance ids environment variable):
       ```json
        {
        "schemaVersion": "0.3",
        "description": "Patch EC2 instances",
        "mainSteps": [
            {
            "action": "aws:runCommand",
            "name": "InstallUpdates",
            "inputs": {
                "DocumentName": "AWS-RunPatchBaseline",
                "InstanceIds": ["{{ INSTANCE_IDS }}"]
            }
            }
        ]
        }
       ```
     - Name it `PatchEC2Instances`.

4. **Automate Snapshot Cleanup with Lambda**
   - Create a Lambda function:
     - In Lambda, click **Create Function**.
     - Name: `CleanOldSnapshots`, Runtime: **Python 3.13**.
     - Create an IAM role with `ec2:DescribeSnapshots` and `ec2:DeleteSnapshot` permissions.
     - Add this code:
       ```python
       import boto3
       from datetime import datetime, timedelta

       def lambda_handler(event, context):
           ec2 = boto3.client('ec2')
           snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
           for snap in snapshots:
               if snap['StartTime'] < datetime.now(snap['StartTime'].tzinfo) - timedelta(days=7):
                   ec2.delete_snapshot(SnapshotId=snap['SnapshotId'])
           return {'status': 'Snapshots cleaned'}
       ```
   - Schedule it:
     - In EventBridge, create a rule with `rate(1 day)` and target the Lambda function.

5. **Test Automation**
   - Run `PatchEC2Instances` on one instance via Systems Manager.
   - Manually trigger the Lambda function and verify snapshot deletion.

6. **Cleanup**
   - Terminate EC2 instances.
   - Delete snapshots, Lambda function, and EventBridge rule.

**Reflection:** What other tasks could you automate to reduce toil?

