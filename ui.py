import pygame
import math
import sys
import os
import lang
from collectible import (FOOD_DATA, DRAW_FN,
                         ATTR_POSITIVE, ATTR_NEGATIVE, ATTR_NEUTRAL)
from achievement import ACHIEVEMENTS, CATEGORY_ORDER, BY_CATEGORY


def _resource_path(filename):
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


# 팀원 소개 — 좌상단 placeholder를 제외한 1~5번 칸에 순서대로 배치
# (파일명, 다국어 소개 키). 이름은 파일명에서 추출하고 소개는 lang.T로 다국어화.
_TEAM_MATES = [
    ('내영님.png',  'teammate_naeyoung_intro'),
    ('서하님.png',  'teammate_seoha_intro'),
    ('서현님.png',  'teammate_seohyeon_intro'),
    ('수민님.png',  'teammate_sumin_intro'),
    ('투타오.png',  'teammate_tutao_intro'),
]

# 좌상단 소희 버튼: 클릭마다 사이클
_SOHEE_FILES = ['기본소희.png', '안경소희.png', '놀란소희.png', '울상소희.png']
_SOHEE_DIALOGUES = [
    "안녕? 나는 이 게임의 개발자 소희야! ✧(◕‿◕)✧\n"
    "재미있게 달리면서 건강한 선택을 배워보자!",

    "엣헴! ( ◕ ω ◕ )✧\n"
    "나는 이 게임의 기획, 설계, 개발, 디자인을 맡았어!\n"
    "내 몸을 위한 선택도 똑똑하게 해보자!",

    "헉! 또 눌렀어?! Σ(°ロ°)\n"
    "관찰력이 대단한데?\n"
    "먹기 전에 한 번 생각하기! 약속이야 ✿",

    "으앙… 여기까지 봐줬구나 (ㅠ_ㅠ)\n"
    "실패해도 괜찮아!\n"
    "건강 습관도 매일 조금씩 레벨업!",
]


