---
description: Deploy Ella to Railway
---

1. **Push to GitHub**: Ensure your latest code is pushed to your GitHub repository `stevenAIEngineer/Ella`.
2. **Login to Railway**: Go to [railway.app](https://railway.app) and login with your GitHub account.
3. **New Project**: Click "New Project" -> "Deploy from GitHub repo".
4. **Select Repo**: Choose `Ella`.
5. **Configure Variables**:
   - In the project dashboard, go to the "Variables" tab.
   - Add `GOOGLE_API_KEY`: Paste your API key (`AIzaSy...`).
6. **Start Command**: Railway usually auto-detects Python, but ensure the Start Command in "Settings" is:
   `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
7. **Deploy**: Railway will build and deploy. Once done, it will provide a public URL (e.g., `ella-production.up.railway.app`).
