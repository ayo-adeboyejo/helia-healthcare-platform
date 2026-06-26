# Helia — Containerised Healthcare Appointment Booking Platform

> **Using Docker Compose, FastAPI, Polyglot Persistence and AWS**

A production-grade microservices healthcare platform deployed on AWS EC2, demonstrating end-to-end containerisation, cloud integration, and DevOps best practices.

---

## Architecture

```
Internet
    │
    ▼ port 80
EC2 Security Group (helia-sg)
    │
    ▼
EC2 t3.medium — Ubuntu 22.04 — Elastic IP
    │
    ▼
Docker Engine
    │
    ▼
nginx :80 (only public-facing container)
    │
    ├──► frontend :3000 (React)
    │
    └──► api-gateway :8000
              │
              ├── auth-service        :8001  → PostgreSQL (authdb)   + Redis
              ├── user-service        :8002  → PostgreSQL (userdb)
              ├── appointment-service :8003  → PostgreSQL (appointmentdb) + Redis
              ├── notification-service:8004  → AWS SES
              ├── payment-service     :8005  → PostgreSQL (paymentdb)
              ├── medical-records-svc :8006  → MongoDB + AWS S3
              └── search-service      :8007  → Elasticsearch
```

All services communicate on an internal Docker bridge network (`helia-network`). Only nginx is exposed to the internet on port 80. No service ports are accessible from outside the EC2 instance.

---

## Tech stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Application | Python FastAPI | All microservices |
| Orchestration | Docker Compose | Container management |
| Reverse proxy | nginx | Single entry point, request routing |
| Relational DB | PostgreSQL 15 | Auth, users, appointments, payments |
| Document DB | MongoDB 7 | Medical records, prescriptions |
| Search engine | Elasticsearch 8 | Doctor discovery and filtering |
| Cache / queue | Redis 7 | Token blacklist, slot locking, rate limiting |
| File storage | Amazon S3 | Medical documents, uploads |
| Email | Amazon SES | Appointment notifications |
| Secrets | AWS Secrets Manager | All credentials, encrypted at rest |
| Compute | AWS EC2 t3.medium | Ubuntu 22.04 LTS |
| Identity | AWS IAM role | EC2 instance profile, no access keys |

---

## AWS infrastructure required

Before deploying the application, the following AWS resources must exist:

### 1. EC2 instance

- Instance type: **t3.medium** (2 vCPU, 4GB RAM)
- AMI: **Ubuntu Server 22.04 LTS**
- Storage: **20 GiB gp3**
- User data: creates `helia_adm` user with SSH access on first boot

### 2. Elastic IP

Allocate a static Elastic IP and attach it to the instance. This ensures the IP address never changes when the instance stops and starts.

### 3. Security group (`helia-sg`)

| Type | Protocol | Port | Source | Purpose |
|------|----------|------|--------|---------|
| SSH | TCP | 22 | Your IP only | Administration |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web traffic (future) |

### 4. IAM role (`helia-s3-secretManager-access`)

Create an IAM role with the following managed policies and attach it to the EC2 instance:

- `AmazonS3FullAccess`
- `SecretsManagerReadWrite`

The application authenticates with AWS entirely through this role — no access keys are stored anywhere.

### 5. AWS Secrets Manager

Create a secret named **`helia/production`** in region **`ap-south-1`** (Mumbai).

Secret type: **Other type of secret → Plaintext**

```json
{
  "postgres_user":                   "helia",
  "postgres_password":               "GENERATE_STRONG_PASSWORD",
  "postgres_auth_db":                "authdb",
  "postgres_user_db":                "userdb",
  "postgres_appointment_db":         "appointmentdb",
  "postgres_payment_db":             "paymentdb",
  "mongo_user":                      "helia",
  "mongo_password":                  "GENERATE_STRONG_PASSWORD",
  "mongo_db":                        "helia_records",
  "redis_password":                  "GENERATE_STRONG_PASSWORD",
  "elastic_username":                "elastic",
  "elastic_password":                "GENERATE_STRONG_PASSWORD",
  "jwt_secret":                      "GENERATE_64_CHARACTER_RANDOM_STRING",
  "jwt_algorithm":                   "HS256",
  "jwt_access_token_expire_minutes": "60",
  "jwt_refresh_token_expire_days":   "7"
}
```

Generate strong passwords on the EC2 instance:

