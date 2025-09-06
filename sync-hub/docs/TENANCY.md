# Sync Hub Multi-Tenancy Model

## Overview
Sync Hub implements a **pooled multi-tenancy** model where all tenants share the same infrastructure resources, but data is logically isolated using tenant identifiers.

## Tenancy Architecture

### Pooled Model Benefits
- **Cost Efficiency**: Shared infrastructure reduces per-tenant costs
- **Operational Simplicity**: Single deployment and maintenance
- **Resource Utilization**: Better resource sharing and scaling
- **Feature Parity**: All tenants get the same features simultaneously

### Data Isolation Strategy

#### Tenant Identification
- Every record in DynamoDB carries a `tenant_id` field
- Tenant ID is extracted from JWT token claims (`sub` field)
- Default tenant ID: `"default"` for demo purposes

#### Database Schema
```
DynamoDB Tables:
├── settings
│   ├── PK: tenant_id (string)
│   └── SK: setting_id (string)
├── bookmarks  
│   ├── PK: tenant_id (string)
│   └── SK: bookmark_id (string)
├── groups
│   ├── PK: tenant_id (string)
│   └── SK: group_id (string)
├── group_members
│   ├── PK: tenant_id (string)
│   └── SK: group_id#user_id (string)
└── sessions
    ├── PK: tenant_id (string)
    └── SK: session_id (string)
```

## Security & Isolation

### Application-Level Isolation
- **Lambda Functions**: Extract tenant_id from JWT claims
- **Database Queries**: All queries scoped to tenant_id
- **API Responses**: Only return data belonging to the requesting tenant

### Authentication Flow
1. User authenticates via Cognito
2. JWT token contains user identity in `sub` claim
3. Lambda extracts `sub` as tenant_id
4. All database operations filtered by tenant_id

### Code Example
```python
# Extract tenant from JWT
def extract_tenant_id(event):
    if "authorizer" in event.get("requestContext", {}):
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        return claims.get("sub", "default")
    return "default"

# Query with tenant isolation
def get_user_settings(tenant_id):
    response = settings_table.query(
        KeyConditionExpression=Key('tenant_id').eq(tenant_id)
    )
    return response["Items"]
```

## Tenant Onboarding

### New Tenant Setup
1. **User Registration**: Via Cognito User Pool
2. **Tenant ID Assignment**: Cognito `sub` becomes tenant_id
3. **Data Initialization**: Empty tenant namespace created automatically
4. **Access Control**: Immediate access to tenant-scoped resources

### No Manual Provisioning Required
- Resources are shared across all tenants
- No per-tenant infrastructure deployment
- Automatic scaling handles tenant growth

## Data Management

### Tenant Data Lifecycle
- **Creation**: Data automatically scoped to tenant_id
- **Access**: Only tenant's own data is accessible
- **Backup**: S3 backups include tenant_id in object keys
- **Deletion**: Tenant data can be purged by tenant_id filter

### Cross-Tenant Features
- **Public Settings**: `is_public=true` settings visible across tenants
- **Group Sharing**: Groups can invite users from same tenant
- **Analytics**: Aggregated metrics across all tenants (anonymized)

## Scaling Considerations

### Horizontal Scaling
- **DynamoDB**: Auto-scales based on demand across all tenants
- **Lambda**: Concurrent executions shared across tenants
- **API Gateway**: Request throttling applied globally

### Performance Isolation
- **Hot Tenants**: Large tenants don't impact smaller ones due to auto-scaling
- **Query Patterns**: Efficient partition key design prevents hot partitions
- **Caching**: CloudFront caches public content across tenants

## Monitoring & Observability

### Tenant-Aware Metrics
```python
# Add tenant dimension to metrics
metrics.add_metric(
    name="RequestCount", 
    unit=MetricUnit.Count, 
    value=1,
    metadata={"tenant_id": tenant_id}
)
```

### Logging Strategy
- **Structured Logs**: Include tenant_id in all log entries
- **Correlation IDs**: Track requests across services per tenant
- **Error Tracking**: Tenant-specific error rates and patterns

## Compliance & Governance

### Data Residency
- All tenant data stored in `us-east-1` region
- No cross-region data replication
- Consistent data location for compliance

### Audit Trail
- **DynamoDB Streams**: Capture all data changes with tenant context
- **CloudTrail**: API-level audit logs
- **Application Logs**: Business logic audit events

### Data Privacy
- **Encryption**: Data encrypted at rest and in transit
- **Access Logs**: No tenant data in access logs
- **Anonymization**: Metrics and analytics anonymized

## Tenant Isolation Testing

### Validation Checklist
- [ ] User A cannot access User B's settings
- [ ] Group membership properly scoped to tenant
- [ ] Public settings visible across tenants
- [ ] Device pairing isolated per tenant
- [ ] Backup data properly partitioned

### Test Scenarios
```python
# Test tenant isolation
def test_tenant_isolation():
    # Create data for tenant A
    create_setting(tenant_id="tenant-a", name="test", value="a")
    
    # Verify tenant B cannot access
    settings = get_settings(tenant_id="tenant-b")
    assert len(settings) == 0
    
    # Verify tenant A can access
    settings = get_settings(tenant_id="tenant-a") 
    assert len(settings) == 1
```

## Migration & Backup Strategy

### Tenant Data Export
```python
def export_tenant_data(tenant_id):
    """Export all data for a specific tenant"""
    data = {
        "settings": get_all_settings(tenant_id),
        "bookmarks": get_all_bookmarks(tenant_id),
        "groups": get_all_groups(tenant_id)
    }
    return data
```

### Disaster Recovery
- **Point-in-Time Recovery**: Enabled on all DynamoDB tables
- **S3 Versioning**: Multiple versions of backup data
- **Cross-Region Backup**: Optional for enterprise tenants

## Cost Allocation

### Tenant Usage Tracking
- **API Requests**: Track per tenant via JWT claims
- **Storage**: DynamoDB item count per tenant_id
- **Compute**: Lambda invocation metrics by tenant

### Billing Model Options
1. **Flat Rate**: Fixed price per tenant
2. **Usage-Based**: Cost based on API calls and storage
3. **Tiered**: Different pricing tiers based on usage volume

## Future Enhancements

### Advanced Isolation
- **VPC Isolation**: Dedicated VPCs for enterprise tenants
- **Dedicated Instances**: Reserved capacity for large tenants
- **Custom Domains**: Tenant-specific API endpoints

### Tenant Management
- **Admin Portal**: Tenant configuration and monitoring
- **Usage Analytics**: Per-tenant usage dashboards
- **Billing Integration**: Automated billing based on usage
