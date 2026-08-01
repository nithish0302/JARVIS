// Project JARVIS Interfaces Entrypoint
export interface IEngineService {
  start(): Promise<void>;
  stop(): Promise<void>;
}
