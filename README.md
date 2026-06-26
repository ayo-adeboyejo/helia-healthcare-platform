# Helia — Containerised Healthcare Appointment Booking Platform

> **Using Docker Compose, FastAPI & Polyglot Persistence**

A production-pattern microservices healthcare platform demonstrating end-to-end containerisation, cloud deployment, and DevOps best practices. Built as a portfolio project — runs locally without any cloud accounts, and deploys to AWS with full managed service integration.

---

## Architecture

```
                          ┌─────────────────────────────────────┐
                          │  Docker network: helia-network       │
                          │                                      │
Browser → nginx :80 ─────►│  frontend (React + nginx)           │
                          │         │ /api/*                     │
                          │         ▼                            │
                          │  api-gateway :8000                   │
                          │    │    │    │    │    │    │        │
                          │    ▼    ▼    ▼    ▼    ▼    ▼       │
                          │  auth  user appt  pay  med  srch    │
                          │  8001  8002 8003  8005 8006 8007    │
                          │    │         │         │    │        │
                          │    ▼         ▼         ▼    ▼       │
                          │  PostgreSQL  Redis  MongoDB  ES      │
                          └─────────────────────────────────────┘
```

### Services

| Service | Port | Technology | Database |
|---------|------|------------|----------|
| auth-service | 8001 | FastAPI | PostgreSQL + Redis |
| user-service | 8002 | FastAPI | PostgreSQL |
| appointment-service | 8003 | FastAPI | PostgreSQL + Redis |
| notification-service | 8004 | FastAPI | — (SES / Mailhog) |
| payment-service | 8005 | FastAPI | PostgreSQL |
| medical-records-service | 8006 | FastAPI | MongoDB + S3/MinIO |
| search-service | 8007 | FastAPI | Elasticsearch |
| api-gateway | 8000 | FastAPI | Redis |
| frontend | — | React + nginx | — |

### Data stores

| Store | Purpose |
|-------|---------|
| PostgreSQL | Auth, users, appointments, payments (relational, ACID) |
| MongoDB | Medical records, prescriptions (flexible schema) |
| Elasticsearch | Doctor search and discovery (full-text, filters) |
| Redis | Token blacklist, slot locking, rate limiting, caching |
| S3 / MinIO | Document and file storage |

---

## Running locally (no AWS account needed)

### Prerequisites

- Docker Desktop installed and running
- Git

### Quick start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/helia.git
cd helia

# Copy environment file (safe defaults included)
make setup
# or: cp .env.example .env

# Start everything
make dev
# or: docker compose up --build
```

That's it. Docker pulls all images and starts every service automatically.

### What runs in development

```
MinIO     → replaces AWS S3 for file storage
Mailhog   → catches all emails (nothing sent to real inboxes)
.env file → replaces AWS Secrets Manager for credentials
```

No AWS account, no cloud credentials, no configuration needed beyond the `.env` file.

### Access points (development)

| URL | What |
|-----|------|
| http://localhost | Helia web application |
| http://localhost:8025 | Mailhog — view all caught emails |
| http://localhost:9001 | MinIO console — view uploaded files |
| http://localhost:8000/docs | API Gateway — Swagger UI |
| http://localhost:8001/docs | Auth Service — Swagger UI |
| http://localhost:8002/docs | User Service — Swagger UI |
| http://localhost:8003/docs | Appointment Service — Swagger UI |
| http://localhost:8005/docs | Payment Service — Swagger UI |
| http://localhost:8006/docs | Medical Records Service — Swagger UI |
| http://localhost:8007/docs | Search Service — Swagger UI |

---

## Deploying to AWS

### Prerequisites

- AWS account
- EC2 instance — t3.medium, Ubuntu 22.04 LTS
- Elastic IP attached to the instance
- IAM role with `AmazonS3FullAccess` and `SecretsManagerReadWrite` attached to EC2
- AWS Secrets Manager secret named `helia/production`
- S3 bucket named `helia-files`
- Docker and Docker Compose installed on EC2

### Step 1 — Create the secret in AWS Secrets Manager

In the AWS Console → Secrets Manager → Store a new secret → Other type → Plaintext:

```json
{
  "postgres_user":                   "helia",
  "postgres_password":               "STRONG_PASSWORD",
  "postgres_auth_db":                "authdb",
  "postgres_user_db":                "userdb",
  "postgres_appointment_db":         "appointmentdb",
  "postgres_payment_db":             "paymentdb",
  "mongo_user":                      "helia",
  "mongo_password":                  "STRONG_PASSWORD",
  "mongo_db":                        "helia_records",
  "redis_password":                  "STRONG_PASSWORD",
  "elastic_username":                "elastic",
  "elastic_password":                "STRONG_PASSWORD",
  "jwt_secret":                      "VERY_LONG_RANDOM_STRING_64_CHARS_MINIMUM",
  "jwt_algorithm":                   "HS256",
  "jwt_access_token_expire_minutes": "60",
  "jwt_refresh_token_expire_days":   "7"
}
```

Name the secret: `helia/production`

### Step 2 — Prepare the .env file on EC2

SSH into your EC2 instance and create the `.env` file:

```bash
ssh -i your-key.pem helia_adm@<elastic-ip>
cd /opt/helia

