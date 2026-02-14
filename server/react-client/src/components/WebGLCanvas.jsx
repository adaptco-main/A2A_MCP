import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';

/**
 * WebGLCanvas Component
 * Renders the Game Engine state using Three.js for hardware acceleration.
 */
const WebGLCanvas = ({ gameState }) => {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);

  useEffect(() => {
    // 1. Initialize Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050505);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });

    renderer.setSize(window.innerWidth, window.innerHeight);
    mountRef.current.appendChild(renderer.domElement);

    camera.position.z = 5;

    // 2. Lights
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xffffff, 1, 100);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    // 3. Simple Mock objects for Game State
    const geometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
    const material = new THREE.MeshPhongMaterial({ color: 0x00ff00 });
    const cube = new THREE.Mesh(geometry, material);
    scene.add(cube);

    // 4. WebSocket Connection
    // Connection to the Node.js server which proxies the C++ engine
    const ws = new WebSocket('ws://localhost:8080');

    ws.onopen = () => {
      console.log('Connected to Game Server');
    };

    // Map to track meshes
    const spriteMeshes = useRef(new Map());

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // console.log('Engine State:', data);

        if (data.type === 'render_frame' && data.sprites && Array.isArray(data.sprites)) {
          // Very naive rendering: Clear all and redraw
          // Optimizations would involve object pooling or updating existing meshes
          spriteMeshes.current.forEach(mesh => scene.remove(mesh));
          spriteMeshes.current.clear();

          data.sprites.forEach((sprite, i) => {
            const geometry = new THREE.PlaneGeometry(sprite.w, sprite.h);
            // Random color based on texture ID hash to differentiate
            // For now just green
            const material = new THREE.MeshBasicMaterial({ color: 0x00ff00, side: THREE.DoubleSide });
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(sprite.x, sprite.y, 0);
            scene.add(mesh);
            spriteMeshes.current.set(i, mesh);
          });
        }

      } catch (e) {
        // console.error('Failed to parse engine state:', e);
      }
    };

    ws.onclose = () => {
      console.log('Disconnected from Game Server');
    };

    const animate = () => {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };

    animate();

    // 5. Cleanup
    return () => {
      ws.close();
      mountRef.current?.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        zIndex: 1
      }}
    />
  );
};

export default WebGLCanvas;
