# Restaurant QR Feedback & Google Review Assistance System

> **Phase 1 Architecture, Project Foundation & Technical Setup**
> A single-tenant, commercial customer feedback and review assistance system built for independent per-restaurant deployment.

---

## 1. Business & Architectural Model

This system is **NOT** a shared multi-tenant SaaS application. 

Every restaurant customer receives an **independent, self-contained deployment**:
- Its own application instance
- Its own dedicated database
- Its own branding, color scheme, and typography
- Its own permanent dynamic QR code
- Its own Google Business Review link
- Its own minimal administration dashboard
- Its own subscription record

**Strict Boundary Rule**: There is zero shared database state or cross-restaurant analytics. When deploying for Restaurant A (e.g. *Paradise Restaurant*) and Restaurant B (e.g. *Food Palace*), each runs independently on its own container or domain with isolated environment configurations.

---

## 2. Product Interfaces

### A. Customer Feedback Interface (`/r/:slug`)
1. **Dynamic QR Entry**: Customer scans the restaurant's physical QR code on tables or bills.
2. **Branded Touchpoint**: Displays restaurant logo, primary brand color, and welcome messaging.
3. **Multi-Factor Experience Rating**: Food & Drinks, Staff & Service, and Ambience rated from 1 to 5 stars.
4. **Contextual Tag Selection**: Quick positive or improvement tags.
5. **Google Review Assistance**: Non-coercive invitation to open the official Google Review page.
6. **Policy Compliance**: 
   - Never auto-submits Google reviews.
   - Never fabricates customer ratings.
   - Never gates or selectively hides the Google Review link from unsatisfied customers.
   - The customer always remains in full control.

### B. Minimal Restaurant Dashboard (`/admin/dashboard`)
Designed for non-technical restaurant owners and staff. Strictly restricted to **4 essential metrics**:
1. **Total QR Scans**: Volume of physical table/card scans.
2. **Total Feedback Submissions**: Direct customer reviews submitted.
3. **Google Review Link Clicks**: Customers who proceeded to the official Google review page.
4. **Monthly Activity Breakdown**: Chronological table tracking scans, feedback, and clicks over time.

---

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, Motor (Async MongoDB Driver), Segno (Pure-Python dynamic QR generation), PyJWT, Bcrypt.
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide React, clsx, tailwind-merge.
- **Database**: MongoDB (independent database per restaurant installation).
- **Testing**: PyTest, PyTest-Asyncio, HTTPX, MongoMock-Motor.

---

## 4. Database Collections

The database foundation defines 6 dedicated collections in each restaurant's isolated database:

| Collection Name | Purpose | Primary Indexes | Anonymous / PII-Free |
| :--- | :--- | :--- | :--- |
| `restaurant_settings` | Venue branding, logo, colors, Google review URL | `slug` (Unique), `is_active` | Venue Configuration |
| `admin_users` | Administrator accounts for the venue | `email` (Unique) | Password hashed with Bcrypt |
| `qr_scans` | Recorded scan events | `created_at` (Desc), `session_id` | Salted SHA-256 IP hash (No raw IP) |
| `feedback_submissions` | Customer food, service & ambience ratings | `created_at` (Desc), `session_id`, `overall_experience` | Anonymous session ID |
| `review_link_clicks` | Clicks towards official Google review page | `created_at` (Desc), `session_id` | Distinct from feedback & reviews |
| `subscription_records` | Installation license and validity status | `status`, `expires_at` | Billing readiness |

---

## 5. Dynamic QR Architecture

- **Permanent URL Structure**: The QR encodes a stable destination URL (e.g. `https://domain.com/r/paradise-restaurant`).
- **No Reprinting Required**: The printed physical QR code never changes, even if restaurant branding, Google URLs, or subscription plans are modified.
- **Subscription Grace Handling**: If a subscription lapses, the QR routes to a graceful `/service-expired` page until renewed, preserving all printed collateral.

---

