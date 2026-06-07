// アナログ入力（RPM・ステア角）→ リアルタイム発音（Web Audio）。
//
// 低遅延設計:
// - useLiveCan().onFrame(cb) から update() を直接叩く（Vue 描画ループを介さない）。
// - パラメータは setTargetAtTime でグライド（クリック/ジッパーノイズ回避、かつ即応）。
// - AudioContext({ latencyHint: 'interactive' }) で出力バッファ最小化。
//
// マッピング:
// - RPM → 音程（マイナーペンタトニックに量子化。何を弾いても音楽的）
// - ステア角 → 左右パン ＋ ローパス開度（明るさ/ワウ）

export class EngineSynth {
  private ctx: AudioContext | null = null
  private osc: OscillatorNode | null = null
  private sub: OscillatorNode | null = null
  private filter: BiquadFilterNode | null = null
  private gain: GainNode | null = null
  private panner: StereoPannerNode | null = null
  private running = false

  // A マイナーペンタトニック ~3 オクターブ
  private readonly scale: number[]

  // 表示用に最後のノート周波数/パンを保持
  lastFreq = 0
  lastPan = 0

  constructor() {
    const base = 220 // A3
    const steps = [0, 3, 5, 7, 10] // minor pentatonic (semitones)
    const s: number[] = []
    for (let oct = 0; oct < 3; oct++) {
      for (const st of steps) s.push(base * Math.pow(2, (oct * 12 + st) / 12))
    }
    s.push(base * Math.pow(2, 36 / 12))
    this.scale = s
  }

  get isRunning(): boolean {
    return this.running
  }

  // ブラウザの autoplay 制限のため、ユーザー操作（クリック）から呼ぶこと。
  async start(): Promise<void> {
    if (this.running) return
    const ctx = new AudioContext({ latencyHint: 'interactive' })
    await ctx.resume()

    const osc = ctx.createOscillator()
    osc.type = 'sawtooth'
    const sub = ctx.createOscillator()
    sub.type = 'sine'
    const filter = ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.value = 800
    filter.Q.value = 6
    const gain = ctx.createGain()
    gain.gain.value = 0
    const panner = ctx.createStereoPanner()

    osc.connect(filter)
    sub.connect(filter)
    filter.connect(gain)
    gain.connect(panner)
    panner.connect(ctx.destination)

    osc.frequency.value = 220
    sub.frequency.value = 110
    osc.start()
    sub.start()
    gain.gain.setTargetAtTime(0.16, ctx.currentTime, 0.05) // フェードイン

    this.ctx = ctx
    this.osc = osc
    this.sub = sub
    this.filter = filter
    this.gain = gain
    this.panner = panner
    this.running = true
  }

  update(rpm: number, steeringDeg: number): void {
    if (!this.running || !this.ctx || !this.osc || !this.sub || !this.filter || !this.panner) {
      return
    }
    const t = this.ctx.currentTime

    // RPM → 音階インデックス（800〜7000rpm を音階全域へ）
    const lo = 800
    const hi = 7000
    const norm = Math.max(0, Math.min(1, (rpm - lo) / (hi - lo)))
    const idx = Math.round(norm * (this.scale.length - 1))
    const freq = this.scale[idx] ?? 220
    this.osc.frequency.setTargetAtTime(freq, t, 0.04)
    this.sub.frequency.setTargetAtTime(freq / 2, t, 0.04)

    // ステア角 → 左右パン（±450°で振り切り）
    const pan = Math.max(-1, Math.min(1, steeringDeg / 450))
    this.panner.pan.setTargetAtTime(pan, t, 0.05)

    // 明るさ: RPM ＋ ステア切れ角で開く
    const cutoff = Math.min(6000, 400 + norm * 3000 + (Math.abs(steeringDeg) / 450) * 2200)
    this.filter.frequency.setTargetAtTime(cutoff, t, 0.05)

    this.lastFreq = freq
    this.lastPan = pan
  }

  stop(): void {
    if (!this.running || !this.ctx) return
    const ctx = this.ctx
    const osc = this.osc
    const sub = this.sub
    this.gain?.gain.setTargetAtTime(0, ctx.currentTime, 0.05)
    window.setTimeout(() => {
      try {
        osc?.stop()
        sub?.stop()
        ctx.close()
      } catch {
        /* ignore */
      }
    }, 200)
    this.running = false
    this.ctx = null
    this.osc = null
    this.sub = null
    this.filter = null
    this.gain = null
    this.panner = null
  }
}
