# StudLicensing

## Installation
Run the following commands to clone or pull the latest StudLicensing repo:
```bash
# First time clone
git clone git@github.com:mtimani/StudLicensing.git

# If repo already cloned
git pull origin main
```

Generate `.env` files with the following command:
```bash
chmod +x generate_env.sh
./generate_env.sh
sudo rm -rf StudLicensing/db_data 
```
> [!WARNING]
> Do not forget to modify the `studlicensing@gmail.com` email password in the `.env` and `./StudLicensing/backend/app/.env`

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
