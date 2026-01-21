# Stage 1: Build the C++ Engine
FROM gcc:13 AS engine-builder

WORKDIR /app

# Copy source files
COPY include/ include/
COPY src/ src/
COPY Makefile .

# Build the engine
RUN mkdir -p bin && \
    g++ -I./include -std=c++17 \
    src/main.cpp \
    src/engine/*.cpp \
    src/agents/*.cpp \
    src/safety/*.cpp \
    -o bin/ghost-void_engine

# Stage 2: Build the React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/server/react-client

COPY server/react-client/package*.json ./
RUN npm ci

COPY server/react-client/ ./
RUN npm run build

# Stage 3: Runtime
FROM node:20-alpine

WORKDIR /app

# Install dependencies for running native binaries
RUN apk add --no-cache libstdc++ libgcc

# Copy built engine from stage 1
COPY --from=engine-builder /app/bin/ghost-void_engine ./bin/ghost-void_engine
RUN chmod +x ./bin/ghost-void_engine

# Copy server files
COPY server/package*.json ./server/
WORKDIR /app/server
RUN npm ci --omit=dev

# Copy server source
COPY server/*.js ./

# Copy built frontend from stage 2
COPY --from=frontend-builder /app/server/react-client/dist ./public/

WORKDIR /app/server

EXPOSE 8080

CMD ["node", "server.js"]
