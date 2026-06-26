#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# seed.sh — Seeds Helia with initial data
# Run after: docker compose up --build
# ─────────────────────────────────────────────────────────────────────────────
set -e

BASE_URL="http://localhost:8000"

echo "🌱 Seeding Helia..."
echo ""

echo "1️⃣  Creating admin user..."
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@helia.local","password":"Admin1234","role":"patient"}'
echo ""

echo ""
echo "2️⃣  Creating test patient..."
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@helia.local","password":"Patient1234","role":"patient"}'
echo ""

echo ""
echo "3️⃣  Creating test doctor..."
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@helia.local","password":"Doctor1234","role":"doctor"}'
echo ""

echo ""
echo "⚠️  Email verification required before login."
echo "   Open Mailhog at http://localhost:8025 and verify each account."
echo ""
echo "4️⃣  Once verified, get an access token and create specialties:"
echo ""
echo "   Run this to get a token (after verifying email):"
echo "   TOKEN=\$(curl -s -X POST $BASE_URL/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"admin@helia.local\",\"password\":\"Admin1234\"}' \\"
echo "     | grep -o '\"access_token\":\"[^\"]*\"' | cut -d'\"' -f4)"
echo ""
echo "5️⃣  Then create specialties:"
echo "   for s in Cardiology Dermatology Neurology Orthopaedics Paediatrics 'General Practice' Psychiatry Ophthalmology; do"
echo "     curl -s -X POST $BASE_URL/specialties \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -H \"Authorization: Bearer \$TOKEN\" \\"
echo "       -d \"{\\\"name\\\":\\\"\$s\\\"}\""
echo "   done"
echo ""
echo "✅ User registration complete!"
echo ""
echo "Test accounts (verify emails first at http://localhost:8025):"
echo "  Patient: patient@helia.local / Patient1234"
echo "  Doctor:  doctor@helia.local  / Doctor1234"
echo "  Admin:   admin@helia.local   / Admin1234"
