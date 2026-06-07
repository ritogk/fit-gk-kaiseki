// WS で受け取るライブ信号のスキーマ（server/signals.py と一致）。

export interface LiveSignals {
  rpm: number
  throttle: number // %
  speed: number // km/h
  steeringAngle: number // deg
  steeringRate: number // deg/s
  brake: number // raw
  brakePressed: boolean
  gasPressed: boolean
  coolantTemp: number // C
  batteryVoltage: number // V
  gear: number // raw enum
  outsideTemp: number // C
  wheelFL: number
  wheelFR: number
  wheelRL: number
  wheelRR: number
  latAccel: number // m/s^2 (現状 0 固定)
  longAccel: number // m/s^2 (車速の時間微分)
}

export interface RawGauge {
  name: string
  value: number
  unit: string
  min: number
  max: number
}

export interface RawFrame {
  id: number
  hex: string
  dlc: number
  data: number[]
  count: number
}

export interface FrameMessage {
  type: 'frame'
  t: number
  alive: boolean
  signals: LiveSignals
  raw: RawGauge[]
  frames: RawFrame[]
}

export const ZERO_SIGNALS: LiveSignals = {
  rpm: 0,
  throttle: 0,
  speed: 0,
  steeringAngle: 0,
  steeringRate: 0,
  brake: 0,
  brakePressed: false,
  gasPressed: false,
  coolantTemp: 0,
  batteryVoltage: 0,
  gear: 0,
  outsideTemp: 0,
  wheelFL: 0,
  wheelFR: 0,
  wheelRL: 0,
  wheelRR: 0,
  latAccel: 0,
  longAccel: 0,
}
