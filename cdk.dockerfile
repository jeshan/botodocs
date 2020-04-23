FROM node:13.12.0-slim

WORKDIR /app

COPY package.*json ./
RUN npm i

COPY cdk.*json ./
#COPY lib lib
#COPY bin bin

ENTRYPOINT ["npm", "run", "cdk"]
