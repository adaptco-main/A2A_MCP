import React, { useState } from 'react';
import { useGameSocket } from './hooks/useGameSocket';
import { GameCanvas } from './components/GameCanvas';
import WebGLCanvas from './components/WebGLCanvas';
import { HUD } from './components/HUD';
import { ConnectionStatus } from './components/ConnectionStatus';

function App() {
    const { status, gameState, sendInput } = useGameSocket('ws://localhost:8080');
    const [useWebGL, setUseWebGL] = useState(false);

    return (
        <div style={{ position: 'relative', width: '800px', height: '600px', margin: '0 auto' }}>
            <ConnectionStatus status={status} />
            <button 
                onClick={() => setUseWebGL(!useWebGL)}
                style={{ position: 'absolute', top: 10, right: 10, zIndex: 10 }}
            >
                {useWebGL ? 'Switch to 2D' : 'Switch to WebGL'}
            </button>
            {useWebGL ? (
                <WebGLCanvas gameState={gameState} />
            ) : (
                <GameCanvas gameState={gameState} sendInput={sendInput} />
            )}
            <HUD score={0} energy={100} />
        </div>
    );
}

export default App;
