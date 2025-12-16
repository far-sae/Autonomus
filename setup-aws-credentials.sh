#!/bin/bash

echo "🔐 AWS Credentials Setup for Compliance Platform"
echo "================================================="
echo ""

# Check if AWS CLI is installed
if command -v aws &> /dev/null; then
    echo "✓ AWS CLI is installed"
    
    # Try to get credentials from AWS CLI
    AWS_KEY=$(aws configure get aws_access_key_id 2>/dev/null)
    AWS_SECRET=$(aws configure get aws_secret_access_key 2>/dev/null)
    AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
    
    if [ -n "$AWS_KEY" ] && [ -n "$AWS_SECRET" ]; then
        echo "✓ Found AWS credentials from AWS CLI"
        echo ""
        echo "Using credentials:"
        echo "  Access Key: ${AWS_KEY:0:10}..."
        echo "  Region: $AWS_REGION"
        echo ""
        
        # Update .env file
        cat > .env << ENVEOF
# AWS Credentials for Production
AWS_ACCESS_KEY_ID=$AWS_KEY
AWS_SECRET_ACCESS_KEY=$AWS_SECRET
AWS_DEFAULT_REGION=$AWS_REGION
ENVEOF
        
        echo "✅ .env file updated with your AWS credentials"
        echo ""
        echo "Starting the platform..."
        docker-compose up -d
        
        echo ""
        echo "✅ Platform started successfully!"
        echo ""
        echo "Access the platform at: http://localhost:3000"
        echo "Login: admin@example.com / admin123"
    else
        echo "❌ No AWS credentials found in AWS CLI"
        echo ""
        echo "Please run: aws configure"
        echo "Or manually edit the .env file"
    fi
else
    echo "❌ AWS CLI not installed"
    echo ""
    echo "Please manually edit the .env file with your AWS credentials:"
    echo ""
    echo "1. Open .env file in a text editor"
    echo "2. Replace 'your_access_key_here' with your AWS Access Key ID"
    echo "3. Replace 'your_secret_access_key_here' with your AWS Secret Access Key"
    echo "4. Run: docker-compose up -d"
    echo ""
    echo "Get credentials from: https://console.aws.amazon.com/iam/home#/security_credentials"
fi
