import pygame
import random
import math


class Particle:
    def __init__(self, x, y, color, vx, vy, size, lifetime, gravity=0.18):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.vx = vx
        self.vy = vy
        self.size = size
        self.lifetime = lifetime
        self.max_life = lifetime
        self.gravity = gravity

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.96   # 마찰
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen):
        ratio = self.lifetime / self.max_life
        size  = max(1, int(self.size * ratio))
        r, g, b = self.color
        pygame.draw.circle(screen,
                           (int(r * ratio), int(g * ratio), int(b * ratio)),
                           (int(self.x), int(self.y)), size)


class ParticleManager:
    def __init__(self):
        self.particles = []

    def _emit_burst(self, x, y, count, speed_range, size_range, life_range,
                    gravity, color_fn, vy_offset=0.0,
                    angle_range=(0, 2 * math.pi), x_jitter=0):
        for _ in range(count):
            angle = random.uniform(*angle_range)
            speed = random.uniform(*speed_range)
            jx = random.randint(-x_jitter, x_jitter) if x_jitter else 0
            self.particles.append(Particle(
                x + jx, y, color_fn(),
                math.cos(angle) * speed,
                math.sin(angle) * speed + vy_offset,
                random.randint(*size_range),
                random.randint(*life_range),
                gravity=gravity,
            ))

    # ── 착지 먼지 ──────────────────────────────────────────
    def emit_land_dust(self, x, y):
        colors = [(190, 160, 110), (165, 130, 85), (210, 180, 130)]
        self._emit_burst(x, y, 9, (1.5, 4.0), (3, 7), (14, 28), 0.12,
                         lambda: random.choice(colors), vy_offset=-1.0,
                         angle_range=(math.pi, 2 * math.pi), x_jitter=12)

    # ── 젤리 수집 팡 ──────────────────────────────────────
    def emit_collect(self, x, y, color):
        bright = tuple(min(255, int(c * 1.2)) for c in color)
        self._emit_burst(x, y, 7, (2.0, 5.5), (3, 6), (12, 22), 0.15,
                         lambda: bright, vy_offset=-1.5)

    # ── 피격 이펙트 ────────────────────────────────────────
    def emit_hit(self, x, y):
        colors = [(255, 80, 80), (255, 160, 50), (255, 220, 50)]
        self._emit_burst(x, y, 16, (2.5, 8.0), (4, 9), (18, 40), 0.20,
                         lambda: random.choice(colors), vy_offset=-2.5)

    # ── 게임오버 폭발 ──────────────────────────────────────
    def emit_game_over(self, x, y):
        colors = [
            (255,  80,  80), (255, 150,  50), (255, 230,  50),
            (255, 100, 160), (180,  80, 255), (255, 255, 255),
        ]
        self._emit_burst(x, y, 45, (3.0, 13.0), (5, 13), (35, 80), 0.22,
                         lambda: random.choice(colors), vy_offset=-5.0)

    # ── 루프 ──────────────────────────────────────────────
    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)