## 6. Security Foundation

- **Cryptographic Hashing**: Bcrypt with adaptive salt rounds (12) for admin passwords.
- **JWT Authorization**: Cryptographically signed access tokens for admin endpoints with strict expiration.
- **OWASP Defensive Headers**: Injected via custom middleware (`X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Strict-Transport-Security`, `Permissions-Policy`).
- **Denial of Service Mitigations**:
  - Request body size limiter (1 MB max payload).
  - Sliding-window in-memory rate limiting per client IP (higher allowance for regular routes, throttled for scan endpoints).
- **Privacy & Anonymity**: Client IPs for scans are hashed using salted SHA-256; no raw customer IP or unnecessary PII is stored.
- **Sanitized Logging**: Log formatter actively redacts passwords, tokens, secrets, and database connection strings before output.

---

## 7. Project Structure

```
qr-review-scanner/
├── backend/
│   ├── app/
│   │   ├── api/                 # REST API endpoints (v1)
│   │   │   ├── deps.py          # Database & auth dependency injection
│   │   │   └── v1/
│   │   │       ├── public.py    # Customer feedback, scans, QR streaming
│   │   │       ├── auth.py      # Admin login & session me
│   │   │       ├── admin.py     # Restaurant settings & QR export
│   │   │       ├── analytics.py # 4 dashboard categories
│   │   │       └── router.py    # Route aggregator
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings & environment validation
│   │   │   ├── security.py      # Bcrypt & JWT implementation
│   │   │   └── logging.py       # Secret-scrubbing logger
│   │   ├── db/
│   │   │   ├── collections.py   # Collection name constants
│   │   │   └── mongodb.py       # Motor async lifecycle & index builder
│   │   ├── middleware/
│   │   │   ├── rate_limiter.py  # Rate limiter middleware
│   │   │   ├── request_size.py  # Request size guard middleware
│   │   │   └── security_headers.py # OWASP headers middleware
│   │   ├── models/              # MongoDB document definitions
│   │   ├── schemas/             # Pydantic request/response DTOs
│   │   ├── services/            # Isolated business logic layer
│   │   └── main.py              # FastAPI app & lifespan manager
│   ├── tests/                   # 32 Automated unit & integration tests
│   ├── .env.example             # Backend configuration template
│   ├── requirements.txt         # Production dependencies
│   ├── requirements-dev.txt     # Test dependencies
│   └── run.py                   # Development server runner
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── r/[slug]/        # Customer Feedback & Review Page
│   │   │   ├── admin/dashboard/ # Minimal 4-category Dashboard
│   │   │   ├── admin/qr/        # Dynamic QR viewer & PNG/SVG downloader
│   │   │   ├── admin/settings/  # Restaurant branding & review link editor
│   │   │   ├── admin/login/     # Admin portal authentication
│   │   │   ├── service-expired/ # Expired subscription screen
│   │   │   └── page.tsx         # Home / Landing page
│   │   ├── components/
│   │   │   ├── ui/              # Button, Card, Input, Textarea, Badge
│   │   │   ├── common/          # Navbar, Spinner, ErrorAlert, EmptyState
│   │   │   ├── customer/        # StarRating, ExperienceSelector, FeedbackForm, GoogleReviewPrompt
│   │   │   └── admin/           # MetricCard, MonthlyActivityTable
│   │   ├── lib/                 # API client, auth helpers, utility classes
│   │   └── types/               # TypeScript interfaces
│   ├── .env.example             # Frontend configuration template
│   └── package.json
├── docker-compose.yml           # Turnkey deployment with isolated MongoDB
└── README.md
```

---

## 8. Installation & Local Development

### Prerequisites
- Node.js 18+ (Tested on v24)
- Python 3.11+ (Tested on 3.12)
- MongoDB instance (or Docker)

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your secret keys and restaurant details

# Run automated test suite
pytest -c pytest.ini tests -v

