[![SOC2-Analyzer CI/CD](https://github.com/ajy0127/soc2_report_reviewer/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/ajy0127/soc2_report_reviewer/actions/workflows/ci-cd.yml)

# GitHub Actions CI/CD for SOC2-Analyzer

This directory contains the GitHub Actions workflow configuration for the SOC2-Analyzer project.

## Workflow Overview

The CI/CD pipeline performs the following tasks:

1. **Run Tests**: Executes all unit tests to ensure code functionality
2. **Validate CloudFormation**: Checks the CloudFormation template for errors using cfn-lint
3. **Code Quality**: Runs linting tools to ensure code quality

## Workflow Triggers

The workflow is triggered on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

## Deployment

This project does not include automatic deployment from GitHub Actions. Users should deploy the application manually using the CloudFormation template:

1. Clone the repository
2. Run the deployment script locally:
   ```
   ./scripts/deploy.sh --profile your-profile --region your-region
   ```

For more details on deployment options, see the main README.md file.

## Customization

You can customize the workflow by editing the `.github/workflows/ci-cd.yml` file. Common customizations include:

- Changing the Python version
- Adding more test or linting steps
- Adding notifications (e.g., Slack, email) 
