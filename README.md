# StudLicensing

## Installation
Run the following commands to clone or pull the latest StudLicensing repo:
```bash
# First time clone
git clone https://github.com/mtimani/StudLicensing.git

# If repo already cloned
git pull origin main
```

Create a .env file containing credentials for the Postgresql database:
```env
POSTGRES_USER=YOUR_POSTGRESQL_USER
POSTGRES_PASSWORD=YOUR_POSTGRESQL_PASSWORD
POSTGRES_DB=YOUR_POSTGRESQL_DB
```

Start and stop docker containers:
```bash
# Run and build with docker-compose.yml
docker compose up

# Stop and destroy the containers
docker compose down
```

> [!WARNING]
> In order for the code modifications be reflected in the docker containers, you must perform a `docker compose down` followed by a `docker compose up`