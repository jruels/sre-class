# 1. Create EC2 Instances
# -----------------------
# Replace with your Lab 1 security group ID
export SG_ID="sg-0123456789abcdef0"
# Get latest Amazon Linux 2 AMI in your region
export AMI_ID=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
            "Name=state,Values=available" \
  --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" \
  --output text)
# Launch 2 t2.micro instances
export INSTANCE_IDS=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t2.micro \
  --security-group-ids $SG_ID \
  --count 2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Lab2Instance}]' \
  --query "Instances[].InstanceId" \
  --output text)
echo "Launched instances: $INSTANCE_IDS"

# 2. Create EBS Snapshots
# -----------------------
for ID in $INSTANCE_IDS; do
  VOL_ID=$(aws ec2 describe-volumes \
    --filters Name=attachment.instance-id,Values=$ID \
              Name=attachment.device,Values=/dev/xvda \
    --query "Volumes[0].VolumeId" --output text)
  SNAP_ID=$(aws ec2 create-snapshot \
    --volume-id $VOL_ID \
    --description "Root snapshot of $ID" \
    --query "SnapshotId" --output text)
  echo "Created snapshot $SNAP_ID for volume $VOL_ID"
done

# 3. Set Up Systems Manager for Patching
# --------------------------------------
# Create IAM role for SSM on EC2
cat > assume-ec2.json <<EOF
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect":"Allow",
      "Principal":{"Service":"ec2.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name SSMInstanceRole \
  --assume-role-policy-document file://assume-ec2.json

aws iam attach-role-policy \
  --role-name SSMInstanceRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

aws iam create-instance-profile \
  --instance-profile-name SSMInstanceRole

aws iam add-role-to-instance-profile \
  --instance-profile-name SSMInstanceRole \
  --role-name SSMInstanceRole

# Associate the new IAM role with each instance
for ID in $INSTANCE_IDS; do
  aws ec2 associate-iam-instance-profile \
    --instance-id $ID \
    --iam-instance-profile Name=SSMInstanceRole
done

# Create Automation Document
cat > PatchEC2Instances.json <<EOF
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

EOF

aws ssm create-document \
  --name PatchEC2Instances \
  --document-type Automation \
  --content file://PatchEC2Instances.json