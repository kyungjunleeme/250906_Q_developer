# Multi-Tenant SaaS Platform

Python-only multi-tenant SaaS built with AWS CDK, FastAPI, DynamoDB, and Cognito.

## Architecture

- **Auth**: Cognito User Pool with multi-tenancy
- **Data**: DynamoDB tables for tenants, users, items
- **API**: FastAPI on Lambda with JWT middleware
- **Web**: Two App Runner services (user/admin) with SSR
- **Observability**: CloudWatch dashboards and alarms

## Structure

```
├── cdk/                    # CDK infrastructure
├── services/              # Application services
│   ├── api/              # FastAPI backend
│   ├── web_user/         # User web app
│   └── web_admin/        # Admin web app
├── shared/               # Shared libraries
└── ops/                  # Operations scripts
```

## Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Deploy to dev
cdk deploy --all --profile dev

# Run smoke tests
python ops/smoke/test_health.py
```
