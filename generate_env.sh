#!/bin/bash
# Create a .env file with random secure variables

# Remove old .env files
rm -rf ./.env
rm -rf ./StudLicensing/backend/app/.env

# Generate a 30-character long random hex string (15 bytes * 2 = 30 characters)
POSTGRES_PASSWORD=$(openssl rand -hex 30)

# Generate a 60-character long random hex string (30 bytes * 2 = 60 characters)
SECRET_KEY=$(openssl rand -hex 60)

# Write the environment variables to the .env file
cat > .env <<EOF
POSTGRES_USER=StudLicensingUser
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=StudLicensingDB
POSTGRES_PORT=5432
SECRET_KEY=${SECRET_KEY}
TZ=Europe/Paris
BACKEND_URL=127.0.0.1:8000
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=studlicensing@gmail.com
SMTP_PASSWORD=ENTER_PASSWORD
FROM_EMAIL=studlicensing@gmail.com
EOF

echo ".env file created successfully."

# Copy the .env file to StudLicensing/backend/app/
TARGET_DIR="StudLicensing/backend/app"
if [ -d "${TARGET_DIR}" ]; then
    cp .env "${TARGET_DIR}/.env"
    echo "Copied .env to ${TARGET_DIR}/"
else
    echo "Error: Directory ${TARGET_DIR} does not exist. Please check the path."
fi
