# Sync Hub Architecture

## Overview
Sync Hub is a multi-tenant SaaS platform for VS Code Extension + Web Console service built on AWS using Python CDK and Lambda.

## Architecture Components

### 1. Authentication Stack (AuthStack)
- **Cognito User Pool**: Manages user authentication and authorization
- **User Pool Client**: Configured for web and device flows
- **Hosted UI**: Social login with Google + email sign-up
- **JWT Authorizer**: Protects API endpoints

### 2. Data Stack (DataStack)
- **DynamoDB Tables**: All partitioned by `tenant_id`
  - `settings`: User/group settings with versioning
  - `bookmarks`: User bookmarks with tags
  - `groups`: Group definitions and metadata
  - `group_members`: Group membership with RBAC
  - `sessions`: Device pairing and emoji feedback
- **S3 Bucket**: Versioned backups with block public access
- **Point-in-Time Recovery**: Enabled on all tables
- **DynamoDB Streams**: For history tracking

### 3. API Stack (ApiStack)
- **HTTP API Gateway v2**: RESTful API with JWT authentication
- **Lambda Function**: Single function handling all routes
- **Lambda Powertools**: Structured logging, tracing, metrics
- **X-Ray Tracing**: Distributed tracing enabled
- **CORS**: Configured for extension and web access
- **Throttling**: Rate limiting configured

### 4. Web Stack (WebStack)
- **S3 Static Hosting**: Web console assets
- **CloudFront Distribution**: CDN with SPA routing
- **Origin Access Identity**: Secure S3 access

### 5. Observability Stack (ObservabilityStack)
- **CloudWatch Dashboard**: API metrics and Lambda errors
- **CloudWatch Alarms**: 5XX errors and latency monitoring
- **SNS Alerts**: Notification system for critical issues
- **Log Retention**: 30-day retention policy

## Security Best Practices

### IAM
- Least-privilege roles for Lambda functions
- Separate roles for each service
- No hardcoded credentials

### Data Protection
- DynamoDB Point-in-Time Recovery enabled
- S3 Block Public Access enforced
- Encryption at rest (default AWS managed keys)
- JWT-based API authentication

### Network Security
- API Gateway with throttling
- CORS properly configured
- CloudFront for web asset delivery

## Multi-Tenancy Model

### Pooled Architecture
- Single set of resources shared across tenants
- Every record carries `tenant_id` for isolation
- Tenant isolation enforced at application layer
- Cost-effective for large number of tenants

### Data Isolation
```
DynamoDB Partition Key: tenant_id
Sort Key: resource_id (setting_id, bookmark_id, etc.)
```

### Access Control
- JWT claims contain tenant context
- Lambda functions extract tenant_id from JWT
- All database operations scoped to tenant_id

## Deployment Architecture

### Cross-Stack Communication
- SSM Parameter Store for sharing outputs
- Stack dependencies managed by CDK
- Environment-specific parameter namespaces

### Staging Support
- Environment separation via parameter prefixes
- Independent resource naming
- Configurable deployment targets (dev/stg/prd)

## API Design

### Authentication Flow
1. **Web**: OAuth2 authorization code flow via Cognito Hosted UI
2. **VS Code Extension**: Device code flow for headless authentication

### Endpoint Structure
```
/_health (public)
/auth/device/* (JWT required)
/settings/* (JWT required, except /settings/public)
/bookmarks/* (JWT required)
/groups/* (JWT required)
/sessions/* (JWT required)
```

### Response Format
- Consistent JSON responses
- Error handling with proper HTTP status codes
- Structured logging for debugging

## Monitoring & Observability

### Metrics
- API Gateway: Request count, latency, errors
- Lambda: Duration, errors, concurrent executions
- DynamoDB: Read/write capacity, throttles

### Logging
- Structured JSON logs via Lambda Powertools
- Correlation IDs for request tracing
- 30-day retention policy

### Alerting
- 5XX error rate > 10 requests in 10 minutes
- API latency > 5 seconds for 3 consecutive periods
- Lambda error rate monitoring

## Scalability Considerations

### Auto-Scaling
- Lambda: Automatic scaling based on demand
- DynamoDB: On-demand billing mode
- API Gateway: Built-in scaling

### Performance Optimization
- DynamoDB single-table design per service
- Efficient query patterns with GSIs if needed
- CloudFront caching for web assets

### Cost Optimization
- Pay-per-request DynamoDB billing
- Lambda cost optimization via memory tuning
- S3 lifecycle policies for backups
