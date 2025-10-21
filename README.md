# wallet-service

---

This repository's responsible for serving wallet data, updating and ctreating new wallets. 

---

### Configurations:
make sure to have `.env` , `server.pem` and  `server.key` files in the root directory.

---

#### The `.env` file:
```.dotenv
# database configurations
DATABASE_URL=             <JDBC_DATABASE_URL>
SM_DB_KEY=                <DATABSAE_SM_KEY>
LOCAL=                    <1=LOCAL, 0=AWS>

# AWS configurations
AWS_REGION=               <AWS_REGION>
AWS_ACCESS_KEY=           <AWS_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY=    <AWS_SECRET_ACCESS_KEY>
```
---

#### The `server.key` and `server.pem` files:
both files are required for SSL connection.
they are simply the key and certificate for the server.
---

### Dockers:

- We can build dockers from the `Setup` directory. 
- Note that inside the `Setup` directory, we have a `GoldenCI` and `RunnerCI` directories.
- The `GoldenCI` directory is responsible for building the docker base image. (Mostly dependencies, update, and prerequests)
- The `RunnerCI` directory is responsible for running the docker image from the golden base image. (Mostly the application)

Examples:
```shell
# build base image
docker build -t golden:latest -f Setup/GoldenCI/Dockerfile . --no-cache

# build runner image
docker build -t runner:golden-latest -f Setup/RunnerCI/Dockerfile . --no-cache

# run runner image
docker run -it -d -p 443:443 runner:golden-latest --name runner-wallet-service
```
---
