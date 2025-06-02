Below are the instructions to install and set up the AWS CLI if you haven’t done so yet. These steps are tailored for Windows, macOS, and Linux users, ensuring you can configure the AWS CLI to interact with your AWS account.


# AWS CLI Installation and Setup Guide

This guide provides step-by-step instructions to install and configure the AWS Command Line Interface (CLI) on Windows, macOS, and Linux systems. Alternatively, you can follow the detailed instructions from the [AWS CLI webpage](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

## Prerequisites
- A blank AWS account with administrative access
- A local machine (Windows, macOS, or Linux)
- Internet access

## Step 1: Install AWS CLI

### For Windows Users
1. **Download the AWS CLI Installer**:  
   - Go to the [AWS CLI download page](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html/) and download the Windows installer (`.msi` file).
2. **Run the Installer**:  
   - Double-click the downloaded `.msi` file and follow the on-screen prompts to complete the installation.
3. **Verify Installation**:  
   - Open Command Prompt and type:  
     ```bash
     aws --version
     ```
   - You should see output like `aws-cli/2.13.0`, confirming the installation.

### For macOS Users
1. **Install Homebrew** (if not already installed):  
   - Open Terminal and run:  
     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```
2. **Install AWS CLI**:  
   - In Terminal, run:  
     ```bash
     brew install awscli
     ```
3. **Verify Installation**:  
   - Check the version by running:  
     ```bash
     aws --version
     ```

### For Linux Users
1. **Install AWS CLI**:  
   - For Ubuntu/Debian:  
     ```bash
     sudo apt update
     sudo apt install awscli
     ```
   - For CentOS/RHEL:  
     ```bash
     sudo yum install awscli
     ```
2. **Verify Installation**:  
   - Run:  
     ```bash
     aws --version
     ```

## Step 2: Configure AWS CLI
1. **Run Configuration Command**:  
   - In your terminal or Command Prompt, type:  
     ```bash
     aws configure
     ```
2. **Enter AWS Credentials**:  
   - You’ll be prompted to input the following:  
     - **AWS Access Key ID**: Obtain this from your AWS account (create an IAM user if needed).  
     - **AWS Secret Access Key**: The corresponding secret key for the access key.  
     - **Default Region Name**: Enter a region, e.g., `us-east-1`.  
     - **Default Output Format**: Choose `json` or `text` (e.g., type `json`).  
3. **Verify Configuration**:  
   - Test your setup by running:  
     ```bash
     aws sts get-caller-identity
     ```
   - This command should return your AWS account details, confirming the CLI is correctly configured.

## Next Steps
Once the AWS CLI is installed and configured, you’re ready to use it to manage AWS resources programmatically. Refer to your course materials for further instructions on using the CLI in your AWS SRE demo.
