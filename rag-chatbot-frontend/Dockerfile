# rag-chatbot-frontend/Dockerfile

# ---- Stage 1: Build React App ----
# Use the specific Node version requested. Use Alpine for smaller size.
FROM node:18.19.1-alpine AS build-stage

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# OPTIONAL: If you absolutely MUST use npm 9.2.0 and the base image doesn't have it
# RUN npm install -g npm@9.2.0

# Install dependencies. 'npm ci' is often preferred for reproducible builds.
RUN npm ci
# If npm ci fails, fall back to: RUN npm install

# Copy the rest of the frontend application code
COPY . .

# Build the React app for production
RUN npm run build

# ---- Stage 2: Serve with Nginx ----
# Use a lightweight Nginx image
FROM nginx:alpine

# Copy the optimized build output from the build stage to Nginx's web root directory
COPY --from=build-stage /app/build /usr/share/nginx/html

# Copy your custom Nginx configuration file
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 (Nginx's default port)
EXPOSE 80

# Command to start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]