class UI:
    COLOR_WHITE  = (255, 255, 255)
    COLOR_YELLOW = (255, 230,  50)
    COLOR_RED    = (255,  80,  80)
    COLOR_GREEN  = (180, 255, 180)
    COLOR_GRAY   = (200, 200, 200)
    COLOR_SHADOW = (  0,   0,   0)
    HEART_FULL   = (255,  70, 100)
    HEART_EMPTY  = ( 90,  50,  60)
    COMBO_COLORS = {1: (255, 210, 100), 2: (255, 160, 50),
                    3: (255, 100,  50), 4: (255,  60, 200)}

    EFFECT_BG = {
        ATTR_POSITIVE: ( 38,  92,  56),
        ATTR_NEGATIVE: (110,  46,  46),
        ATTR_NEUTRAL:  ( 50,  82, 118),
    }
    EFFECT_FG = {
        ATTR_POSITIVE: (200, 255, 200),
        ATTR_NEGATIVE: (255, 195, 195),
        ATTR_NEUTRAL:  (200, 230, 255),
    }
    EFFECT_BORDER = {
        ATTR_POSITIVE: ( 90, 200, 130),
        ATTR_NEGATIVE: (220, 110, 110),
        ATTR_NEUTRAL:  (110, 180, 240),
    }

    # 음식 도감 — 셀 배경/테두리 (속성별)
    GALLERY_BG = {
        ATTR_POSITIVE: ( 35,  78,  50),
        ATTR_NEGATIVE: ( 92,  44,  46),
        ATTR_NEUTRAL:  ( 40,  64, 100),
    }
    GALLERY_BORDER = {
        ATTR_POSITIVE: (110, 200, 130),
        ATTR_NEGATIVE: (220, 110, 110),
        ATTR_NEUTRAL:  (110, 180, 240),
    }
    # 툴팁 — 속성별 강조 색상·번역키
    TOOLTIP_ATTR_COL = {
        ATTR_POSITIVE: (160, 240, 170),
        ATTR_NEGATIVE: (255, 170, 170),
        ATTR_NEUTRAL:  (170, 215, 255),
    }
    ATTR_LANG_KEY = {
        ATTR_POSITIVE: 'attr_pos',
        ATTR_NEGATIVE: 'attr_neg',
        ATTR_NEUTRAL:  'attr_neutral',
    }

    def __init__(self, width, height, lang_code='ko'):
        self.width  = width
        self.height = height
        self._lang_code = lang_code
        self._init_fonts(lang_code)
        self.gallery_btn_rect       = None
        self.achievements_btn_rect  = None
        self.title_rect             = None   # 메뉴 타이틀 hit-rect (이스터에그용)
        self.gallery_cell_rects     = []   # [(rect, food_id), ...] — 매 draw마다 갱신
        self._popup_queue   = []
        self._popup_current = None
        self._popup_surfs   = None  # (label, name, desc) — push 시점에 prerender
        self._popup_y       = -100.0
        self._popup_state   = 'idle'
        self._popup_timer   = 0
        self._effect_popups = []        # {text, attr, age, duration}
        self.settings_btn_rect  = None
        self.devinfo_btn_rect   = None
        self.slider_rects       = []
        self._slider_track_x    = 0
        self._slider_track_w    = 0
        self._devinfo_max_scroll = 0
        self._ach_max_scroll     = 0
        # 스크롤 드래그용 view → {thumb_rect, track_y, track_h, thumb_h, thumb_top, max_scroll}
        self._scroll_views       = {}
        self._warn_panel        = pygame.Surface((28, 36), pygame.SRCALPHA)
        self._vision_blur_surf  = self._make_vision_blur_surf()
        self._thirsty_surf      = self._make_thirsty_surf()
        # 음식 셀 흑백 캐시: food_id -> Surface
        self._food_locked_cache = {}
        # 도감 음식 이름 캐시 + 잠금 ??? 캐시 (도감 화면 60FPS render 회피)
        # 언어 변경 시 set_language()에서 비움.
        self._food_name_surf    = {}      # food_id -> Surface
        self._food_locked_name  = None    # '???' Surface (lang 무관)
        # 업적 이름·설명 캐시 (해금 / 잠금 별도)
        self._ach_text_cache    = {}      # (aid, unlocked) -> (name_surf, desc_surf)
        # 스킬명 base surface 캐시 (5초 동안 매 프레임 render 회피)
        self._skill_name_cache  = {}      # effect_id -> Surface
        # 메뉴 타이틀 size 캐시
        self._title_size        = None
        # 팝업 글리프 폴백 폰트 체인 (지연 초기화)
        self._font_chain_cache  = None
        # 이스터에그 토스트 메시지: (text, expire_ms)
        self._easter_msg        = None
        # 팀원 이미지 — 첫 호출 시 로드 (지연)
        self._team_mate_imgs    = None
        self._sohee_imgs        = None
        self._sohee_idx         = 0
        self.sohee_btn_rect     = None
        self._gameinfo_clip     = None

    def _load_team_mate_imgs(self, size):
        if self._team_mate_imgs is not None:
            return
        self._team_mate_imgs = []
        for fname, intro_key in _TEAM_MATES:
            display_name = fname.rsplit('.', 1)[0]
            try:
                path = _resource_path(os.path.join('team_mate', fname))
                img  = pygame.image.load(path).convert_alpha()
                img  = pygame.transform.smoothscale(img, (size, size))
            except Exception as e:
                print(f"[UI] team_mate 이미지 로드 실패 {fname}: {e}")
                img = None
            self._team_mate_imgs.append((display_name, intro_key, img))

    def _load_sohee_imgs(self, size):
        if self._sohee_imgs is not None:
            return
        self._sohee_imgs = []
        for fname in _SOHEE_FILES:
            try:
                path = _resource_path(os.path.join('team_mate', '소희', fname))
                img  = pygame.image.load(path).convert_alpha()
                img  = pygame.transform.smoothscale(img, (size, size))
            except Exception as e:
                print(f"[UI] 소희 이미지 로드 실패 {fname}: {e}")
                img = None
            self._sohee_imgs.append(img)

    def show_easter_egg_message(self, text, duration_ms=3500):
        self._easter_msg = (text, pygame.time.get_ticks() + duration_ms)

    def draw_easter_egg_message(self, screen):
        if not self._easter_msg:
            return
        text, expire = self._easter_msg
        now = pygame.time.get_ticks()
        if now > expire:
            self._easter_msg = None
            return
        # 화면 중앙 상단에 노란 배지로 표시
        surf = self._render_with_fallback(text, (60, 38, 8))
        pad = 14
        bw = surf.get_width() + pad * 2
        bh = surf.get_height() + pad
        bx = self.width // 2 - bw // 2
        by = 64
        pygame.draw.rect(screen, (255, 235, 90),  (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(screen, (200, 155, 20),  (bx, by, bw, bh), border_radius=10, width=2)
        screen.blit(surf, (bx + pad, by + pad // 2))

    def try_cycle_sohee(self, pos):
        """소희 버튼 적중 시 다음 이미지로 사이클. 적중 여부 반환."""
        if not (self.sohee_btn_rect and self._gameinfo_clip and self._sohee_imgs):
            return False
        visible = self.sohee_btn_rect.clip(self._gameinfo_clip)
        if visible.width <= 0 or not visible.collidepoint(pos):
            return False
        self._sohee_idx = (self._sohee_idx + 1) % len(self._sohee_imgs)
        return True

    def _font_chain(self):
        # 글리프 단위 폴백 — pygame은 글리프 폴백을 안 하고 font.metrics()도 거짓말함
        # (예: Malgun Gothic은 ✨/✿가 있다고 보고하지만 실제론 TOFU 박스를 그림).
        # 그래서 metrics 의존을 버리고 코드포인트 범위로 직접 폰트를 매핑한다.
        if self._font_chain_cache is not None:
            return self._font_chain_cache

        roles = {}
        def load(role, names, size=17):
            for n in names:
                p = pygame.font.match_font(n)
                if p:
                    roles[role] = pygame.font.Font(p, size)
                    return
        load('korean', ['malgun gothic', 'gulim', 'batang'])
        load('symbol', ['segoe ui symbol'])
        load('emoji',  ['segoe ui emoji'])
        load('latin',  ['segoe ui', 'arial'])
        # 둘 다 못 찾으면 popup font로 fallback
        if 'korean' not in roles:
            roles['korean'] = self.font_popup
        self._font_chain_cache = roles
        return roles

    def _font_for_char(self, ch, roles):
        cp = ord(ch)
        # 1. 컬러 이모지 (SMP, U+1F000+) — Segoe UI Emoji가 컬러 비트맵 렌더 가능
        if cp >= 0x1F000:
            return roles.get('emoji') or roles.get('symbol') or roles['korean']
        # 2. 기호·딩뱃·도형 — Malgun이 거짓말하니 무조건 Symbol 우선
        if (0x02B0 <= cp <= 0x02FF or  # Spacing Modifier Letters (˘ ˊ ˋ)
            0x2190 <= cp <= 0x21FF or  # Arrows
            0x2200 <= cp <= 0x22FF or  # Mathematical Operators (⊙)
            0x2300 <= cp <= 0x23FF or  # Misc Technical
            0x25A0 <= cp <= 0x25FF or  # Geometric Shapes (◕ ◎)
            0x2600 <= cp <= 0x27BF):   # Misc Symbols + Dingbats (✨ ✧ ✿ ❀ ★ ☆)
            return roles.get('symbol') or roles['korean']
        # 3. 아랍 문자 (٩ و) — Segoe UI/Arial 가 정상 렌더
        if 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F:
            return roles.get('latin') or roles['korean']
        # 4. 그 외 — Malgun Gothic (한글/Latin/Greek/CJK 호환/Halfwidth/Fullwidth 등 다 처리)
        return roles['korean']

    def _render_with_fallback(self, text, color):
        roles = self._font_chain()
        if not text:
            return pygame.Surface((1, 1), pygame.SRCALPHA)

        runs = []
        cur_font = None
        cur_buf  = []
        for ch in text:
            chosen = self._font_for_char(ch, roles)
            if chosen is cur_font:
                cur_buf.append(ch)
            else:
                if cur_buf:
                    runs.append((cur_font, ''.join(cur_buf)))
                cur_font = chosen
                cur_buf = [ch]
        if cur_buf:
            runs.append((cur_font, ''.join(cur_buf)))

        rendered = [(f.render(s, True, color), f) for f, s in runs]
        # pygame의 get_descent()는 음수를 반환하므로 abs로 양수 보정
        max_ascent   = max(f.get_ascent()       for _, f in rendered)
        max_descent  = max(abs(f.get_descent()) for _, f in rendered)
        max_linesize = max(f.get_linesize()     for _, f in rendered)
        total_w = sum(s.get_width() for s, _ in rendered)
        out_h   = max(max_ascent + max_descent, max_linesize)
        out = pygame.Surface((total_w, out_h), pygame.SRCALPHA)
        x = 0
        for surf, f in rendered:
            out.blit(surf, (x, max_ascent - f.get_ascent()))
            x += surf.get_width()
        return out

    def _draw_yellow_speech_popup(self, screen, mouse_pos, text):
        lines      = text.split('\n')
        line_surfs = [self._render_with_fallback(line, (60, 38, 8)) for line in lines]
        line_h     = max((s.get_height() for s in line_surfs), default=22)
        pad        = 12
        bw         = max((s.get_width() for s in line_surfs), default=120) + pad * 2
        bh         = len(lines) * line_h + pad * 2

        # 위치: 기본은 마우스 우하단, 화면 안쪽으로 클램프
        tx = mouse_pos[0] + 18
        ty = mouse_pos[1] + 14
        flipped_h = False
        flipped_v = False
        if tx + bw > self.width - 6:
            tx = mouse_pos[0] - bw - 18
            flipped_h = True
        if ty + bh > self.height - 6:
            ty = mouse_pos[1] - bh - 14
            flipped_v = True
        tx = max(6, tx)
        ty = max(6, ty)

        # 그림자
        sh = pygame.Surface((bw + 8, bh + 8), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 80), (4, 4, bw, bh), border_radius=10)
        screen.blit(sh, (tx - 2, ty - 2))

        # 본체 (노란색 네모 말풍선)
        body   = (255, 235,  90)
        border = (200, 155,  20)
        pygame.draw.rect(screen, body,   (tx, ty, bw, bh), border_radius=10)
        pygame.draw.rect(screen, border, (tx, ty, bw, bh), border_radius=10, width=2)

        # 꼬리: 마우스 방향으로 작게
        if not flipped_v:
            tail_y    = ty
            tail_tip_y = ty - 9
        else:
            tail_y    = ty + bh
            tail_tip_y = ty + bh + 9
        if not flipped_h:
            base1 = (tx + 18, tail_y)
            base2 = (tx + 32, tail_y)
            tip   = (tx + 14, tail_tip_y)
        else:
            base1 = (tx + bw - 32, tail_y)
            base2 = (tx + bw - 18, tail_y)
            tip   = (tx + bw - 14, tail_tip_y)
        pygame.draw.polygon(screen, body, [base1, base2, tip])
        pygame.draw.line(screen, border, base1, tip, 2)
        pygame.draw.line(screen, border, base2, tip, 2)
        # 본체와 꼬리 경계 가리기
        pygame.draw.line(screen, body, base1, base2, 3)

        # 텍스트
        for i, surf in enumerate(line_surfs):
            screen.blit(surf, (tx + pad, ty + pad + i * line_h))

    def _make_vision_blur_surf(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width // 2, self.height // 2
        for r, a in ((280, 0), (240, 80), (200, 160), (160, 220)):
            pygame.draw.circle(surf, (10, 10, 10, a), (cx, cy), r)
        return surf

    def _make_thirsty_surf(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        surf.fill((140, 80, 30, 60))
        return surf

    # 폰트 파일 매핑 — 언어별로 메인 폰트만 다르게 로드
    # ko/en: Hakgyoansim (한국어 + Latin), vi: Quicksand (Vietnamese 다이아크리틱 가독성)
    _MAIN_FONT_BY_LANG = {
        'ko': 'Hakgyoansim_SiganpyoR.ttf',
        'en': 'Hakgyoansim_SiganpyoR.ttf',
        'vi': 'Quicksand.ttf',
    }

    def _init_fonts(self, lang_code='ko'):
        # 팝업/이스터에그 전용 폰트: 시스템 폰트로 빠르게 로드 (폴백 체인이 따로 처리)
        try:
            self.font_popup = pygame.font.SysFont(
                'malgun gothic, segoe ui symbol, segoe ui, dejavu sans, arial', 17)
        except Exception:
            self.font_popup = pygame.font.Font(None, 22)

        font_file = self._MAIN_FONT_BY_LANG.get(lang_code, 'Hakgyoansim_SiganpyoR.ttf')
        try:
            path = _resource_path(font_file)
            self.font_large  = pygame.font.Font(path, 52)
            self.font_medium = pygame.font.Font(path, 32)
            self.font_small  = pygame.font.Font(path, 22)
            self.font_tiny   = pygame.font.Font(path, 17)
            self.font_micro  = pygame.font.Font(path, 13)
            return
        except Exception as e:
            print(f"[UI] 커스텀 폰트 로드 실패, 시스템 폰트 사용: {e}")
        for name in ["malgun gothic", "gulim", "batang", "dotum"]:
            try:
                if pygame.font.SysFont(name, 10):
                    self.font_large  = pygame.font.SysFont(name, 52, bold=True)
                    self.font_medium = pygame.font.SysFont(name, 32, bold=True)
                    self.font_small  = pygame.font.SysFont(name, 22)
                    self.font_tiny   = pygame.font.SysFont(name, 18)
                    self.font_micro  = pygame.font.SysFont(name, 13)
                    return
            except Exception:
                pass
        self.font_large  = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 40)
        self.font_small  = pygame.font.Font(None, 28)
        self.font_tiny   = pygame.font.Font(None, 22)
        self.font_micro  = pygame.font.Font(None, 16)

    def set_language(self, lang_code):
        # 언어 변경 시 메인 폰트 교체. 베트남어는 Quicksand, 그 외는 Hakgyoansim.
        cur = self._MAIN_FONT_BY_LANG.get(getattr(self, '_lang_code', 'ko'))
        new = self._MAIN_FONT_BY_LANG.get(lang_code)
        self._lang_code = lang_code
        # 텍스트 캐시 무효화 (언어가 바뀌면 모든 lang.T() 결과가 달라짐)
        self._food_name_surf.clear()
        self._food_locked_name = None
        self._ach_text_cache.clear()
        self._skill_name_cache.clear()
        self._title_size = None
        if cur == new:
            return   # 같은 폰트면 재로드 불필요
        self._init_fonts(lang_code)

    def _draw_medal(self, screen, cx, cy, unlocked=True, size=10):
        if unlocked:
            ribbon = (200,  60,  70)
            body   = (245, 200,  70)
            edge   = (175, 130,  30)
            star   = (255, 250, 215)
            star_e = (175, 130,  40)
        else:
            ribbon = ( 90,  90,  95)
            body   = (140, 140, 145)
            edge   = ( 80,  80,  85)
            star   = (200, 200, 205)
            star_e = ( 90,  90,  95)

        # 리본 V (메달 위)
        rh = size + 2
        pygame.draw.polygon(screen, ribbon, [
            (cx - size + 1, cy - size - 2),
            (cx,            cy - 1),
            (cx - 4,        cy - size + rh - 4),
        ])
        pygame.draw.polygon(screen, ribbon, [
            (cx + size - 1, cy - size - 2),
            (cx,            cy - 1),
            (cx + 4,        cy - size + rh - 4),
        ])

        # 메달 본체
        pygame.draw.circle(screen, body, (cx, cy + 2), size)
        pygame.draw.circle(screen, edge, (cx, cy + 2), size, 2)

        # 가운데 별 (5각)
        r1 = size - 3
        r2 = max(2, r1 // 2)
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r   = r1 if i % 2 == 0 else r2
            pts.append((cx + r * math.cos(ang), cy + 2 + r * math.sin(ang)))
        pygame.draw.polygon(screen, star,   pts)
        pygame.draw.polygon(screen, star_e, pts, 1)

    def _draw_gear_icon(self, screen, rect, hover=False):
        cx, cy = rect.centerx, rect.centery
        if hover:
            body, edge, hole = (200, 205, 210), (105, 110, 115), ( 70,  75,  80)
        else:
            body, edge, hole = (165, 170, 175), ( 90,  95, 100), ( 60,  65,  70)

        teeth   = 8
        outer_r = 11
        inner_r = 8
        seg     = (math.pi * 2) / teeth
        tip_w   = 0.30   # tooth top span (fraction of seg)
        valley_w = 0.18  # valley span (fraction of seg)

        pts = []
        for i in range(teeth):
            base = i * seg - math.pi / 2   # 위쪽부터 시작
            pts.append((cx + outer_r * math.cos(base - seg * tip_w),
                        cy + outer_r * math.sin(base - seg * tip_w)))
            pts.append((cx + outer_r * math.cos(base + seg * tip_w),
                        cy + outer_r * math.sin(base + seg * tip_w)))
            valley = base + seg / 2
            pts.append((cx + inner_r * math.cos(valley - seg * valley_w),
                        cy + inner_r * math.sin(valley - seg * valley_w)))
            pts.append((cx + inner_r * math.cos(valley + seg * valley_w),
                        cy + inner_r * math.sin(valley + seg * valley_w)))

        pygame.draw.polygon(screen, body, pts)
        pygame.draw.polygon(screen, edge, pts, 1)
        # 가운데 구멍
        pygame.draw.circle(screen, hole, (cx, cy), 3)
        pygame.draw.circle(screen, edge, (cx, cy), 3, 1)

    def _draw_info_icon(self, screen, rect, hover=False):
        cx, cy = rect.centerx, rect.centery
        if hover:
            bubble, edge, text = (245, 250, 240), (100, 150, 115), ( 40,  90,  60)
        else:
            bubble, edge, text = (215, 230, 215), ( 80, 120,  95), ( 35,  75,  50)

        bubble_y = cy - 2
        radius   = 10

        pygame.draw.circle(screen, bubble, (cx, bubble_y), radius)

        # 꼬리: 좌하단으로 뾰족한 작은 삼각형
        p1  = (cx - 5, bubble_y + 6)
        p2  = (cx - 1, bubble_y + 8)
        tip = (cx - 7, cy + 9)
        pygame.draw.polygon(screen, bubble, [p1, p2, tip])

        pygame.draw.circle(screen, edge, (cx, bubble_y), radius, 2)
        pygame.draw.line(screen, edge, p1,  tip, 2)
        pygame.draw.line(screen, edge, p2,  tip, 2)
        # 말풍선과 꼬리 경계 가리기
        pygame.draw.line(screen, bubble, p1, p2, 3)

        # "i" 글자: 점 + 세로 막대
        pygame.draw.circle(screen, text, (cx, bubble_y - 5), 2)
        pygame.draw.rect(screen, text, (cx - 1, bubble_y - 1, 3, 7))

    def _draw_book_icon(self, screen, rect, hover=False):
        """rect 내부에 빨간 책 모양만 그림 (배경 박스 없음). 호버 시 약간 밝게."""
        cx, cy = rect.centerx, rect.centery
        bw, bh = 18, 20
        bx, by = cx - bw // 2, cy - bh // 2

        cover_c = (200,  75,  70) if hover else (165,  60,  55)
        spine_c = (140,  45,  40) if hover else (105,  30,  28)
        gold_c  = (245, 200,  85) if hover else (230, 185,  70)

        # 종이 (살짝 우·하단으로 비집음)
        pages = pygame.Rect(bx + 2, by + 2, bw, bh - 1)
        pygame.draw.rect(screen, (250, 245, 225), pages, border_radius=1)
        pygame.draw.rect(screen, (200, 190, 165), pages, border_radius=1, width=1)
        # 페이지 가로선 2개
        for y_off in (7, 13):
            pygame.draw.line(screen, (190, 175, 140),
                             (bx + 5, by + y_off),
                             (bx + bw - 1, by + y_off), 1)

        # 표지 본체
        cover = pygame.Rect(bx, by, bw - 2, bh - 1)
        pygame.draw.rect(screen, cover_c, cover, border_radius=2)
        pygame.draw.rect(screen, spine_c, cover, border_radius=2, width=1)

        # 책등
        pygame.draw.rect(screen, spine_c, (bx, by, 3, bh - 1))

        # 가운데 금색 라벨
        pygame.draw.rect(screen, gold_c,        (bx + 5, by + 8, bw - 9, 4))
        pygame.draw.rect(screen, (170, 130, 40),(bx + 5, by + 8, bw - 9, 4), 1)

    def _draw_text(self, screen, text, font, color, x, y, center=False):
        shadow = font.render(text, True, self.COLOR_SHADOW)
        surf   = font.render(text, True, color)
        sr, tr = shadow.get_rect(), surf.get_rect()
        if center:
            sr.center = (x + 2, y + 2); tr.center = (x, y)
        else:
            sr.topleft = (x + 2, y + 2); tr.topleft = (x, y)
        screen.blit(shadow, sr)
        screen.blit(surf,   tr)

    def _wrap_text(self, text, font, max_width):
        lines = []
        for para in text.split('\n\n'):
            words = para.replace('\n', ' ').split()
            line = ''
            for word in words:
                test = (line + ' ' + word).strip()
                if font.size(test)[0] <= max_width:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
            lines.append('')
        if lines and lines[-1] == '':
            lines.pop()
        return lines

    def _draw_overlay(self, screen, alpha=140):
        ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        screen.blit(ov, (0, 0))

    def _draw_panel(self, screen, rect, body_col, border_col, radius=14, border_w=2):
        """둥근 모서리 패널: body fill + border. 6+곳에서 사용."""
        pygame.draw.rect(screen, body_col,   rect, border_radius=radius)
        pygame.draw.rect(screen, border_col, rect, border_radius=radius, width=border_w)

    def _draw_progress_bar(self, screen, x, y, w, h, ratio,
                           track_col, fill_col, border_col=None, radius=4):
        """게이지/슬라이더 공통 — track + fill + (옵션) border."""
        pygame.draw.rect(screen, track_col, (x, y, w, h), border_radius=radius)
        filled = int(w * max(0.0, min(1.0, ratio)))
        if filled > 0:
            pygame.draw.rect(screen, fill_col, (x, y, filled, h), border_radius=radius)
        if border_col is not None:
            pygame.draw.rect(screen, border_col, (x, y, w, h), border_radius=radius, width=1)

    def _draw_scroll_decor(self, screen, content_rect, scroll, max_scroll,
                           total_h, fade_rgb, sb_track_col, sb_thumb_col,
                           view=None):
        cx, cy, cw, ch = content_rect
        if scroll > 0:
            fade = pygame.Surface((cw, 18), pygame.SRCALPHA)
            for i in range(18):
                a = int(180 * (1 - i / 18))
                pygame.draw.line(fade, (*fade_rgb, a), (0, i), (cw, i))
            screen.blit(fade, (cx, cy))
        if scroll < max_scroll:
            fade = pygame.Surface((cw, 18), pygame.SRCALPHA)
            for i in range(18):
                a = int(180 * (i / 18))
                pygame.draw.line(fade, (*fade_rgb, a), (0, i), (cw, i))
            screen.blit(fade, (cx, cy + ch - 18))
        if max_scroll > 0:
            sb_x = cx + cw - 9
            thumb_h = max(24, int(ch * ch / (total_h + ch)))
            thumb_y = cy + int((ch - thumb_h) * scroll / max(1, max_scroll))
            pygame.draw.rect(screen, sb_track_col, (sb_x, cy, 4, ch), border_radius=2)
            pygame.draw.rect(screen, sb_thumb_col, (sb_x, thumb_y, 4, thumb_h), border_radius=2)
            if view:
                # 4px 폭은 잡기 어려우니 hit-test 영역을 좌우로 6px씩 넓힘
                self._scroll_views[view] = {
                    'thumb_rect': pygame.Rect(sb_x - 6, thumb_y - 2, 16, thumb_h + 4),
                    'track_y':    cy,
                    'track_h':    ch,
                    'thumb_h':    thumb_h,
                    'thumb_top':  thumb_y,
                    'max_scroll': max_scroll,
                }
        elif view:
            self._scroll_views.pop(view, None)

    def scroll_thumb_hit(self, view, pos):
        """썸 hit-test. 적중이면 (mouse_y - thumb_top) 오프셋 반환, 아니면 None."""
        info = self._scroll_views.get(view)
        if not info or not info['thumb_rect'].collidepoint(pos):
            return None
        return pos[1] - info['thumb_top']

    def scroll_value_for(self, view, thumb_top_y):
        info = self._scroll_views.get(view)
        if not info:
            return 0
        range_y = info['track_h'] - info['thumb_h']
        if range_y <= 0:
            return 0
        rel = max(0, min(range_y, thumb_top_y - info['track_y']))
        return int(rel * info['max_scroll'] / range_y)

    def _draw_heart(self, screen, cx, cy, full, size=13):
        color = self.HEART_FULL if full else self.HEART_EMPTY
        r = size // 2
        pygame.draw.circle(screen, color, (cx - r + 2, cy - 1), r)
        pygame.draw.circle(screen, color, (cx + r - 2, cy - 1), r)
        pygame.draw.polygon(screen, color, [
            (cx - size + 2, cy + 2), (cx + size - 2, cy + 2), (cx, cy + size + 3),
        ])

    # ── 칭찬스티커 팝업 ──────────────────────────────────────
    def push_achievement(self, ach):
        self._popup_queue.append(ach)

    def update_popup(self):
        if self._popup_state == 'idle':
            if self._popup_queue:
                ach = self._popup_queue.pop(0)
                self._popup_current = ach
                # 표시 동안 매 프레임 render되던 3개 텍스트를 진입 시점에 1회만 render.
                lbl_surf  = self.font_tiny.render(lang.T('ach_popup_label'),
                                                  True, (160, 80, 10))
                name_surf = self.font_medium.render(lang.T(f"ach_{ach['id']}_name"),
                                                    True, (80, 35, 5))
                desc_surf = self.font_tiny.render(lang.T(f"ach_{ach['id']}_desc"),
                                                  True, (120, 55, 10))
                self._popup_surfs = (lbl_surf, name_surf, desc_surf)
                self._popup_state   = 'slide_in'
                self._popup_y       = -100.0
        elif self._popup_state == 'slide_in':
            self._popup_y = min(self._popup_y + 7, 12)
            if self._popup_y >= 12:
                self._popup_state = 'show'
                self._popup_timer = 0
        elif self._popup_state == 'show':
            self._popup_timer += 1
            if self._popup_timer >= 150:
                self._popup_state = 'slide_out'
        elif self._popup_state == 'slide_out':
            self._popup_y -= 7
            if self._popup_y <= -100:
                self._popup_state   = 'idle'
                self._popup_current = None

    # ── 효과 팝업 (버프/디버프) ──────────────────────────
    def push_effect(self, text, attr):
        # 텍스트 surface는 push 시점에 한 번만 render (75프레임 동안 매 프레임 render 회피)
        fg_c = self.EFFECT_FG.get(attr, (255, 255, 255))
        self._effect_popups.append({
            'attr':       attr,
            'age':        0,
            'duration':   75,    # 1.25초
            'text_surf':  self.font_small.render(text, True, fg_c),
        })
        if len(self._effect_popups) > 5:
            self._effect_popups.pop(0)

    def update_effect_popups(self):
        for p in self._effect_popups:
            p['age'] += 1
        self._effect_popups = [p for p in self._effect_popups if p['age'] < p['duration']]

    def draw_effect_popups(self, screen):
        if not self._effect_popups:
            return
        cx       = self.width // 2
        base_y   = 140
        visible  = self._effect_popups[-3:]
        for i, p in enumerate(visible):
            age = p['age']
            dur = p['duration']
            if age < 8:
                alpha = int(255 * age / 8)
                slide = -8 + int(8 * age / 8)
            elif age > dur - 12:
                alpha = max(0, int(255 * (dur - age) / 12))
                slide = 0
            else:
                alpha = 255
                slide = 0

            attr   = p['attr']
            bg_c   = self.EFFECT_BG.get(attr,     (60, 60, 60))
            bd_c   = self.EFFECT_BORDER.get(attr, (160, 160, 160))

            text_surf = p['text_surf']
            tw, th    = text_surf.get_size()
            bw, bh    = tw + 32, th + 8
            bx        = cx - bw // 2
            by        = base_y + i * (bh + 4) + slide

            banner = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pygame.draw.rect(banner, (*bg_c, min(alpha, 220)),
                             (0, 0, bw, bh), border_radius=6)
            pygame.draw.rect(banner, (*bd_c, alpha),
                             (0, 0, bw, bh), border_radius=6, width=2)
            screen.blit(banner, (bx, by))

            text_surf.set_alpha(alpha)
            screen.blit(text_surf, (cx - tw // 2, by + 4))

    def draw_achievement_popup(self, screen):
        if self._popup_current is None:
            return
        ach = self._popup_current
        pw, ph = 300, 84
        px = self.width // 2 - pw // 2
        py = int(self._popup_y)
        cx = px + pw // 2

        sh = pygame.Surface((pw + 6, ph + 6), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 60), (4, 4, pw, ph), border_radius=14)
        screen.blit(sh, (px - 2, py - 2))

        pygame.draw.rect(screen, (255, 222, 48), (px, py, pw, ph), border_radius=14)
        pygame.draw.rect(screen, (235, 165, 20), (px, py, pw, ph), border_radius=14, width=3)

        lbl, nm, desc = self._popup_surfs
        screen.blit(lbl,  lbl.get_rect(center=(cx, py + 14)))
        screen.blit(nm,   nm.get_rect(center=(cx, py + 40)))
        screen.blit(desc, desc.get_rect(center=(cx, py + 65)))

    # ── HUD ───────────────────────────────────────────────
    def draw_hud(self, screen, score, high_score, speed,
                 hp, combo, multiplier,
                 magnet_timer=0, magnet_total=600, shield_active=False,
                 distance=0.0, warnings=None,
                 skill_gauge=0.0, skill_active=False,
                 skill_effect=None, skill_ratio=0.0,
                 water_ratio=1.0, thirsty=False):

        self._draw_text(screen, f"{lang.T('hud_score')}: {score:,}", self.font_medium,
                        self.COLOR_WHITE, 18, 12)
        self._draw_text(screen, f"{lang.T('hud_best')}: {high_score:,}", self.font_tiny,
                        self.COLOR_YELLOW, 18, 48)
        self._draw_text(screen, f"{distance:,.0f} m", self.font_small,
                        (200, 240, 255), 18, 68)

        self._draw_text(screen, f"{lang.T('hud_speed')} {speed:.1f}x", self.font_tiny,
                        self.COLOR_GREEN, self.width - 110, 12)

        self._draw_text(screen, "HP", self.font_tiny, self.COLOR_WHITE,
                        self.width - 28 - hp * 34 - 28, 40)
        for i in range(hp):
            self._draw_heart(screen, self.width - 28 - i * 34, 46, full=True)

        # 물게이지 — HP 하트 줄 바로 아래
        self._draw_water_gauge(screen, water_ratio, thirsty)

        bar_x = self.width - 115
        bar_y = 92    # 물게이지 아래로 밀림
        if magnet_timer > 0:
            self._draw_powerup_bar(screen, bar_x, bar_y,
                                   magnet_timer, max(1, magnet_total),
                                   (255, 220, 50),
                                   lang.T('hud_magnet'))
            bar_y += 22
        if shield_active:
            t = pygame.time.get_ticks()
            c = int(160 + 95 * math.sin(t * 0.006))
            self._draw_text(screen, lang.T('hud_shield'), self.font_tiny,
                            (c, c, 255), bar_x, bar_y)

        if combo >= 10:
            self._draw_combo(screen, combo, multiplier)

        if skill_active and skill_effect:
            self._draw_skill_active(screen, skill_effect, skill_ratio)

        if warnings:
            self._draw_warnings(screen, warnings)

        self._draw_skill_gauge(screen, skill_gauge)
        self._draw_text(screen, lang.T('hud_pause_hint'), self.font_tiny,
                        (150, 150, 150), self.width - 105, self.height - 24)

    # ── 물게이지 ──────────────────────────────────────────
    def _draw_water_gauge(self, screen, ratio, thirsty):
        bar_w = 100
        bar_h = 8
        bar_x = self.width - bar_w - 14
        bar_y = 70
        # 라벨 (왼쪽 작은 물방울)
        drop_cx = bar_x - 12
        drop_cy = bar_y + bar_h // 2
        drop_color = (90, 170, 255) if not thirsty else (255, 80, 80)
        pygame.draw.polygon(screen, drop_color, [
            (drop_cx,     drop_cy - 5),
            (drop_cx - 4, drop_cy + 1),
            (drop_cx,     drop_cy + 4),
            (drop_cx + 4, drop_cy + 1),
        ])
        # 채움 색상 결정 후 공통 progress bar 헬퍼로 그림
        if thirsty:
            t = pygame.time.get_ticks()
            blink = int(180 + 75 * math.sin(t * 0.018))
            fill_col = (blink, 60, 60)
        elif ratio < 0.30:
            fill_col = (255, 160, 60)
        else:
            fill_col = (80, 180, 255)
        self._draw_progress_bar(screen, bar_x, bar_y, bar_w, bar_h, ratio,
                                track_col=(30, 50, 80), fill_col=fill_col,
                                border_col=(90, 130, 180))

    # ── 시야 좁힘 / 갈증 비네팅 ─────────────────────────────
    def draw_overlay_effects(self, screen, vision_blur=False, thirsty=False):
        if vision_blur:
            screen.blit(self._vision_blur_surf, (0, 0))
        if thirsty:
            screen.blit(self._thirsty_surf, (0, 0))

    def _draw_skill_gauge(self, screen, ratio):
        t     = pygame.time.get_ticks()
        bar_w = 150
        bar_h = 10
        bx    = self.width // 2 - bar_w // 2
        by    = self.height - 30

        if ratio >= 1.0:
            pulse = int(200 + 55 * math.sin(t * 0.012))
            col   = (pulse, int(pulse * 0.82), 0)
        else:
            col = (110, 80, 255)
        self._draw_progress_bar(screen, bx, by, bar_w, bar_h, ratio,
                                track_col=(30, 20, 50), fill_col=col,
                                border_col=(80, 60, 180), radius=5)

        lbl_col = (255, 220, 80) if ratio >= 1.0 else (180, 160, 230)
        self._draw_text(screen, lang.T('gauge_label'), self.font_tiny,
                        lbl_col, self.width // 2, by - 14, center=True)
        if ratio >= 1.0:
            self._draw_text(screen, lang.T('gauge_activate'), self.font_tiny,
                            (255, 230, 80), bx + bar_w + 6, by - 2)

    def _draw_skill_active(self, screen, effect, ratio):
        t      = pygame.time.get_ticks()
        color  = effect['color']
        pulse  = 1.0 + 0.07 * math.sin(t * 0.015)
        # base surface 캐시 (4종 스킬 × 5초 = 매 프레임 render 회피)
        eid = effect['id']
        surf = self._skill_name_cache.get(eid)
        if surf is None:
            surf = self.font_large.render(
                lang.T(f"skill_{eid}_name"), True, color)
            self._skill_name_cache[eid] = surf
        scaled = pygame.transform.scale(
            surf,
            (int(surf.get_width() * pulse), int(surf.get_height() * pulse)),
        )
        cx = self.width // 2
        screen.blit(scaled, scaled.get_rect(center=(cx, 95)))

        bar_w  = 200
        bx     = cx - bar_w // 2
        by     = 120
        self._draw_progress_bar(screen, bx, by, bar_w, 8, ratio,
                                track_col=(40, 30, 60), fill_col=color)

    def _draw_powerup_bar(self, screen, x, y, current, total, color, label):
        bar_w = 90
        self._draw_progress_bar(screen, x, y, bar_w, 10, current / total,
                                track_col=(50, 40, 10), fill_col=color)
        self._draw_text(screen, label, self.font_tiny, color, x - 30, y - 2)
        # 남은 초 (60fps 기준), 작은 글씨로 바 우측에
        secs = max(0, math.ceil(current / 60))
        self._draw_text(screen, f"{secs}s", self.font_micro, color,
                        x + bar_w + 4, y - 1)

    def _draw_combo(self, screen, combo, multiplier):
        t     = pygame.time.get_ticks()
        pulse = 1.0 + 0.06 * math.sin(t * 0.012)
        color = self.COMBO_COLORS.get(multiplier, self.COLOR_YELLOW)
        cx    = self.width // 2
        font_mult = self.font_large if multiplier >= 3 else self.font_medium
        surf_mult = font_mult.render(f"x{multiplier}", True, color)
        scaled    = pygame.transform.scale(
            surf_mult,
            (int(surf_mult.get_width() * pulse),
             int(surf_mult.get_height() * pulse)),
        )
        screen.blit(scaled, scaled.get_rect(center=(cx, 28)))
        self._draw_text(screen, f"{lang.T('combo_label')} {combo}", self.font_small,
                        color, cx, 58, center=True)

    def _draw_warnings(self, screen, warnings):
        t = pygame.time.get_ticks()
        for w in warnings:
            ratio  = w['ratio']
            warn_y = max(30, min(self.height - 30, w['y']))
            warn_x = self.width - 22

            alpha = int(80 + 120 * ratio)
            self._warn_panel.fill((180, 0, 0, alpha))
            screen.blit(self._warn_panel, (warn_x - 6, warn_y - 18))

            blink_speed = 0.01 + ratio * 0.025
            visible     = math.sin(t * blink_speed) > -0.2
            if visible:
                self._draw_text(screen, "⚠", self.font_small,
                                (255, 230, 50), warn_x, warn_y - 10)

            ax = warn_x - 2
            ay = warn_y + 12
            pygame.draw.polygon(screen, (255, 100, 100), [
                (ax,      ay),
                (ax + 10, ay - 6),
                (ax + 10, ay + 6),
            ])

    # ── 카운트다운 ─────────────────────────────────────────
    def draw_countdown(self, screen, value):
        self._draw_overlay(screen, 100)
        cx, cy = self.width // 2, self.height // 2
        if value > 0:
            t     = pygame.time.get_ticks()
            pulse = 1.0 + 0.12 * math.sin(t * 0.015)
            surf  = self.font_large.render(str(value), True, self.COLOR_YELLOW)
            scaled = pygame.transform.scale(
                surf,
                (int(surf.get_width() * pulse * 2.0),
                 int(surf.get_height() * pulse * 2.0)),
            )
            screen.blit(scaled, scaled.get_rect(center=(cx, cy)))
        else:
            self._draw_text(screen, lang.T('countdown_go'), self.font_large,
                            (100, 255, 150), cx, cy, center=True)

    # ── 일시정지 ───────────────────────────────────────────
    def draw_paused(self, screen):
        self._draw_overlay(screen, 150)
        cx, cy = self.width // 2, self.height // 2
        self._draw_text(screen, lang.T('pause_title'), self.font_large,
                        self.COLOR_WHITE, cx, cy - 60, center=True)
        self._draw_text(screen, lang.T('pause_continue'), self.font_medium,
                        self.COLOR_YELLOW, cx, cy + 10, center=True)
        self._draw_text(screen, lang.T('pause_menu'), self.font_small,
                        self.COLOR_GRAY, cx, cy + 55, center=True)

    # ── 메뉴 ──────────────────────────────────────────────
    def draw_menu(self, screen):
        self._draw_overlay(screen, 110)
        cx, cy = self.width // 2, self.height // 2

        # 우상단 음식 도감 책 버튼 (배경 박스 없음, 책 자체가 버튼)
        btn_size = 22
        ix = self.width - 14 - btn_size
        iy = 14
        self.gallery_btn_rect = pygame.Rect(ix, iy, btn_size, btn_size)
        mouse_pos = pygame.mouse.get_pos()
        hover = self.gallery_btn_rect.collidepoint(mouse_pos)
        self._draw_book_icon(screen, self.gallery_btn_rect, hover=hover)

        # 좌상단 업적 메달 버튼
        self.achievements_btn_rect = pygame.Rect(14, 14, btn_size, btn_size)
        ach_hover = self.achievements_btn_rect.collidepoint(mouse_pos)
        self._draw_medal(screen,
                         self.achievements_btn_rect.centerx,
                         self.achievements_btn_rect.centery - 1,
                         unlocked=True, size=10 if ach_hover else 9)

        # 타이틀 size 캐시 — set_language()에서 비움
        if self._title_size is None:
            self._title_size = self.font_large.size(lang.T('title'))
        tw, th = self._title_size
        self.title_rect = pygame.Rect(cx - tw // 2, cy - 90 - th // 2, tw, th)
        self._draw_text(screen, lang.T('title'), self.font_large,
                        self.COLOR_YELLOW, cx, cy - 90, center=True)
        self._draw_text(screen, lang.T('menu_start'),
                        self.font_medium, self.COLOR_WHITE, cx, cy - 10, center=True)
        self._draw_text(screen, lang.T('menu_controls'),
                        self.font_small, self.COLOR_GRAY, cx, cy + 38, center=True)
        self._draw_text(screen, lang.T('menu_info'),
                        self.font_tiny, self.COLOR_GRAY, cx, cy + 68, center=True)
        self._draw_text(screen, lang.T('menu_skill_hint'),
                        self.font_tiny, (180, 160, 230), cx, cy + 90, center=True)
        self._draw_text(screen, lang.T('menu_water_hint'),
                        self.font_tiny, (160, 200, 255), cx, cy + 110, center=True)

        # 좌하단 설정(톱니바퀴) / 우하단 게임 정보(말풍선+i) 버튼
        bot_y = self.height - 14 - btn_size
        self.settings_btn_rect = pygame.Rect(14, bot_y, btn_size, btn_size)
        set_hover = self.settings_btn_rect.collidepoint(mouse_pos)
        self._draw_gear_icon(screen, self.settings_btn_rect, hover=set_hover)

        self.devinfo_btn_rect = pygame.Rect(self.width - 14 - btn_size, bot_y,
                                            btn_size, btn_size)
        info_hover = self.devinfo_btn_rect.collidepoint(mouse_pos)
        self._draw_info_icon(screen, self.devinfo_btn_rect, hover=info_hover)

        self.draw_easter_egg_message(screen)

    # ── 설정 화면 ─────────────────────────────────────────
    def draw_settings(self, screen, bgm_vol, sfx_vol, selected, language='ko'):
        self._draw_overlay(screen, 175)
        cx = self.width // 2

        pw, ph = 520, 272
        px = cx - pw // 2
        py = self.height // 2 - ph // 2
        self._draw_panel(screen, (px, py, pw, ph), (28, 22, 48), (90, 75, 140), radius=16)

        self._draw_text(screen, lang.T('settings_title'), self.font_large, self.COLOR_YELLOW,
                        cx, py + 22, center=True)

        track_x = px + 195
        track_w = 195
        rows_y  = [py + 96, py + 148, py + 200]

        self._slider_track_x = track_x
        self._slider_track_w = track_w
        self.slider_rects    = []

        # BGM and SFX sliders
        slider_labels = [lang.T('settings_bgm'), lang.T('settings_sfx')]
        vols          = [bgm_vol, sfx_vol]
        for i, (label, vol, row_y) in enumerate(zip(slider_labels, vols, rows_y[:2])):
            is_sel  = (i == selected)
            col     = self.COLOR_YELLOW if is_sel else (195, 190, 220)
            marker  = '>' if is_sel else ' '
            self._draw_text(screen, f'{marker} {label}', self.font_small, col, px + 18, row_y)

            fill_col = self.COLOR_YELLOW if is_sel else (110, 90, 195)
            self._draw_progress_bar(screen, track_x, row_y + 6, track_w, 10, vol,
                                    track_col=(55, 45, 85), fill_col=fill_col,
                                    border_col=(105, 90, 155), radius=5)

            hx = track_x + int(track_w * vol)
            knob_col = self.COLOR_YELLOW if is_sel else (175, 155, 225)
            pygame.draw.circle(screen, knob_col, (hx, row_y + 11), 9)
            pygame.draw.circle(screen, (255, 255, 255), (hx, row_y + 11), 9, 1)

            pct = f'{round(vol * 100)}%'
            self._draw_text(screen, pct, self.font_small, col, track_x + track_w + 14, row_y)

            self.slider_rects.append(
                pygame.Rect(track_x - 5, row_y - 4, track_w + 10, 32)
            )

        # Language selector (row 2)
        lang_y   = rows_y[2]
        is_sel   = (selected == 2)
        col      = self.COLOR_YELLOW if is_sel else (195, 190, 220)
        marker   = '>' if is_sel else ' '
        self._draw_text(screen, f'{marker} {lang.T("settings_lang")}',
                        self.font_small, col, px + 18, lang_y)

        lang_names  = ['ko', 'en', 'vi']
        lang_labels = [lang.T('lang_ko'), lang.T('lang_en'), lang.T('lang_vi')]
        cur_idx     = lang_names.index(language) if language in lang_names else 0
        lang_val    = lang_labels[cur_idx]

        # < LangName >
        lx = track_x + track_w // 2
        self._draw_text(screen, f'< {lang_val} >', self.font_small, col, lx, lang_y, center=True)

        self.slider_rects.append(
            pygame.Rect(px + 18, lang_y - 4, pw - 36, 32)
        )

        self._draw_text(screen,
                        lang.T('settings_hint'),
                        self.font_tiny, (155, 145, 195),
                        cx, py + ph - 20, center=True)

    def handle_settings_click(self, pos):
        for i, rect in enumerate(self.slider_rects):
            if rect.collidepoint(pos):
                if i == 2:
                    return (2, 'cycle')
                rel_x = pos[0] - self._slider_track_x
                vol   = round(max(0.0, min(1.0, rel_x / self._slider_track_w)), 1)
                return i, vol
        return None

    # ── 음식 도감 ─────────────────────────────────────────
    def draw_gallery(self, screen, seen_foods=None):
        if seen_foods is None:
            seen_foods = set()
        self._draw_overlay(screen, 200)
        cx = self.width // 2

        # 패널
        pad_x, pad_y = 10, 10
        pw, ph = self.width - pad_x * 2, self.height - pad_y * 2
        px, py = pad_x, pad_y
        self._draw_panel(screen, (px, py, pw, ph), (28, 32, 50), (110, 120, 180))

        # 제목 + 진행도 (seen_foods는 _process_collected에서 실제 음식 ID만 들어감)
        self._draw_text(screen, lang.T('gallery_title'), self.font_medium,
                        self.COLOR_YELLOW, cx, py + 22, center=True)
        prog_text = f"{len(seen_foods)} / {len(FOOD_DATA)}"
        self._draw_text(screen, prog_text, self.font_tiny,
                        (180, 190, 230), cx, py + 50, center=True)

        # 그리드: 5열 × 5행 = 25
        cols   = 5
        rows   = 5
        cell_w = (pw - 24) // cols
        cell_h = (ph - 100) // rows
        grid_top = py + 70

        mouse_pos    = pygame.mouse.get_pos()
        hovered_food = None
        hovered_locked = False
        cell_rects   = []

        for i, food in enumerate(FOOD_DATA):
            r, c = divmod(i, cols)
            x = px + 12 + c * cell_w
            y = grid_top + r * cell_h
            rect = pygame.Rect(x + 4, y + 2, cell_w - 8, cell_h - 6)
            cell_rects.append((rect, food['id']))

            unlocked = food['id'] in seen_foods
            attr     = food['attr']

            if unlocked:
                bg_col = self.GALLERY_BG.get(attr, (40, 40, 60))
                bd_col = self.GALLERY_BORDER.get(attr, (160, 160, 200))
            else:
                bg_col = ( 38,  40,  50)
                bd_col = ( 90,  92, 105)

            if rect.collidepoint(mouse_pos):
                hovered_food   = food
                hovered_locked = not unlocked
                bg_col = tuple(min(255, ch + 25) for ch in bg_col)

            self._draw_panel(screen, rect, bg_col, bd_col, radius=8)

            if unlocked:
                DRAW_FN[food['id']](screen, rect.centerx, rect.y + 22)
                ns = self._food_name_surf.get(food['id'])
                if ns is None:
                    ns = self.font_tiny.render(
                        lang.T(f"food_{food['id']}_name"), True, (240, 240, 250))
                    self._food_name_surf[food['id']] = ns
            else:
                self._draw_locked_food(screen, food['id'], rect.centerx, rect.y + 22)
                if self._food_locked_name is None:
                    self._food_locked_name = self.font_tiny.render(
                        '???', True, (160, 165, 180))
                ns = self._food_locked_name
            screen.blit(ns, ns.get_rect(center=(rect.centerx, rect.bottom - 14)))

        self.gallery_cell_rects = cell_rects

        self._draw_text(screen, lang.T('gallery_hint'), self.font_tiny,
                        (140, 145, 180), cx, py + ph - 14, center=True)

        if hovered_food is not None:
            self._draw_food_tooltip(screen, hovered_food, mouse_pos,
                                    locked=hovered_locked)

    def _draw_locked_food(self, screen, food_id, cx, cy):
        cache = self._food_locked_cache.get(food_id)
        if cache is None:
            tmp = pygame.Surface((52, 52), pygame.SRCALPHA)
            DRAW_FN[food_id](tmp, 26, 22)
            cache = pygame.transform.grayscale(tmp)
            cache.fill((130, 130, 130, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self._food_locked_cache[food_id] = cache
        screen.blit(cache, (cx - 26, cy - 22))

    def _draw_food_tooltip(self, screen, food, mouse_pos, locked=False):
        attr        = food['attr']
        stage_label = lang.T(f"stage_{food['stage']}")

        if locked:
            lines = (
                ('???',                                self.font_small, (220, 220, 230)),
                (f"{stage_label}  ·  ???",             self.font_tiny,  (170, 175, 195)),
                ('???',                                self.font_tiny,  (190, 190, 200)),
                (lang.T('gallery_locked_hint'),        self.font_tiny,  (160, 165, 185)),
            )
        else:
            attr_label = lang.T(self.ATTR_LANG_KEY.get(attr, 'attr_neutral'))
            attr_col   = self.TOOLTIP_ATTR_COL.get(attr, (255, 255, 255))
            name_str   = lang.T(f"food_{food['id']}_name")
            eff_str    = lang.T(f"effect_{food['effect_id']}_short")
            score_str  = f"+{food['score']}"
            lines = (
                (name_str,                              self.font_small, (255, 255, 255)),
                (f"{attr_label}  ·  {stage_label}",     self.font_tiny,  attr_col),
                (eff_str,                               self.font_tiny,  (240, 230, 180)),
                (f"{lang.T('hud_score')}  {score_str}", self.font_tiny,  (200, 240, 255)),
            )

        surfs = [font.render(t, True, col) for t, font, col in lines]
        bw = max(s.get_width()  for s in surfs) + 24
        bh = sum(s.get_height() for s in surfs) + 6 * len(surfs) + 8

        # 위치 (마우스 우하단, 화면 안쪽으로 클램프)
        tx = mouse_pos[0] + 16
        ty = mouse_pos[1] + 16
        if tx + bw > self.width  - 4: tx = mouse_pos[0] - bw - 12
        if ty + bh > self.height - 4: ty = mouse_pos[1] - bh - 12
        tx = max(4, tx)
        ty = max(4, ty)

        self._draw_panel(screen, (tx, ty, bw, bh), (20, 24, 38), (130, 145, 200), radius=8)

        cy = ty + 8
        for s in surfs:
            screen.blit(s, (tx + 12, cy))
            cy += s.get_height() + 6

    # ── 업적 진행도 ───────────────────────────────────────
    def draw_achievements(self, screen, scroll, lifetime_unlocked):
        self._draw_overlay(screen, 200)
        cx = self.width // 2

        # 패널 (도감과 동일한 풀스크린 레이아웃)
        pad_x, pad_y = 10, 10
        pw, ph = self.width - pad_x * 2, self.height - pad_y * 2
        px, py = pad_x, pad_y
        self._draw_panel(screen, (px, py, pw, ph), (30, 28, 44), (165, 145, 90))

        # 제목 + 진행도
        self._draw_text(screen, lang.T('ach_title'), self.font_medium,
                        self.COLOR_YELLOW, cx, py + 22, center=True)
        prog = f"{len(lifetime_unlocked)} / {len(ACHIEVEMENTS)}"
        self._draw_text(screen, prog, self.font_tiny,
                        (220, 200, 140), cx, py + 50, center=True)

        CONT_X  = px + 1
        CONT_Y1 = py + 70
        CONT_W  = pw - 2
        CONT_H  = ph - 70 - 32

        pygame.draw.line(screen, (110, 95, 60),
                         (px + 20, CONT_Y1), (px + pw - 20, CONT_Y1), 1)

        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(CONT_X, CONT_Y1, CONT_W, CONT_H))

        LX      = px + 24
        ROW_W   = pw - 48
        HDR_H   = 30
        ROW_H   = 48
        CAT_GAP = 8

        cur_y   = CONT_Y1 + 8 - scroll
        total_h = 0

        def advance(h):
            nonlocal cur_y, total_h
            cur_y   += h
            total_h += h

        for cat in CATEGORY_ORDER:
            items = BY_CATEGORY.get(cat, [])
            if not items:
                continue
            self._draw_text(screen, lang.T(f'ach_cat_{cat}'), self.font_small,
                            (235, 200, 120), LX, cur_y)
            pygame.draw.line(screen, (110, 95, 60),
                             (LX, cur_y + HDR_H - 6),
                             (LX + ROW_W, cur_y + HDR_H - 6), 1)
            advance(HDR_H)

            for a in items:
                aid      = a['id']
                unlocked = aid in lifetime_unlocked
                self._draw_ach_row(screen, LX, cur_y, ROW_W, ROW_H, aid, unlocked)
                advance(ROW_H)
            advance(CAT_GAP)

        screen.set_clip(old_clip)

        self._ach_max_scroll = max(0, total_h - CONT_H + 16)
        self._draw_scroll_decor(
            screen, (CONT_X, CONT_Y1, CONT_W, CONT_H),
            scroll, self._ach_max_scroll, total_h,
            fade_rgb=(30, 28, 44),
            sb_track_col=(75, 65, 45),
            sb_thumb_col=(200, 170, 100),
            view='ach',
        )

        self._draw_text(screen, lang.T('ach_scroll_hint'), self.font_tiny,
                        (170, 155, 110), cx, py + ph - 18, center=True)

    def _draw_ach_row(self, screen, x, y, w, h, aid, unlocked):
        if unlocked:
            bg_col, bd_col   = (52, 46, 70), (140, 120, 80)
            name_col, desc_col = (255, 240, 200), (200, 195, 220)
        else:
            bg_col, bd_col   = (40, 38, 50), (75, 72, 90)
            name_col, desc_col = (170, 165, 180), (130, 128, 145)

        rect = pygame.Rect(x, y, w, h - 4)
        self._draw_panel(screen, rect, bg_col, bd_col, radius=8, border_w=1)

        self._draw_medal(screen, x + 22, y + (h - 4) // 2,
                         unlocked=unlocked, size=12)

        # 텍스트 surface 캐시 (50개 × 60FPS render 회피)
        cache = self._ach_text_cache.get((aid, unlocked))
        if cache is None:
            if unlocked:
                name_t = lang.T(f'ach_{aid}_name')
                desc_t = lang.T(f'ach_{aid}_desc')
            else:
                name_t = desc_t = '???'
            cache = (self.font_small.render(name_t, True, name_col),
                     self.font_tiny.render(desc_t, True, desc_col))
            self._ach_text_cache[(aid, unlocked)] = cache
        ns, ds = cache
        screen.blit(ns, (x + 50, y + 4))
        screen.blit(ds, (x + 50, y + 26))

    # ── 게임 정보 (스크롤 가능) ───────────────────────────
    def draw_gameinfo(self, screen, scroll=0):
        self._draw_overlay(screen, 175)
        cx = self.width // 2
        mouse_pos = pygame.mouse.get_pos()
        team_hover_text  = None
        sohee_hover_text = None

        pw, ph = 520, 370
        px = cx - pw // 2
        py = self.height // 2 - ph // 2
        self._draw_panel(screen, (px, py, pw, ph), (22, 38, 28), (90, 155, 110), radius=16)

        # 고정 제목
        self._draw_text(screen, lang.T('gameinfo_title'), self.font_large, (160, 230, 180),
                        cx, py + 22, center=True)

        CONT_X  = px + 1
        CONT_Y1 = py + 64
        CONT_W  = pw - 2
        CONT_H  = ph - 64 - 32

        pygame.draw.line(screen, (70, 120, 85),
                         (px + 20, CONT_Y1), (px + pw - 20, CONT_Y1), 1)

        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(CONT_X, CONT_Y1, CONT_W, CONT_H))

        LX   = px + 36
        VX   = px + 210
        SH   = 34
        RH   = 27
        SG   = 10
        ITXT = (140, 200, 160)
        VTXT = self.COLOR_WHITE

        cur_y   = CONT_Y1 + 10 - scroll
        total_h = 0

        def advance(h):
            nonlocal cur_y, total_h
            cur_y   += h
            total_h += h

        def sec_hdr(key):
            self._draw_text(screen, lang.T(key), self.font_small, (160, 220, 175), LX, cur_y)
            pygame.draw.line(screen, (70, 120, 85),
                             (LX, cur_y + SH - 4), (LX + pw - 72, cur_y + SH - 4), 1)
            advance(SH)

        def row(lbl_key, val_key):
            self._draw_text(screen, lang.T(lbl_key), self.font_tiny, ITXT, LX, cur_y)
            self._draw_text(screen, lang.T(val_key), self.font_tiny, VTXT, VX, cur_y)
            advance(RH)

        def sep():
            advance(SG)

        # 섹션 1: 개발자 정보
        sec_hdr('gi_dev_title')
        row('gi_game_name_lbl', 'gi_game_name_val')
        row('gi_version_lbl',   'gi_version_val')
        row('gi_dev_lbl',       'gi_dev_val')
        row('gi_tool_lbl',      'gi_tool_val')
        sep()

        # 섹션 2: 팀 소개
        sec_hdr('gi_team_title')
        advance(6)
        wrap_w = CONT_W - 72
        for line in self._wrap_text(lang.T('gi_team_intro'), self.font_tiny, wrap_w):
            if line:
                self._draw_text(screen, line, self.font_tiny, ITXT, LX, cur_y)
                advance(RH - 4)
            else:
                advance(8)
        advance(6)
        pygame.draw.line(screen, (50, 90, 65),
                         (LX, cur_y), (LX + pw - 72, cur_y), 1)
        advance(SG + 6)
        self._draw_text(screen, lang.T('gi_team_members_title'), self.font_tiny,
                        (160, 220, 175), LX, cur_y)
        advance(RH + 2)
        char_w, char_h, gap_x, gap_y = 100, 100, 20, 16
        grid_w = 3 * char_w + 2 * gap_x
        grid_x = px + (pw - grid_w) // 2
        self._load_team_mate_imgs(char_w)
        self._load_sohee_imgs(char_w)

        clip_rect = pygame.Rect(CONT_X, CONT_Y1, CONT_W, CONT_H)
        self._gameinfo_clip = clip_rect
        for i in range(6):
            ri, ci = divmod(i, 3)
            bx = grid_x + ci * (char_w + gap_x)
            by = cur_y + ri * (char_h + gap_y)
            rect = pygame.Rect(bx, by, char_w, char_h)

            if i == 0:
                # 좌상단 — 소희 버튼 (클릭마다 4장 사이클, 테두리 없음)
                self.sohee_btn_rect = rect
                if self._sohee_imgs:
                    img = self._sohee_imgs[self._sohee_idx]
                    if img is not None:
                        screen.blit(img, (bx, by))
                visible = rect.clip(clip_rect)
                if (visible.width > 0 and visible.collidepoint(mouse_pos)
                        and self._sohee_idx < len(_SOHEE_DIALOGUES)):
                    sohee_hover_text = _SOHEE_DIALOGUES[self._sohee_idx]
                continue

            idx = i - 1
            if idx >= len(self._team_mate_imgs):
                continue
            name, intro_key, img = self._team_mate_imgs[idx]
            if img is not None:
                screen.blit(img, (bx, by))
            else:
                pygame.draw.rect(screen, (90, 95, 105), rect, border_radius=12)

            visible = rect.clip(clip_rect)
            if visible.width > 0 and visible.collidepoint(mouse_pos):
                team_hover_text = lang.T(intro_key)

        advance(2 * char_h + gap_y + 10)
        sep()

        # 섹션 3: 게임 개발 목적
        sec_hdr('gi_purpose_title')
        advance(6)
        for line in self._wrap_text(lang.T('gi_purpose_text'), self.font_tiny, wrap_w):
            if line:
                self._draw_text(screen, line, self.font_tiny, ITXT, LX, cur_y)
                advance(RH - 4)
            else:
                advance(8)
        sep()

        # 섹션 4: 폰트 저작권
        sec_hdr('gi_font_title')
        # 한국어/영어 메인 폰트
        row('gi_font_lbl',    'gi_font_val')
        row('gi_author_lbl',  'gi_author_val')
        row('gi_source_lbl',  'gi_source_val')
        row('gi_license_lbl', 'gi_license_val')
        sep()
        # 베트남어 폰트
        row('gi_font2_lbl',   'gi_font2_val')
        row('gi_author2_lbl', 'gi_author2_val')
        row('gi_source2_lbl', 'gi_source2_val')
        row('gi_license2_lbl','gi_license2_val')

        screen.set_clip(old_clip)

        self._devinfo_max_scroll = max(0, total_h - CONT_H + 16)
        self._draw_scroll_decor(
            screen, (CONT_X, CONT_Y1, CONT_W, CONT_H),
            scroll, self._devinfo_max_scroll, total_h,
            fade_rgb=(22, 38, 28),
            sb_track_col=(50, 80, 55),
            sb_thumb_col=(120, 190, 140),
            view='devinfo',
        )

        self._draw_text(screen, lang.T('gi_scroll_hint'), self.font_tiny,
                        (120, 170, 140), cx, py + ph - 18, center=True)

        if team_hover_text:
            self._draw_yellow_speech_popup(screen, mouse_pos, team_hover_text)
        if sohee_hover_text:
            self._draw_yellow_speech_popup(screen, mouse_pos, sohee_hover_text)
        self.draw_easter_egg_message(screen)

    # ── 게임오버 ───────────────────────────────────────────
    def draw_game_over(self, screen, score, high_score, distance=0.0):
        self._draw_overlay(screen, 155)
        cx, cy = self.width // 2, self.height // 2
        self._draw_text(screen, lang.T('gameover_title'), self.font_large,
                        self.COLOR_RED, cx, cy - 100, center=True)
        self._draw_text(screen, f"{lang.T('gameover_score')}: {score:,}", self.font_medium,
                        self.COLOR_WHITE, cx, cy - 38, center=True)
        self._draw_text(screen, f"{lang.T('gameover_dist')}: {distance:,.0f} m", self.font_small,
                        (200, 240, 255), cx, cy + 5, center=True)
        if score > 0 and score >= high_score:
            self._draw_text(screen, lang.T('gameover_new_best'), self.font_medium,
                            self.COLOR_YELLOW, cx, cy + 38, center=True)
        else:
            self._draw_text(screen, f"{lang.T('gameover_high')}: {high_score:,}", self.font_small,
                            self.COLOR_YELLOW, cx, cy + 38, center=True)
        self._draw_text(screen, lang.T('gameover_hint'),
                        self.font_small, self.COLOR_GRAY, cx, cy + 78, center=True)
