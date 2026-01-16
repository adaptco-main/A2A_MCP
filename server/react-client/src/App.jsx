import React from 'react';
import { useGameSocket } from './hooks/useGameSocket';
import { GameCanvas } from './components/GameCanvas';
import { HUD } from './components/HUD';
import { ConnectionStatus } from './components/ConnectionStatus';

function App() {
    const { status, gameState, sendInput } = useGameSocket('ws://localhost:8080');

    return (
        <div style={{ position: 'relative', width: '800px', height: '600px', margin: '0 auto' }}>
            <ConnectionStatus status={status} />
            <GameCanvas gameState={gameState} sendInput={sendInput} />
            <HUD score={0} energy={100} />
        </div>
    );
}

export default App;
