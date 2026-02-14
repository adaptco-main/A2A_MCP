const WebSocket = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const express = require('express');
const http = require('http');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Serve static files from 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

const PORT = 8080;
server.listen(PORT, () => {
    console.log(`Server started on http://localhost:${PORT}`);
});

// console.log('WebSocket Server started on port 8080'); // Removed separate log

// Path to the compiled engine executable
// Assuming it's in ../bin/ghost-void_engine.exe
const enginePath = path.resolve(__dirname, '../bin/ghost-void_engine');

wss.on('connection', (ws) => {
    console.log('Client connected');

    // Spawn the game engine process
    const engine = spawn(enginePath, [], {
        stdio: ['pipe', 'pipe', 'inherit'] // Pipe stdin/stdout, inherit stderr
    });

    let buffer = '';
    engine.stdout.on('data', (data) => {
        buffer += data.toString();

        let boundary = buffer.indexOf('\n');
        while (boundary !== -1) {
            const line = buffer.substring(0, boundary).trim();
            buffer = buffer.substring(boundary + 1);
            boundary = buffer.indexOf('\n');

            if (line) {
                // Validate JSON before broadcasting
                try {
                    const json = JSON.parse(line);
                    const payload = JSON.stringify(json);
                    // Broadcast to all connected clients (Frontend & Agent)
                    wss.clients.forEach((client) => {
                        if (client.readyState === WebSocket.OPEN) {
                            client.send(payload);
                        }
                    });
                } catch (parseError) {
                    console.error('Invalid JSON from engine:', line.substring(0, 100) + '...');
                }
            }
        }
    });

    ws.on('message', (message) => {
        // Forward client commands to the engine
        // Expected format: JSON string ending with newline
        engine.stdin.write(message + '\n');
    });

    // Start Game Loop (Drive the engine)
    const gameLoop = setInterval(() => {
        if (engine.exitCode === null) {
            engine.stdin.write('tick\n');
        }
    }, 1000 / 60); // 60 FPS

    ws.on('close', () => {
        console.log('Client disconnected');
        clearInterval(gameLoop);
        engine.kill();
    });

    engine.on('close', (code) => {
        console.log(`Engine process exited with code ${code}`);
        ws.close();
    });
});
