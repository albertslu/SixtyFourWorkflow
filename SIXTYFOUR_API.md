# Sixtyfour API Integration Guide

## 🔗 API Information

**Base URL**: `https://api.sixtyfour.ai`

**Authentication**: API Key via `x-api-key` header

**Documentation**: [docs.sixtyfour.ai](https://docs.sixtyfour.ai)

## 🔑 Getting Your API Credentials

1. **Sign up** at [app.sixtyfour.ai](https://app.sixtyfour.ai)
2. **Navigate to your dashboard** to find your credentials:
   - **API Key**: Used for authentication
   - **Organization ID**: Your organization identifier

## 📡 Available Endpoints

### 1. Enrich Lead (`/enrich-lead`)

Enriches lead information with additional data points.

**Method**: `POST`

**Headers**:
```
x-api-key: your_api_key_here
Content-Type: application/json
```

**Request Body**:
```json
{
  "lead_info": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "company": "TechCorp",
    "title": "Software Engineer",
    "linkedin": "https://www.linkedin.com/in/johndoe"
  },
  "struct": {
    "name": "Full name",
    "email": "Email address",
    "company": "Company name",
    "title": "Job title",
    "linkedin": "LinkedIn URL",
    "website": "Company website",
    "location": "Location",
    "industry": "Industry",
    "education": "Educational background including university"
  }
}
```

**Response**:
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "company": "TechCorp",
  "title": "Senior Software Engineer",
  "linkedin": "https://www.linkedin.com/in/johndoe",
  "website": "https://techcorp.com",
  "location": "San Francisco, CA",
  "industry": "Technology",
  "education": "Stanford University - Computer Science"
}
```

### 2. Find Email (`/find-email`)

Finds email addresses for individuals based on their information.

**Method**: `POST`

**Headers**:
```
x-api-key: your_api_key_here
Content-Type: application/json
```

**Request Body**:
```json
{
  "person_info": {
    "name": "Jane Smith",
    "company": "InnovateCorp",
    "title": "Product Manager",
    "linkedin": "https://www.linkedin.com/in/janesmith"
  },
  "struct": {
    "email": "Primary email address",
    "confidence": "Confidence score for the email",
    "source": "Source of the email information"
  }
}
```

**Response**:
```json
{
  "email": "jane.smith@innovatecorp.com",
  "confidence": 0.95,
  "source": "company_website"
}
```

## 🔧 Implementation in the Workflow Engine

The workflow engine implements these endpoints through:

1. **SixtyfourService** (`backend/app/services/sixtyfour_service.py`)
   - Handles API authentication
   - Manages concurrent requests for better performance
   - Implements error handling and retries

2. **Workflow Blocks**:
   - **Enrich Lead Block**: Uses `/enrich-lead` endpoint
   - **Find Email Block**: Uses `/find-email` endpoint

3. **Batch Processing**:
   - Processes multiple leads concurrently
   - Optimizes API usage with configurable batch sizes
   - Handles rate limiting gracefully

## ⚡ Performance Optimizations

1. **Concurrent Processing**: Multiple API calls run in parallel
2. **Batch Configuration**: Adjustable batch sizes per block
3. **Timeout Management**: Configurable timeouts per request
4. **Error Handling**: Graceful handling of failed requests
5. **Progress Tracking**: Real-time progress updates

## 🔒 Security Best Practices

1. **Environment Variables**: Store API keys securely
2. **Header Authentication**: Use `x-api-key` header
3. **HTTPS Only**: All requests use secure connections
4. **Rate Limiting**: Respect API rate limits
5. **Error Logging**: Log errors without exposing sensitive data

## 📊 Rate Limits

- Check Sixtyfour's documentation for current rate limits
- The workflow engine implements backoff strategies
- Batch processing helps optimize API usage

## 🐛 Troubleshooting

### Common Issues:

1. **Authentication Errors (401)**:
   - Verify API key is correct
   - Check that `x-api-key` header is included

2. **Rate Limit Errors (429)**:
   - Reduce batch size in block configuration
   - Implement delays between requests

3. **Timeout Errors**:
   - Increase timeout values in block configuration
   - Check network connectivity

4. **Invalid Request Errors (400)**:
   - Verify request body structure
   - Check required fields are provided

### Debug Steps:

1. Check application logs in `backend/logs/`
2. Verify environment variables are loaded
3. Test API endpoints directly with curl or Postman
4. Check Sixtyfour's API status page

## 📝 Example Usage

```python
from app.services.sixtyfour_service import sixtyfour_service

# Enrich a single lead
lead_data = {
    "name": "John Doe",
    "company": "TechCorp"
}

enriched = await sixtyfour_service.enrich_lead(lead_data)

# Batch enrich multiple leads
leads = [
    {"name": "John Doe", "company": "TechCorp"},
    {"name": "Jane Smith", "company": "InnovateCorp"}
]

results = await sixtyfour_service.batch_enrich_leads(leads)
```

## 🔄 Updates and Changes

- Monitor Sixtyfour's documentation for API updates
- Update the workflow engine when new endpoints are available
- Test thoroughly when upgrading API versions
