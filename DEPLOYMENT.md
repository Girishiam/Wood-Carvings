# WoodCarvings AI - Render Deployment Guide

Complete guide for deploying the WoodCarvings AI Image Generation System to Render.

## 📋 Overview

This application consists of:
- **Backend**: FastAPI application with Google Vertex AI integration
- **Frontend**: React + Vite static site

## 🚀 Quick Deploy to Render

### Prerequisites

1. **GitHub Repository**: Push your code to GitHub
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Google Cloud Setup**:
   - Create a Google Cloud project
   - Enable Vertex AI API
   - Create a service account with Vertex AI access
   - Download the service account key JSON

### Method 1: Using render.yaml (Recommended)

1. **Push Code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create New Blueprint on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables**

   Set these in the Render dashboard for the **backend service**:

   | Variable | Description | Example |
   |----------|-------------|---------|
   | `GEMINI_API_KEY` | Google Gemini API key | `AIza...` |
   | `VERTEX_PROJECT_ID` | GCP Project ID | `my-project-123` |
   | `VERTEX_LOCATION` | Vertex AI region | `us-central1` |
   | `VERTEX_API_KEY` | GCP Service Account Key (JSON) | `{"type":"service_account"...}` |
   | `DROPBOX_SHARED_FOLDER_LINK` | (Optional) Dropbox folder link | `https://...` |
   | `ALLOWED_ORIGINS` | Frontend URLs (comma-separated) | `https://woodcarvings-frontend.onrender.com` |

4. **Update render.yaml URLs**

   After services are created, update these URLs in `render.yaml`:
   - Backend: Update `FRONTEND_URL` with actual frontend URL
   - Frontend: Update `VITE_API_URL` with actual backend URL

5. **Deploy**
   - Render will automatically build and deploy both services
   - Monitor logs for any errors

### Method 2: Manual Service Creation

#### Backend Service

1. **Create Web Service**
   - Go to Render Dashboard → "New +" → "Web Service"
   - Connect your repository
   - Configure:
     - **Name**: `woodcarvings-api`
     - **Runtime**: Python 3
     - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Free (or Starter for better performance)

2. **Add Environment Variables** (see table above)

3. **Set Health Check Path**: `/health`

#### Frontend Service

1. **Create Static Site**
   - Go to Render Dashboard → "New +" → "Static Site"
   - Connect your repository
   - Configure:
     - **Name**: `woodcarvings-frontend`
     - **Build Command**: `cd frontend && npm install && npm run build`
     - **Publish Directory**: `frontend/dist`

2. **Add Environment Variable**
   - `VITE_API_URL`: Your backend URL (e.g., `https://woodcarvings-api.onrender.com`)

3. **Configure Redirects** (for SPA routing)
   - Add rewrite rule: `/*` → `/index.html`

## 🐳 Alternative: Docker Deployment

If you prefer Docker:

```bash
# Build image
docker build -t woodcarvings-api .

# Run locally
docker run -p 8000:8000 --env-file .env woodcarvings-api

# Deploy to Render using Docker
# In Render dashboard, select "Docker" as runtime
# Use Dockerfile for build configuration
```

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file locally (don't commit it!):

```env
GEMINI_API_KEY=your_gemini_api_key
VERTEX_PROJECT_ID=your_gcp_project_id
VERTEX_LOCATION=us-central1
VERTEX_API_KEY={"type":"service_account",...}
DROPBOX_SHARED_FOLDER_LINK=https://www.dropbox.com/...
ALLOWED_ORIGINS=http://localhost:3001,https://your-frontend.onrender.com
```

### Frontend Environment Variables

Create `frontend/.env` (don't commit it!):

```env
VITE_API_URL=http://localhost:8000  # Development
# VITE_API_URL=https://your-backend.onrender.com  # Production
```

## 🧪 Testing Before Deployment

### Test Backend Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py

# Test health endpoint
curl http://localhost:8000/health
```

### Test Frontend Locally

```bash
# Install dependencies
cd frontend
npm install

# Run dev server
npm run dev

# Visit http://localhost:3001
```

### Test Production Build

```bash
# Build frontend
cd frontend
npm run build

# Serve built files
npm run preview
```

## 🔍 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version (3.11 recommended)

2. **CORS errors**
   - Verify `ALLOWED_ORIGINS` includes your frontend URL
   - Check that URLs don't have trailing slashes

3. **Vertex AI authentication errors**
   - Ensure `VERTEX_API_KEY` is valid JSON
   - Check GCP service account has Vertex AI permissions
   - Verify Vertex AI API is enabled in GCP

4. **Frontend can't connect to backend**
   - Check `VITE_API_URL` is set correctly
   - Ensure backend service is running
   - Verify CORS configuration

5. **Build timeouts on Render**
   - Upgrade to Starter plan for more build resources
   - Optimize dependencies
   - Use Docker deployment for faster builds

### Logs

View logs in Render dashboard:
- Backend: `Services` → `woodcarvings-api` → `Logs`
- Frontend: `Static Sites` → `woodcarvings-frontend` → `Logs`

## 📊 Performance Optimization

### Backend

1. **Upgrade Plan**: Free tier sleeps after inactivity. Consider Starter plan.
2. **Caching**: Implement Redis for caching generated images
3. **Database**: Add PostgreSQL for persistent storage
4. **CDN**: Use Cloudflare or similar for API caching

### Frontend

1. **Image Optimization**: Compress generated images before display
2. **Code Splitting**: Vite handles this automatically
3. **CDN**: Render serves static sites via CDN automatically

## 🔒 Security Checklist

- [ ] Environment variables set securely (not in code)
- [ ] CORS properly configured (not using `*`)
- [ ] API keys have minimum required permissions
- [ ] HTTPS enforced (Render does this automatically)
- [ ] Rate limiting implemented (add if needed)
- [ ] Input validation on all endpoints

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [Google Vertex AI](https://cloud.google.com/vertex-ai/docs)

## 🆘 Support

If you encounter issues:
1. Check Render logs for error messages
2. Review this deployment guide
3. Test locally first
4. Check Google Cloud quotas and permissions

## 📝 Deployment Checklist

Before deploying:

- [ ] Code pushed to GitHub
- [ ] `requirements.txt` up to date
- [ ] Environment variables documented
- [ ] `.gitignore` excludes sensitive files
- [ ] `render.yaml` configured correctly
- [ ] Google Cloud credentials ready
- [ ] Tested locally
- [ ] Frontend build works (`npm run build`)
- [ ] Backend health check works
- [ ] CORS configured for production domain

After deploying:

- [ ] Both services deployed successfully
- [ ] Health check endpoint responding
- [ ] Frontend loads correctly
- [ ] API calls work from frontend
- [ ] Image generation works
- [ ] Error handling works
- [ ] Logs show no errors

## 🔄 Continuous Deployment

Render automatically redeploys when you push to your main branch:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Render will automatically detect and redeploy
```

## 💰 Cost Estimation

**Free Tier:**
- Backend: Spins down after inactivity, limited compute
- Frontend: Free static site hosting with CDN
- Total: $0/month

**Starter Tier (Recommended for Production):**
- Backend: $7/month - Always on, 512MB RAM
- Frontend: Free
- Total: $7/month

**Note**: Google Cloud Vertex AI costs are separate and based on API usage.
