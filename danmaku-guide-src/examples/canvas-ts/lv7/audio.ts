import type { Game } from './game';

// #region tone
// 합성은 효과 로딩 때만 수행한다. 시간·공간 O(샘플 수), 게임 난수는 소비하지 않는다.
export function tone(frequency: number, duration: number, rate = 22050): Float32Array {
  const count = Math.floor(duration * rate), result = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    const envelope = Math.min(1, i / 110) * (1 - i / Math.max(1, count));
    result[i] = Math.sin(2 * Math.PI * frequency * i / rate) * envelope * .14;
  }
  return result;
}
// #endregion

export class Audio {
  enabled = false;
  unlocking = false;
  context: AudioContext | null = null;
  sounds: AudioBuffer[] = [];
  music: AudioBufferSourceNode | null = null;
  gain: GainNode | null = null;
  constructor(readonly create: () => AudioContext = () => new AudioContext()) {}

  // #region audio-buffer
  buffer(samples: Float32Array): AudioBuffer {
    const result = this.context!.createBuffer(1, samples.length, 22050);
    result.getChannelData(0).set(samples);
    return result;
  }
  // #endregion

  // #region melody
  melody(): Float32Array {
    const result = new Float32Array(8 * 8820);
    [220, 330, 440, 330, 262, 392, 523, 392].forEach((frequency, i) => result.set(tone(frequency, .4), i * 8820));
    return result;
  }
  // #endregion

  // #region audio-unlock
  async unlock(): Promise<void> {
    if (this.enabled || this.unlocking) return;
    this.unlocking = true;
    try {
      this.context ??= this.create();
      await this.context.resume();
      this.sounds = [660, 130, 220, 880, 90, 990, 440, 110].map((f) => this.buffer(tone(f, .08)));
      this.gain = this.context.createGain(); this.gain.gain.value = .2;
      this.gain.connect(this.context.destination);
      this.music = this.context.createBufferSource();
      this.music.buffer = this.buffer(this.melody()); this.music.loop = true;
      this.music.connect(this.gain); this.music.start();
      this.enabled = true;
    } catch { this.enabled = false; }
    finally { this.unlocking = false; }
  }
  // #endregion

  // #region audio-consume
  consume(game: Pick<Game, 'eventCount' | 'eventKind' | 'status' | 'paused'>): void {
    if (!this.enabled || !this.context) return;
    let played = 0;
    for (let i = 0; i < game.eventCount; i++) {
      const kind = game.eventKind[i], mask = 1 << kind;
      if (played & mask) continue;
      const source = this.context.createBufferSource();
      source.buffer = this.sounds[kind - 1];
      source.connect(this.context.destination); source.start();
      played |= mask;
    }
    if (this.gain) this.gain.gain.value = game.paused || game.status !== 1 ? .08 : .2;
  }
  // #endregion

  // #region audio-active
  setActive(active: boolean): void {
    if (!this.enabled || !this.context) return;
    if (active && this.context.state === 'suspended') void this.context.resume().catch(() => {});
    else if (!active && this.context.state === 'running') void this.context.suspend().catch(() => {});
  }
  // #endregion

  // #region audio-close
  close(): void {
    this.music?.stop(); this.music?.disconnect();
    void this.context?.close();
    this.enabled = false;
  }
  // #endregion
}
