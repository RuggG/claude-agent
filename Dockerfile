FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy built application
COPY dist ./dist

# Set environment
ENV NODE_ENV=production

# Expose port (Render uses PORT env var)
EXPOSE 3000

# Start the server
CMD ["node", "dist/index.js"]
