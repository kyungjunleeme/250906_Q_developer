# Sync Hub API Documentation

## Base URL
```
https://{api-id}.execute-api.us-east-1.amazonaws.com
```

## Authentication
Most endpoints require JWT authentication via `Authorization: Bearer <token>` header.
Tokens are obtained through Cognito authentication flows.

## Endpoints

### Health Check
```http
GET /_health
```
**Public endpoint** - No authentication required.

**Response:**
```json
{
  "ok": true
}
```

---

### Device Authentication

#### Start Device Flow
```http
POST /auth/device/start
Authorization: Bearer <token>
```

**Response:**
```json
{
  "device_code": "ABC12345",
  "session_id": "uuid",
  "expires_in": 600
}
```

#### Confirm Device Flow
```http
POST /auth/device/confirm
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_code": "ABC12345"
}
```

**Response:**
```json
{
  "status": "confirmed"
}
```

---

### Settings Management

#### List User Settings
```http
GET /settings
Authorization: Bearer <token>
```

**Response:**
```json
{
  "settings": [
    {
      "tenant_id": "user-123",
      "setting_id": "uuid",
      "name": "VS Code Theme",
      "value": "Dark+ (default dark)",
      "is_public": false,
      "version": 1,
      "created_at": 1640995200,
      "updated_at": 1640995200
    }
  ]
}
```

#### Create Setting
```http
POST /settings
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Font Size",
  "value": "14",
  "is_public": false
}
```

#### Get Setting
```http
GET /settings/{setting_id}
Authorization: Bearer <token>
```

#### Update Setting
```http
PUT /settings/{setting_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Font Size",
  "value": "16"
}
```

#### Delete Setting
```http
DELETE /settings/{setting_id}
Authorization: Bearer <token>
```

#### Get Setting History
```http
GET /settings/{setting_id}/history
Authorization: Bearer <token>
```

**Response:**
```json
{
  "history": [
    {
      "setting_id": "uuid#v1",
      "name": "Font Size",
      "value": "14",
      "version": 1,
      "created_at": 1640995200
    }
  ]
}
```

#### Rollback Setting
```http
POST /settings/{setting_id}/rollback
Authorization: Bearer <token>
Content-Type: application/json

{
  "version": 1
}
```

#### Update Setting Visibility
```http
PUT /settings/{setting_id}/visibility
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_public": true
}
```

#### List Public Settings
```http
GET /settings/public
```
**Public endpoint** - No authentication required.

**Response:**
```json
{
  "settings": [
    {
      "tenant_id": "user-123",
      "setting_id": "uuid",
      "name": "Popular Theme",
      "value": "Monokai",
      "is_public": true,
      "version": 2
    }
  ]
}
```

---

### Bookmarks Management

#### List Bookmarks
```http
GET /bookmarks
Authorization: Bearer <token>
```

#### Create Bookmark
```http
POST /bookmarks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "AWS Documentation",
  "url": "https://docs.aws.amazon.com",
  "tags": ["aws", "documentation"]
}
```

#### Get Bookmark
```http
GET /bookmarks/{bookmark_id}
Authorization: Bearer <token>
```

#### Update Bookmark
```http
PUT /bookmarks/{bookmark_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated Title",
  "tags": ["aws", "docs", "cloud"]
}
```

#### Delete Bookmark
```http
DELETE /bookmarks/{bookmark_id}
Authorization: Bearer <token>
```

---

### Groups Management

#### List Groups
```http
GET /groups
Authorization: Bearer <token>
```

#### Create Group
```http
POST /groups
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Development Team",
  "description": "Main dev team settings"
}
```

#### Get Group
```http
GET /groups/{group_id}
Authorization: Bearer <token>
```

#### Update Group
```http
PUT /groups/{group_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Team Name",
  "description": "Updated description"
}
```

#### Delete Group
```http
DELETE /groups/{group_id}
Authorization: Bearer <token>
```

#### Invite Member
```http
POST /groups/{group_id}/invite
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "user-456",
  "role": "member"
}
```

**Roles:** `owner`, `admin`, `member`

#### List Group Members
```http
GET /groups/{group_id}/members
Authorization: Bearer <token>
```

**Response:**
```json
{
  "members": [
    {
      "tenant_id": "user-123",
      "group_id": "group-uuid",
      "user_id": "user-123",
      "role": "owner",
      "joined_at": 1640995200
    }
  ]
}
```

---

### Session Feedback

#### Add Emoji Feedback
```http
POST /sessions/{session_id}/emoji
Authorization: Bearer <token>
Content-Type: application/json

{
  "emoji": "👍"
}
```

**Response:**
```json
{
  "emoji": "👍",
  "session_id": "session-uuid"
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "error": "Error message description"
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting
- Rate limit: 1000 requests per second
- Burst limit: 2000 requests
- Throttled requests return `429 Too Many Requests`

## CORS
CORS is enabled for all origins (`*`) with the following headers:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: *`
- `Access-Control-Allow-Headers: *`

## Example Usage

### cURL Examples

#### Health Check
```bash
curl https://api.synchub.com/_health
```

#### Create Setting (with auth)
```bash
curl -X POST https://api.synchub.com/settings \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Theme", "value": "Dark", "is_public": true}'
```

#### List Public Settings
```bash
curl https://api.synchub.com/settings/public
```
