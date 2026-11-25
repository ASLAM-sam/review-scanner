# Complete Vercel Deployment Guide
## Restaurant QR Feedback & Google Review Assistance System
### Independent Single-Tenant Cloud Deployment

This guide explains step-by-step how to deploy an independent restaurant installation to **Vercel** with a cloud **MongoDB Atlas** database.

---

## 1. Architecture Overview on Vercel

In accordance with our strict single-tenant business model, each restaurant gets its own independent deployment and database:

```
┌─────────────────────────────────────────────────────────────┐
│ Customer & Admin Browsers                                   │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ Vercel Frontend Project      │ │ Vercel Backend Project     │
│ (Next.js 14 App Router)      │ │ (Python Serverless FastAPI)│
│ Root Directory: `frontend`   │ │ Root Directory: `backend`  │
│ e.g. paradise.vercel.app     │ │ e.g. paradise-api.vercel.app
└──────────────┬───────────────┘ └─────────────┬──────────────┘
               │                               │
               │ (Proxy rewrites /api/v1/*)    │
               └───────────────────────────────┤
                                               ▼
                                 ┌────────────────────────────┐
                                 │ MongoDB Atlas (Cloud)      │
                                 │ Dedicated Database:        │
                                 │ `restaurant_<slug>`        │
                                 └────────────────────────────┘
```

* **Frontend (Next.js):** Hosted on Vercel with automatic edge caching and fast client rendering.
* **Backend (FastAPI):** Hosted on Vercel using the official Python Serverless Runtime (`@vercel/python`) via `backend/api/index.py` and `backend/vercel.json`.
* **Zero CORS issues:** The frontend is configured with Next.js rewrites (`BACKEND_URL`), allowing the browser to communicate with `/api/v1` as a same-origin endpoint while forwarding to the backend serverlessly.
* **Dual Auth:** Uses HTTP-only cookies and Authorization Bearer headers for 100% cross-device compatibility.

---

## 2. Step 1: Set Up Cloud Database (MongoDB Atlas)

Serverless functions on Vercel require a persistent cloud database.

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and create a free account.
2. Create a new cluster (The **M0 Free Shared Tier** is fully supported).
3. In **Database Access**:
   * Add a new database user (e.g. `db_admin_paradise`).
   * Create a strong, secure password (avoid special characters that break URI encoding or URL-encode them).
4. In **Network Access**:
   * Click **Add IP Address**.
   * Choose **Allow Access from Anywhere (`0.0.0.0/0`)**.
   * *Why:* Vercel Serverless Functions execute on dynamic IP addresses from AWS Lambda, so `0.0.0.0/0` is required.
5. In **Database Deployments**:
   * Click **Connect** -> **Drivers** -> **Python (version 3.12 or later)**.
   * Copy the connection string format:
     ```
     mongodb+srv://db_admin_paradise:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
     ```

---

## 3. Step 2: Deploy Backend to Vercel

