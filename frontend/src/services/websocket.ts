import { useStore } from '../stores/projectStore';

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private url: string;
  private onMessageCallback: (data: any) => void;

  constructor(onMessage: (data: any) => void) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = `${wsProtocol}//${window.location.host}/ws`;
    this.onMessageCallback = onMessage;
  }

  connect() {
    const store = useStore.getState();
    const token = store.token;
    const connectUrl = token ? `${this.url}?token=${encodeURIComponent(token)}` : this.url;

    store.setConnecting(true);
    this.socket = new WebSocket(connectUrl);

    this.socket.onopen = () => {
      useStore.getState().setConnecting(false);
      console.log('AKSHAT WS Connection Established');
    };

    this.socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        this.onMessageCallback(payload);
      } catch (err) {
        console.error('AKSHAT WS Message parsing error:', err);
      }
    };

    this.socket.onclose = () => {
      useStore.getState().setConnecting(false);
      console.log('AKSHAT WS Connection Closed, retrying in 5s...');
      setTimeout(() => this.connect(), 5000);
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
    }
  }
}
