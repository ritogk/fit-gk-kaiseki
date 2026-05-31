// 共通パッド定義。LiveMode / StepSequencer の両方から利用する。
// launchpad/keymap-live.conf をミラーした論理上のパッド集合。

export interface Pad {
  id: string
  label: string
  key: string
  color: string
  mode: 'hold' | 'pulse'
}

export const LIGHT_PADS: Pad[] = [
  { id: 'low_beam',   label: 'LB',  key: 'q', color: 'amber', mode: 'hold' },
  { id: 'high_beam',  label: 'HB',  key: 'w', color: 'amber', mode: 'hold' },
  { id: 'hazard',     label: 'HZ',  key: 'e', color: 'amber', mode: 'hold' },
  { id: 'position',   label: 'PS',  key: 'a', color: 'amber', mode: 'hold' },
  { id: 'fog',        label: 'FG',  key: 's', color: 'amber', mode: 'hold' },
  { id: 'turn_left',  label: 'TL',  key: 'r', color: 'amber', mode: 'hold' },
  { id: 'turn_right', label: 'TR',  key: 'd', color: 'amber', mode: 'hold' },
]

export const ACTION_PADS: Pad[] = [
  { id: 'lock',    label: 'LOCK',   key: 'z', color: 'purple', mode: 'pulse' },
  { id: 'unlock',  label: 'UNLOCK', key: 'x', color: 'purple', mode: 'pulse' },
  { id: 'chirp',   label: 'CHIRP',  key: 'c', color: 'purple', mode: 'pulse' },
]

export const UTIL_PADS: Pad[] = [
  { id: 'room_lamp',       label: 'ROOM',   key: 't', color: 'amber',  mode: 'hold' },
  { id: 'cargo_light',     label: 'CARGO',  key: 'y', color: 'amber',  mode: 'hold' },
  { id: 'chirp_hold',      label: 'CHIRP+', key: 'u', color: 'purple', mode: 'hold' },
  { id: 'wiper_front_low', label: 'WI-FL',  key: 'g', color: 'blue',   mode: 'hold' },
  { id: 'wiper_front_hi',  label: 'WI-FH',  key: 'h', color: 'blue',   mode: 'hold' },
  { id: 'wiper_rear',      label: 'WI-R',   key: 'j', color: 'blue',   mode: 'hold' },
  { id: 'washer_front',    label: 'WA-F',   key: 'k', color: 'cyan',   mode: 'hold' },
  { id: 'washer_rear',     label: 'WA-R',   key: 'l', color: 'cyan',   mode: 'hold' },
]

export const HORN_SHORT_PAD: Pad = { id: 'horn_short', label: 'H.S', key: 'b', color: 'yellow', mode: 'pulse' }
export const HORN_PAD: Pad = { id: 'horn', label: 'HORN', key: ' ', color: 'orange', mode: 'hold' }

export const ALL_PADS: Pad[] = [...LIGHT_PADS, ...ACTION_PADS, ...UTIL_PADS, HORN_SHORT_PAD, HORN_PAD]

const padById = new Map(ALL_PADS.map((p) => [p.id, p]))

export function getPad(id: string): Pad {
  return padById.get(id)!
}

export function findPadByKey(key: string): Pad | undefined {
  const k = key === ' ' ? ' ' : key
  return ALL_PADS.find((p) => p.key === k)
}

// パッド色 → 点灯/消灯時の Tailwind クラス
export function padColorClass(pad: Pad, on: boolean): string {
  const map: Record<string, string> = {
    amber:  on ? 'bg-amber-400 shadow-amber-400/50'  : 'bg-slate-700 hover:bg-slate-600',
    yellow: on ? 'bg-yellow-300 shadow-yellow-300/50' : 'bg-yellow-900 hover:bg-yellow-800',
    white:  on ? 'bg-white shadow-white/50'           : 'bg-slate-700 hover:bg-slate-600',
    orange: on ? 'bg-orange-400 shadow-orange-400/50' : 'bg-orange-900 hover:bg-orange-800',
    cyan:   on ? 'bg-cyan-400 shadow-cyan-400/50'     : 'bg-slate-700 hover:bg-slate-600',
    green:  on ? 'bg-green-400 shadow-green-400/50'   : 'bg-slate-700 hover:bg-slate-600',
    blue:   on ? 'bg-blue-400 shadow-blue-400/50'     : 'bg-slate-700 hover:bg-slate-600',
    purple: on ? 'bg-purple-400 shadow-purple-400/50' : 'bg-slate-700 hover:bg-slate-600',
    red:    on ? 'bg-red-500 shadow-red-500/50'       : 'bg-red-900 hover:bg-red-800',
  }
  return map[pad.color] ?? ''
}

// CarFace モニター用: コマンドID → ライト位置(1-7)
export const CMD_TO_POS: Record<string, number> = {
  hazard: 1, high_beam: 2, low_beam: 3, position: 4, fog: 5, turn_left: 6, turn_right: 7,
}
