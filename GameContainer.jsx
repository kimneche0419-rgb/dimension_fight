import React, { useState, useEffect } from 'react';

const GameContainer = () => {
  const [loading, setLoading] = useState(true);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#0a0f1e',
      color: '#00b4ff',
      fontFamily: 'monospace'
    }}>
      <h1>DIMENSION FIGHT</h1>
      <div style={{
        position: 'relative',
        width: '800px',
        height: '600px',
        border: '2px solid #00b4ff',
        boxShadow: '0 0 20px #00b4ff44'
      }}>
        <iframe 
          src="/index.html" 
          title="Dimension Fight"
          width="800"
          height="600"
          frameBorder="0"
          scrolling="no"
          style={{ overflow: 'hidden' }}
          onLoad={() => setLoading(false)}
        />
        {loading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#0a0f1e'
          }}>
            <p>LOADING CORE SYSTEMS...</p>
          </div>
        )}
      </div>
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <p>Use WASD to Move | Shift to Phase Shift | Space to Boost</p>
        <p>Progress is automatically saved to your browser and our server.</p>
      </div>
    </div>
  );
};

export default GameContainer;
