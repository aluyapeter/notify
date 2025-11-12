# Use official Node image
FROM node:20

# Create app directory
WORKDIR /app

# Install app dependencies
COPY package*.json ./
RUN npm install

# Copy app source
COPY . .

# Build NestJS app
RUN npm run build

# Expose port
EXPOSE 8002

# Start the app
CMD ["node", "dist/main.js"]
