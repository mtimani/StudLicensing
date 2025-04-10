# 📜 StudLicensing
Welcome to the StudLicensing repository!

![StudLicensing](https://github.com/user-attachments/assets/0636f522-6239-45a1-ab92-ec4f983f9475)

StudLicensing is a powerful and user-friendly license management solution designed to help you create, distribute, and manage software licenses for your products and applications. Whether you're handling internal tools or commercial software, StudLicensing simplifies the entire licensing lifecycle for your company and clients.

## 🚀 Features
- 🔐 Generate and manage license keys with ease
- 🧾 Assign licenses to users or clients
- 📦 Support for multiple products and applications
- ⏳ Track license expiration and renewals
- ⚙️ Easy integration into your existing systems
- 🖥️ Clean, intuitive user interface

## 🛠️ Use Cases
- Software vendors distributing licenses to customers
- Internal tools requiring controlled access
- SaaS platforms managing subscription-based licensing

## 📦 Getting Started

### Installation
Run the following commands to clone or pull the latest StudLicensing repo:
```bash
# First time clone
git clone git@github.com:mtimani/StudLicensing.git

# If repo already cloned
git pull origin main
```

### Environment variables generation
Generate `.env` files with the following command:
```bash
chmod +x generate_env.sh
./generate_env.sh
sudo rm -rf StudLicensing/db_data 
```
> [!WARNING]
> Do not forget to modify the `studlicensing@gmail.com` email password in the `.env` and `./StudLicensing/backend/app/.env`

### Start the application + useful commands to restart / reset containers and database
Start and stop docker containers:
```bash
# Run and build with docker-compose.yml
docker compose up

# Stop and destroy the containers
docker compose down

# Restart all containers with updated code
docker compose down && docker rmi studlicensing-backend:latest && docker compose up

# Restart all containers with updated code and reset database and uploads
docker compose down && docker rmi studlicensing-backend:latest && cd StudLicensing && sudo rm -rf uploads db_data && cd .. && docker compose up
```

> [!WARNING]
> In order for the code modifications be reflected in the docker containers, you must perform a `docker compose down && docker rmi studlicensing-backend:latest && docker compose up`
