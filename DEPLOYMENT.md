# Production Deployment & Operations Guide
## Restaurant QR Feedback & Google Review Assistance System

> **Independent Single-Tenant Deployment Architecture**
> Version: Phase 6 Production Release
> Pricing & Plan: ₹249 / month (`24900` paise INR)

---

## 1. Architectural Model & Guarantees

This software is **strictly single-tenant**. Each restaurant receives:
- An isolated frontend application instance.
- An isolated FastAPI backend application instance.
- An isolated MongoDB database (`restaurant_<slug>`).
- Dedicated restaurant branding, configuration, and admin credentials.
- A permanent QR URL (e.g., `https://reviews.paradiserestaurant.com/r/paradise-restaurant`).
- Dedicated subscription status and payment history records.

**There is zero cross-restaurant data sharing, zero multi-tenancy leakage, and no central platform dashboard.**

---

## 2. Server Requirements & Prerequisites

### System Requirements (Per Installation)
- **Operating System**: Ubuntu 22.04 LTS or Debian 12 (Linux VM / VPS or Docker container).
- **CPU**: 1 vCPU minimum (2 vCPUs recommended for high-volume dining).
- **RAM**: 2 GB RAM minimum (4 GB recommended).
- **Disk**: 20 GB SSD storage.
- **Runtimes**:
  - Python 3.12+ (Backend)
  - Node.js 18.x or 20.x LTS (Frontend)
  - MongoDB 7.0+ (Dedicated database)
- **Reverse Proxy**: Nginx 1.24+ or Caddy 2.7+ with Let's Encrypt TLS.

---

## 3. Environment Configuration Checklist

Create a secure `.env` file in the `backend/` directory based on the checklist below:

```ini
# ==============================================================================
# 1. CORE ENVIRONMENT & SECURITY
# ==============================================================================
ENVIRONMENT=production
DEBUG=False
APP_NAME=Restaurant QR Feedback & Review Assistance System
API_V1_PREFIX=/api/v1

# CRITICAL: Must be a cryptographically random string (min 32 characters)
# Generate with: openssl rand -hex 32
SECRET_KEY=9f3b8c2d1e0a4f5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b

# Domain CORS configuration
ALLOWED_ORIGINS=https://reviews.paradiserestaurant.com,https://admin.paradiserestaurant.com

# ==============================================================================
# 2. ISOLATED DATABASE (PER RESTAURANT)
# ==============================================================================
MONGODB_URI=mongodb://dbuser_paradise:SecurePassword123@127.0.0.1:27017/restaurant_paradise?authSource=restaurant_paradise
MONGODB_DB_NAME=restaurant_paradise
MONGODB_CONNECT_TIMEOUT_MS=5000

# ==============================================================================
# 3. INITIAL RESTAURANT IDENTITY & BRANDING
# ==============================================================================
RESTAURANT_NAME="Paradise Restaurant"
RESTAURANT_SLUG="paradise-restaurant"
RESTAURANT_DESCRIPTION="Authentic Hyderabadi Biryani & Fine Indian Cuisine"
RESTAURANT_LOGO_URL="https://reviews.paradiserestaurant.com/logo.png"
RESTAURANT_PRIMARY_COLOR="#16a34a"
RESTAURANT_SECONDARY_COLOR="#15803d"
RESTAURANT_GOOGLE_REVIEW_URL="https://g.page/r/CbXxYzYourGoogleReviewLink/review"
RESTAURANT_QR_BASE_URL="https://reviews.paradiserestaurant.com/r"
RESTAURANT_TIMEZONE="Asia/Kolkata"

# ==============================================================================
# 4. INITIAL ADMIN CREDENTIALS
# ==============================================================================
INITIAL_ADMIN_EMAIL=admin@paradiserestaurant.com
INITIAL_ADMIN_PASSWORD=ReplaceWithStrongPassword#2026

# ==============================================================================
# 5. COMMERCIAL SUBSCRIPTION & BILLING
# ==============================================================================
SUBSCRIPTION_REQUIRED=True
SUBSCRIPTION_STATUS_DEFAULT=inactive
ALLOW_COMPLIMENTARY_TRIAL=False
SUBSCRIPTION_PLAN_NAME="Standard Monthly"
SUBSCRIPTION_PLAN_ID="plan_standard_monthly"
SUBSCRIPTION_AMOUNT_PAISE=24900
SUBSCRIPTION_BILLING_INTERVAL=monthly
PAYMENT_CURRENCY=INR
SUBSCRIPTION_GRACE_DAYS=0

# ==============================================================================
# 6. RAZORPAY PAYMENT GATEWAY CREDENTIALS
# ==============================================================================
PAYMENT_PROVIDER=razorpay
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxx

# ==============================================================================
# 7. RATE LIMITING & SECURITY THRESHOLDS
# ==============================================================================
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_SCAN_PER_MINUTE=60
RATE_LIMIT_PAYMENT_PER_MINUTE=15
RATE_LIMIT_WEBHOOK_PER_MINUTE=60
MAX_REQUEST_BODY_SIZE=1048576
```