```bash
# Generate a strong password (run once per password)
openssl rand -base64 32

# Generate the JWT secret (must be long)
openssl rand -base64 64
```

### 6. S3 bucket (`helia-files`)

Create an S3 bucket in `ap-south-1` with:

- **Block all public access:** enabled
- **Versioning:** enabled
- **Server-side encryption:** SSE-S3
- **Bucket policy:** deny unencrypted connections, allow only `helia-s3-secretManager-access`

Folder structure inside the bucket:

```
helia-files/
├── prescriptions/
├── lab-results/
├── consultation-notes/
└── profile-images/
```

---

## Deploying to EC2

### Step 1 — Install Docker on the EC2 instance

SSH in as `helia_adm`:

```bash
ssh -i your-key.pem helia_adm@<elastic-ip>
```

Install Docker:

```bash
# Update packages
sudo apt-get update -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add helia_adm to docker group
sudo usermod -aG docker helia_adm

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Log out and back in for group change to take effect
exit
ssh -i your-key.pem helia_adm@<elastic-ip>

# Verify
docker --version
```

Install Docker Compose:

```bash
sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

Set Elasticsearch memory requirement:

```bash
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Step 2 — Install AWS CLI

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
sudo apt-get install -y unzip
unzip /tmp/awscliv2.zip -d /tmp
sudo /tmp/aws/install
rm -rf /tmp/awscliv2.zip /tmp/aws

# Verify IAM role is attached
aws sts get-caller-identity
```

You should see your account ID and the `helia-s3-secretManager-access` ARN. If this fails, the IAM role is not attached — go to EC2 → Actions → Security → Modify IAM role.

### Step 3 — Clone the repository

```bash
cd /opt
sudo mkdir helia
sudo chown helia_adm:helia_adm helia
git clone https://github.com/ayo-adeboyejo/helia-healthcare-platform.git helia
cd helia
```

### Step 4 — Generate the .env file from AWS Secrets Manager

Docker Compose needs database passwords to initialise PostgreSQL, MongoDB, Redis and Elasticsearch. These passwords live in AWS Secrets Manager. The following command fetches them and appends them to the `.env` file:

```bash
# First copy the non-sensitive config template
cp .env.example .env

# Fetch secrets from AWS Secrets Manager and append to .env
aws secretsmanager get-secret-value \
    --secret-id "helia/production" \
    --region "ap-south-1" \
    --query "SecretString" \
    --output text | python3 -c "
import sys, json
s = json.load(sys.stdin)
print(f'POSTGRES_PASSWORD={s[\"postgres_password\"]}')
print(f'MONGO_PASSWORD={s[\"mongo_password\"]}')
print(f'REDIS_PASSWORD={s[\"redis_password\"]}')
print(f'ELASTIC_PASSWORD={s[\"elastic_password\"]}')
" >> .env
```

Verify the `.env` file has been populated:

```bash
cat .env
```

You should see all values filled in — no empty passwords.

> The `.env` file is listed in `.gitignore` and is never committed to the repository. It exists only on the EC2 instance.

### Step 5 — Build and start all containers

```bash
docker compose up --build -d
```

Docker Compose reads `docker-compose.yml` and the `.env` file, builds all service images, and starts every container in the correct order — infrastructure first, then application services, then nginx. The `--build` flag ensures fresh images are built from the current code. The `-d` flag runs everything in the background.

### Step 6 — Verify

```bash
# Check all containers are running and healthy
docker compose ps

# Stream logs
docker compose logs -f

# Test the application
curl http://<elastic-ip>/api/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "api-gateway",
  "version": "1.0.0"
}
```

Open `http://<elastic-ip>` in your browser to access the Helia web application.

---

## How secrets management works

```
AWS Secrets Manager (helia/production)
      │
      │  aws secretsmanager get-secret-value
      │  (authenticated via EC2 IAM role — no access keys)
      ▼
Passwords written to .env on EC2 instance
      │
      ▼
docker compose up --build -d
      │
      ├──► postgres container
      │      reads POSTGRES_PASSWORD from .env
      │      creates database user on first boot
      │
      ├──► mongodb container
      │      reads MONGO_PASSWORD from .env
      │      creates root user on first boot
      │
      └──► application services start
             each service calls Secrets Manager independently
             loads jwt_secret, passwords etc. into memory at startup
             credentials never written to application logs or disk
```

