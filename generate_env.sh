#!/bin/bash
# Create a .env file with random secure variables

# Remove old .env files
rm -rf ./.env
rm -rf ./StudLicensing/backend/app/.env

# Generate a 60-character long random hex string (30 bytes * 2 = 60 characters)
POSTGRES_PASSWORD=$(openssl rand -hex 30)

# Generate a 120-character long random hex string (60 bytes * 2 = 120 characters)
SECRET_KEY=$(openssl rand -hex 60)

# Generate a 20-character long random password for the Super Administrator user (10 bytes * 2 = 20 characters)
SUPERADMIN_ACCOUNT_PASSWORD=$(openssl rand -hex 10)

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
SUPERADMIN_ACCOUNT_USERNAME=administrator@studlicensing.local
SUPERADMIN_ACCOUNT_PASSWORD=${SUPERADMIN_ACCOUNT_PASSWORD}
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
