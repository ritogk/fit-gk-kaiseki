export interface CommandMeta {
  lid: number
  iocp: number
  default_duration_s?: number
  description: string
}

export type CommandMap = Record<string, CommandMeta>

export interface LogEntry {
  time: string
  method: string
  url: string
  text: string
  error: boolean
}

export type Scene = number[]
