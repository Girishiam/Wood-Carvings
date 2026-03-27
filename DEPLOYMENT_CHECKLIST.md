# Deployment Checklist - Print This!

Use this checklist to track your deployment progress.

---

## 📋 Pre-Deployment Setup

### Google Cloud (5 min)
- [ ] Created Google Cloud account
- [ ] Created project: `woodcarvings-ai`
- [ ] Enabled Vertex AI API
- [ ] Created service account: `woodcarvings-service`
- [ ] Added role: "Vertex AI User"
- [ ] Downloaded service account JSON key
- [ ] Saved project ID: `________________`

### GitHub (2 min)
- [ ] Code is committed
- [ ] Code is pushed to GitHub
- [ ] Repository URL: `____________________________`

### Render Account
- [ ] Created Render account
- [ ] Logged in to dashboard

---

## 🚀 Render Deployment

### Service Creation
- [ ] Created Blueprint OR manual services
- [ ] Backend service created: `woodcarvings-api`
- [ ] Frontend service created: `woodcarvings-frontend`

### Backend Environment Variables
Set in `woodcarvings-api` → Environment:

- [ ] `VERTEX_PROJECT_ID` = `________________`
- [ ] `VERTEX_LOCATION` = `us-central1`
- [ ] `VERTEX_API_KEY` = (JSON contents pasted)
- [ ] `GEMINI_API_KEY` = `________________` (optional)
- [ ] `ALLOWED_ORIGINS` = (will update after deploy)

### Frontend Environment Variables
Set in `woodcarvings-frontend` → Environment:

- [ ] `VITE_API_URL` = (will update after deploy)

### Initial Deployment
- [ ] Backend is building (check logs)
- [ ] Frontend is building (check logs)
- [ ] Backend build completed
- [ ] Frontend build completed

---

## 🔗 URL Configuration

### Get URLs
- [ ] Backend URL: `https://____________________________`
- [ ] Frontend URL: `https://____________________________`

### Update Environment Variables
- [ ] Updated backend `ALLOWED_ORIGINS` with frontend URL
- [ ] Updated frontend `VITE_API_URL` with backend URL
- [ ] Triggered manual deploy on frontend
- [ ] Services redeployed successfully

---

## ✅ Testing

### Backend Tests
- [ ] `/health` endpoint returns: `{"status":"active","version":"1.0.0"}`
- [ ] No errors in backend logs

### Frontend Tests
- [ ] Frontend loads in browser
- [ ] No console errors (F12)
- [ ] Connection indicator shows status

### Full Integration Test
- [ ] Entered test prompt
- [ ] Selected mode and difficulty
- [ ] Clicked "Execute Generation"
- [ ] Image generated successfully
- [ ] Can download image
- [ ] Total time: ~30-60 seconds

---

## 🎯 Post-Deployment

### Monitoring
- [ ] Checked logs for errors
- [ ] Set up deploy notifications
- [ ] Added billing alerts in Google Cloud

### Documentation
- [ ] Saved backend URL
- [ ] Saved frontend URL
- [ ] Documented environment variables
- [ ] Created backup of service account JSON

### Optional Improvements
- [ ] Upgrade to Starter plan ($7/mo) for always-on
- [ ] Add custom domain
- [ ] Set up analytics
- [ ] Configure rate limiting

---

## 🆘 Troubleshooting Checklist

If something doesn't work:

- [ ] Checked service logs in Render
- [ ] Verified all environment variables are set
- [ ] Confirmed URLs don't have trailing slashes
- [ ] Tested backend `/health` endpoint
- [ ] Verified Vertex AI API is enabled
- [ ] Checked service account has correct role
- [ ] Waited 60 seconds for free tier wake-up
- [ ] Tried clearing browser cache
- [ ] Tested in incognito/private window

---

## 📝 Important URLs & Info

**Save These:**

| Item | Value |
|------|-------|
| Frontend URL | `https://____________________________` |
| Backend URL | `https://____________________________` |
| GitHub Repo | `https://____________________________` |
| Google Project ID | `____________________________` |
| Render Account Email | `____________________________` |

**Credentials Location:**
- Service Account JSON: `____________________________`
- .env file (local): `____________________________`

---

## 🎉 Deployment Complete!

**Date Deployed**: _______________

**Deployment Notes**:
```
_________________________________________________
_________________________________________________
_________________________________________________
```

---

**Print this checklist and check off items as you complete them!**
