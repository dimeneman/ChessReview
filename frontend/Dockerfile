# ==============================================================================
# ChessReview - Frontend Production Dockerfile
# ==============================================================================
# Multi-stage build:
#   Stage 1: Build React/Vite production bundle
#   Stage 2: Serve optimized static assets via Nginx Alpine
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Stage
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies deterministically
RUN npm ci

# Copy frontend source files
COPY frontend/ ./

# Build arguments for Vite environment variables
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Build production assets
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Nginx Runtime
# ------------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

LABEL maintainer="ChessReview Team" \
      description="Production Nginx container serving ChessReview React frontend" \
      version="1.0.0"

# Remove default nginx configuration and html files
RUN rm -rf /etc/nginx/conf.d/* /usr/share/nginx/html/*

# Copy custom Nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Health check probe
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

