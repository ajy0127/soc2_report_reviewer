# SOC2-Analyzer Deployment Scripts

This directory contains scripts for deploying the SOC2-Analyzer Lambda function with different approaches for handling binary dependencies.

## Deployment Options

When deploying Python Lambda functions with binary dependencies (like `pymupdf` and `ocrmypdf`), you need to ensure that the binaries are compatible with the Lambda execution environment (Amazon Linux). Here are two approaches:

### Option 1: Docker-based Deployment (`deploy.sh`)

This approach uses Docker to build the Lambda package in an environment that matches the Lambda runtime. This ensures binary dependencies are compiled correctly for the target environment.

```bash
./scripts/deploy.sh [options]
```

**Options:**
- `--stack-name NAME`: CloudFormation stack name (default: "soc2-analyzer")
- `--region REGION`: AWS region (default: "us-east-1")
- `--profile PROFILE`: AWS CLI profile (default: "sandbox")
- `--s3-bucket BUCKET`: S3 bucket for CloudFormation artifacts (optional)
- `--environment ENV`: Environment name (default: "dev")
- `--email EMAIL`: Notification email (default: "alexanderjyawn@gmail.com")
- `--no-docker`: Skip using Docker for building dependencies (not recommended)

### Option 2: Lambda Layer Deployment (`deploy_with_layer.sh`)

This approach creates a separate Lambda Layer for binary dependencies and deploys the Lambda function with minimal dependencies, attaching the layer for the binary components.

```bash
./scripts/deploy_with_layer.sh [options]
```

**Options:**
- `--stack-name NAME`: CloudFormation stack name (default: "soc2-analyzer")
- `--region REGION`: AWS region (default: "us-east-1")
- `--profile PROFILE`: AWS CLI profile (default: "sandbox")
- `--s3-bucket BUCKET`: S3 bucket for CloudFormation artifacts (optional)
- `--environment ENV`: Environment name (default: "dev")
- `--email EMAIL`: Notification email (default: "alexanderjyawn@gmail.com")
- `--layer-name NAME`: Lambda Layer name (default: "soc2-analyzer-dependencies")

## Creating Lambda Layers Manually

You can also create the Lambda Layer separately:

```bash
./scripts/layer/create_layer.sh [options]
```

**Options:**
- `--layer-name NAME`: Layer name (default: "soc2-analyzer-dependencies")
- `--region REGION`: AWS region (default: "us-east-1")
- `--profile PROFILE`: AWS CLI profile (default: "sandbox")
- `--runtime RUNTIME`: Python runtime (default: "python3.9")

## Troubleshooting

### Common Issues

1. **"invalid ELF header" errors**: This indicates binary dependencies aren't compatible with the Lambda environment. Use the Docker-based deployment or Lambda Layer approach to fix this.

2. **"RequestEntityTooLargeException"**: The Lambda package is too large for direct upload. Both scripts handle this by uploading to S3 first.

3. **Missing dependencies**: Make sure all required packages are listed in `src/lambda/requirements.txt`. 