### Frontend Environment Configuration (`frontend/.env.production`):
```ini
NEXT_PUBLIC_API_URL=https://api.paradiserestaurant.com/api/v1
```

---

## 4. Razorpay Payment Gateway & Webhook Setup

### Step 1: Razorpay Dashboard Configuration
1. Log in to [Razorpay Dashboard](https://dashboard.razorpay.com).
2. Generate API Keys under **Settings > API Keys** (Key ID & Key Secret).
3. Navigate to **Settings > Webhooks > Add New Webhook**:
   - **Webhook URL**: `https://api.paradiserestaurant.com/api/v1/webhook/razorpay`
   - **Secret**: Enter a high-entropy secret string and copy it to `RAZORPAY_WEBHOOK_SECRET` in `.env`.
   - **Active Events**:
     - `payment.captured`
     - `payment.failed`
     - `payment.refunded`
     - `refund.processed`

### Step 2: Verification Flow
1. When admin initiates a renewal on `/admin/subscription`, the backend calls Razorpay Orders API (`POST /v1/orders`) for ₹249 (`24900` paise INR).
2. Razorpay Checkout modal handles payment.
3. On completion, frontend posts checkout credentials (`razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`) to `/admin/subscription/verify-payment`.
4. The backend:
   - Verifies HMAC-SHA256 signature using `RAZORPAY_KEY_SECRET`.
   - Performs **server-to-server payment lookup** via Razorpay API (`GET /v1/payments/{payment_id}`).
   - Asserts that `order_id` matches, `amount` is `24900` paise, `currency` is `INR`, and status is `captured` (or automatically captures if `authorized`).
   - Idempotently extends subscription validity by exactly one calendar month.

---

## 5. Database Backup and Recovery Runbook

Each restaurant has its own database (`restaurant_<slug>`). Backups must run on an automated schedule.

### Automated Daily Backup Script (`/usr/local/bin/backup-restaurant-db.sh`)
```bash
#!/usr/bin/env bash
set -euo pipefail

DB_NAME="restaurant_paradise"
BACKUP_DIR="/var/backups/mongodb"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.archive.gz"
RETENTION_DAYS=30

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting backup of database: ${DB_NAME}..."
mongodump --db="${DB_NAME}" --archive="${BACKUP_FILE}" --gzip

echo "[$(date)] Backup completed successfully: ${BACKUP_FILE}"

# Rotate backups older than retention window
find "${BACKUP_DIR}" -name "${DB_NAME}_*.archive.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Old backups purged (older than ${RETENTION_DAYS} days)."
```

Make executable and schedule in cron:
```bash
chmod +x /usr/local/bin/backup-restaurant-db.sh
# Add to root crontab: Run every night at 2:00 AM
echo "0 2 * * * /usr/local/bin/backup-restaurant-db.sh >> /var/log/mongodb_backup.log 2>&1" | crontab -
```

### Disaster Recovery / Database Restoration
To restore a restaurant database from an archive file:
```bash
# 1. Verify archive exists and is non-empty
ls -lh /var/backups/mongodb/restaurant_paradise_20261121_020000.archive.gz

# 2. Restore with --drop to ensure clean state
mongorestore --db="restaurant_paradise" --drop --archive="/var/backups/mongodb/restaurant_paradise_20261121_020000.archive.gz" --gzip

# 3. Verify indexes are intact
mongosh restaurant_paradise --eval "db.getCollectionNames().forEach(c => print(c, JSON.stringify(db[c].getIndexes())));"
```

---

## 6. Multi-Worker Rate Limiting Architectural Note

The built-in `RateLimiterMiddleware` provides an in-memory sliding window rate limiter:
- Validates client IP against IP address standards, safely reading Cloudflare/reverse proxy headers.
- Enforces strict route-specific thresholds:
  - Auth `/auth/login`: 10 req/min
  - Feedback `/public/feedback`: 10 req/min
  - QR Scan `/public/qr/scan`: 60 req/min
  - Payment `/subscription/*`: 15 req/min
  - Webhook `/webhook/*`: 60 req/min
  - General routes: 120 req/min
- Memory-bounded with automated periodic garbage collection to prevent leaks under floods.

### Multi-Worker / Clustered Deployments:
In single-tenant deployments, a standard Uvicorn setup runs 1 or 2 workers per restaurant, which provides sufficient process isolation. If deploying Uvicorn with multiple workers (`--workers 4`) or scaling horizontally across container replicas:
- Requests from the same IP will be distributed across workers; each worker enforces its own sliding window.
- If strict cluster-wide rate limiting synchronization is required, configure a shared Redis instance with a token bucket or sliding-window script as a drop-in replacement for `self.request_history`.

---

## 7. Service Management & Systemd Configuration

### Backend Systemd Service (`/etc/systemd/system/qr-backend-paradise.service`)
```ini
[Unit]
Description=QR Review Scanner FastAPI Backend - Paradise Restaurant
After=network.target mongodb.service

[Service]
Type=simple
User=appuser
WorkingDirectory=/var/www/paradise-restaurant/backend
EnvironmentFile=/var/www/paradise-restaurant/backend/.env
ExecStart=/var/www/paradise-restaurant/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Frontend PM2 Process Configuration (`ecosystem.config.js`)
```javascript
module.exports = {
  apps: [
    {
      name: "qr-frontend-paradise",
      cwd: "/var/www/paradise-restaurant/frontend",
      script: "node_modules/next/dist/bin/next",
      args: "start -p 3000",
      instances: 1,
      autorestart: true,
      env: {
        NODE_ENV: "production",
        PORT: 3000,
      },
    },
  ],
};
```

---

## 8. Nginx Reverse Proxy & TLS Configuration

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name reviews.paradiserestaurant.com api.paradiserestaurant.com;
    return 301 https://$host$request_uri;
}

# Frontend
server {
    listen 443 ssl http2;
    server_name reviews.paradiserestaurant.com;

    ssl_certificate /etc/letsencrypt/live/reviews.paradiserestaurant.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/reviews.paradiserestaurant.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API
server {
    listen 443 ssl http2;
    server_name api.paradiserestaurant.com;

    ssl_certificate /etc/letsencrypt/live/api.paradiserestaurant.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.paradiserestaurant.com/privkey.pem;

    client_max_body_size 1M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 9. Post-Deployment Smoke Verification

Run these verification steps immediately after initial deployment:

1. **Health Check**:
   ```bash
   curl -sS https://api.paradiserestaurant.com/api/v1/health | grep '"status":"healthy"'
   ```
2. **Permanent QR Resolution**:
   ```bash
   curl -I https://reviews.paradiserestaurant.com/r/paradise-restaurant
   ```
3. **Database Index Check**:
   Verify unique indexes exist on `admin_users.email`, `restaurant_settings.slug`, `payment_records.provider_order_id`.
4. **Subscription Expiry Flow**:
   Verify customer interface displays the friendly service paused state if subscription is inactive or lapsed.
5. **Renewal Verification**:
   Log in to admin dashboard (`/admin/login`), navigate to `/admin/subscription`, trigger a test order in Razorpay test mode, verify activation.