# Start development server
python run.py
# Server runs on http://localhost:8000 (API docs at http://localhost:8000/docs)
```

### 2. Frontend Setup
```bash
cd frontend

# Install npm packages
npm install

# Configure environment
cp .env.example .env.local

# Run production build validation
npm run build

# Start Next.js development server
npm run dev
# Interface runs on http://localhost:3000
```

---

## 9. Automated Test Suite Results

The backend includes a comprehensive 32-test suite executed using `mongomock-motor`:

```
backend/tests/test_admin_api.py::test_get_admin_restaurant_settings_unauthorized PASSED
backend/tests/test_admin_api.py::test_get_admin_restaurant_settings_authorized PASSED
backend/tests/test_admin_api.py::test_update_admin_restaurant_settings PASSED
backend/tests/test_admin_api.py::test_get_admin_qr_details PASSED
backend/tests/test_admin_api.py::test_get_admin_subscription_status PASSED
backend/tests/test_analytics_api.py::test_analytics_overview_unauthorized PASSED
backend/tests/test_analytics_api.py::test_analytics_overview_authorized_and_accurate_counts PASSED
backend/tests/test_auth.py::test_password_hashing PASSED
backend/tests/test_auth.py::test_jwt_token_lifecycle PASSED
backend/tests/test_auth.py::test_jwt_invalid_token PASSED
backend/tests/test_auth.py::test_admin_login_success PASSED
backend/tests/test_auth.py::test_admin_login_failure PASSED
backend/tests/test_auth.py::test_protected_me_endpoint_authorized PASSED
backend/tests/test_auth.py::test_protected_me_endpoint_unauthorized PASSED
backend/tests/test_config.py::test_settings_defaults PASSED
backend/tests/test_config.py::test_cors_origins_parsing PASSED
backend/tests/test_config.py::test_secret_key_presence PASSED
backend/tests/test_db.py::test_collections_exist_and_seed_data PASSED
backend/tests/test_db.py::test_qr_scan_collection_insert PASSED
backend/tests/test_db.py::test_feedback_collection_insert PASSED
backend/tests/test_db.py::test_review_click_collection_insert PASSED
backend/tests/test_db.py::test_subscription_collection_insert PASSED
backend/tests/test_public_api.py::test_health_check PASSED
backend/tests/test_public_api.py::test_get_public_restaurant PASSED
backend/tests/test_public_api.py::test_qr_scan_flow PASSED
backend/tests/test_public_api.py::test_submit_valid_feedback PASSED
backend/tests/test_public_api.py::test_submit_feedback_invalid_ratings PASSED
backend/tests/test_public_api.py::test_record_review_link_click PASSED
backend/tests/test_public_api.py::test_get_qr_image_stream PASSED
backend/tests/test_qr_service.py::test_qr_asset_generation PASSED
backend/tests/test_qr_service.py::test_ip_hashing_anonymity PASSED
backend/tests/test_qr_service.py::test_subscription_status_check PASSED

============================= 32 passed in 18.83s =============================
```

---

## 10. Turnkey Deployment via Docker Compose

To deploy an isolated installation for any customer restaurant:

```bash
# 1. Clone repository into the restaurant's target server directory
git clone <repo-url> /opt/restaurant-paradise
cd /opt/restaurant-paradise

# 2. Configure restaurant-specific environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 3. Spin up isolated MongoDB, Backend, and Frontend containers
docker-compose up -d --build
```

---

## 11. Phase 5: Subscription Management & Payment Architecture

### A. Business Model & Pricing
- **Pricing**: ₹249 per calendar month per restaurant installation (strictly configurable in server environment).
- **Storage**: Monetary values are stored exclusively in **integer paise** (`24900` paise = ₹249).
- **No Floating Point Calculations**: Monetary arithmetic avoids IEEE 754 precision issues.
- **Single-Tenant Independence**: Subscription records and payment transactions are stored in each restaurant's dedicated database. There is zero central subscription sharing.

### B. Permanent QR Code Rule (Non-Negotiable)
- **Zero Reprinting**: The physical QR code points to the permanent URL:
  `https://<domain>/r/<restaurant-slug>`
- **Active State**: Customer scans QR -> Feedback form opens -> Customer submits feedback -> Optional Google review link.
- **Expired State**: Customer scans SAME QR -> SAME URL opens -> Customer sees polite `/service-expired` page -> Feedback submission is blocked server-side -> QR URL never changes.
- **Renewed State**: Admin renews for ₹249 -> Signature verified server-side -> Subscription activates -> Existing printed QR codes resume working immediately without reprinting.

### C. Subscription State Machine
- `inactive`: Initial state before first payment.
- `pending`: Payment order created, awaiting checkout completion.
- `active`: Verified paid subscription within valid calendar month.
- `expired`: Current time reached or exceeded `expires_at` + grace period. Customer APIs blocked.
- `payment_failed`: Payment attempt failed or rejected by provider.
- `cancelled`: Subscription administratively cancelled.

### D. Deterministic Calendar Month Arithmetic
- Billing intervals span exact calendar months, not fixed 30-day blocks.
- End-of-month boundaries are handled deterministically:
  - Jan 31 -> Feb 28 (or Feb 29 on leap year)
  - March 31 -> April 30
  - May 31 -> June 30
- **Early Renewal**: Renewing before expiry extends from the **existing `expires_at`** date, never shortening already-paid days.
- **Post-Expiry Renewal**: Starts from the payment verification timestamp and runs for 1 calendar month.

### E. Payment Gateway Architecture (Razorpay)
1. **Server-Side Order Creation** (`POST /api/v1/admin/subscription/create-order`):
   - Server strictly enforces ₹249 (24900 paise). The frontend cannot alter the amount.
   - Idempotency key prevents duplicate orders.
2. **Cryptographic Verification** (`POST /api/v1/admin/subscription/verify-payment`):
   - Validates `HMAC-SHA256(order_id + "|" + payment_id, RAZORPAY_KEY_SECRET) == signature`.
   - Idempotent: Repeated verification requests return existing state and never double-extend.
3. **Webhook Verification** (`POST /api/v1/webhook/razorpay`):
   - Validates `HMAC-SHA256(raw_body, RAZORPAY_WEBHOOK_SECRET) == X-Razorpay-Signature`.
   - Event tracking deduplicates webhooks.
   - Handles `payment.captured`, `order.paid`, and `payment.failed`.

### F. Server-Side Expiry Enforcement
Direct API calls cannot bypass subscription checks:
- `POST /api/v1/public/feedback`: Returns HTTP 403 `SUBSCRIPTION_EXPIRED` if expired.
- `POST /api/v1/public/review-click`: Returns HTTP 403 `SUBSCRIPTION_EXPIRED` if expired.
- `GET /api/v1/public/prompts`: Returns HTTP 403 `SUBSCRIPTION_EXPIRED` if expired.
- `POST /api/v1/public/qr/scan`: Returns `subscription_status: "expired"`.
- `GET /api/v1/public/restaurant`: Returns `subscription_status: "expired"`.
- `/admin/*`: Admins retain full login access to renew and review payment history.

### G. Environment Variables
```env
# Subscription & Billing
SUBSCRIPTION_REQUIRED=True
SUBSCRIPTION_PLAN_NAME=Standard Monthly
SUBSCRIPTION_PLAN_ID=plan_standard_monthly
SUBSCRIPTION_AMOUNT_PAISE=24900
SUBSCRIPTION_BILLING_INTERVAL=monthly
PAYMENT_CURRENCY=INR
SUBSCRIPTION_GRACE_DAYS=0

# Razorpay Payment Gateway
PAYMENT_PROVIDER=razorpay
RAZORPAY_KEY_ID=rzp_live_xxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxxxxxxxxxxxxx
```
*Note: In local development and testing, mock mode is automatically engaged when Razorpay keys are omitted.*

