import pygame
import math

# 캐릭터 색상
_SKIN   = (255, 210, 165)
_HAIR   = (30,  22,  12)
_COLLAR = (230, 230, 242)   # 흰 카라
_SHOE   = (36,  28,  18)    # 검정 신발
_BAG    = (105,  62,  20)   # 갈색 책가방
_BAG_P  = ( 75,  44,  10)   # 가방 주머니
_STRAP  = (130,  78,  28)   # 가방 어깨끈
_EYE    = (40,  25,  10)    # 눈동자

# 이스터에그: 타이틀 7회 클릭 → 다음 게임부터 교복 색 사이클
# (shirt, pants) 7쌍. 0번이 기본 남색.
OUTFITS = [
    ((50,  60, 115), ( 32,  42,  82)),   # 0. 남색 (기본)
    ((220, 120, 150), (165,  75, 105)),  # 1. 핑크
    ((70,  140,  90), ( 45,  95,  60)),  # 2. 초록
    ((180,  60,  60), (130,  40,  40)),  # 3. 빨강
    ((130,  90, 170), ( 90,  55, 125)),  # 4. 보라
    ((230, 140,  55), (175,  95,  30)),  # 5. 주황
    (( 65, 155, 160), ( 40, 110, 115)),  # 6. 청록
]


def cycle_outfit():
    Player.outfit_idx = (Player.outfit_idx + 1) % len(OUTFITS)


