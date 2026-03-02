# Build stage
FROM node:24-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
# nginx-unprivileged runs as the nginx user (uid 101) with pre-configured
# cache directory permissions, avoiding chown failures in non-root Kubernetes pods.
FROM nginxinc/nginx-unprivileged:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 8080 (nginx-unprivileged listens on 8080 by default)
EXPOSE 8080

# Set environment variable for DAPI port (can be overridden)
ENV DAPI_PORT=5000

# Use entrypoint script to configure nginx before starting
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
