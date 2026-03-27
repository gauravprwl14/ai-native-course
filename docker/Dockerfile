# Stage 1: Build the Docusaurus site
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for layer caching
COPY website/package.json website/package-lock.json* ./

RUN npm ci --frozen-lockfile

# Copy the rest of the site
COPY website/ .

# Build static files
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:1.27-alpine AS server

# Copy the nginx config
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Copy built static files from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/ai-native-course/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
