FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy application source
COPY frontend/ ./

EXPOSE 80

CMD ["npm", "run", "build", "&&", "vite", "preview", "--host", "0.0.0.0"]