# Development-oriented image for the React (Vite) frontend.
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better layer caching).
COPY package.json ./
RUN npm install

# Copy source.
COPY . .

EXPOSE 5173

# Vite dev server with proxy to the backend (see vite.config.ts).
CMD ["npm", "run", "dev"]
