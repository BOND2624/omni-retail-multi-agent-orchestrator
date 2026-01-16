# Deploy to Render - Step by Step Guide

This guide will help you deploy your Omni-Retail Orchestrator to Render with full WebSocket support.

## Prerequisites

1. ✅ GitHub account
2. ✅ Render account (sign up at [render.com](https://render.com) - free, no credit card needed)
3. ✅ OpenRouter API key

## Step 1: Prepare Your Code

### 1.1 Update server.py for Render

Make sure `server.py` reads the PORT environment variable (Render requires this):

```python
import os
# ... other imports ...

if __name__ == "__main__":
    # ... database initialization ...
    
    # Use PORT from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
```

### 1.2 Push to GitHub

Make sure your code is on GitHub:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with GitHub (easiest option)
4. Authorize Render to access your repositories

## Step 3: Create Web Service

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Click **"Connect account"** if you haven't already
3. Select your repository: `omni-retail-multiagent-orchestrator`
4. Click **"Connect"**

## Step 4: Configure Service Settings

Fill in the following:

### Basic Settings
- **Name**: `omni-retail-orchestrator` (or your choice)
- **Region**: Choose closest to you (e.g., `Oregon (US West)`)
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty (or `.` if needed)

### Build & Deploy
- **Environment**: `Python 3`
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  python server.py
  ```

### Advanced Settings (Optional)
- **Auto-Deploy**: `Yes` (deploys automatically on every push)
- **Health Check Path**: Leave empty (or `/api/health` if you add it)

## Step 5: Add Environment Variables

In the **"Environment"** section, add:

1. Click **"Add Environment Variable"**
2. Add:
   - **Key**: `OPENROUTER_API_KEY`
   - **Value**: Your OpenRouter API key
3. Click **"Save Changes"**

**Note**: Render automatically sets `PORT` environment variable (usually `10000`), so you don't need to set it manually.

## Step 6: Deploy

1. Scroll down and click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Build your application
   - Start your server
   - Provide a public URL

## Step 7: Access Your App

Once deployment completes (takes 2-5 minutes), Render will provide a URL like:
```
https://omni-retail-orchestrator.onrender.com
```

Click the URL or copy it to access your application!

## Step 8: Test WebSocket Connection

1. Open your deployed URL
2. The UI should load
3. Try sending a query
4. WebSocket connection should work automatically (no special config needed)

## Important Notes

### Free Tier Limitations

⚠️ **Service Sleeps After 15 Minutes of Inactivity**
- First request after sleep takes ~30-60 seconds (cold start)
- Subsequent requests are fast
- **Solution**: Use a ping service (see below)

### Keep Service Awake (Optional)

To prevent your service from sleeping:

1. **Option 1: Use UptimeRobot (Free)**
   - Sign up at [uptimerobot.com](https://uptimerobot.com)
   - Add a monitor for your Render URL
   - Set it to ping every 5-10 minutes
   - This keeps your service awake

2. **Option 2: Upgrade to Paid Plan**
   - Render paid plans keep services always-on
   - Starts at $7/month

### Database Storage

- **SQLite**: Works but data is ephemeral (lost on redeploy)
- **PostgreSQL**: Render offers free PostgreSQL (recommended for production)
  - Add via "New +" → "PostgreSQL"
  - Connection string automatically set as `DATABASE_URL`

## Troubleshooting

### Port Issues

If you see port errors:
- Make sure `server.py` reads `PORT` from environment: `port = int(os.getenv("PORT", 8000))`
- Render sets `PORT` automatically (usually `10000`)

### WebSocket Connection Issues

- Render fully supports WebSockets
- Make sure your frontend uses `wss://` for HTTPS (not `ws://`)
- Check browser console for connection errors

### Build Failures

- Check build logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Make sure Python version is compatible (Render uses Python 3.10+)

### Database Initialization Errors

- Check that database files can be created
- SQLite works but is ephemeral
- Consider PostgreSQL for persistence

## Updating Your Code

To update your deployed app:

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update code"
   git push origin main
   ```
3. Render automatically detects the push and redeploys
4. Wait 2-5 minutes for deployment to complete

## Monitoring

- **Logs**: View real-time logs in Render dashboard
- **Metrics**: Check CPU, memory, and request metrics
- **Status**: Monitor service health and uptime

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test WebSocket connections
3. ✅ Set up UptimeRobot to keep service awake (optional)
4. ✅ Share your deployed URL!

## Need Help?

- Check Render logs for detailed error messages
- Review Render documentation: [render.com/docs](https://render.com/docs)
- Common issues are usually in the build logs

Good luck with your deployment! 🚀
