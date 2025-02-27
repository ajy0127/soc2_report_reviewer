# SOC2-Analyzer Deployment Scripts

This directory contains scripts for deploying the SOC2-Analyzer Lambda function with approaches for handling binary dependencies.

## Deployment Options

When deploying Python Lambda functions with binary dependencies (like `pymupdf` and `ocrmypdf`), you need to ensure that the binaries are compatible with the Lambda execution environment (Amazon Linux).

### Option 1: CloudFormation-managed Lambda Layer (`deploy_with_cf_layer.sh`) - RECOMMENDED

This approach creates a Lambda Layer and references it directly within the CloudFormation template, providing the most integrated infrastructure-as-code solution. **This is the recommended deployment method.**

```bash
./scripts/deploy_with_cf_layer.sh [options]
```

**Options:**
- `--stack-name NAME`: CloudFormation stack name (default: "soc2-analyzer")
- `--region REGION`: AWS region (default: "us-east-1")
- `--profile PROFILE`: AWS CLI profile (default: "sandbox")
- `--s3-bucket BUCKET`: S3 bucket for CloudFormation artifacts (optional)
- `--environment ENV`: Environment name (default: "dev")
- `--email EMAIL`: Notification email (default: "alexanderjyawn@gmail.com")
- `--skip-layer`: Skip creating a Lambda Layer (not recommended)

**Docker Requirements:**
- This script requires Docker to be installed and running to build Lambda-compatible binary dependencies
- To install Docker: [Get Docker Desktop](https://www.docker.com/products/docker-desktop/)

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

1. **"invalid ELF header" errors**: 
   - This indicates binary dependencies aren't compatible with the Lambda environment
   - Solution: Use the recommended CloudFormation-managed Lambda Layer approach (`deploy_with_cf_layer.sh`) which builds dependencies in a Lambda-compatible environment

2. **"RequestEntityTooLargeException"**: 
   - The Lambda package is too large for direct upload
   - Solution: All our deployment scripts handle this by uploading to S3 first and using Lambda Layers for dependencies

3. **Missing dependencies**: 
   - Make sure all required packages are listed in `src/lambda/requirements.txt`

4. **Docker not running**: 
   - Error: "Cannot connect to the Docker daemon" or "Is the docker daemon running?"
   - Solution: Start Docker Desktop before running the deployment script
   - Alternative: If you can't use Docker, use the `--skip-layer` option with `deploy_with_cf_layer.sh`, but be aware this may result in "invalid ELF header" errors with binary dependencies

### Docker Requirements Explained

All of our deployment approaches use Docker to build Lambda-compatible binary dependencies. This is because:

1. Lambda runs on Amazon Linux, which may differ from your local environment
2. Binary dependencies like `pymupdf` and `ocrmypdf` need to be compiled for the correct platform
3. Docker provides an isolated environment that matches the Lambda runtime

The `deploy_with_cf_layer.sh` script (recommended) handles this by:
- Building dependencies in a Docker container that matches the Lambda environment
- Packaging them as a Lambda Layer
- Uploading the Layer to S3
- Referencing the Layer in CloudFormation
- Keeping your function code separate from binary dependencies 