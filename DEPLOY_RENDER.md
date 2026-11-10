# Deploying KiranaVaani to Render (render.com)

This guide walks you through deploying **KiranaVaani (किरानावाणी)** as a full-stack web service on [Render](https://render.com) in under 3 minutes.

---

## Architecture Overview

KiranaVaani is packaged as a **unified multi-stage container**:
- **Frontend**: React 18 + Vite + Tailwind CSS compiled into production assets (`frontend/dist`).
- **Backend**: FastAPI + Uvicorn serving both REST/WebSocket speech APIs and static frontend assets at the root (`/`).
- **Zero CORS Issues**: Because frontend and backend are served from the same domain, no cross-origin configuration or reverse proxy is needed.
- **Cost**: Runs comfortably within Render's **Free Tier** ($0/month).

---

## Method 1: 1-Click Render Blueprint (Recommended)

Render provides Infrastructure-as-Code via `render.yaml` included in this repository.

### Step 1: Go to Render Dashboard
1. Sign in to your account at [dashboard.render.com](https://dashboard.render.com).
2. Click the **New +** button in the top navigation bar.
3. Select **Blueprint**.

### Step 2: Connect Your GitHub Repository
1. Connect your GitHub account (if not already connected).
2. Select your repository: `vikassharma270907-alt/kiranavaani`.
3. Branch: `main`.

### Step 3: Review & Deploy
1. Render will automatically parse `render.yaml` and configure:
   - **Service Name**: `kiranavaani`
   - **Runtime**: `Docker`
   - **Plan**: `Free`
   - **Health Check Path**: `/health`
2. If prompted for `GNANI_API_KEY`:
   - Enter your Gnani AI API key (or leave empty to run in built-in mock/demo mode).
3. Click **Apply**.
4. Render will start the build. Once completed (~2-3 minutes), your service will be live at `https://kiranavaani.onrender.com` (or your chosen service slug).

---

## Method 2: Manual Web Service Setup

If you prefer setting up the Web Service manually via Render's UI:

### Step 1: Create New Web Service
1. In [dashboard.render.com](https://dashboard.render.com), click **New +** > **Web Service**.
2. Choose **Build and deploy from a Git repository** > **Next**.
3. Select `vikassharma270907-alt/kiranavaani`.

### Step 2: Configure Service Details
Fill in the following fields:

| Field | Value |
| :--- | :--- |
| **Name** | `kiranavaani` (or your preferred name) |
| **Region** | `Oregon (US West)` or `Singapore (Southeast Asia)` |
| **Branch** | `main` |
| **Root Directory** | *(leave empty)* |
| **Runtime** | **Docker** |
| **Instance Type** | **Free** |

### Step 3: Set Environment Variables & Health Check
Scroll down and expand **Advanced**:
1. Under **Health Check Path**, enter:
   ```
   /health
   ```
2. Under **Environment Variables**, add:
   - `PORT`: `10000` (Render binds to this port)
   - `GNANI_API_KEY`: `your_gnani_api_key_here` *(Optional: omit for demo mode)*
   - `GNANI_STT_MODEL`: `prisma-v3.0`
   - `GNANI_TTS_MODEL`: `timbre-v2.5`
   - `CONFIDENCE_THRESHOLD`: `0.78`

### Step 4: Deploy
Click **Create Web Service**. Render will pull the repository, run the multi-stage Docker build, and start your live instance.

---

## Verifying Your Live Deployment

Once Render finishes deploying (marked by a green **Live** badge):

### 1. Interactive Web Cockpit
Visit your public Render URL:
```
https://<your-service-name>.onrender.com/
```
You will see the full KiranaVaani interactive cockpit with audio recorder, live transcription, shopping cart, and clarification gates.

### 2. Backend Health Check
Test the health probe:
```bash
curl https://<your-service-name>.onrender.com/health
```
Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "service": "KiranaVaani Backend",
  "gnani_live_configured": false,
  "gnani_stt_model": "prisma-v3.0",
  "gnani_tts_model": "timbre-v2.5",
  "catalogue_sku_count": 35,
  "supported_languages": ["hi-IN", "en-IN", "Hinglish (Code-Mixed)"]
}
```

### 3. Interactive Swagger API Documentation
Explore and test all REST endpoints directly in your browser:
```
https://<your-service-name>.onrender.com/docs
```

---

## Important Notes on Render Free Tier

1. **Cold Starts**: Render spins down free web services after 15 minutes of inactivity. When a new request arrives, Render spins up the container in ~30–50 seconds.
2. **Continuous Deployment**: Any commit pushed to the `main` branch of `vikassharma270907-alt/kiranavaani` will automatically trigger a new deployment on Render.
3. **Logs**: You can view real-time logs under the **Logs** tab in your Render dashboard to inspect incoming speech requests, fuzzy matching scores, and clarification dialog triggers.
