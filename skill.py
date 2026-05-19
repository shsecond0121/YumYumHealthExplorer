import random

GAUGE_MAX   = 100
SKILL_TICKS = 300   # 5초 (60fps)

EFFECTS = [
    {'id': 'invincible',  'name': '무적 질주!',  'color': (255, 140,  50)},
    {'id': 'slowdown',    'name': '시간 감속!',  'color': (100, 200, 255)},
    {'id': 'jelly_party', 'name': '젤리 파티!',  'color': (255, 100, 200)},
    {'id': 'score_blast', 'name': '점수 폭발!',  'color': (255, 230,  50)},
]


class SkillManager:
    def __init__(self):
        self.gauge  = 0.0
        self.active = False
        self.effect = None
        self.timer  = 0

    def add_gauge(self, normal=0, star=0, crystal=0):
        self.gauge = min(GAUGE_MAX,
                         self.gauge + normal * 1 + star * 3 + crystal * 5)

    def try_activate(self):
        """게이지가 가득 찼을 때 Z키로 호출. 랜덤 효과 반환, 미충족 시 None."""
        if self.gauge >= GAUGE_MAX and not self.active:
            self.effect = random.choice(EFFECTS)
            self.active = True
            self.timer  = SKILL_TICKS
            self.gauge  = 0.0
            return self.effect
        return None

    def update(self):
        if self.active:
            self.timer -= 1
            if self.timer <= 0:
                self.active = False
                self.effect = None

    @property
    def gauge_ratio(self):
        return self.gauge / GAUGE_MAX

    @property
    def skill_ratio(self):
        return self.timer / SKILL_TICKS if self.active else 0.0

    @property
    def effect_id(self):
        return self.effect['id'] if self.effect else None
