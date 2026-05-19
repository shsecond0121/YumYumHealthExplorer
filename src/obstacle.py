import pygame
import random
import math


EASY_PATTERNS = [
    [("spike", 0)],
    [("wide",  0)],
    [("air",   0)],
]
MED_PATTERNS = [
    [("spike", 0), ("spike", 210)],
    [("wide",  0), ("wide",  220)],
    [("air",   0), ("air",   200)],
    [("spike", 0), ("air",   185)],
    [("air",   0), ("spike", 170)],
    [("wide",  0), ("air",   165)],
]
HARD_PATTERNS = [
    [("spike", 0), ("spike", 195), ("spike", 390)],
    [("air",   0), ("spike", 155), ("air",   315)],
    [("spike", 0), ("air",   165), ("spike", 335)],
    [("wide",  0), ("air",   155), ("wide",  335)],
    [("spike", 0), ("wide",  210), ("air",   370)],
]
HARD_MOVING = [
    [("air",   0, True)],
    [("air",   0, True), ("spike", 195)],
    [("spike", 0),       ("air",   180, True)],
    [("air",   0, True), ("air",   245, True)],
    [("wide",  0),       ("air",   170, True)],
    [("air",   0, True), ("spike", 155), ("air", 320, True)],
]

# 미리 합쳐둔 풀 (매 spawn마다 리스트 생성 방지)
_POOL_VEASY      = EASY_PATTERNS
_POOL_EASY       = EASY_PATTERNS + MED_PATTERNS
_POOL_MED        = MED_PATTERNS + HARD_PATTERNS
_POOL_HARD       = HARD_PATTERNS + HARD_MOVING
_POOL_VEASY_LATE = EASY_PATTERNS + HARD_MOVING
_POOL_EASY_LATE  = EASY_PATTERNS + MED_PATTERNS + HARD_MOVING
_POOL_MED_LATE   = MED_PATTERNS + HARD_PATTERNS + HARD_MOVING

_WARN_RANGE = 380


