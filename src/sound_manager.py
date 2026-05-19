import array
import math
import pygame


def _clamp01(v):
    return max(0.0, min(1.0, v))


def _synth(freq, duration, volume=0.32, wave='sine', freq_end=None):
    """22050Hz, 16-bit signed stereo PCM 사운드를 절차적으로 생성."""
    rate = 22050
    n = int(rate * duration)
    buf = array.array('h')

    for i in range(n):
        t = i / rate

        attack = max(1, int(n * 0.05))
        release_start = int(n * 0.70)
        if i < attack:
            env = i / attack
        elif i < release_start:
            env = 1.0
        else:
            env = max(0.0, (n - i) / max(n - release_start, 1))

        f = freq if freq_end is None else freq + (freq_end - freq) * (i / n)

        if wave == 'sine':
            raw = math.sin(2 * math.pi * f * t)
        elif wave == 'square':
            raw = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -0.7
        elif wave == 'tri':
            raw = 2 * abs(2 * ((f * t) % 1) - 1) - 1
        else:
            raw = math.sin(2 * math.pi * f * t)

        sample = int(volume * 32767 * env * raw)
        sample = max(-32768, min(32767, sample))
        buf.append(sample)
        buf.append(sample)

    return pygame.mixer.Sound(buffer=buf)


# ── BGM ─────────────────────────────────────────────────────

_NOTE_FREQ = {
    'R':  0,
    'C3': 130.81, 'F3': 174.61, 'G3': 196.00,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00,
}

# 8박 루프 멜로디 (C장조, 경쾌한 느낌)
_BGM_MELODY = [
    ('C5', 0.5), ('D5', 0.5), ('E5', 0.5), ('G5', 0.5),
    ('A5', 0.5), ('G5', 0.5), ('E5', 0.5), ('C5', 0.5),
    ('G4', 0.5), ('A4', 0.5), ('C5', 0.5), ('E5', 0.5),
    ('G5', 0.5), ('A5', 0.5), ('G5', 1.0),
]

# 8박 루프 베이스 (I-IV-V-I 진행)
_BGM_BASS = [
    ('C3', 2.0), ('F3', 2.0), ('G3', 2.0), ('C3', 2.0),
]

# 게임오버 하강 멜로디
_GAMEOVER_MELODY = [
    ('C5', 0.5), ('B4', 0.5), ('A4', 0.5), ('G4', 0.5),
    ('F4', 0.5), ('E4', 0.5), ('D4', 0.5), ('C4', 0.5),
    ('C4', 2.0),
]

_BGM_CHANNEL = 6


def _build_bgm_sound(bpm, melody, bass):
    """BPM과 음표 패턴으로 Sound 객체 생성 (절차적 합성)."""
    rate   = 22050
    beat_s = 60.0 / bpm

    mel_beats = sum(b for _, b in melody)
    bas_beats = sum(b for _, b in bass)
    n_total   = int(rate * max(mel_beats, bas_beats) * beat_s)
    if n_total == 0:
        return None

    mix = [0.0] * n_total

    def add_layer(pattern, volume, wave):
        pos = 0
        for note, beats in pattern:
            n    = int(beats * beat_s * rate)
            freq = _NOTE_FREQ.get(note, 0)
            if freq > 0:
                atk    = max(1, int(n * 0.05))
                rel    = max(1, int(n * 0.30))
                rel_st = n - rel
                two_pi_freq = 2 * math.pi * freq
                for i in range(n):
                    t = i / rate
                    if i < atk:
                        env = i / atk
                    elif i >= rel_st:
                        env = max(0.0, (n - i) / rel)
                    else:
                        env = 1.0
                    if wave == 'sine':
                        raw = math.sin(two_pi_freq * t)
                    else:  # tri
                        raw = 2 * abs(2 * ((freq * t) % 1) - 1) - 1
                    idx = pos + i
                    if idx < n_total:
                        mix[idx] += volume * env * raw
            pos += n

    add_layer(melody, 0.28, 'sine')
    add_layer(bass,   0.18, 'tri')

    buf = array.array('h')
    for v in mix:
        s = int(max(-1.0, min(1.0, v)) * 32767)
        buf.append(s)
        buf.append(s)

    return pygame.mixer.Sound(buffer=buf)


