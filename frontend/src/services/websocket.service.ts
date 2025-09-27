import { io, Socket } from 'socket.io-client';
import { WebSocketMessage } from '../types';

class WebSocketService {
  private socket: Socket | null = null;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();

  connect(url: string = 'ws://localhost:8000/ws'): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = io(url, {
        transports: ['websocket'],
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected');
        resolve();
      });

      this.socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
      });

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        reject(error);
      });

      this.socket.on('message', (message: WebSocketMessage) => {
        this.handleMessage(message);
      });
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.messageHandlers.clear();
  }

  sendMessage(message: any) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('message', message);
    } else {
      console.error('WebSocket not connected');
    }
  }

  executeTask(taskId: string) {
    this.sendMessage({
      type: 'execute_task',
      task_id: taskId
    });
  }

  getVNCInfo() {
    this.sendMessage({
      type: 'get_vnc_info'
    });
  }

  onMessage(messageType: string, handler: (message: WebSocketMessage) => void) {
    this.messageHandlers.set(messageType, handler);
  }

  offMessage(messageType: string) {
    this.messageHandlers.delete(messageType);
  }

  private handleMessage(message: WebSocketMessage) {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message);
    }

    // Also call generic message handler if exists
    const genericHandler = this.messageHandlers.get('*');
    if (genericHandler) {
      genericHandler(message);
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const websocketService = new WebSocketService();