class Player:
    outfit_idx = 0   # 클래스 레벨 — 모든 인스턴스가 공유 (게임 간 유지)

    STAND_H = 55
    SLIDE_H = 22
    WIDTH   = 45
    MAX_HP  = 3
    INVINCIBLE_FRAMES = 120  # 2초
    SLIDE_DURATION = 50

    def __init__(self, x, ground_y):
        self.ground_y = ground_y
        self.x        = x
        self.width    = self.WIDTH
        self.height   = float(self.STAND_H)
        self.y        = float(ground_y - self.STAND_H)

        self.vel_y    = 0.0
        self.gravity  = 0.75
        self.jump_force = -17.0
        self.jumps_left = 2
        self.on_ground  = True
        self.is_double_jumping = False

        self.sliding      = False
        self.slide_timer  = 0
        self.slide_held   = False

        self.hp         = self.MAX_HP
        self.invincible = 0
        self.alive      = True

        self.run_frame      = 0
        self.frame_timer    = 0
        self.just_landed    = False
        self._slide_buffered = False

        # 디버프/버프로 외부에서 갱신되는 배율·플래그 (game.py가 매 프레임 set)
        self.jump_force_mult     = 1.0
        self.slide_dur_mult      = 1.0
        self.double_jump_blocked = False
        self.slide_blocked       = False

        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, int(self.height))

        # 방어막 오라/더블점프 이펙트 — alpha만 매 프레임 변하므로
        # base Surface 한 번만 만들고 set_alpha로 펄스 (Surface 재할당 회피)
        aw, ah = self.WIDTH + 34, self.STAND_H + 34
        self._aura_surf = pygame.Surface((aw, ah), pygame.SRCALPHA)
        pygame.draw.ellipse(self._aura_surf, (80, 180, 255), (0, 0, aw, ah))
        jw = self.WIDTH + 20
        self._jump_surf = pygame.Surface((jw, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(self._jump_surf, (255, 200, 50), (0, 0, jw, 18))

    # ── 조작 ──────────────────────────────────────────────
    def jump(self):
        if self.jumps_left > 0:
            is_double = (self.jumps_left == 1)
            # dizzy 디버프: 더블점프 봉인
            if is_double and self.double_jump_blocked:
                return False, False
            self.vel_y      = self.jump_force * self.jump_force_mult
            self.jumps_left -= 1
            self.on_ground  = False
            self.is_double_jumping = is_double
            if self.sliding:
                self.sliding     = False
                self.slide_timer = 0
                self.height      = float(self.STAND_H)
            return True, is_double
        return False, False

    def _slide_duration(self):
        return max(8, int(self.SLIDE_DURATION * self.slide_dur_mult))

    def slide(self):
        if self.slide_blocked:
            self._slide_buffered = False
            return
        if self.on_ground:
            self._slide_buffered = False
            self.sliding     = True
            self.slide_timer = self._slide_duration()
            self.height      = float(self.SLIDE_H)
            self.y           = float(self.ground_y - self.SLIDE_H)
        else:
            self._slide_buffered = True

    def end_slide(self):
        self._slide_buffered = False
        if self.sliding:
            self.sliding     = False
            self.slide_timer = 0
            self.height      = float(self.STAND_H)
            self.y           = float(self.ground_y - self.STAND_H)

    def take_hit(self):
        if self.invincible > 0:
            return False
        self.hp -= 1
        self.invincible = self.INVINCIBLE_FRAMES
        if self.hp <= 0:
            self.alive = False
        return True

    # ── 업데이트 ───────────────────────────────────────────
    def update(self):
        # 슬라이드 봉인 시 버퍼 자동 비움
        if self.slide_blocked:
            self._slide_buffered = False
            if self.sliding:
                self.sliding     = False
                self.slide_timer = 0
                self.height      = float(self.STAND_H)
                self.y           = float(self.ground_y - self.STAND_H)
        was_on_ground = self.on_ground

        if self.sliding and not self.slide_held:
            self.slide_timer -= 1
            if self.slide_timer <= 0:
                self.sliding = False
                self.height  = float(self.STAND_H)

        if not (self.sliding and self.on_ground):
            self.vel_y += self.gravity
            self.y     += self.vel_y

        floor = float(self.ground_y - self.height)
        if self.y >= floor:
            self.y          = floor
            self.vel_y      = 0.0
            self.jumps_left = 2
            self.is_double_jumping = False
            self.just_landed = not was_on_ground
            self.on_ground   = True
            if self._slide_buffered:
                self._slide_buffered = False
                self.sliding     = True
                self.slide_timer = self._slide_duration()
                self.height      = float(self.SLIDE_H)
                self.y           = float(self.ground_y - self.SLIDE_H)
        else:
            self.just_landed = False
            self.on_ground   = False

        if self.invincible > 0:
            self.invincible -= 1

        self.rect.update(int(self.x), int(self.y), self.width, int(self.height))

        if self.on_ground and not self.sliding:
            self.frame_timer += 1
            if self.frame_timer >= 8:
                self.run_frame   = (self.run_frame + 1) % 4
                self.frame_timer = 0

    # ── 그리기 ─────────────────────────────────────────────
    def draw(self, screen, shield_active=False):
        if self.invincible > 0 and (self.invincible // 5) % 2 == 1:
            return

        x = int(self.x)
        y = int(self.y)
        w = self.width
        h = int(self.height)

        # 방어막 오라
        if shield_active:
            t = pygame.time.get_ticks()
            self._aura_surf.set_alpha(int(110 + 70 * math.sin(t * 0.006)))
            screen.blit(self._aura_surf, (x - 17, y - 17))

        if self.sliding:
            self._draw_slide(screen, x, y, w, h)
        else:
            self._draw_stand(screen, x, y, w, h)

        # 더블점프 이펙트
        if self.is_double_jumping:
            self._jump_surf.set_alpha(int(abs(math.sin(pygame.time.get_ticks() * 0.01)) * 180))
            screen.blit(self._jump_surf, (x - 10, y + h))

    def _draw_stand(self, screen, x, y, w, h):
        # 신발 x 오프셋으로 달리기 표현 (앞다리, 뒷다리)
        # (front_shoe_dx, back_shoe_dx)
        shoe_frames = [(-4, 3), (-1, 0), (3, -4), (-1, 0)]
        fsx, bsx = shoe_frames[self.run_frame]
        _SHIRT, _PANTS = OUTFITS[Player.outfit_idx]

        # ── 뒷다리 (먼저 그려서 몸통 뒤에 깔림) ──
        pygame.draw.rect(screen, _PANTS,
                         (x + 22, y + h - 15, 10, 11), border_radius=3)
        pygame.draw.rect(screen, _SHOE,
                         (x + 21 + bsx, y + h - 6, 13, 6), border_radius=3)

        # ── 책가방 (등/왼쪽) ──
        pygame.draw.rect(screen, _BAG,
                         (x + 2, y + 21, 11, 21), border_radius=4)
        pygame.draw.rect(screen, _BAG_P,
                         (x + 3, y + 32,  9,  7), border_radius=3)
        # 어깨끈
        pygame.draw.line(screen, _STRAP,
                         (x + 12, y + 23), (x + 14, y + 37), 3)

        # ── 몸통 (교복 상의) ──
        pygame.draw.rect(screen, _SHIRT,
                         (x + 12, y + 22, 22, 16), border_radius=5)
        # 카라 (흰 넥타이/카라)
        pygame.draw.rect(screen, _COLLAR,
                         (x + 21, y + 22, 8, 5), border_radius=2)

        # ── 앞다리 ──
        pygame.draw.rect(screen, _PANTS,
                         (x + 14, y + h - 15, 10, 11), border_radius=3)
        pygame.draw.rect(screen, _SHOE,
                         (x + 13 + fsx, y + h - 6, 13, 6), border_radius=3)

        # ── 머리 (피부) ──
        hx, hy, hr = x + 24, y + 12, 11
        pygame.draw.circle(screen, _SKIN, (hx, hy), hr)

        # ── 머리카락 (상단을 덮는 폴리곤) ──
        hair_pts = [
            (hx - hr,      hy),
            (hx - hr + 2,  hy - 5),
            (hx - 5,       hy - hr + 1),
            (hx,           hy - hr - 1),
            (hx + 5,       hy - hr + 1),
            (hx + hr - 2,  hy - 5),
            (hx + hr,      hy),
        ]
        pygame.draw.polygon(screen, _HAIR, hair_pts)

        # ── 눈·입 ──
        eye_dy = -1 if not self.on_ground else 0
        if self.invincible > 0:
            # 슬픈 눈썹 (안쪽이 위로 올라간 형태)
            pygame.draw.line(screen, _HAIR,
                             (x + 16, y + 9 + eye_dy), (x + 22, y + 7 + eye_dy), 2)
            pygame.draw.line(screen, _HAIR,
                             (x + 26, y + 7 + eye_dy), (x + 32, y + 9 + eye_dy), 2)
            # 눈물 맺힌 눈
            for ex in (x + 20, x + 29):
                pygame.draw.circle(screen, (255, 255, 255), (ex, y + 13 + eye_dy), 5)
                pygame.draw.circle(screen, (200, 185, 170), (ex, y + 13 + eye_dy), 5, 1)
                pygame.draw.circle(screen, _EYE,            (ex, y + 13 + eye_dy), 3)
                pygame.draw.circle(screen, (255, 255, 255), (ex + 1, y + 11 + eye_dy), 1)
                pygame.draw.circle(screen, (160, 215, 255), (ex - 1, y + 18 + eye_dy), 2)
            # 슬픈 입 (뒤집힌 호)
            pygame.draw.arc(screen, (195, 105, 80),
                            (x + 18, y + 18, 12, 5), 0, math.pi, 2)
        else:
            for ex in (x + 20, x + 29):
                pygame.draw.circle(screen, (255, 255, 255), (ex, y + 13 + eye_dy), 5)
                pygame.draw.circle(screen, (200, 185, 170), (ex, y + 13 + eye_dy), 5, 1)
                pygame.draw.circle(screen, _EYE,            (ex, y + 13 + eye_dy), 3)
                pygame.draw.circle(screen, (255, 255, 255), (ex + 1, y + 11 + eye_dy), 1)
            pygame.draw.arc(screen, (195, 105, 80),
                            (x + 18, y + 16, 12, 6), math.pi, 0, 2)

        # ── 팔 (뛰는 동작) ──
        arm_anim = [(4, 2), (1, 5), (-3, 2), (1, 5)]
        adx, ady = arm_anim[self.run_frame]
        pygame.draw.line(screen, _SHIRT,
                         (x + 30, y + 27), (x + 30 + adx, y + 29 + ady), 6)
        pygame.draw.circle(screen, _SKIN, (x + 31 + adx, y + 30 + ady), 4)

    def _draw_slide(self, screen, x, y, w, h):
        # h = 22 (SLIDE_H): 몸을 낮추고 앞으로 숙인 슬라이딩 포즈
        _SHIRT, _PANTS = OUTFITS[Player.outfit_idx]

        # ── 뒷다리 (왼쪽으로 뻗음) ──
        pygame.draw.rect(screen, _PANTS,
                         (x - 6, y + 10, 22, 9), border_radius=3)
        pygame.draw.rect(screen, _SHOE,
                         (x - 8, y + 15, 13, 6), border_radius=2)

        # ── 책가방 (등 위) ──
        pygame.draw.rect(screen, _BAG,
                         (x + 4, y,     17, 13), border_radius=4)
        pygame.draw.rect(screen, _BAG_P,
                         (x + 5, y + 8, 14,  4), border_radius=2)

        # ── 몸통 ──
        pygame.draw.ellipse(screen, _SHIRT, (x + 9, y + 4, 26, 14))
        pygame.draw.rect(screen, _COLLAR,   (x + 24, y + 4, 7, 4), border_radius=2)

        # ── 앞다리 (앞으로 뻗음) ──
        pygame.draw.rect(screen, _PANTS,
                         (x + 24, y + 11, 19, 9), border_radius=3)
        pygame.draw.rect(screen, _SHOE,
                         (x + 37, y + 15, 11, 6), border_radius=2)

        # ── 머리 ──
        hx, hy = x + 38, y + 8
        pygame.draw.circle(screen, _SKIN, (hx, hy), 9)

        hair_pts = [
            (hx - 9, hy),     (hx - 7, hy - 5),
            (hx - 2, hy - 9), (hx + 3, hy - 8),
            (hx + 7, hy - 4), (hx + 9, hy),
        ]
        pygame.draw.polygon(screen, _HAIR, hair_pts)

        # ── 눈 (흰자 + 눈동자) ──
        if self.invincible > 0:
            pygame.draw.line(screen, _HAIR, (hx - 8, hy - 3), (hx - 2, hy - 5), 2)
            pygame.draw.line(screen, _HAIR, (hx + 3, hy - 5), (hx + 9, hy - 3), 2)
            for ex in (hx - 1, hx + 5):
                pygame.draw.circle(screen, (255, 255, 255), (ex, hy + 1), 4)
                pygame.draw.circle(screen, (200, 185, 170), (ex, hy + 1), 4, 1)
                pygame.draw.circle(screen, _EYE,            (ex, hy + 1), 2)
                pygame.draw.circle(screen, (255, 255, 255), (ex + 1, hy), 1)
                pygame.draw.circle(screen, (160, 215, 255), (ex, hy + 5), 2)
            pygame.draw.arc(screen, (195, 105, 80),
                            (hx - 4, hy + 3, 9, 4), 0, math.pi, 1)
        else:
            for ex in (hx - 1, hx + 5):
                pygame.draw.circle(screen, (255, 255, 255), (ex, hy + 1), 4)
                pygame.draw.circle(screen, (200, 185, 170), (ex, hy + 1), 4, 1)
                pygame.draw.circle(screen, _EYE,            (ex, hy + 1), 2)
                pygame.draw.circle(screen, (255, 255, 255), (ex + 1, hy), 1)
