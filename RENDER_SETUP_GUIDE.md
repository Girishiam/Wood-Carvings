# Complete Render Deployment Guide - Step by Step

Follow this guide exactly to deploy your WoodCarvings AI app to Render.

---

## 📋 PART 1: Prerequisites (10 minutes)

### ✅ Checklist - Do These First

- [ ] GitHub account ([Sign up](https://github.com))
- [ ] Render account ([Sign up](https://render.com))
- [ ] Google Cloud account ([Sign up](https://console.cloud.google.com))
- [ ] Your code is committed to GitHub

---

## 🔧 PART 2: Google Cloud Setup (5 minutes)

### Step 1: Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click the project dropdown (top bar, next to "Google Cloud")
3. Click "NEW PROJECT"
4. Enter project name: `woodcarvings-ai`
5. Click "CREATE"
6. **Wait for project to be created** (~30 seconds)
7. **Select your new project** from the dropdown

### Step 2: Enable Required APIs

1. In the search bar at top, type: `Vertex AI API`
2. Click on "Vertex AI API"
3. Click "ENABLE"
4. Wait for it to enable (~1 minute)

**Optional but recommended:**
1. Search for: `Generative Language API`
2. Click "ENABLE" (for Gemini API support)

### Step 3: Create Service Account

1. In the search bar, type: `Service Accounts`
2. Click "Service Accounts" under IAM & Admin
3. Click "CREATE SERVICE ACCOUNT"
4. Fill in:
   - **Service account name**: `woodcarvings-service`
   - **Service account ID**: (auto-filled)
   - **Description**: `Service account for WoodCarvings AI`
5. Click "CREATE AND CONTINUE"
6. **Grant access**:
   - Click "Select a role"
   - Search for: `Vertex AI User`
   - Select it
   - Click "CONTINUE"
7. Click "DONE"

### Step 4: Generate Service Account Key

1. Find your new service account in the list
2. Click on it
3. Go to "KEYS" tab
4. Click "ADD KEY" → "Create new key"
5. Select "JSON"
6. Click "CREATE"
7. **A file downloads automatically** - this is your key!
8. **IMPORTANT**: Save this file somewhere safe. You'll need it in Step 8.

### Step 5: Get Your Project ID

1. In Google Cloud Console, look at the top bar
2. You'll see your project name and below it: a project ID (like `woodcarvings-ai-123456`)
3. **Copy this project ID** - you'll need it later

---

## 📦 PART 3: Prepare Your Code (2 minutes)

### Step 6: Commit and Push to GitHub

Open your terminal in the project folder:

```bash
# Check status
git status

# Add all files
git add .

# Commit
git commit -m "Ready for Render deployment"

# Push to GitHub
git push origin main
```

**Don't have a GitHub repo yet?**

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit"

# Create a new repo on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/WoodCarvings.git
git branch -M main
git push -u origin main
```

---

## 🚀 PART 4: Deploy to Render (10 minutes)

### Step 7: Create Services on Render

#### Option A: Blueprint Deploy (Automatic - Recommended)

1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub account (if not already)
4. Find and select your `WoodCarvings` repository
5. Click "Connect"
6. Render will detect `render.yaml`
7. **Give it a name**: `woodcarvings`
8. Click "Apply"
9. **Wait** - Render creates both services automatically
10. You'll see:
    - `woodcarvings-api` (Web Service)
    - `woodcarvings-frontend` (Static Site)

#### Option B: Manual Deploy (if Blueprint doesn't work)

**Create Backend Service:**

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select `WoodCarvings` repository
5. Configure:
   - **Name**: `woodcarvings-api`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: (leave blank)
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free
6. **Don't click Create yet!** Scroll down to Environment Variables first.

**Create Frontend Service:**

1. Click "New +" → "Static Site"
2. Connect your repository
3. Select `WoodCarvings`
4. Configure:
   - **Name**: `woodcarvings-frontend`
   - **Branch**: `main`
   - **Root Directory**: (leave blank)
   - **Build Command**:
     ```
     cd frontend && npm install && npm run build
     ```
   - **Publish Directory**:
     ```
     frontend/dist
     ```
5. Click "Create Static Site"

### Step 8: Configure Environment Variables

**For Backend Service:**

1. Go to your `woodcarvings-api` service
2. Click "Environment" in the left sidebar
3. Click "Add Environment Variable"
4. Add these variables one by one:

**Variable 1:**
```
Key: VERTEX_PROJECT_ID
Value: [Your project ID from Step 5]
```

**Variable 2:**
```
Key: VERTEX_LOCATION
Value: us-central1
```

**Variable 3:**
```
Key: VERTEX_API_KEY
Value: [Paste ENTIRE contents of JSON file from Step 4]
```

**To get JSON contents:**
- Open the JSON file you downloaded in Step 4
- Copy EVERYTHING (it will look like `{"type":"service_account",...}`)
- Paste into the value field

**Variable 4 (Optional but recommended):**
```
Key: GEMINI_API_KEY
Value: [Get from https://makersuite.google.com/app/apikey]
```

**Variable 5:**
```
Key: ALLOWED_ORIGINS
Value: https://woodcarvings-frontend.onrender.com
```

**Note:** You'll update ALLOWED_ORIGINS with your actual frontend URL in Step 10.

5. Click "Save Changes"

**For Frontend Service:**

1. Go to your `woodcarvings-frontend` service
2. Click "Environment"
3. Add:

```
Key: VITE_API_URL
Value: https://woodcarvings-api.onrender.com
```

**Note:** You'll update this with your actual backend URL in Step 10.

4. Click "Save Changes"

### Step 9: Wait for Deployment

1. Go to each service dashboard
2. Watch the "Logs" section
3. **Backend**: Takes 5-10 minutes
   - You'll see: "Installing dependencies..."
   - Then: "Starting server..."
   - Success: "Application startup complete"
4. **Frontend**: Takes 2-5 minutes
   - You'll see: "Building..."
   - Then: "Uploading static files..."
   - Success: "Deploy live"

### Step 10: Update URLs (Important!)

**Get Your URLs:**

1. Go to `woodcarvings-api` dashboard
2. At the top, you'll see a URL like: `https://woodcarvings-api-abc123.onrender.com`
3. **Copy this URL**

4. Go to `woodcarvings-frontend` dashboard
5. You'll see a URL like: `https://woodcarvings-frontend-xyz789.onrender.com`
6. **Copy this URL**

**Update Backend Environment:**

1. Go to `woodcarvings-api` → "Environment"
2. Edit `ALLOWED_ORIGINS`
3. Change to your **frontend URL** (from above)
4. Example: `https://woodcarvings-frontend-xyz789.onrender.com`
5. Save Changes
6. Service will automatically redeploy

**Update Frontend Environment:**

1. Go to `woodcarvings-frontend` → "Environment"
2. Edit `VITE_API_URL`
3. Change to your **backend URL** (from above)
4. Example: `https://woodcarvings-api-abc123.onrender.com`
5. Save Changes
6. Click "Manual Deploy" → "Clear build cache & deploy"

### Step 11: Test Your Deployment

**Test Backend:**

1. Open new browser tab
2. Go to: `https://YOUR-BACKEND-URL.onrender.com/health`
3. You should see:
   ```json
   {"status":"active","version":"1.0.0"}
   ```

**Test Frontend:**

1. Go to: `https://YOUR-FRONTEND-URL.onrender.com`
2. You should see the WoodCarvings interface
3. Check the top-right corner - should show connection status

**Test Full Flow:**

1. In the frontend:
   - Enter prompt: "A happy bear carving"
   - Select mode: Sketch
   - Select difficulty: Intermediate
   - Click "Execute Generation"
2. **Wait 30-60 seconds** (first request takes longer)
3. You should see the generated character sheet!

---

## 🎉 You're Live!

Your app is now deployed at:
- **Frontend**: `https://your-frontend-url.onrender.com`
- **Backend API**: `https://your-backend-url.onrender.com`

---

## 🔧 Common Issues & Fixes

### Issue 1: Backend Shows "Service Unavailable"

**Cause**: Free tier services sleep after 15 minutes of inactivity

**Fix**:
- Wait 30-60 seconds for it to wake up
- Or upgrade to Starter plan ($7/mo) for always-on service

### Issue 2: Frontend Can't Connect to Backend

**Symptoms**: "Failed to connect to backend API"

**Fix**:
1. Check backend is running: visit `/health` endpoint
2. Verify `VITE_API_URL` is set correctly
3. Verify `ALLOWED_ORIGINS` includes frontend URL
4. Check URLs don't have trailing slashes

### Issue 3: "Authentication Error" from Google

**Symptoms**: "Permission denied" or "Invalid credentials"

**Fix**:
1. Check `VERTEX_API_KEY` contains valid JSON
2. Verify service account has "Vertex AI User" role
3. Ensure Vertex AI API is enabled in Google Cloud

### Issue 4: Build Fails

**Backend Build Fails:**
- Check `requirements.txt` exists
- Verify Python version (should be 3.11)
- Check logs for specific error

**Frontend Build Fails:**
- Ensure `frontend/package.json` exists
- Check `frontend/dist` is the correct output directory
- Review build logs for npm errors

### Issue 5: Slow First Request

**Cause**: Free tier spins down after inactivity

**Fix**:
- This is normal behavior
- First request takes ~30-60 seconds
- Subsequent requests are fast
- Upgrade to Starter plan for always-on

---

## 💰 Cost Breakdown

**Render:**
- Backend (Free): $0/month (sleeps after inactivity)
- Backend (Starter): $7/month (always on)
- Frontend: $0/month (always free)

**Google Cloud:**
- Free tier: $300 credit (90 days)
- Imagen 3: ~$0.02 per image
- Imagen 4: ~$0.04 per image
- Example: 100 images/month = $2-4/month

**Total: Free to start, ~$7-11/month for production**

---

## 🔄 Automatic Deployments

Every time you push to GitHub, Render automatically redeploys:

```bash
# Make changes to your code
git add .
git commit -m "Updated feature"
git push origin main

# Render automatically detects and redeploys!
# Check deployment status in Render dashboard
```

---

## 📊 Monitoring & Logs

**View Logs:**
1. Go to service dashboard
2. Click "Logs" tab
3. Watch real-time logs
4. Filter by log level

**Check Metrics:**
1. Click "Metrics" tab
2. See CPU, memory, requests
3. Monitor performance

**Set Up Alerts:**
1. Click "Notifications"
2. Add email for deploy failures
3. Get notified of issues

---

## 🆘 Still Stuck?

If something isn't working:

1. **Check Logs**: Always check logs first for error messages
2. **Test Locally**: Run `python main.py` to test backend locally
3. **Verify Environment Variables**: Double-check all variables are set
4. **Check GitHub**: Ensure all code is pushed
5. **Review Docs**: Check [DEPLOYMENT.md](./DEPLOYMENT.md) for details

**Most Common Fix**: Verify your Google Cloud service account JSON is valid and has the right permissions.

---

## ✅ Deployment Checklist

Before going live:

- [ ] Google Cloud project created
- [ ] Vertex AI API enabled
- [ ] Service account created with "Vertex AI User" role
- [ ] Service account key (JSON) downloaded
- [ ] Code pushed to GitHub
- [ ] Render services created
- [ ] All environment variables set
- [ ] URLs updated in environment variables
- [ ] Backend `/health` endpoint works
- [ ] Frontend loads correctly
- [ ] Test image generation works
- [ ] Logs show no errors

After deployment:

- [ ] Test from different devices
- [ ] Monitor costs in Google Cloud
- [ ] Set up billing alerts
- [ ] Share frontend URL with users
- [ ] Consider upgrading to Starter plan for production

---

## 🎯 Next Steps

1. **Custom Domain**: Add your own domain in Render settings
2. **Monitoring**: Set up alerts for downtime
3. **Analytics**: Add Google Analytics to frontend
4. **Optimization**: Monitor API costs and optimize prompts
5. **Scaling**: Upgrade to Starter plan when ready for production

---

**Congratulations! Your WoodCarvings AI is live! 🎉**

Share your frontend URL and start generating amazing character sheets!
