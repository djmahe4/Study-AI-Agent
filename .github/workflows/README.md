# GitHub Actions CI/CD Pipeline

This directory contains GitHub Actions workflows for automated testing and security checks.

## Workflows

### `ci.yml` - Main CI/CD Pipeline

Runs on every pull request and push to main/master/develop branches.

#### Jobs Overview

1. **Python CLI Tests** 
   - Tests CLI help, init, and list commands
   - Verifies interactive mode works
   - Validates core module imports
   - Checks Python syntax

2. **Node.js Version Check**
   - Verifies Node.js version 18+
   - Installs frontend dependencies
   - Runs npm audit for vulnerabilities

3. **Security Analysis**
   - **Safety**: Checks Python dependencies for known vulnerabilities
   - **Bandit**: Scans Python code for security issues
   - **CodeQL**: Performs deep code analysis for security vulnerabilities
   - **TruffleHog**: Detects hardcoded secrets

4. **Code Quality Check**
   - Runs flake8 for Python syntax errors
   - Runs pylint on core modules

5. **Integration Tests**
   - Creates test subject with syllabus
   - Tests topic and question management
   - Validates learning aids generation

6. **Dependency Analysis**
   - Checks for outdated Python packages
   - Checks for outdated Node.js packages

7. **CI Summary**
   - Aggregates results from all jobs
   - Creates summary report

## Required GitHub Permissions

The workflow requires the following permissions:
- `security-events: write` - For CodeQL analysis
- `contents: read` - For repository access

## Security Tools Used

- **Safety** - Python dependency vulnerability scanner
- **Bandit** - Python code security scanner
- **CodeQL** - GitHub's semantic code analysis engine
- **TruffleHog** - Secret scanner
- **npm audit** - Node.js dependency vulnerability scanner

## Artifacts

The workflow produces the following artifacts:
- `bandit-security-report` - JSON report from Bandit scan

## Local Testing

To test the pipeline locally:

```bash
# Test Python CLI
python cli.py --help
python cli.py init
echo -e "help\nexit" | python cli.py

# Test Node.js setup
cd frontend
npm install
npm audit

# Run security checks
pip install safety bandit
safety check
bandit -r . --exclude './frontend,./data,./docs,./.git'
```

## Continuous Improvement

Feel free to extend the workflow with:
- Unit tests when added to the project
- Performance benchmarks
- Documentation generation
- Deployment automation
