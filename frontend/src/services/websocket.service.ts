import { WebSocketMessage } from '../types';

class WebSocketService {
  private socket: WebSocket | null = null;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();

  connect(url: string = `ws://${window.location.hostname}:${window.location.port}/ws`): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        resolve();
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        this.socket = null;
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket connection error:', error);
        reject(error);
      };

      this.socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.messageHandlers.clear();
  }

  sendMessage(message: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
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
    return this.socket?.readyState === WebSocket.OPEN || false;
  }
}

export const websocketService = new WebSocketService();