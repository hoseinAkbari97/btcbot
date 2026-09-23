FROM node:20-alpine

WORKDIR /app

# Copy package manifests first for caching
COPY frontend/package.json frontend/package-lock.json* ./

RUN npm install

# Copy application source
COPY frontend/ ./

# Build at image creation time, not at runtime
RUN npm run build

EXPOSE 4173

# vite preview runs on 4173 by default
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "80"]
