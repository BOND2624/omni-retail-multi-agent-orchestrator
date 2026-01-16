# Quick Render Deployment

## 🚀 Fast Setup (5 minutes)

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Ready for Render"
   git push origin main
   ```

2. **Go to [render.com](https://render.com)** and sign up (free, no credit card)

3. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python server.py`

4. **Add Environment Variable**
   - Key: `OPENROUTER_API_KEY`
   - Value: Your API key

5. **Deploy!**
   - Click "Create Web Service"
   - Wait 2-5 minutes
   - Get your URL: `https://your-app.onrender.com`

## ⚠️ Important Notes

- **Free tier sleeps after 15 min** - First request may be slow (~30-60s)
- **Keep it awake**: Use [UptimeRobot](https://uptimerobot.com) to ping every 10 minutes (free)
- **WebSockets work!** - No special config needed

## 📖 Full Guide

See `DEPLOY_RENDER.md` for detailed instructions.

## 🆘 Troubleshooting

- **Port errors?** - Make sure `server.py` reads `PORT` from environment ✅ (already done)
- **Build fails?** - Check `requirements.txt` has all dependencies
- **WebSocket issues?** - Use `wss://` in frontend (automatic with HTTPS)

Good luck! 🎉
