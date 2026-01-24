# Ghost Void Engine

A custom C++ game engine with a Node.js WebSocket shell and React SPA frontend.

## Architecture

This project consists of three main components:

1. **Engine Core (`src/`)**: A C++ game engine implementing physics, entity management, and procedural level generation.
2. **WebSocket Shell (`server/`)**: A Node.js server that spawns the engine process and bridges communication via WebSockets.
3. **React Frontend (`server/react-client/`)**: A Single Page Application (SPA) that acts as the game client, rendering state on an HTML5 Canvas.

## git Workflow

To host this codebase in Git:

1. **Initialize**: Run `git init` (if not already done).
2. **Ignore**: Ensure `.gitignore` excludes `bin/`, `node_modules/`, and build artifacts.
3. **Commit**: Add and commit your source files.

### Repository Structure

```
root/
├── src/                # C++ Source Code
├── include/            # C++ Headers
├── server/             # Node.js Server
│   ├── server.js       # Entry Point
│   └── react-client/   # React Source
└── Makefile            # Build Configuration
```

## How to Run

### Prerequisities

- C++ Compiler (GCC/Clang/MSVC)
- Node.js & npm

### 1. Build the Engine

```sh
make all
# OR manually:
# g++ -I./include -std=c++17 src/main.cpp src/engine/*.cpp src/agents/*.cpp src/safety/*.cpp -o bin/ghost-void_engine.exe
```

### 2. Build the Frontend

```sh
cd server/react-client
npm install
npm run build
```

### 3. Start the Server

```sh
cd server
npm install
node server.js
```

Visit `http://localhost:8080` to play.
