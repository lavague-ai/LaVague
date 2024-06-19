import { ChromeExtensionDriver } from './driver';

export enum AgentServerState {
  DISCONNECTED,
  CONNECTING,
  CONNECTED,
  ERROR,
}

export class AgentServerConnector {
  private webSocket: WebSocket | null = null;
  readonly driver: ChromeExtensionDriver;
  onStateChange?: (state: AgentServerState) => void;
  onError?: (err: any) => void;
  currentState: AgentServerState = AgentServerState.DISCONNECTED;

  constructor() {
    this.driver = new ChromeExtensionDriver();
  }

  connect(host: string) {
    this.disconnect();
    this.driver.start();
    this.updateState(AgentServerState.CONNECTING);
    try {
      this.webSocket = new WebSocket('ws://' + host);
      this.webSocket.onopen = () => {
        this.updateState(AgentServerState.CONNECTED);
      };
  
      this.webSocket.onmessage = async (event: { data: string; }) => {
        const msg = JSON.parse(event.data);
        try {
          const ret = await this.driver.handleMessage(msg);
          this.sendMessage({
            id: msg.id,
            ret: ret,
            method: msg.command
          });
        } catch (error) {
          console.error('Error processing request', error, event.data);
          this.sendMessage({
            id: msg.id,
            ret: null,
            method: msg.command
          });
          this.error(error);
        }
      };
      this.webSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.error(error);
      };
      this.webSocket.onclose = () => {
        this.updateState(AgentServerState.DISCONNECTED);
      };
      this.keepAlive();
    } catch {
      this.updateState(AgentServerState.DISCONNECTED);
    }
  }

  sendMessage(message: any) {
    if (this.currentState === AgentServerState.CONNECTED) {
      this.webSocket?.send(JSON.stringify(message));
    }
  }

  disconnect() {
    this.driver.stop();
    if (this.webSocket) {
      this.webSocket.close();
      this.webSocket = null;
      this.updateState(AgentServerState.DISCONNECTED);
    }
  }

  sendPrompt(type: 'run' | 'get', args: string) {
    this.sendMessage({ type, args });
  }

  private updateState(state: AgentServerState) {
    if (state !== this.currentState) {
      this.onStateChange?.(state);
      this.currentState = state;
    }
  }

  private error(err: any) {
    this.onError?.(err);
  }

  /**
   * Keep alive interval shorter than 30s to avoid service worker becoming inactive
   */
  private keepAlive() {
    const keepAliveIntervalId = setInterval(
      () => {
        if (this.webSocket && this.webSocket.readyState === this.webSocket.OPEN) {
          this.webSocket.send("PING");
        } else {
          clearInterval(keepAliveIntervalId);
        }
      },
      10_000
    );
  }

}