# Quick Start Guide - Deploy to Render in 5 Minutes

## 🎯 Prerequisites Checklist

Before you begin, make sure you have:

- [ ] GitHub account
- [ ] Render account (free) - [Sign up here](https://render.com)
- [ ] Google Cloud project with Vertex AI enabled
- [ ] Google Cloud service account key JSON file
- [ ] Gemini API key (or use Vertex AI only)

## 📦 Step 1: Prepare Your Code

```bash
# 1. Make sure all changes are committed
git add .
git commit -m "Prepare for Render deployment"

# 2. Push to GitHub
git push origin main
```

## 🚀 Step 2: Deploy to Render

### Option A: One-Click Blueprint Deploy (Recommended)

1. **Go to Render Dashboard**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Blueprint"

2. **Connect Repository**
   - Select your WoodCarvings repository
   - Render will auto-detect `render.yaml`
   - Click "Apply"

3. **Set Environment Variables**

   Go to the **Backend Service** settings and add:

   ```
   GEMINI_API_KEY = [Your Gemini API key]
   VERTEX_PROJECT_ID = [Your GCP project ID]
   VERTEX_LOCATION = us-central1
   VERTEX_API_KEY = [Paste entire service account JSON]
   DROPBOX_SHARED_FOLDER_LINK = [Optional]
   ```

4. **Wait for Deployment**
   - Backend: ~5-10 minutes
   - Frontend: ~2-3 minutes

5. **Update URLs**

   After services are created:
   - Copy your backend URL (e.g., `https://woodcarvings-api.onrender.com`)
   - Go to Frontend service → Environment
   - Update `VITE_API_URL` with your backend URL
   - Trigger manual deploy

   Then:
   - Copy your frontend URL
   - Go to Backend service → Environment
   - Update `ALLOWED_ORIGINS` with your frontend URL

### Option B: Manual Service Creation

#### Backend Service

1. New + → Web Service
2. Connect repository → Select branch
3. Configure:
   - **Name**: woodcarvings-api
   - **Runtime**: Python 3
   - **Build Command**:
     ```
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
4. Add environment variables (see above)
5. Click "Create Web Service"

#### Frontend Service

1. New + → Static Site
2. Connect repository → Select branch
3. Configure:
   - **Name**: woodcarvings-frontend
   - **Build Command**:
     ```
     cd frontend && npm install && npm run build
     ```
   - **Publish Directory**:
     ```
     frontend/dist
     ```
4. Add `VITE_API_URL` environment variable
5. Click "Create Static Site"

## ✅ Step 3: Verify Deployment

1. **Test Backend**
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```
   Should return: `{"status":"active","version":"1.0.0"}`

2. **Test Frontend**
   - Visit your frontend URL
   - You should see the WoodCarvings interface
   - Try the health check indicator in the top-right

3. **Test Full Flow**
   - Enter a prompt: "A happy bear holding a fish"
   - Select mode: Sketch
   - Select difficulty: Intermediate
   - Click "Execute Generation"
   - Wait for results (~30-60 seconds)

## 🔧 Troubleshooting

### Backend won't start
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure Python version is 3.11

### Frontend can't connect to backend
- Check `VITE_API_URL` is set correctly
- Verify backend CORS includes frontend URL
- Check backend is running (visit `/health`)

### Image generation fails
- Verify Vertex AI API is enabled in GCP
- Check service account has correct permissions
- Ensure `VERTEX_API_KEY` is valid JSON

### "Service Unavailable" on Free Tier
- Free tier services sleep after 15 min of inactivity
- First request will be slow (~30-60 seconds to wake up)
- Consider upgrading to Starter plan ($7/mo) for always-on

## 💡 Pro Tips

1. **Faster Deployments**: Use Docker deployment method
2. **Better Performance**: Upgrade backend to Starter plan
3. **Cost Optimization**: Use Imagen 3 (cheaper) for testing
4. **Monitoring**: Enable Render's built-in monitoring
5. **Logs**: Check logs regularly for errors

## 🎉 You're Done!

Your WoodCarvings AI is now live and ready to use!

**Next Steps:**
- Share your frontend URL with others
- Monitor usage in Render dashboard
- Check Google Cloud billing
- Set up custom domain (optional)
- Enable continuous deployment (already active!)

## 📚 Additional Resources

- [Full Deployment Guide](./DEPLOYMENT.md)
- [README](./README.md)
- [Render Docs](https://render.com/docs)

## 🆘 Need Help?

If you get stuck:
1. Check the [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed troubleshooting
2. Review Render logs for error messages
3. Test locally first: `python main.py` and `cd frontend && npm run dev`
4. Verify all environment variables are set correctly

---

**Estimated Total Time**: 10-15 minutes
**Cost**: Free tier available, Starter plan $7/month for production
