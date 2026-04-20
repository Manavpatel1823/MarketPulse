FROM node:20-alpine

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

ENV API_URL=http://backend:8000
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
