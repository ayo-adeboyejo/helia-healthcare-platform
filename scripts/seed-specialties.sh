#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# seed-specialties.sh
# Run this AFTER verifying your email in Mailhog and logging in
# Usage: ./scripts/seed-specialties.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

BASE_URL="http://localhost:8000"
EMAIL="admin@helia.local"
PASSWORD="Admin1234"

echo "🔐 Logging in as $EMAIL..."
RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

echo "Login response: $RESPONSE"
echo ""

# Extract token using grep and cut — no python needed
TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token. Make sure you verified your email first."
  echo "   Check Mailhog at http://localhost:8025"
  exit 1
fi

echo "✅ Token obtained"
echo ""
echo "🏥 Creating specialties..."

SPECIALTIES=(
  "Cardiology"
  "Dermatology"
  "Neurology"
  "Orthopaedics"
  "Paediatrics"
  "General Practice"
  "Psychiatry"
  "Ophthalmology"
  "Gynaecology"
  "Oncology"
)

for specialty in "${SPECIALTIES[@]}"; do
  RESULT=$(curl -s -X POST "$BASE_URL/specialties" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"name\":\"$specialty\"}")
  echo "  ✅ $specialty — $RESULT"
done

echo ""
echo "✅ Specialties seeded successfully!"