1. Push your repository to **GitHub** (private repository recommended).
2. Log into your [Vercel Dashboard](https://vercel.com).
3. Click **Add New...** -> **Project**.
4. Import your GitHub repository.
5. In the project configuration page:
   * **Project Name:** `paradise-restaurant-api` (or `<restaurant-slug>-api`)
   * **Framework Preset:** Select **Other**
   * **Root Directory:** Click **Edit**, select **`backend`**, and click **Continue**.
6. Expand **Environment Variables** and enter the following:

| Variable Name | Example Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Enables production security gates |
| `DEBUG` | `False` | Disables debug traces and Swagger UI in prod |
| `SECRET_KEY` | `r83kd94jfnw0192837465gvhsbzlska0192` | Random cryptographic secret (minimum 32 characters) |
| `MONGODB_URI` | `mongodb+srv://user:pass@cluster0.net/...` | Your MongoDB Atlas connection URI |
| `MONGODB_DB_NAME` | `restaurant_paradise` | Dedicated database for this restaurant |
| `MONGODB_CONNECT_TIMEOUT_MS` | `5000` | Connection timeout in milliseconds |
| `ALLOWED_ORIGINS` | `https://paradise-restaurant.vercel.app` | URL of your frontend Vercel deployment |
| `ALLOWED_ORIGIN_REGEX` | `^https:\/\/.*\.vercel\.app$` | Allows all Vercel preview and production subdomains |
| `COOKIE_SAMESITE` | `lax` | Cookie SameSite mode |
| `INITIAL_ADMIN_USERNAME` | `aslam` | Initial admin account username |
| `INITIAL_ADMIN_PASSWORD` | `aslam0077` | Initial admin account password |
| `RESTAURANT_NAME` | `Paradise Restaurant` | Legal/display name of the restaurant |
| `RESTAURANT_SLUG` | `paradise-restaurant` | Unique slug for QR URLs |
| `RESTAURANT_DESCRIPTION` | `Authentic Fine Dining Cuisine` | Short bio / tagline |
| `RESTAURANT_GOOGLE_REVIEW_URL` | `https://g.page/r/your-google-review-link` | Live Google Maps review invitation link |
| `RESTAURANT_QR_BASE_URL` | `https://paradise-restaurant.vercel.app/r` | Public QR base URL |
| `RAZORPAY_KEY_ID` | `rzp_live_...` (or `rzp_test_...`) | Razorpay API key ID |
| `RAZORPAY_KEY_SECRET` | `<your-razorpay-key-secret>` | Razorpay API key secret |
| `RAZORPAY_WEBHOOK_SECRET` | `<your-webhook-secret>` | Razorpay webhook verification secret |

7. Click **Deploy**.
8. Once deployed, note your backend domain (e.g., `https://paradise-restaurant-api.vercel.app`).
9. Verify backend health by visiting: `https://paradise-restaurant-api.vercel.app/api/v1/health`
   * Should return: `{"status":"healthy","database":"connected",...}`

---

## 4. Step 3: Deploy Frontend to Vercel

1. In your [Vercel Dashboard](https://vercel.com), click **Add New...** -> **Project**.
2. Select the **same GitHub repository**.
3. In the project configuration page:
   * **Project Name:** `paradise-restaurant` (or `<restaurant-slug>`)
   * **Framework Preset:** **Next.js** (automatically detected)
   * **Root Directory:** Click **Edit**, select **`frontend`**, and click **Continue**.
4. Expand **Environment Variables** and enter:

| Variable Name | Recommended Value | Description |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `/api/v1` | Relative URL routed through Next.js proxy |
| `BACKEND_URL` | `https://paradise-restaurant-api.vercel.app` | URL of the backend project deployed in Step 2 |

> **Pro-Tip on `BACKEND_URL`**: Setting `BACKEND_URL` activates the built-in Next.js rewrites configured in `frontend/next.config.mjs`. This routes all `/api/v1/*` requests directly through the Next.js server to the backend. This guarantees **same-origin cookies** and prevents third-party cookie blocking on iOS Safari and Google Chrome!

5. Click **Deploy**.
6. Once deployed, your frontend is live at `https://paradise-restaurant.vercel.app`!

---

## 5. Step 4: Configure Razorpay Webhook

1. Log into your [Razorpay Dashboard](https://dashboard.razorpay.com).
2. Go to **Settings** -> **Webhooks**.
3. Click **Add New Webhook**.
4. Set the **Webhook URL**:
   ```
   https://paradise-restaurant-api.vercel.app/api/v1/subscription/webhook
   ```
5. Set the **Secret**: Enter the exact secret you configured in `RAZORPAY_WEBHOOK_SECRET`.
6. Select the **Active Events**:
   * `payment.captured`
   * `payment.failed`
   * `order.paid`
   * `payment.refunded`
7. Click **Create Webhook**.

---

## 6. Verification Checklist

After deployment, test the following endpoints on your live Vercel URLs:

- [ ] **Backend Health Check:** Open `https://paradise-restaurant-api.vercel.app/api/v1/health` -> verify `"database": "connected"`.
- [ ] **Admin Login:** Open `https://paradise-restaurant.vercel.app/admin/login` -> log in with your configured admin credentials.
- [ ] **Admin Dashboard:** Verify 4 business metrics (Total Scans, Feedback, Review Clicks, 12-Month Table).
- [ ] **QR Feedback Experience:** Open `https://paradise-restaurant.vercel.app/r/paradise-restaurant` on a mobile browser or mobile devtools -> submit feedback.
- [ ] **Google Review Button:** Click "Write a Review on Google" -> verify external tab opens and click metric increments on dashboard.
- [ ] **Permanent QR Code:** Download the PNG and SVG collateral from the Admin QR page.
