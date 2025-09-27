import React, { useEffect, useRef, useState } from 'react';
import { VNCInfo } from '../types';

// Import noVNC types
declare global {
  interface Window {
    RFB: any;
  }
}

interface BrowserStreamProps {
  vncInfo: VNCInfo | null;
  className?: string;
}

const BrowserStream: React.FC<BrowserStreamProps> = ({ vncInfo, className = '' }) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const rfbRef = useRef<any>(null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'failed'>('disconnected');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load noVNC script dynamically
    const loadNoVNC = async () => {
      if (window.RFB) return; // Already loaded

      return new Promise<void>((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/@novnc/novnc@1.4.0/lib/rfb.js';
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load noVNC'));
        document.head.appendChild(script);
      });
    };

    loadNoVNC().catch(err => {
      setError('Failed to load VNC viewer');
      console.error('Error loading noVNC:', err);
    });
  }, []);

  useEffect(() => {
    if (!vncInfo || !window.RFB || !canvasRef.current) return;

    connectToVNC();

    return () => {
      disconnectVNC();
    };
  }, [vncInfo]);

  const connectToVNC = () => {
    if (!vncInfo || !canvasRef.current || !window.RFB) return;

    try {
      setConnectionStatus('connecting');
      setError(null);

      // Clear any existing connection
      disconnectVNC();

      // Create WebSocket URL for noVNC
      const wsUrl = `ws://${vncInfo.host}:${vncInfo.port + 1000}`;

      // Create RFB connection
      rfbRef.current = new window.RFB(canvasRef.current, wsUrl, {
        credentials: {
          password: '' // No password for demo
        }
      });

      // Set up event listeners
      rfbRef.current.addEventListener('connect', () => {
        console.log('VNC connected');
        setConnectionStatus('connected');
        setError(null);
      });

      rfbRef.current.addEventListener('disconnect', (e: any) => {
        console.log('VNC disconnected:', e.detail);
        setConnectionStatus('disconnected');
        if (e.detail.clean === false) {
          setError('Connection lost unexpectedly');
        }
      });

      rfbRef.current.addEventListener('securityfailure', (e: any) => {
        console.error('VNC security failure:', e.detail);
        setConnectionStatus('failed');
        setError('Authentication failed');
      });

      // Configure display settings
      rfbRef.current.scaleViewport = true;
      rfbRef.current.resizeSession = false;

    } catch (err) {
      console.error('Error connecting to VNC:', err);
      setConnectionStatus('failed');
      setError('Failed to establish VNC connection');
    }
  };

  const disconnectVNC = () => {
    if (rfbRef.current) {
      rfbRef.current.disconnect();
      rfbRef.current = null;
    }
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected to remote browser';
      case 'connecting': return 'Connecting to remote browser...';
      case 'failed': return 'Connection failed';
      default: return 'Not connected';
    }
  };

  return (
    <div className={`bg-gray-100 border border-gray-300 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-white px-4 py-2 border-b border-gray-300 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' :
            connectionStatus === 'connecting' ? 'bg-yellow-500' :
            connectionStatus === 'failed' ? 'bg-red-500' : 'bg-gray-400'
          }`}></div>
          <span className={`text-sm font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>

        {vncInfo && (
          <div className="text-xs text-gray-500">
            {vncInfo.host}:{vncInfo.port} ({vncInfo.width}x{vncInfo.height})
          </div>
        )}
      </div>

      {/* VNC Display Area */}
      <div className="relative bg-black" style={{ minHeight: '600px' }}>
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-red-50">
            <div className="text-center">
              <div className="text-red-600 mb-2">⚠️</div>
              <div className="text-red-800 font-medium">{error}</div>
              <button
                onClick={connectToVNC}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Retry Connection
              </button>
            </div>
          </div>
        )}

        {!vncInfo && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <div className="text-center text-gray-600">
              <div className="text-4xl mb-4">🖥️</div>
              <div className="font-medium">No remote browser session</div>
              <div className="text-sm">Start a task to see the browser in action</div>
            </div>
          </div>
        )}

        {connectionStatus === 'connecting' && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75">
            <div className="text-center text-white">
              <div className="animate-spin w-8 h-8 border-2 border-white border-t-transparent rounded-full mx-auto mb-4"></div>
              <div>Connecting to remote browser...</div>
            </div>
          </div>
        )}

        {/* noVNC will render the remote desktop here */}
        <div
          ref={canvasRef}
          className="w-full h-full min-h-[600px]"
          style={{
            background: connectionStatus === 'connected' ? 'transparent' : '#000'
          }}
        />
      </div>
    </div>
  );
};

export default BrowserStream;