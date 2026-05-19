import pygame
import random
import math


class PowerUp:
    MAGNET = 'magnet'
    SHIELD = 'shield'

    COLOR  = {MAGNET: (255, 220, 50), SHIELD: (80, 180, 255)}
    LABEL  = {MAGNET: 'M',            SHIELD: 'S'}

    MAGNET_DURATION       = 600   # 10초 (60fps 기준, 자석 파워업)
    MAGNET_SHORT_DURATION = 300   #  5초 (바나나우유 magnet_short 효과)

    def __init__(self, x, y, kind):
        self.x    = float(x)
        self.base_y = float(y)
        self.kind = kind
        self.radius = 15
        self.collected = False
        self.timer = 0.0
        d = self.radius * 2
        self.rect = pygame.Rect(0, 0, d, d)
        # 글로우 base — color는 kind당 고정, alpha만 펄스 → set_alpha로 조절
        gd = self.radius * 5
        self._glow = pygame.Surface((gd, gd), pygame.SRCALPHA)
        pygame.draw.circle(self._glow, self.COLOR[self.kind],
                           (gd // 2, gd // 2), self.radius * 2)
        self._update_rect()

    def _update_rect(self):
        cy = int(self.base_y + math.sin(self.timer) * 7)
        self.rect.x = int(self.x) - self.radius
        self.rect.y = cy - self.radius

    def update(self, speed):
        self.x -= speed
        self.timer += 0.07
        self._update_rect()

    def draw(self, screen, font_small):
        cx = int(self.x)
        cy = int(self.base_y + math.sin(self.timer) * 7)
        color = self.COLOR[self.kind]
        r = self.radius

        # 글로우 — base는 캐싱, alpha만 매 프레임 갱신
        self._glow.set_alpha(int(55 + 35 * math.sin(self.timer * 2)))
        screen.blit(self._glow, (cx - r * 2 - r // 2, cy - r * 2 - r // 2))

        # 다이아몬드 몸체
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(screen, color, pts)
        inner = [(cx, cy - r + 5), (cx + r - 5, cy),
                 (cx, cy + r - 5), (cx - r + 5, cy)]
        lighter = tuple(min(255, c + 60) for c in color)
        pygame.draw.polygon(screen, lighter, inner)

        # 라벨
        label = font_small.render(self.LABEL[self.kind], True, (30, 30, 30))
        screen.blit(label, label.get_rect(center=(cx, cy)))


class PowerUpManager:
    # 아이템 생성 간격: 600~900 프레임 (10~15초)
    SPAWN_MIN = 600
    SPAWN_MAX = 900

    def __init__(self, screen_width, ground_y):
        self.screen_width = screen_width
        self.ground_y     = ground_y
        self.items        = []
        self.spawn_timer  = 0
        self.next_spawn   = random.randint(self.SPAWN_MIN, self.SPAWN_MAX)

        # 활성 효과
        self.magnet_timer  = 0
        self.magnet_total  = 0   # 가장 최근에 켰을 때의 총 길이 (HUD 비율용)
        self.shield_active = False

        try:
            self.font_small = pygame.font.SysFont("arial", 15, bold=True)
        except Exception:
            self.font_small = pygame.font.Font(None, 20)

    # ── 프로퍼티 ───────────────────────────────────────────
    @property
    def magnet_active(self):
        return self.magnet_timer > 0

    # ── 업데이트 ───────────────────────────────────────────
    def update(self, speed):
        # 화면에 아이템이 없을 때만 생성
        if not self.items:
            self.spawn_timer += 1
            if self.spawn_timer >= self.next_spawn:
                self.spawn_timer = 0
                self.next_spawn  = random.randint(self.SPAWN_MIN, self.SPAWN_MAX)
                kind = random.choice([PowerUp.MAGNET, PowerUp.SHIELD])
                y    = self.ground_y - random.randint(70, 130)
                self.items.append(PowerUp(self.screen_width + 60, y, kind))

        for item in self.items:
            item.update(speed)
        self.items = [it for it in self.items if it.x > -50 and not it.collected]

        if self.magnet_timer > 0:
            self.magnet_timer -= 1

    def check_collision(self, player_rect):
        """플레이어와 충돌한 아이템 종류 반환."""
        activated = []
        for item in self.items:
            if not item.collected and player_rect.colliderect(item.rect):
                item.collected = True
                activated.append(item.kind)
                if item.kind == PowerUp.MAGNET:
                    self.magnet_timer = PowerUp.MAGNET_DURATION
                    self.magnet_total = PowerUp.MAGNET_DURATION
                elif item.kind == PowerUp.SHIELD:
                    self.shield_active = True
        return activated

    def use_shield(self):
        """방어막이 활성화되어 있으면 소모하고 True 반환."""
        if self.shield_active:
            self.shield_active = False
            return True
        return False

    def draw(self, screen):
        for item in self.items:
            if not item.collected:
                item.draw(screen, self.font_small)