class BGMPlayer:
    """게임 BGM 및 게임오버 멜로디를 전용 채널에서 관리."""

    def __init__(self):
        self._ok       = False
        self._ch       = None
        self._cache    = {}   # tier → Sound
        self._go_snd   = None
        self._cur_tier = -1
        self._vol      = 0.5
        try:
            n = pygame.mixer.get_num_channels()
            if n <= _BGM_CHANNEL:
                pygame.mixer.set_num_channels(_BGM_CHANNEL + 1)
            self._ch = pygame.mixer.Channel(_BGM_CHANNEL)
            self._ok = True
        except Exception as e:
            print(f"[BGMPlayer] 초기화 실패: {e}")

    def _tier_bpm(self, speed):
        if speed < 7:   return 0, 100
        if speed < 10:  return 1, 130
        if speed < 13:  return 2, 158
        return 3, 185

    def _get_sound(self, tier, bpm):
        if tier not in self._cache:
            self._cache[tier] = _build_bgm_sound(bpm, _BGM_MELODY, _BGM_BASS)
        return self._cache[tier]

    def start(self, speed):
        """게임 BGM 시작 (COUNTDOWN→PLAYING 전환 시)."""
        if not self._ok:
            return
        tier, bpm = self._tier_bpm(speed)
        snd = self._get_sound(tier, bpm)
        self._ch.stop()
        self._ch.play(snd, loops=-1)
        self._ch.set_volume(self._vol)
        self._cur_tier = tier

    def update(self, speed):
        """속도 티어 변경 시 템포 전환."""
        if not self._ok:
            return
        tier, bpm = self._tier_bpm(speed)
        if tier != self._cur_tier:
            snd = self._get_sound(tier, bpm)
            self._ch.stop()
            self._ch.play(snd, loops=-1)
            self._ch.set_volume(self._vol)
            self._cur_tier = tier

    def pause(self):
        if self._ok:
            self._ch.pause()

    def unpause(self):
        if self._ok:
            self._ch.unpause()

    def stop(self):
        if self._ok:
            self._ch.stop()
        self._cur_tier = -1

    def set_volume(self, vol):
        self._vol = _clamp01(vol)
        if self._ok and self._ch:
            self._ch.set_volume(self._vol)

    def play_game_over(self):
        """게임오버 하강 멜로디 재생."""
        if not self._ok:
            return
        self._ch.stop()
        self._cur_tier = -1
        if self._go_snd is None:
            self._go_snd = _build_bgm_sound(75, _GAMEOVER_MELODY, [])
        if self._go_snd:
            self._ch.play(self._go_snd)
            self._ch.set_volume(self._vol)


class SoundManager:
    def __init__(self):
        self.enabled  = False
        self.sounds   = {}
        self._sfx_vol = 1.0
        self.bgm      = BGMPlayer()
        self._load()

    def _load(self):
        try:
            self.sounds = {
                'jump':        _synth(320,  0.16, wave='sine', freq_end=500),
                'double_jump': _synth(500,  0.16, wave='sine', freq_end=720),
                'slide':       _synth(240,  0.13, wave='tri',  freq_end=130),
                'collect':     _synth(880,  0.09, volume=0.28, wave='sine'),
                'hit':         _synth(100,  0.24, volume=0.40, wave='square', freq_end=45),
                'magnet':      _synth(310,  0.22, wave='tri',  freq_end=460),
                'shield_on':   _synth(520,  0.25, wave='tri',  freq_end=720),
                'shield_hit':  _synth(600,  0.20, wave='tri',  freq_end=180),
                'skill':       _synth(180,  0.35, volume=0.40, wave='tri',  freq_end=680),
            }
            self.enabled = True
        except Exception as e:
            print(f"[SoundManager] 사운드 로드 실패 (무음 모드): {e}")

    def set_bgm_volume(self, vol):
        self.bgm.set_volume(vol)

    def set_sfx_volume(self, vol):
        self._sfx_vol = _clamp01(vol)
        for snd in self.sounds.values():
            snd.set_volume(self._sfx_vol)

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass
