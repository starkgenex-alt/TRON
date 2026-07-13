# Render Deployment Guide for TRON

## 1. Prepare the repo
Push the latest repository changes to GitHub.

## 2. Create the Render web service
- Sign in to Render.
- Create a new Web Service.
- Connect your GitHub repository.
- Select the repository and the branch to deploy.

## 3. Render settings
Render should pick up the configuration from render.yaml automatically.

Recommended settings:
- Build command: `pip install --upgrade pip && pip install -r requirements.txt`
- Start command: `uvicorn queue_server:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

## 4. Environment variables
Add any of the following if you want billing and provider support:
- `STRIPE_API_KEY`
- `PAYSTACK_SECRET_KEY`
- `FLUTTERWAVE_SECRET_KEY`
- `STABLECOIN_PRIVATE_KEY`
- `STABLECOIN_RPC_URL`

For MVP testing, these can remain unset.

## 5. Deploy
Click Deploy. Render will build the app, start the web service, and expose a default URL such as:
- `https://tron-master.onrender.com`

## 6. DNS and SSL
Render handles SSL automatically for its default domains.

To use a custom domain:
1. Go to the Render service dashboard.
2. Open the Domains tab.
3. Add your custom domain, for example `api.tron.example.com`.
4. In your DNS provider, create a CNAME record pointing the hostname to the Render service URL.
5. Render will provision HTTPS automatically.

## 7. Important note about SQLite
The current MVP uses SQLite, so it is fine for early deployment. If you need multi-instance reliability or stronger persistence, move to Render Postgres later.

## 8. Verify the deployment
After deployment, check:
- `https://<your-render-domain>/health`
- `https://<your-render-domain>/`

Expected response:
```json
{"status":"ok"}
```