The `.env` file exists only on the EC2 instance and is never committed to git. It must be regenerated from Secrets Manager whenever passwords rotate or the instance is reprovisioned.

---

## Updating the application

On subsequent deployments:

```bash
cd /opt/helia

# Pull latest code
git pull origin main

# Regenerate .env from Secrets Manager (passwords may have rotated)
aws secretsmanager get-secret-value \
    --secret-id "helia/production" \
    --region "ap-south-1" \
    --query "SecretString" \
    --output text | python3 -c "
import sys, json
s = json.load(sys.stdin)
print(f'POSTGRES_PASSWORD={s[\"postgres_password\"]}')
print(f'MONGO_PASSWORD={s[\"mongo_password\"]}')
print(f'REDIS_PASSWORD={s[\"redis_password\"]}')
print(f'ELASTIC_PASSWORD={s[\"elastic_password\"]}')
" > /tmp/secrets.env

# Merge with non-sensitive config
cp .env.example .env
cat /tmp/secrets.env >> .env
rm /tmp/secrets.env

# Rebuild and restart containers
docker compose down
docker compose up --build -d
```

---

## Common operations

```bash
# View all container statuses
docker compose ps

# Stream all logs
docker compose logs -f

# Stream logs for a specific service
docker compose logs -f auth-service

# Stop the application
docker compose down

# Restart the application (no rebuild)
docker compose up -d

# Full restart with rebuild
docker compose down && docker compose up --build -d

# Remove all containers and data (irreversible)
docker compose down -v --remove-orphans
```

---

## Services and ports (internal only)

All ports below are internal to the Docker network. They are not accessible from the internet.

| Service | Internal port | Database |
|---------|--------------|----------|
| api-gateway | 8000 | Redis |
| auth-service | 8001 | PostgreSQL (authdb) + Redis |
| user-service | 8002 | PostgreSQL (userdb) |
| appointment-service | 8003 | PostgreSQL (appointmentdb) + Redis |
| notification-service | 8004 | AWS SES |
| payment-service | 8005 | PostgreSQL (paymentdb) |
| medical-records-service | 8006 | MongoDB + AWS S3 |
| search-service | 8007 | Elasticsearch |

---

## API reference

All requests go through nginx on port 80 and are proxied to the api-gateway at `/api/*`.

Base URL: `http://<elastic-ip>/api`

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | — | Register patient or doctor |
| POST | /auth/login | — | Login, returns JWT tokens |
| POST | /auth/refresh | — | Refresh access token |
| POST | /auth/logout | ✅ | Logout, blacklists token |
| POST | /auth/reset-password | — | Reset password with token |
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
| POST | /payments | ✅ | Create payment record |
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
| GET | /medical-records/documents/:id/download | ✅ | Get pre-signed S3 download URL |

### Search
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /search/doctors | — | Search doctors (full-text + filters) |
| GET | /search/doctors/autocomplete | — | Autocomplete doctor names |
| POST | /search/doctors/index | — | Index a doctor in Elasticsearch |

---

## DevOps concepts demonstrated

| Concept | Implementation |
|---------|----------------|
| Containerisation | Docker with multi-stage builds |
| Multi-service orchestration | Docker Compose with health checks and dependency ordering |
| Microservices architecture | 8 independent FastAPI services, each owning its own database |
| Polyglot persistence | PostgreSQL, MongoDB, Elasticsearch, Redis — each chosen for the right reason |
| Cloud deployment | AWS EC2 t3.medium, Ubuntu 22.04 |
| Static IP management | AWS Elastic IP |
| Secrets management | AWS Secrets Manager — credentials never on disk or in code |
| IAM role authentication | EC2 instance profile — no access keys anywhere |
| Object storage | AWS S3 with pre-signed URLs, SSE encryption, bucket policy |
| Managed email | AWS SES for appointment notifications |
| Network isolation | Internal Docker bridge network — only nginx on port 80 exposed |
| Reverse proxy | nginx routing frontend and proxying /api/* to gateway |
| Health checks | Per-service Docker health checks with proper startup ordering |
| Structured logging | JSON to stdout on every service — CloudWatch ready |
| Rate limiting | Redis-backed per-IP rate limiting in API gateway |
| Atomic slot locking | Redis prevents double appointment bookings |
| Token security | JWT blacklisting in Redis on logout |
| Secrets bootstrap | AWS CLI fetches Secrets Manager values into .env before containers start |
