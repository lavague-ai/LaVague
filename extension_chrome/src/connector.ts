import { ChromeExtensionDriver } from './driver';
import EventEmitter from 'eventemitter3';

export enum AgentServerState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
}

export enum RunningAgentState {
    IDLE,
    RUNNING,
}

export type EventType = 'init' | 'error' | 'stateChange' | 'runningStateChange' | 'inputMessage' | 'outputMessage' | 'systemMessage';

export class AgentServerConnector {
    private webSocket: WebSocket | null = null;
    private eventEmitter = new EventEmitter();
    readonly driver: ChromeExtensionDriver;
    currentState: AgentServerState = AgentServerState.DISCONNECTED;
    runningAgentState: RunningAgentState = RunningAgentState.IDLE;
    public host = '';
    public forced_disconnection = false;

    constructor() {
        this.driver = new ChromeExtensionDriver();
        this.emit('init', null);
    }

    async connect(host: string) {
        this.disconnect();
        this.updateState(AgentServerState.CONNECTING);
        try {
            const webSocket = new WebSocket('ws://' + host);
            this.host = host;
            this.forced_disconnection = false;

            webSocket.onmessage = async (event: { data: string }) => {
                if (event.data === 'PONG') {
                    return;
                }
                const msg = JSON.parse(event.data);
                this.emit('inputMessage', msg);
                let ret = null;
                try {
                    ret = await this.driver.handleMessage(msg);
                } catch (error) {
                    console.error('Error processing request', error, event.data);
                    this.emit('error', error);
                }
                this.sendMessage(
                    {
                        id: msg.id,
                        ret,
                        method: msg.command,
                    },
                    false
                );
            };
            await new Promise<void>((resolve, reject) => {
                webSocket.onopen = () => {
                    this.updateState(AgentServerState.CONNECTED);
                    resolve();
                };
                webSocket.onerror = reject;
            });
            webSocket.onerror = (error) => this.emit('error', error);
            webSocket.onclose = () => {
                this.updateState(AgentServerState.DISCONNECTED);
                this.updateRunningState(RunningAgentState.IDLE);
            };
            this.webSocket = webSocket;
            this.keepAlive();
            await this.driver.start();
        } catch (e) {
            this.updateState(AgentServerState.DISCONNECTED);
            this.updateRunningState(RunningAgentState.IDLE);
            throw e;
        }
    }

    sendMessage(message: any, emit = true) {
        if (this.currentState !== AgentServerState.CONNECTED) {
            return false;
        }
        this.webSocket?.send(JSON.stringify(message));
        if (emit) {
            this.emit('outputMessage', message);
        }
        return true;
    }

    async disconnect() {
        if (this.webSocket) {
            this.webSocket.close();
            this.webSocket = null;
            this.updateState(AgentServerState.DISCONNECTED);
            this.updateRunningState(RunningAgentState.IDLE);
        }
        await this.driver.stop();
    }

    sendSystemMessage(msg: string) {
        this.emit('systemMessage', {
            args: msg,
        });
    }

    sendPrompt(type: 'run' | 'get' | 'run_step' | 'navigate' | 'prepare_run' | 'retrieve', args: string) {
        this.sendMessage({ type, args });
    }

    runningStateChange(fn: (state: RunningAgentState) => void) {
        return this.on('runningStateChange', fn);
    }

    onStateChange(fn: (state: AgentServerState) => void) {
        return this.on('stateChange', fn);
    }

    onError(fn: (message: string) => void) {
        return this.on('error', fn);
    }

    onInit(fn: (ret: any) => void) {
        return this.on('init', fn);
    }

    onInputMessage(fn: (ret: any) => void) {
        return this.on('inputMessage', fn);
    }

    onSystemMessage(fn: (message: any) => void) {
        return this.on('systemMessage', fn);
    }

    onOutputMessage(fn: (message: any) => void) {
        return this.on('outputMessage', fn);
    }

    on<F extends EventEmitter.EventListener<EventType, EventType>>(event: EventType, fn: F) {
        this.eventEmitter.on(event, fn);
        return () => {
            this.eventEmitter.off(event, fn);
        };
    }

    private emit(event: EventType, ...args: any[]) {
        this.eventEmitter.emit(event, ...args);
    }

    private updateRunningState(state: RunningAgentState) {
        if (state !== this.runningAgentState) {
            this.emit('runningStateChange', state);
            this.runningAgentState = state;
        }
    }

    private updateState(state: AgentServerState) {
        if (state !== this.currentState) {
            this.emit('stateChange', state);
            this.currentState = state;
        }
    }

    /**
     * Keep alive interval shorter than 30s to avoid service worker becoming inactive
     */
    private keepAlive() {
        const keepAliveIntervalId = setInterval(() => {
            if (this.webSocket && this.webSocket.readyState === this.webSocket.OPEN) {
                this.webSocket.send('PING');
            } else {
                clearInterval(keepAliveIntervalId);
            }
        }, 10_000);
    }
}
