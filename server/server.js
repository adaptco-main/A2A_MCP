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

    engine.stdout.on('data', (data) => {
        // Send engine output (state) to the client
        try {
            // Data might come in chunks, for this scaffolding we assume line-delimited JSON
            const lines = data.toString().split('\n');
            for (const line of lines) {
                if (line.trim()) {
                    ws.send(line.trim());
                }
            }
        } catch (e) {
            console.error('Error sending data to client:', e);
        }
    });

    ws.on('message', (message) => {
        // Forward client commands to the engine
        // Expected format: JSON string ending with newline
        engine.stdin.write(message + '\n');
    });

    ws.on('close', () => {
        console.log('Client disconnected');
        engine.kill();
    });

    engine.on('close', (code) => {
        console.log(`Engine process exited with code ${code}`);
        ws.close();
    });
});
