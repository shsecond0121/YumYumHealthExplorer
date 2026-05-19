# 활성 효과(디버프/버프) 매니저.
# 효과 ID별 남은 프레임을 dict로 관리. game.py가 is_active(id) / 프로퍼티로 조회.

# 지속 효과 사양 (60fps 프레임 기준)
TIMED_EFFECTS = {
    # 단순 지속 디버프
    'heavy_jump':   {'duration': 240},
    'heavy_jump_l': {'duration': 240},
    'heavy_combo':  {'duration': 240},
    'vision_blur':  {'duration': 180},
    'slow_freeze':  {'duration': 120},
    'slide_short':  {'duration': 180},
    'gauge_freeze': {'duration': 300},
    'dizzy':        {'duration': 300},   # 더블점프 봉인 (초콜릿)
    'sticky':       {'duration': 180},   # 슬라이드 봉인 (솜사탕)

    # 지속 버프
    'score_mult':   {'duration': 300},

    # 갈증 (자동 토글)
    'thirst':       {'duration': 999999},  # 자동 해제는 game.py가 관리
}


class DebuffManager:
    def __init__(self):
        self._active = {}   # effect_id -> remaining frames

    def add(self, effect_id, frames=None):
        spec = TIMED_EFFECTS.get(effect_id)
        if spec is None:
            return
        if frames is None:
            frames = spec.get('duration', 60)
        # 동일 효과 재진입 시 더 긴 쪽으로 갱신 (스택 X)
        self._active[effect_id] = max(self._active.get(effect_id, 0), frames)

    def clear_negative(self):
        """score_mult(긍정 버프)만 유지하고 부정 디버프만 제거."""
        for k in list(self._active):
            if k != 'score_mult':
                self._active.pop(k, None)

    def update(self):
        for k in list(self._active):
            self._active[k] -= 1
            if self._active[k] <= 0:
                self._active.pop(k, None)

    def is_active(self, effect_id):
        return effect_id in self._active

    # ── 게임 로직이 조회하는 종합 effect 뷰 ─────────────────
    @property
    def jump_force_mult(self):
        m = 1.0
        if self.is_active('heavy_jump'):    m *= 0.70
        if self.is_active('heavy_jump_l'):  m *= 0.75
        if self.is_active('heavy_combo'):   m *= 0.80
        if self.is_active('thirst'):        m *= 0.80
        return m

    @property
    def slide_dur_mult(self):
        if self.is_active('slide_short'):
            return 0.45
        return 1.0

    @property
    def speed_mult(self):
        """장애물·배경 속도 배율 — slow_freeze만."""
        m = 1.0
        if self.is_active('slow_freeze'):
            m *= 0.5
        return m

    @property
    def score_mult(self):
        return 1.5 if self.is_active('score_mult') else 1.0

    @property
    def combo_frozen(self):
        """콤보 누적 정지 — 새 콤보가 안 쌓임."""
        return self.is_active('heavy_combo') or self.is_active('thirst')

    @property
    def gauge_frozen(self):
        return self.is_active('gauge_freeze')

    @property
    def vision_blur(self):
        return self.is_active('vision_blur')

    @property
    def double_jump_blocked(self):
        return self.is_active('dizzy')

    @property
    def slide_blocked(self):
        return self.is_active('sticky')