# Clone the repository
git clone https://github.com/YOUR_USERNAME/helia.git .

# Create production .env
cp .env.example .env
nano .env
```

Set these values in `.env`:

```bash
ENVIRONMENT=production
AWS_REGION=ap-south-1
S3_BUCKET=helia-files
ALLOWED_ORIGINS=http://<your-elastic-ip>

# These come from AWS Secrets Manager but are also
# needed by docker-compose.yml to initialise databases
POSTGRES_USER=helia
POSTGRES_PASSWORD=<same as in Secrets Manager>
POSTGRES_AUTH_DB=authdb
POSTGRES_USER_DB=userdb
POSTGRES_APPOINTMENT_DB=appointmentdb
POSTGRES_PAYMENT_DB=paymentdb
MONGO_USER=helia
MONGO_PASSWORD=<same as in Secrets Manager>
MONGO_DB=helia_records
REDIS_PASSWORD=<same as in Secrets Manager>
ELASTIC_PASSWORD=<same as in Secrets Manager>
```

### Step 3 — Deploy

```bash
# Production mode — uses only docker-compose.yml
# No MinIO, no Mailhog, no exposed ports except nginx on 80
make prod
# or: docker compose -f docker-compose.yml up --build -d
```

### Step 4 — Verify

```bash
# Check all containers are running
make ps

# Stream logs
make prod-logs

# Test the API
curl http://<elastic-ip>/api/health
```

---

## Environment switching — how it works

The codebase detects the environment at startup and behaves accordingly:

```
ENVIRONMENT=development
  └── Reads credentials from .env file
  └── S3 requests go to MinIO (http://minio:9000)
  └── Emails go to Mailhog (SMTP on port 1025)
  └── All service ports exposed on host
  └── Debug logging enabled

ENVIRONMENT=production
  └── Reads credentials from AWS Secrets Manager
  └── S3 requests go to real AWS S3 (via IAM role, no keys needed)
  └── Emails sent via AWS SES
  └── No ports exposed except nginx on 80
  └── Info logging only
```

Same codebase, same Docker images, same `docker compose up` command. Only the environment variable changes.

---

## Project structure

```
helia/
├── docker-compose.yml           # Production — AWS services, locked down ports
├── docker-compose.override.yml  # Development additions — MinIO, Mailhog, exposed ports
├── Makefile                     # Simple commands: make dev, make prod, make down
├── .env.example                 # Template with safe local defaults — commit this
├── .env                         # Your actual values — never commit this
├── nginx/
│   └── nginx.conf               # Reverse proxy config
├── scripts/
│   ├── init-postgres.sh         # Creates all 4 databases on first boot
│   └── seed.sh                  # Seeds test data (optional)
├── frontend/                    # React app served by nginx
└── services/
    ├── auth-service/            # FastAPI — registration, login, JWT
    ├── user-service/            # FastAPI — patient and doctor profiles
    ├── appointment-service/     # FastAPI — booking, slots, waitlist
    ├── notification-service/    # FastAPI — email via SES or Mailhog
    ├── payment-service/         # FastAPI — fees, invoices, earnings
    ├── medical-records-service/ # FastAPI — records, documents, S3
    ├── search-service/          # FastAPI — Elasticsearch doctor search
    └── api-gateway/             # FastAPI — routing, auth, rate limiting
```

---

## Key DevOps concepts demonstrated

| Concept | Implementation |
|---------|----------------|
| Containerisation | Docker multi-stage builds for all services |
| Multi-service orchestration | Docker Compose with health checks and dependency ordering |
| Polyglot persistence | PostgreSQL, MongoDB, Elasticsearch, Redis, S3 — each chosen for the right reason |
| Environment parity | Same code runs locally and in production via environment switching |
| Secrets management | AWS Secrets Manager in production, .env in development |
| Cloud storage | AWS S3 (production) / MinIO (development) via same boto3 API |
| Managed email | AWS SES (production) / Mailhog (development) |
| Reverse proxy | nginx routing frontend and proxying /api/* to gateway |
| Network isolation | All services on internal Docker network, only nginx exposed |
| Health checks | Per-service Docker health checks with proper startup ordering |
| Structured logging | JSON to stdout on every service — CloudWatch-ready |
| Rate limiting | Redis-backed per-IP rate limiting in API gateway |
| Atomic operations | Redis slot locking prevents double appointment bookings |
| IAM role auth | EC2 instance role — no access keys in code or on disk |

---

## API reference

All requests go through the gateway at `http://localhost:8000` (dev) or `http://<ip>/api` (prod via nginx).

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | — | Register new user |
| POST | /auth/login | — | Login, returns JWT |
| POST | /auth/refresh | — | Refresh access token |
| POST | /auth/logout | ✅ | Logout, blacklists token |
| POST | /auth/reset-password | — | Reset password with token |
| POST | /auth/verify-token | — | Internal token verification |
| GET | /auth/me | ✅ | Get current user |

### Users
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /patients | ✅ | Create patient profile |
| GET | /patients/:user_id | ✅ | Get patient profile |
| PUT | /patients/:user_id | ✅ | Update patient profile |
| POST | /doctors | ✅ | Create doctor profile |
| GET | /doctors | — | List doctors with filters |
| GET | /doctors/:id | — | Get doctor profile |
| GET | /doctors/:id/availability | — | Get availability slots |
| POST | /doctors/:id/reviews | ✅ | Add review |
| GET | /specialties | — | List specialties |

### Appointments
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /appointments/slots | — | Available slots for doctor + date |
| POST | /appointments | ✅ | Book appointment |
| GET | /appointments | ✅ | My appointments |
| GET | /appointments/:id | ✅ | Single appointment |
| PUT | /appointments/:id | ✅ | Update appointment |
| DELETE | /appointments/:id | ✅ | Cancel appointment |
| POST | /appointments/waitlist | ✅ | Join waitlist |

### Payments
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /payments | ✅ | Create payment |
| PUT | /payments/:id/confirm | ✅ | Confirm payment |
| GET | /payments | ✅ | My payments |
| GET | /payments/invoices | ✅ | My invoices |
| GET | /payments/earnings | ✅ Doctor | Doctor earnings |
| POST | /payments/refund | ✅ | Request refund |

### Medical Records
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /medical-records/history/:patient_id | ✅ | Patient medical history |
| PUT | /medical-records/history/:patient_id | ✅ | Update medical history |
| POST | /medical-records/prescriptions | ✅ Doctor | Create prescription |
| GET | /medical-records/prescriptions/:patient_id | ✅ | Get prescriptions |
| POST | /medical-records/notes | ✅ Doctor | Create consultation note |
| GET | /medical-records/notes/:patient_id | ✅ | Get consultation notes |
| POST | /medical-records/documents/upload | ✅ | Upload document to S3 |
| GET | /medical-records/documents/:document_id/download | ✅ | Get pre-signed download URL |

### Search
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /search/doctors | — | Search doctors |
| GET | /search/doctors/autocomplete | — | Autocomplete doctor names |
| POST | /search/doctors/index | — | Index a doctor |

---

## Stopping and cleaning up

```bash
# Stop all containers (data preserved)
make down

# Stop and delete all data (WARNING — irreversible)
make clean
```
