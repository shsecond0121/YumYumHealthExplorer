import pygame
import random
import math


# ── 테마 정의 ─────────────────────────────────────────────────
THEMES = [
    {
        'name':        '학교',
        'dist':        0,
        'sky_top':     (195, 195, 202),   # 실내 회색 벽
        'sky_bot':     (182, 182, 190),
        'ground':      (148, 140, 132),   # 학교 복도 바닥
        'ground_hi':   (165, 158, 150),
        'ground_dark': (118, 110, 102),
        'hill':        (155, 148, 142),   # 창틀 색 (벽보다 약간 어두움)
        'cloud':       None,              # 실내 - 구름 없음
        'indoor':      True,
        'deco':        'school',
    },
    {
        'name':        '길거리',
        'dist':        300,
        'sky_top':     ( 55, 138, 218),
        'sky_bot':     (115, 182, 245),
        'ground':      ( 72,  72,  78),
        'ground_hi':   ( 88,  88,  94),
        'ground_dark': ( 52,  52,  58),
        'hill':        ( 85,  80,  75),
        'cloud':       (252, 253, 255),
        'indoor':      False,
        'deco':        'street',
    },
    {
        'name':        '놀이터',
        'dist':        700,
        'sky_top':     ( 65,  18,  88),
        'sky_bot':     (255, 128,  18),
        'ground':      (182, 145,  70),
        'ground_hi':   (208, 172,  98),
        'ground_dark': (148, 115,  48),
        'hill':        ( 75,  42,  28),
        'cloud':       (255, 158,  68),
        'indoor':      False,
        'deco':        'playground',
    },
    {
        'name':        '집',
        'dist':        1200,
        'sky_top':     (245, 232, 198),
        'sky_bot':     (232, 218, 182),
        'ground':      (152, 102,  52),
        'ground_hi':   (178, 128,  72),
        'ground_dark': (118,  78,  36),
        'hill':        ( 98,  68,  38),
        'cloud':       None,
        'indoor':      True,
        'deco':        'home',
    },
]

