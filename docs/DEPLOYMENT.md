# Production Deployment Guide

## Architecture
- **Backend**: Render (Python/FastAPI) → `https://verimed-api.onrender.com`
- **Database**: Neon Postgres 17
- **Frontend**: Netlify (Next.js)
- **Assets**: Data files bundled with backend

---

## 1. Set Up Neon Postgres 17

1. Go to [console.neon.tech](https://console.neon.tech)
2. Create new project → Select **Postgres 17**
3. Copy connection string (looks like):
   ```
   postgresql://user:<password>@host/dbname?sslmode=require
   ```
4. Save this — you'll need it in Render env vars

---

## 2. Deploy Backend to Render

### Connect GitHub repo
1. Go to [render.com](https://render.com) → New → Web Service
2. Select "Deploy existing GitHub repo" (connect account if needed)
3. Choose `verimed` repo
4. Fill deployment settings:
   - **Root Directory**: `backend`
   - **Name**: `verimed-api`
   - **Environment**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`

### Set Environment Variables in Render:
```
ANTHROPIC_API_KEY=<your-key>
NVIDIA_OPENAI_API_KEY=<your-key>
NVIDIA_OPENAI_API_URL=https://integrate.api.nvidia.com/v1/chat/completions
NVIDIA_OPENAI_MODEL=openai/gpt-oss-20b
DATA_DIR=data
DATABASE_URL=<neon-connection-string>
ALLOWED_ORIGINS=https://verimed-web.netlify.app,https://verimed-api.onrender.com
```

### Deploy
- Click Deploy
- Render auto-builds and deploys to `https://verimed-api.onrender.com`

---

## 3. Deploy Frontend to Netlify

### Connect repo
1. Go to [netlify.com](https://www.netlify.com) → Add new site → Import from Git
2. Select `frontend/nextjs-app` folder
3. Framework: **Next.js**

### Set Environment Variables:
```
NEXT_PUBLIC_API_URL=https://verimed-api.onrender.com
```

### Deploy
- Click Deploy
- Netlify assigns subdomain (production URL: `https://verimed-web.netlify.app`)
- **Update Render's `ALLOWED_ORIGINS` with this URL**

---

## 4. Migrate Data (SQLite → Postgres)

For now, keep SQLite for conversation persistence:
- Bundle `backend/data/verimed.sqlite3` with container
- No schema migration needed for MVP
- Later: implement `alembic` for Postgres migrations

---

## 5. Reference Images

Ensure `backend/data/reference_images/` is in repo and gets deployed:
```bash
# Verify before deploy:
find data/reference_images -type f | wc -l
```

---

## Environment Checklist

- [ ] Neon Postgres connection string copied
- [ ] Render API key generated
- [ ] GitHub connected to Render
- [ ] Netlify account created
- [ ] `ANTHROPIC_API_KEY` and `NVIDIA_OPENAI_API_KEY` added to both services
- [ ] `ALLOWED_ORIGINS` includes `https://verimed-web.netlify.app`
- [ ] Reference images committed to repo
- [ ] First deploy test: `/api/health` returns `{"status": "ok"}`
- [ ] Frontend loads and calls backend API

---

## Monitoring

### Render
- Logs: `https://dashboard.render.com → verimed-api → Logs`
- Health checks: Render pings `/` every 30s

### Netlify
- Logs: `https://app.netlify.com → Site settings → Functions/Deploy logs`

---

## Scaling Notes

If you exceed free tier limits:
- **Render**: Standard plan ($7/mo) for production workloads
- **Neon**: Pay-as-you-go ($0.10/GB stored)
- **Netlify**: Automatic scaling on managed infrastructure

---

## Rollback

### Backend (Render)
- Dashboard → Deployments → Select previous build → Redeploy

### Frontend (Netlify)
- Dashboard → Deployments → Select previous build → Redeploy