class Obstacle:
    AIR_Y_OFFSET = 90

    def __init__(self, x, ground_y, obstacle_type, moving=False, theme='school'):
        self.type     = obstacle_type
        self.ground_y = ground_y
        self.theme    = theme

        if obstacle_type == "spike":
            self.width, self.height = 32, 75
            self.y = ground_y - self.height
        elif obstacle_type == "wide":
            self.width, self.height = 65, 38
            self.y = ground_y - self.height
        elif obstacle_type == "air":
            self.width, self.height = 55, 50
            self.y = ground_y - self.AIR_Y_OFFSET

        self.x    = float(x)
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)

        self.moving = moving and obstacle_type == "air"
        if self.moving:
            self.base_y     = float(self.y)
            self.move_amp   = random.randint(28, 48)
            self.move_spd   = random.uniform(0.032, 0.052)
            self.move_phase = random.uniform(0, math.pi * 2)

    def update(self, speed):
        self.x -= speed
        self.rect.x = int(self.x)
        if self.moving:
            self.move_phase += self.move_spd
            self.y = self.base_y + math.sin(self.move_phase) * self.move_amp
            self.rect.y = int(self.y)

    # ── 그리기 메인 ───────────────────────────────────────────
    def draw(self, screen):
        if   self.theme == 'school':     self._draw_school(screen)
        elif self.theme == 'street':     self._draw_street(screen)
        elif self.theme == 'playground': self._draw_playground(screen)
        elif self.theme == 'home':       self._draw_home(screen)
        if self.moving:
            self._draw_move_arrows(screen)

    # ── 학교: 선생님 / 책 더미 / 책가방 ──────────────────────
    def _draw_school(self, screen):
        if self.type == 'air':
            self._draw_backpack(screen)
        else:
            self._draw_teacher(screen)

    def _draw_teacher(self, screen):
        r  = self.rect
        x, y = r.x, r.y
        skin  = (255, 215, 180)
        hair  = ( 40,  25,  10)
        shirt = ( 50,  80, 165)
        pants = ( 40,  45,  60)
        shoes = ( 20,  20,  20)
        ptr   = (180, 140,  55)

        if self.type == 'spike':
            cx = x + r.width // 2
            # 머리
            pygame.draw.circle(screen, skin,  (cx, y + 11), 9)
            pygame.draw.rect(screen,   hair,  (cx - 9, y + 2, 18, 7))
            # 안경
            pygame.draw.circle(screen, (60, 60, 60), (cx - 4, y + 11), 3, 1)
            pygame.draw.circle(screen, (60, 60, 60), (cx + 4, y + 11), 3, 1)
            pygame.draw.line(screen, (60, 60, 60), (cx - 1, y + 11), (cx + 1, y + 11), 1)
            # 몸 (셔츠)
            pygame.draw.rect(screen, shirt, (cx - 10, y + 20, 20, 22))
            # 팔
            pygame.draw.rect(screen, skin, (cx - 14, y + 22, 5, 16))
            pygame.draw.rect(screen, skin, (cx +  9, y + 22, 5, 14))
            # 지시봉
            pygame.draw.line(screen, ptr, (cx + 12, y + 22), (cx + 16, y + 6), 2)
            # 바지
            pygame.draw.rect(screen, pants, (cx - 10, y + 42, 20, 20))
            pygame.draw.rect(screen, pants, (cx - 10, y + 62,  8, 10))
            pygame.draw.rect(screen, pants, (cx +  2, y + 62,  8, 10))
            # 신발
            pygame.draw.rect(screen, shoes, (cx - 12, y + 70, 10, 5), border_radius=2)
            pygame.draw.rect(screen, shoes, (cx +  2, y + 70, 10, 5), border_radius=2)

        else:  # wide: 책 더미
            book_colors = [
                (220,  50,  50),
                ( 50, 100, 220),
                ( 50, 180,  80),
                (220, 180,  50),
            ]
            bh = r.height // len(book_colors)
            for i, bc in enumerate(book_colors):
                bx = r.x + (i % 2) * 3
                by = r.y + i * bh
                pygame.draw.rect(screen, bc,
                                 (bx + 1, by + 1, r.width - 4, bh - 2), border_radius=2)
                dark = tuple(max(0, c - 45) for c in bc)
                pygame.draw.line(screen, dark,
                                 (bx + 1, by + bh - 1), (bx + r.width - 4, by + bh - 1), 1)

    def _draw_backpack(self, screen):
        r  = self.rect
        x, y, w, h = r.x, r.y, r.width, r.height
        bag_c  = ( 30,  55, 130)
        strap_c= ( 50,  75, 155)
        pocket = ( 45,  65, 145)
        zip_c  = (200, 185,  80)
        # 본체
        pygame.draw.rect(screen, bag_c,   (x + 4, y + 4, w - 8, h - 4), border_radius=6)
        # 앞 포켓
        pygame.draw.rect(screen, pocket,  (x + 10, y + h//2 + 2, w - 20, h//3), border_radius=3)
        # 지퍼
        pygame.draw.line(screen, zip_c,   (x + 12, y + h//2), (x + w - 12, y + h//2), 2)
        # 손잡이
        pygame.draw.rect(screen, strap_c, (x + w//2 - 7, y, 14, 8), border_radius=3)
        # 어깨끈
        pygame.draw.rect(screen, strap_c, (x +  6, y + 4,  7, h - 10), border_radius=3)
        pygame.draw.rect(screen, strap_c, (x + w - 13, y + 4, 7, h - 10), border_radius=3)

    # ── 길거리: 트래픽콘 / 새 ─────────────────────────────────
    def _draw_street(self, screen):
        if self.type == 'air':
            self._draw_bird(screen)
        else:
            self._draw_traffic_cone(screen)

    def _draw_traffic_cone(self, screen):
        r      = self.rect
        x, y   = r.x, r.y
        orange = (255, 100,  20)
        white  = (255, 255, 255)
        black  = ( 20,  20,  20)

        if self.type == 'spike':
            cx     = x + r.width // 2
            base_h = 12
            cone_h = r.height - base_h
            # 베이스
            pygame.draw.rect(screen, black,
                             (x + 2, r.bottom - base_h, r.width - 4, base_h), border_radius=2)
            # 콘 몸체
            pygame.draw.polygon(screen, orange, [
                (cx,          y),
                (x + 2,       r.bottom - base_h),
                (r.right - 2, r.bottom - base_h),
            ])
            # 흰 줄무늬 1
            r1 = 0.38
            sw1 = int((r.width - 4) * r1)
            pygame.draw.rect(screen, white,
                             (cx - sw1 // 2, y + int(cone_h * r1), sw1, 7))
            # 흰 줄무늬 2
            r2 = 0.62
            sw2 = int((r.width - 4) * r2)
            pygame.draw.rect(screen, white,
                             (cx - sw2 // 2, y + int(cone_h * r2), sw2, 6))

        else:  # wide: 꼬깔콘 2개
            for cx in [x + 17, x + 47]:
                cone_top = y + 2
                cone_bot = r.bottom - 8
                pygame.draw.polygon(screen, orange, [
                    (cx,       cone_top),
                    (cx - 13,  cone_bot),
                    (cx + 13,  cone_bot),
                ])
                sh = cone_top + (cone_bot - cone_top) * 0.5
                sw = int((cone_bot - cone_top) * 0.5 * 0.85)
                pygame.draw.rect(screen, white,
                                 (cx - sw // 2, int(sh), sw, 5))
                pygame.draw.rect(screen, black,
                                 (cx - 13, cone_bot, 26, 8), border_radius=2)

    def _draw_bird(self, screen):
        r  = self.rect
        cx = r.centerx
        cy = r.centery
        bc = (35, 35, 45)

        # 날개 (M자)
        pygame.draw.polygon(screen, bc, [
            (cx - 26, cy + 4), (cx - 16, cy - 13), (cx - 4, cy - 1),
        ])
        pygame.draw.polygon(screen, bc, [
            (cx + 26, cy + 4), (cx + 16, cy - 13), (cx + 4, cy - 1),
        ])
        # 몸통
        pygame.draw.ellipse(screen, bc, (cx - 8, cy - 5, 16, 10))
        # 눈
        pygame.draw.circle(screen, (255, 255, 255), (cx + 3, cy - 2), 3)
        pygame.draw.circle(screen, (10,  10,  10),  (cx + 4, cy - 2), 2)
        # 부리
        pygame.draw.polygon(screen, (255, 180, 0), [
            (cx + 8, cy - 1), (cx + 15, cy + 1), (cx + 8, cy + 3),
        ])
        # 꼬리
        pygame.draw.polygon(screen, bc, [
            (cx - 8, cy), (cx - 16, cy - 5), (cx - 16, cy + 5),
        ])

    # ── 놀이터: 쓰레기통 / 새 ────────────────────────────────
    def _draw_playground(self, screen):
        if self.type == 'air':
            self._draw_bird(screen)
        else:
            self._draw_trash_bin(screen)

    def _draw_trash_bin(self, screen):
        r     = self.rect
        x, y  = r.x, r.y
        bin_c = ( 58,  85,  58)
        lid_c = ( 45,  68,  45)
        bnd_c = ( 48,  70,  48)

        if self.type == 'spike':
            cx = x + r.width // 2
            # 손잡이 (뚜껑 위)
            pygame.draw.arc(screen, bnd_c,
                            (cx - 10, y - 6, 20, 14), 0, math.pi, 3)
            # 뚜껑
            pygame.draw.ellipse(screen, lid_c, (x + 1, y, r.width - 2, 16))
            # 몸체
            pygame.draw.rect(screen, bin_c,
                             (x + 2, y + 8, r.width - 4, r.height - 8), border_radius=3)
            # 가로 밴드
            for i in range(1, 3):
                by = y + 8 + (r.height - 8) * i // 3
                pygame.draw.line(screen, bnd_c, (x + 2, by), (r.right - 2, by), 2)

        else:  # wide: 낮고 넓은 통
            # 뚜껑
            pygame.draw.ellipse(screen, lid_c, (x + 1, y, r.width - 2, 12))
            # 몸체
            pygame.draw.rect(screen, bin_c,
                             (x + 2, y + 6, r.width - 4, r.height - 6), border_radius=3)
            # 가로 밴드
            for by in [y + 18, y + 28]:
                pygame.draw.line(screen, bnd_c, (x + 2, by), (r.right - 2, by), 2)
            # 재활용 원
            pygame.draw.circle(screen, bnd_c, r.center, 9, 2)

    # ── 집: 화분 / 종이비행기 ────────────────────────────────
    def _draw_home(self, screen):
        if self.type == 'air':
            self._draw_paper_plane(screen)
        else:
            self._draw_flowerpot(screen)

    def _draw_flowerpot(self, screen):
        r     = self.rect
        x, y  = r.x, r.y
        pot_c = (185,  85,  35)
        rim_c = (205, 105,  55)
        soil  = ( 75,  50,  25)
        leaf  = ( 55, 158,  55)
        stem  = ( 72, 112,  38)

        if self.type == 'spike':
            cx      = x + r.width // 2
            pot_top = y + 34
            pygame.draw.polygon(screen, pot_c, [
                (x + 3,      pot_top),
                (r.right - 3, pot_top),
                (r.right - 7, r.bottom),
                (x + 7,       r.bottom),
            ])
            pygame.draw.rect(screen, rim_c,
                             (x + 1, pot_top - 5, r.width - 2, 7), border_radius=2)
            pygame.draw.ellipse(screen, soil,
                                (x + 3, pot_top - 4, r.width - 6, 8))
            # 줄기
            pygame.draw.line(screen, stem, (cx, pot_top), (cx - 5, y + 14), 3)
            pygame.draw.line(screen, stem, (cx, pot_top), (cx + 4, y + 10), 3)
            # 잎
            pygame.draw.ellipse(screen, leaf, (cx - 20, y + 5,  22, 18))
            pygame.draw.ellipse(screen, leaf, (cx - 4,  y,      22, 18))
            pygame.draw.ellipse(screen, leaf, (cx - 13, y + 18, 20, 14))

        else:  # wide: 낮고 넓은 화분 + 다육
            cx      = x + r.width // 2
            pot_top = y + 17
            pygame.draw.polygon(screen, pot_c, [
                (x + 4,       pot_top),
                (r.right - 4, pot_top),
                (r.right - 8, r.bottom),
                (x + 8,       r.bottom),
            ])
            pygame.draw.rect(screen, rim_c,
                             (x + 2, pot_top - 5, r.width - 4, 7), border_radius=2)
            pygame.draw.ellipse(screen, soil,
                                (x + 5, pot_top - 4, r.width - 10, 8))
            for deg in range(-50, 60, 22):
                angle = math.radians(deg)
                ex = cx + int(math.cos(angle) * 22)
                ey = pot_top - 4 - int(abs(math.sin(angle)) * 8)
                pygame.draw.ellipse(screen, leaf, (ex - 10, ey - 6, 18, 12))

    def _draw_paper_plane(self, screen):
        r  = self.rect
        cx, cy = r.centerx, r.centery
        w_c = (248, 248, 255)
        f_c = (180, 180, 210)
        e_c = (148, 148, 188)
        nose = (r.right - 3, cy)
        top  = (r.x + 4,     cy - 15)
        bot  = (r.x + 4,     cy + 15)
        mid  = (cx - 2,      cy)
        # 위쪽 날개
        pygame.draw.polygon(screen, w_c,           [nose, top, mid])
        # 아래쪽 날개
        pygame.draw.polygon(screen, (232, 232, 252), [nose, mid, bot])
        # 접힘 선
        pygame.draw.line(screen, e_c, nose, (r.x + 4, cy), 1)
        pygame.draw.line(screen, f_c, top, mid, 1)
        # 꼬리 삼각형
        pygame.draw.polygon(screen, f_c,
                            [(r.x + 4, cy - 15), (r.x + 4, cy + 15), (r.x + 14, cy)])

    # ── 이동 화살표 (moving air 장애물) ──────────────────────
    def _draw_move_arrows(self, screen):
        cx  = self.rect.centerx
        c   = (255, 255, 180)
        ty  = self.rect.y - 5
        by_ = self.rect.bottom + 5
        pygame.draw.polygon(screen, c, [(cx, ty - 6), (cx - 5, ty), (cx + 5, ty)])
        pygame.draw.polygon(screen, c, [(cx, by_ + 6), (cx - 5, by_), (cx + 5, by_)])

class ObstacleManager:
    def __init__(self, screen_width, ground_y):
        self.screen_width   = screen_width
        self.ground_y       = ground_y
        self.obstacles      = []
        self.spawn_timer    = 0
        self.spawn_interval = 150
        self.current_theme  = 'school'

    def set_theme(self, theme):
        self.current_theme = theme

    def _pick_pattern(self, speed, distance=0.0):
        late = distance >= 400 and speed < 13
        if speed < 7:
            pool = _POOL_VEASY_LATE if late else _POOL_VEASY
        elif speed < 11:
            pool = _POOL_EASY_LATE if late else _POOL_EASY
        elif speed < 13:
            pool = _POOL_MED_LATE if late else _POOL_MED
        else:
            pool = _POOL_HARD
        return random.choice(pool)

    def update(self, speed, distance=0.0):
        self.spawn_timer  += 1
        self.spawn_interval = max(62, int(160 - speed * 7))

        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            pattern = self._pick_pattern(speed, distance)
            base_x  = self.screen_width + 60
            for entry in pattern:
                kind, offset = entry[0], entry[1]
                moving = entry[2] if len(entry) > 2 else False
                self.obstacles.append(
                    Obstacle(base_x + offset, self.ground_y,
                             kind, moving=moving, theme=self.current_theme)
                )

        for obs in self.obstacles:
            obs.update(speed)

        self.obstacles = [o for o in self.obstacles if o.x > -130]

    def check_collision(self, player_rect):
        shrunk = player_rect.inflate(-10, -10)
        for obs in self.obstacles:
            if shrunk.colliderect(obs.rect):
                return True
        return False

    def get_incoming_warnings(self):
        warnings = []
        for obs in self.obstacles:
            if obs.type == 'air':
                dist_from_edge = obs.x - self.screen_width
                if 0 <= dist_from_edge < _WARN_RANGE:
                    ratio = 1.0 - dist_from_edge / _WARN_RANGE
                    warnings.append({'y': int(obs.y + obs.height // 2), 'ratio': ratio})
        return warnings

    def draw(self, screen):
        for obs in self.obstacles:
            obs.draw(screen)