_TRANS_FRAMES = 120
STAGE_LENGTH  = 100   # 스테이지 전환 거리 (약 33초 @ 초기 속도)
_LOCKER_W     = 52
_LOCKER_H     = 78
_LOCKER_ROWS  = 2


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _make_window_sky(w, h, cloud_data, cloud_count=None):
    sky_top = (155, 205, 255)
    sky_bot = (215, 238, 255)
    surf = pygame.Surface((w, h))
    for y in range(h):
        c = _lerp_color(sky_top, sky_bot, y / h)
        pygame.draw.line(surf, c, (0, y), (w, y))
    selected = random.sample(cloud_data, cloud_count) if cloud_count is not None else cloud_data
    for cx, cy, cw, ch in selected:
        cs = pygame.Surface((cw + 20, ch + 12), pygame.SRCALPHA)
        pygame.draw.ellipse(cs, (240, 245, 255, 210), (5, 4, cw, ch))
        pygame.draw.ellipse(cs, (240, 245, 255, 190), (10, 1, cw - 12, ch - 4))
        surf.blit(cs, (cx - cw // 2, cy - ch // 2))
    return surf


# ── 구름 ──────────────────────────────────────────────────────
class Cloud:
    def __init__(self, x, y, speed_factor, alpha):
        self.x            = float(x)
        self.y            = y
        self.speed_factor = speed_factor
        self.w            = random.randint(70, 140)
        self.h            = random.randint(28, 50)
        self.alpha        = alpha
        # 구름 외형은 인스턴스 단위로 고정 — 한 번만 렌더해서 캐시.
        # 색상별 캐시는 dict (sky/노을 등 색상이 바뀌면 재생성).
        self._surf_cache = {}

    def update(self, game_speed):
        self.x -= self.speed_factor * (game_speed / 5.0)

    def _surf_for(self, color):
        s = self._surf_cache.get(color)
        if s is None:
            c = (*color, self.alpha)
            s = pygame.Surface((self.w + 40, self.h + 22), pygame.SRCALPHA)
            pygame.draw.ellipse(s, c, (10,  12, self.w,         self.h))
            pygame.draw.ellipse(s, c, (22,   2, self.w - 22,    self.h - 6))
            pygame.draw.ellipse(s, c, (self.w // 2 - 5, 6, 48, self.h - 10))
            self._surf_cache[color] = s
        return s

    def draw(self, screen, color=(240, 245, 255)):
        screen.blit(self._surf_for(color), (int(self.x), self.y))


# ── 배경 장식 오브젝트 ─────────────────────────────────────────
class Deco:
    SPEED = 0.25

    def __init__(self, x, ground_y, theme):
        self.x        = float(x)
        self.ground_y = ground_y
        self.theme    = theme
        self._setup()

    # ── 초기화 ────────────────────────────────────────────────
    def _setup(self):
        self.speed_factor = 0.25   # 기본 스크롤 속도
        if self.theme == 'school':
            self.speed_factor = 1.0  # 학교 창문은 빠르게 이동
            # 사물함 상단(locker_top = ground_y - 156)보다 위에 맞춤
            locker_top = self.ground_y - _LOCKER_H * _LOCKER_ROWS
            max_h      = locker_top - 40   # 사물함 상단과 충분한 여백 확보
            self.win_w = random.randint(200, 260)
            self.win_h = random.randint(min(110, max_h), min(145, max_h))
            self._win_surf = self._make_school_sky(self.win_w, self.win_h)

        elif self.theme == 'street':
            self.kind = random.choices(['building', 'tree'], weights=[6, 4])[0]
            if self.kind == 'building':
                self.w        = random.randint(58, 115)
                self.h        = random.randint(115, 205)
                self.win_cols = random.randint(1, 3)
                self.win_rows = random.randint(3, 6)
            else:
                self.trunk_h = random.randint(45, 78)
                self.trunk_w = random.randint(12, 20)
                self.crown_r = random.randint(28, 46)

        elif self.theme == 'playground':
            self.kind  = random.choice(['swing', 'slide', 'bench'])
            self.scale = random.uniform(0.85, 1.15)

        elif self.theme == 'home':
            self.kind = random.choices(
                ['fridge', 'washer'], weights=[5, 5]
            )[0]
            if self.kind == 'fridge':
                self.w = random.randint(52, 68)
                self.h = random.randint(118, 148)
            else:  # washer
                self.w = random.randint(64, 80)
                self.h = random.randint(72, 92)

    def _make_school_sky(self, w, h):
        cloud_data = [
            (int(w * 0.20), int(h * 0.24), 48, 18),
            (int(w * 0.60), int(h * 0.36), 62, 22),
            (int(w * 0.40), int(h * 0.14), 40, 14),
        ]
        return _make_window_sky(w, h, cloud_data, random.randint(1, 3))

    # ── 업데이트 ──────────────────────────────────────────────
    def update(self, speed):
        self.x -= self.speed_factor * (speed / 5.0)

    # ── 그리기 디스패치 ───────────────────────────────────────
    def draw(self, screen, color):
        ix, gy = int(self.x), self.ground_y
        if   self.theme == 'school':     self._draw_school(screen, ix, gy, color)
        elif self.theme == 'street':     self._draw_street(screen, ix, gy)
        elif self.theme == 'playground': self._draw_playground(screen, ix, gy, color)
        elif self.theme == 'home':       self._draw_home(screen, ix, gy, color)

    # ── 학교 (교실 창문) ──────────────────────────────────────
    def _draw_school(self, screen, x, gy, color):
        locker_top = gy - _LOCKER_H * _LOCKER_ROWS
        wy = max(10, locker_top - self.win_h - 30)    # 사물함 상단에서 30px 위에 창문 하단 배치
        fc = tuple(max(0, c - 30) for c in color)
        pygame.draw.rect(screen, fc,
                         (x - 4, wy - 4, self.win_w + 18, self.win_h + 18),
                         border_radius=4)
        screen.blit(self._win_surf, (x + 5, wy + 5))
        mid_x = x + 5 + self.win_w // 2
        mid_y = wy + 5 + self.win_h // 2
        pygame.draw.line(screen, fc, (mid_x, wy + 5), (mid_x, wy + 5 + self.win_h), 5)
        pygame.draw.line(screen, fc, (x + 5, mid_y), (x + 5 + self.win_w, mid_y), 5)

    # ── 길거리 (빌딩 회청색 / 가로수 녹색, 색상 분리) ─────────
    def _draw_street(self, screen, x, gy):
        if self.kind == 'building':
            bc = (62,  68,  82)     # 빌딩: 짙은 회청색
            wc = (105, 120, 148)    # 창문: 약간 밝은 회색
            pygame.draw.rect(screen, bc, (x, gy - self.h, self.w, self.h))
            ww = max(7, (self.w - 14) // max(1, self.win_cols) - 4)
            wh = max(8, (self.h - 25) // max(1, self.win_rows) - 5)
            for row in range(self.win_rows):
                for col in range(self.win_cols):
                    wx = x + 7  + col * (ww + 5)
                    wy = gy - self.h + 14 + row * (wh + 5)
                    pygame.draw.rect(screen, wc, (wx, wy, ww, wh))
        else:
            tc = (55,  38,  18)     # 기둥: 짙은 갈색
            cc = (32,  78,  42)     # 수관: 짙은 녹색
            tx = x + self.crown_r - self.trunk_w // 2
            pygame.draw.rect(screen, tc,
                             (tx, gy - self.trunk_h, self.trunk_w, self.trunk_h))
            pygame.draw.circle(screen, cc,
                               (x + self.crown_r, gy - self.trunk_h), self.crown_r)

    # ── 놀이터 기구 ──────────────────────────────────────────
    def _draw_playground(self, screen, x, gy, color):
        s = self.scale
        if self.kind == 'swing':
            ph = int(75 * s); pw = int(60 * s)
            pygame.draw.line(screen, color, (x + 8,      gy), (x + 22,      gy - ph), 4)
            pygame.draw.line(screen, color, (x + pw - 8, gy), (x + pw - 22, gy - ph), 4)
            pygame.draw.line(screen, color,
                             (x + 22, gy - ph), (x + pw - 22, gy - ph), 4)
            mx   = x + pw // 2
            rope = int(40 * s)
            pygame.draw.line(screen, color, (mx - 8, gy - ph), (mx - 8, gy - ph + rope), 2)
            pygame.draw.line(screen, color, (mx + 8, gy - ph), (mx + 8, gy - ph + rope), 2)
            pygame.draw.rect(screen, color, (mx - 10, gy - ph + rope, 20, 5))
        elif self.kind == 'slide':
            sh = int(78 * s)
            pygame.draw.rect(screen, color, (x + 5, gy - sh, 8, sh))
            pygame.draw.polygon(screen, color, [
                (x + 13,        gy - sh),
                (x + int(72*s), gy - 16),
                (x + int(72*s), gy),
                (x + 13,        gy - sh + 16),
            ])
            pygame.draw.rect(screen, color, (x + 3, gy - sh - 7, 22, 9))
        else:
            bw = int(90 * s)
            pygame.draw.rect(screen, color, (x,          gy - 26, bw, 7))
            pygame.draw.rect(screen, color, (x,          gy - 44, bw, 7))
            pygame.draw.rect(screen, color, (x,          gy - 44,  7, 44))
            pygame.draw.rect(screen, color, (x + bw - 7, gy - 44,  7, 44))

    # ── 집 (냉장고/세탁기) ──────────────────────────────────────
    def _draw_home(self, screen, x, gy, color):
        if self.kind == 'fridge':
            self._draw_fridge(screen, x, gy)
        else:
            self._draw_washer(screen, x, gy)

    def _draw_fridge(self, screen, x, gy):
        w, h      = self.w, self.h
        body      = (238, 240, 242)
        trim      = (175, 180, 185)
        hdl       = (140, 145, 150)
        freeze_h  = h // 3

        pygame.draw.rect(screen, body, (x, gy - h, w, h), border_radius=3)
        pygame.draw.rect(screen, trim, (x, gy - h, w, h), border_radius=3, width=2)
        # 냉동실·냉장실 구분선
        pygame.draw.line(screen, trim,
                         (x + 2, gy - h + freeze_h), (x + w - 2, gy - h + freeze_h), 2)
        # 손잡이 (냉동실)
        pygame.draw.rect(screen, hdl,
                         (x + w - 10, gy - h + 8, 4, freeze_h - 16), border_radius=2)
        # 손잡이 (냉장실)
        pygame.draw.rect(screen, hdl,
                         (x + w - 10, gy - h + freeze_h + 8, 4, h - freeze_h - 20),
                         border_radius=2)
        # 상단 디스플레이
        pygame.draw.rect(screen, trim, (x + 5, gy - h + 5, w - 15, 8), border_radius=2)

    def _draw_washer(self, screen, x, gy):
        w, h     = self.w, self.h
        body     = (238, 240, 242)
        trim     = (175, 180, 185)
        panel_c  = (215, 218, 222)
        drum_c   = ( 90, 130, 195)
        glass_c  = (165, 205, 242)
        panel_h  = h // 5

        pygame.draw.rect(screen, body, (x, gy - h, w, h), border_radius=3)
        pygame.draw.rect(screen, trim, (x, gy - h, w, h), border_radius=3, width=2)
        # 컨트롤 패널
        pygame.draw.rect(screen, panel_c, (x, gy - h, w, panel_h), border_radius=3)
        pygame.draw.line(screen, trim,
                         (x + 1, gy - h + panel_h), (x + w - 1, gy - h + panel_h), 1)
        # 다이얼 노브
        kx, ky = x + w // 2, gy - h + panel_h // 2
        pygame.draw.circle(screen, trim, (kx, ky), 7)
        pygame.draw.circle(screen, body, (kx, ky), 5)
        pygame.draw.line(screen, trim, (kx, ky - 5), (kx, ky - 2), 2)
        # 드럼 원형 창문
        drum_cx = x + w // 2
        drum_cy = gy - h + panel_h + (h - panel_h) // 2
        drum_r  = min(w // 2, (h - panel_h) // 2) - 7
        pygame.draw.circle(screen, trim,   (drum_cx, drum_cy), drum_r + 3)
        pygame.draw.circle(screen, drum_c, (drum_cx, drum_cy), drum_r)
        pygame.draw.circle(screen, glass_c,
                           (drum_cx - drum_r // 3, drum_cy - drum_r // 3), drum_r // 3)


# ── 배경 전체 ─────────────────────────────────────────────────
class Background:

    def __init__(self, width, height, ground_y):
        self.width        = width
        self.height       = height
        self.ground_y     = ground_y
        self.tile_offset  = 0.0
        self.tile_size    = 64
        self._lane_off    = 0.0
        self._wall_off    = 0.0   # 사물함 스크롤 오프셋

        self._theme_idx      = 0
        self._trans_timer    = 0
        self._next_theme     = None
        self._next_trans_dist = STAGE_LENGTH
        self._sky_surface    = None
        self._sky_cache_key  = None

        self.clouds_far  = [
            Cloud(random.randint(0, width), random.randint(15, 90),
                  speed_factor=0.30, alpha=140)
            for _ in range(4)
        ]
        self.clouds_near = [
            Cloud(random.randint(0, width), random.randint(80, 170),
                  speed_factor=0.70, alpha=210)
            for _ in range(3)
        ]
        self.decos = []

        # 학교/집 고정 창문 (Deco 시스템 사용 안 함)
        self._school_win_surf = self._make_school_win_surf(440, 145)
        self._home_win_stars  = [
            (random.randint(4, 106), random.randint(4, 96),
             random.randint(160, 255))
            for _ in range(14)
        ]

    # ── 현재 테마 이름 ────────────────────────────────────────
    @property
    def current_theme(self):
        return THEMES[self._theme_idx]['deco']

    # ── 색상 보간 ─────────────────────────────────────────────
    def _get_colors(self):
        cur = THEMES[self._theme_idx]
        if self._trans_timer == 0 or self._next_theme is None:
            return cur
        nxt = self._next_theme
        t   = self._trans_timer / _TRANS_FRAMES
        res = {}
        for k in ('sky_top', 'sky_bot', 'ground', 'ground_hi', 'ground_dark', 'hill'):
            res[k] = _lerp_color(cur[k], nxt[k], t)
        cc, nc = cur.get('cloud'), nxt.get('cloud')
        if cc and nc:
            res['cloud'] = _lerp_color(cc, nc, t)
        else:
            res['cloud'] = cc if t < 0.5 else nc
        res['indoor'] = nxt.get('indoor', False) if t >= 0.5 else cur.get('indoor', False)
        res['deco']   = cur['deco']
        return res

    # ── 업데이트 ──────────────────────────────────────────────
    def update(self, speed, distance=0.0):
        self.tile_offset = (self.tile_offset + speed)       % self.tile_size
        self._lane_off   = (self._lane_off   + speed)       % 120
        self._wall_off   = (self._wall_off   + speed / 20.0) % _LOCKER_W

        if self._trans_timer == 0:
            if distance >= self._next_trans_dist:
                self._trans_timer = 1
                self._next_theme  = THEMES[(self._theme_idx + 1) % len(THEMES)]
                self.decos        = []   # 전환 시작 즉시 잔상 제거

        if self._trans_timer > 0:
            self._trans_timer += 1
            if self._trans_timer >= _TRANS_FRAMES:
                self._theme_idx       = (self._theme_idx + 1) % len(THEMES)
                self._trans_timer     = 0
                self._next_theme      = None
                self.decos            = []
                self._next_trans_dist += STAGE_LENGTH

        cur_deco = THEMES[self._theme_idx]['deco']
        for d in self.decos:
            d.update(speed)
        self.decos = [d for d in self.decos if d.x > -280]
        # 전환 중이 아닐 때만 deco 스폰 (school 제외)
        if self._trans_timer == 0 and cur_deco != 'school':
            while len(self.decos) < 5:
                self.decos.append(
                    Deco(self.width + random.randint(60, 280), self.ground_y, cur_deco)
                )

        for c in self.clouds_far:
            c.update(speed)
        for c in self.clouds_near:
            c.update(speed)
        self.clouds_far  = [c for c in self.clouds_far  if c.x > -180]
        self.clouds_near = [c for c in self.clouds_near if c.x > -180]
        while len(self.clouds_far) < 4:
            self.clouds_far.append(
                Cloud(self.width + 50, random.randint(15, 90),
                      speed_factor=0.30, alpha=140)
            )
        while len(self.clouds_near) < 3:
            self.clouds_near.append(
                Cloud(self.width + 50, random.randint(80, 170),
                      speed_factor=0.70, alpha=210)
            )

    # ── 하늘/벽 그라데이션 (색상 동일 시 캐시 blit) ──────────
    def _draw_sky(self, screen, top, bot):
        key = (top, bot)
        if key != self._sky_cache_key:
            surf = pygame.Surface((self.width, self.ground_y))
            band = 5
            for y in range(0, self.ground_y, band):
                pygame.draw.rect(surf, _lerp_color(top, bot, y / self.ground_y),
                                 (0, y, self.width, band + 1))
            self._sky_surface   = surf
            self._sky_cache_key = key
        screen.blit(self._sky_surface, (0, 0))

    # ── 사물함 (학교 실내) ────────────────────────────────────
    def _draw_lockers(self, screen):
        total_h = _LOCKER_H * _LOCKER_ROWS
        start_y = self.ground_y - total_h
        base_c  = (162, 105,  58)
        dark_c  = (122,  75,  35)
        hdl_c   = ( 88,  56,  28)

        off = int(self._wall_off)
        for i in range(self.width // _LOCKER_W + 2):
            lx = i * _LOCKER_W - off
            for row in range(_LOCKER_ROWS):
                ry = start_y + row * _LOCKER_H
                pygame.draw.rect(screen, base_c,
                                 (lx + 1, ry + 1, _LOCKER_W - 2, _LOCKER_H - 2))
                pygame.draw.rect(screen, dark_c,
                                 (lx, ry, _LOCKER_W, _LOCKER_H), 2)
                for s in range(3):
                    pygame.draw.rect(screen, dark_c,
                                     (lx + 8, ry + 8 + s * 6, _LOCKER_W - 16, 3))
                pygame.draw.rect(screen, hdl_c,
                                 (lx + _LOCKER_W - 13, ry + _LOCKER_H // 2 - 6,
                                  5, 12), border_radius=2)

    # ── 학교 고정 창문 ────────────────────────────────────────
    def _make_school_win_surf(self, w, h):
        cloud_data = [
            (int(w * 0.18), int(h * 0.28), 58, 20),
            (int(w * 0.56), int(h * 0.35), 72, 24),
            (int(w * 0.82), int(h * 0.20), 46, 16),
        ]
        return _make_window_sky(w, h, cloud_data)

    def _draw_school_window(self, screen):
        locker_top = self.ground_y - _LOCKER_H * _LOCKER_ROWS
        win_w, win_h = self._school_win_surf.get_size()
        cx  = self.width // 2
        wy  = max(15, (locker_top - win_h) // 2)   # 벽과 사물함 사이 수직 중앙
        fc  = (128, 123, 130)
        pygame.draw.rect(screen, fc,
                         (cx - win_w // 2 - 8, wy - 8, win_w + 16, win_h + 16),
                         border_radius=4)
        screen.blit(self._school_win_surf, (cx - win_w // 2, wy))
        mx = cx
        my = wy + win_h // 2
        pygame.draw.line(screen, fc, (mx, wy), (mx, wy + win_h), 7)
        pygame.draw.line(screen, fc, (cx - win_w // 2, my), (cx + win_w // 2, my), 7)

    # ── 집 고정 창문 (야경) ───────────────────────────────────
    def _draw_home_window(self, screen):
        win_w, win_h = 120, 105
        wx  = self.width - 165
        wy  = 55
        fc  = (110, 82, 52)
        pygame.draw.rect(screen, fc,
                         (wx - 6, wy - 6, win_w + 12, win_h + 12),
                         border_radius=3)
        pygame.draw.rect(screen, (14, 17, 48), (wx, wy, win_w, win_h))
        for sx, sy, br in self._home_win_stars:
            pygame.draw.circle(screen, (br, br, min(255, br + 20)),
                               (wx + sx, wy + sy), 1)
        mx = wx + win_w // 2
        my = wy + win_h // 2
        pygame.draw.line(screen, fc, (mx, wy), (mx, wy + win_h), 4)
        pygame.draw.line(screen, fc, (wx, my), (wx + win_w, my), 4)

    # ── 땅 ───────────────────────────────────────────────────
    def _draw_ground(self, screen, gc, ghi, gdrk, deco_name):
        pygame.draw.rect(screen, gc,
                         (0, self.ground_y, self.width, self.height - self.ground_y))
        pygame.draw.rect(screen, ghi,
                         (0, self.ground_y, self.width, 5))

        if deco_name == 'street':
            off = int(self._lane_off)
            for i in range(self.width // 120 + 2):
                lx = i * 120 - off
                pygame.draw.rect(screen, (220, 200, 30),
                                 (lx, self.ground_y + 12, 58, 4))
        else:
            off = int(self.tile_offset)
            for i in range(self.width // self.tile_size + 2):
                tx = i * self.tile_size - off
                pygame.draw.line(screen, gdrk,
                                 (tx, self.ground_y + 5), (tx, self.height), 2)
            pygame.draw.rect(screen, gdrk,
                             (0, self.ground_y + 14, self.width, 3))

    # ── 그리기 ────────────────────────────────────────────────
    def draw(self, screen):
        colors    = self._get_colors()
        is_indoor = colors.get('indoor', False)
        deco_name = THEMES[self._theme_idx]['deco']

        # 1. 하늘/벽
        self._draw_sky(screen, colors['sky_top'], colors['sky_bot'])

        # 2. 고정 창문 (학교·집 전용) — 전환 중에는 즉시 숨김
        if self._trans_timer == 0:
            if deco_name == 'school':
                self._draw_school_window(screen)
            elif deco_name == 'home':
                self._draw_home_window(screen)

        # 3. 사물함 (학교 실내) — 전환 중에는 즉시 숨김
        if deco_name == 'school' and is_indoor and self._trans_timer == 0:
            self._draw_lockers(screen)

        # 4. 장식 실루엣 (빌딩/가로수/놀이기구/가구)
        for d in self.decos:
            d.draw(screen, colors['hill'])

        # 5. 먼 구름 (실내면 없음)
        cloud_c = colors.get('cloud')
        if cloud_c and not is_indoor:
            for c in self.clouds_far:
                c.draw(screen, cloud_c)

        # 6. 땅
        self._draw_ground(screen,
                          colors['ground'], colors['ground_hi'],
                          colors['ground_dark'], deco_name)

        # 7. 가까운 구름 (실내면 없음)
        if cloud_c and not is_indoor:
            for c in self.clouds_near:
                c.draw(screen, cloud_c)
