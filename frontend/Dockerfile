FROM node:18-alpine

WORKDIR /app

# Bağımlılıkları kopyala ve kur
COPY package*.json ./
RUN npm ci

# Uygulama kodunu kopyala
COPY . .

# Port
EXPOSE 3000

# Varsayılan komut
CMD ["npm", "run", "dev"]