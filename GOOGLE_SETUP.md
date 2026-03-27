# Google Cloud Setup - Simplified Guide

## Why You Need This
Your app uses Google's Imagen AI models to generate images. This requires a Google Cloud account.

## 5-Minute Setup

### Step 1: Create Google Cloud Project (Free)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select Project" → "New Project"
3. Name it: `woodcarvings-ai`
4. Click "Create"

### Step 2: Enable Vertex AI API

1. In the search bar, type "Vertex AI API"
2. Click "Enable"
3. Wait ~30 seconds

### Step 3: Create Service Account

1. Go to [IAM & Admin → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "Create Service Account"
3. Name: `woodcarvings-service`
4. Click "Create and Continue"
5. Add role: "Vertex AI User"
6. Click "Continue" → "Done"

### Step 4: Generate Key

1. Click on your new service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON"
5. Click "Create"
6. **Save the downloaded JSON file securely**

### Step 5: Set Environment Variables

#### For Local Development (.env):
```env
VERTEX_PROJECT_ID=woodcarvings-ai
VERTEX_LOCATION=us-central1
VERTEX_API_KEY={"type":"service_account","project_id":"woodcarvings-ai",...}
```

Paste the entire JSON file contents into `VERTEX_API_KEY`.

#### For Render Deployment:
1. Go to Render Dashboard → Your Service → Environment
2. Add variable: `VERTEX_API_KEY`
3. Paste the entire JSON contents
4. Save

## Cost

- **Free tier**: $300 credit for 90 days
- **After free tier**: ~$0.02 per image (Imagen 3) or ~$0.04 per image (Imagen 4)
- **Typical usage**: 100 images = $2-4

## Security

✅ **Never commit the JSON key to git** (already in .gitignore)
✅ **Store in environment variables only**
✅ **Rotate keys periodically** (recommended every 90 days)

## Troubleshooting

**Error: "API not enabled"**
→ Enable Vertex AI API in Google Cloud Console

**Error: "Permission denied"**
→ Ensure service account has "Vertex AI User" role

**Error: "Invalid credentials"**
→ Check that VERTEX_API_KEY is valid JSON

## Alternative: Use API Key Instead

If you prefer simpler auth, you can use Gemini API (already in your code):

```env
GEMINI_API_KEY=AIza...
# Get from: https://makersuite.google.com/app/apikey
```

This is simpler but has different rate limits and pricing.

## That's It!

Once configured, the authentication happens automatically. You never need to think about it again.
