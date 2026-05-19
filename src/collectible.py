import pygame
import random
import math
from itertools import chain


# ── 속성 enum ──────────────────────────────────────────────
ATTR_POSITIVE = 'pos'
ATTR_NEGATIVE = 'neg'
ATTR_NEUTRAL  = 'neutral'


# ── 음식 마스터 데이터 (25종) ──────────────────────────────
# duration: 지속 효과의 프레임 수 (60fps), 즉시 효과는 0
FOOD_DATA = [
    # 학교 (긍정 3 / 부정 3)
    {'id': 'milk',       'stage': 'school', 'attr': ATTR_POSITIVE, 'effect_id': 'hp_or_score',  'duration': 0,   'score': 100},
    {'id': 'apple',      'stage': 'school', 'attr': ATTR_POSITIVE, 'effect_id': 'combo_plus',   'duration': 0,   'score': 200},
    {'id': 'kimbap',     'stage': 'school', 'attr': ATTR_POSITIVE, 'effect_id': 'gauge_l',      'duration': 0,   'score': 150},
    {'id': 'cup_ramen',  'stage': 'school', 'attr': ATTR_NEGATIVE, 'effect_id': 'heavy_jump',   'duration': 240, 'score': 50},
    {'id': 'chocolate',  'stage': 'school', 'attr': ATTR_NEGATIVE, 'effect_id': 'dizzy',        'duration': 300, 'score': 50},
    {'id': 'candy',      'stage': 'school', 'attr': ATTR_NEGATIVE, 'effect_id': 'combo_break',  'duration': 0,   'score': 50},
    # 길거리 (긍정 3 / 부정 3)
    {'id': 'banana_milk',     'stage': 'street', 'attr': ATTR_POSITIVE, 'effect_id': 'magnet_short', 'duration': 0,   'score': 100},
    {'id': 'triangle_kimbap', 'stage': 'street', 'attr': ATTR_POSITIVE, 'effect_id': 'score_bonus',  'duration': 0,   'score': 250},
    {'id': 'soy_milk',        'stage': 'street', 'attr': ATTR_POSITIVE, 'effect_id': 'gauge_s',      'duration': 0,   'score': 100},
    {'id': 'tteokbokki',      'stage': 'street', 'attr': ATTR_NEGATIVE, 'effect_id': 'vision_blur',  'duration': 180, 'score': 50},
    {'id': 'burger',          'stage': 'street', 'attr': ATTR_NEGATIVE, 'effect_id': 'heavy_jump_l', 'duration': 240, 'score': 50},
    {'id': 'slushie',         'stage': 'street', 'attr': ATTR_NEGATIVE, 'effect_id': 'slow_freeze',  'duration': 120, 'score': 50},
    # 놀이터 (긍정 3 / 부정 3)
    {'id': 'cola',                 'stage': 'playground', 'attr': ATTR_NEGATIVE, 'effect_id': 'water_drain',  'duration': 0,   'score': 50},
    {'id': 'cherry_tomato',        'stage': 'playground', 'attr': ATTR_POSITIVE, 'effect_id': 'cleanse',      'duration': 0,   'score': 100},
    {'id': 'fruit_juice',          'stage': 'playground', 'attr': ATTR_POSITIVE, 'effect_id': 'score_l',      'duration': 0,   'score': 250},
    {'id': 'roasted_sweet_potato', 'stage': 'playground', 'attr': ATTR_POSITIVE, 'effect_id': 'score_mult',   'duration': 300, 'score': 100},
    {'id': 'cotton_candy',         'stage': 'playground', 'attr': ATTR_NEGATIVE, 'effect_id': 'sticky',       'duration': 180, 'score': 50},
    {'id': 'ice_cream',            'stage': 'playground', 'attr': ATTR_NEGATIVE, 'effect_id': 'slide_short',  'duration': 180, 'score': 50},
    # 집 (긍정 3 / 부정 3)
    {'id': 'rice_bowl',     'stage': 'home', 'attr': ATTR_POSITIVE, 'effect_id': 'rice_combo',   'duration': 0,   'score': 200},
    {'id': 'seaweed_soup',  'stage': 'home', 'attr': ATTR_POSITIVE, 'effect_id': 'hp_chance',    'duration': 0,   'score': 150},
    {'id': 'grilled_fish',  'stage': 'home', 'attr': ATTR_POSITIVE, 'effect_id': 'shield_grant', 'duration': 0,   'score': 200},
    {'id': 'instant_ramen', 'stage': 'home', 'attr': ATTR_NEGATIVE, 'effect_id': 'heavy_combo',  'duration': 240, 'score': 50},
    {'id': 'pizza',         'stage': 'home', 'attr': ATTR_NEGATIVE, 'effect_id': 'gauge_freeze', 'duration': 300, 'score': 50},
    {'id': 'snack_bag',     'stage': 'home', 'attr': ATTR_NEGATIVE, 'effect_id': 'gauge_drain',  'duration': 0,   'score': 50},
    # 모든 스테이지 (무속성, 별도 스폰)
    {'id': 'water_bottle',  'stage': 'all',  'attr': ATTR_NEUTRAL,  'effect_id': 'water_refill', 'duration': 0,   'score': 30},
]

FOOD_BY_ID = {f['id']: f for f in FOOD_DATA}

# 스테이지별 출현 풀 (생수는 별도 스폰이라 제외)
STAGE_FOODS = {
    'school':     [f for f in FOOD_DATA if f['stage'] == 'school'],
    'street':     [f for f in FOOD_DATA if f['stage'] == 'street'],
    'playground': [f for f in FOOD_DATA if f['stage'] == 'playground'],
    'home':       [f for f in FOOD_DATA if f['stage'] == 'home'],
}

# 속성별 사전 분리 (스폰마다 필터하지 않도록)
STAGE_FOODS_POS = {
    k: [f for f in v if f['attr'] == ATTR_POSITIVE] for k, v in STAGE_FOODS.items()
}
STAGE_FOODS_NEG = {
    k: [f for f in v if f['attr'] == ATTR_NEGATIVE] for k, v in STAGE_FOODS.items()
}

# 수집 시 파티클 색상 (속성별)
PARTICLE_COLOR = {
    ATTR_POSITIVE: [(120, 255, 120), (180, 255, 180), (220, 255, 220)],
    ATTR_NEGATIVE: [(255, 100,  80), (255, 160,  50), (255, 220,  50)],
    ATTR_NEUTRAL:  [(120, 200, 255), (180, 220, 255), (200, 240, 255)],
}


# ── 25종 그리기 함수 ───────────────────────────────────────
# 각 함수는 (surface, cx, cy)를 받아 28x28 안쪽에 음식 아이콘을 그림.

def _draw_cola(s, cx, cy):
    pygame.draw.rect(s, (180, 30, 30), (cx - 9, cy - 13, 18, 26), border_radius=2)
    pygame.draw.rect(s, (140, 20, 20), (cx - 9, cy - 13, 18, 4), border_radius=2)
    pygame.draw.rect(s, (255, 255, 255), (cx - 6, cy - 2, 12, 6))
    pygame.draw.line(s, (200, 30, 30), (cx - 5, cy + 1), (cx + 5, cy + 1), 1)
    pygame.draw.circle(s, (255, 240, 240), (cx - 7, cy + 11), 2)
    pygame.draw.circle(s, (255, 240, 240), (cx + 5, cy + 13), 1)


def _draw_milk(s, cx, cy):
    pygame.draw.rect(s, (250, 250, 250), (cx - 9, cy - 11, 18, 24))
    pygame.draw.polygon(s, (250, 250, 250),
                        [(cx - 9, cy - 11), (cx, cy - 15), (cx + 9, cy - 11)])
    pygame.draw.rect(s, (200, 200, 220), (cx - 9, cy - 11, 18, 24), 1)
    pygame.draw.line(s, (255, 220, 50), (cx + 3, cy - 15), (cx + 3, cy - 5), 2)
    pygame.draw.rect(s, (60, 130, 220), (cx - 7, cy - 3, 14, 4))


def _draw_apple(s, cx, cy):
    pygame.draw.circle(s, (220, 30, 30), (cx, cy + 1), 11)
    pygame.draw.circle(s, (255, 80, 80), (cx - 3, cy - 2), 3)
    pygame.draw.line(s, (90, 50, 30), (cx, cy - 10), (cx + 1, cy - 13), 2)
    pygame.draw.ellipse(s, (60, 160, 70), (cx + 1, cy - 14, 7, 4))


def _draw_kimbap(s, cx, cy):
    pygame.draw.circle(s, (30, 30, 30), (cx, cy), 12)
    pygame.draw.circle(s, (245, 245, 240), (cx, cy), 9)
    pygame.draw.circle(s, (240, 200, 80), (cx - 3, cy - 2), 2)   # 단무지
    pygame.draw.circle(s, (220, 100, 60), (cx + 3, cy - 2), 2)   # 당근
    pygame.draw.circle(s, (90, 160, 80),  (cx, cy + 3), 2)       # 시금치


def _draw_cup_ramen(s, cx, cy):
    pygame.draw.polygon(s, (200, 50, 50), [
        (cx - 11, cy - 10), (cx + 11, cy - 10),
        (cx + 9,  cy + 10), (cx - 9,  cy + 10),
    ])
    pygame.draw.rect(s, (245, 245, 245), (cx - 10, cy - 3, 20, 5))
    pygame.draw.ellipse(s, (240, 210, 100), (cx - 10, cy - 13, 20, 6))
    pygame.draw.line(s, (220, 220, 230), (cx - 3, cy - 15), (cx - 2, cy - 19), 1)
    pygame.draw.line(s, (220, 220, 230), (cx + 3, cy - 15), (cx + 4, cy - 20), 1)


def _draw_chocolate(s, cx, cy):
    pygame.draw.rect(s, (90, 50, 25), (cx - 11, cy - 9, 22, 18))
    pygame.draw.rect(s, (60, 30, 15), (cx - 11, cy - 9, 22, 18), 1)
    pygame.draw.line(s, (60, 30, 15), (cx, cy - 9), (cx, cy + 9), 1)
    pygame.draw.line(s, (60, 30, 15), (cx - 11, cy), (cx + 11, cy), 1)
    pygame.draw.rect(s, (130, 80, 45), (cx - 10, cy - 8, 9, 7))


def _draw_candy(s, cx, cy):
    pygame.draw.polygon(s, (255, 180, 200),
                        [(cx - 7, cy), (cx - 13, cy - 4), (cx - 13, cy + 4)])
    pygame.draw.polygon(s, (255, 180, 200),
                        [(cx + 7, cy), (cx + 13, cy - 4), (cx + 13, cy + 4)])
    pygame.draw.circle(s, (255, 100, 150), (cx, cy), 7)
    pygame.draw.circle(s, (255, 160, 190), (cx - 2, cy - 2), 2)


def _draw_banana_milk(s, cx, cy):
    pygame.draw.ellipse(s, (255, 220, 80), (cx - 8, cy - 13, 16, 16))
    pygame.draw.rect(s, (255, 220, 80), (cx - 8, cy - 5, 16, 18), border_radius=3)
    pygame.draw.rect(s, (140, 90, 50), (cx - 8, cy - 1, 16, 6))
    pygame.draw.rect(s, (255, 240, 130), (cx - 5, cy - 15, 10, 4))


def _draw_triangle_kimbap(s, cx, cy):
    pygame.draw.polygon(s, (30, 30, 30),
                        [(cx, cy - 12), (cx - 11, cy + 8), (cx + 11, cy + 8)])
    pygame.draw.polygon(s, (245, 245, 240),
                        [(cx, cy - 7), (cx - 7, cy + 5), (cx + 7, cy + 5)])
    pygame.draw.rect(s, (30, 30, 30), (cx - 11, cy + 5, 22, 4))


def _draw_soy_milk(s, cx, cy):
    pygame.draw.rect(s, (245, 245, 240), (cx - 9, cy - 11, 18, 24))
    pygame.draw.polygon(s, (245, 245, 240),
                        [(cx - 9, cy - 11), (cx, cy - 15), (cx + 9, cy - 11)])
    pygame.draw.rect(s, (200, 200, 200), (cx - 9, cy - 11, 18, 24), 1)
    pygame.draw.ellipse(s, (180, 130, 70), (cx - 5, cy - 2, 10, 7))
    pygame.draw.ellipse(s, (180, 130, 70), (cx - 3, cy + 5, 8, 5))


def _draw_tteokbokki(s, cx, cy):
    pygame.draw.ellipse(s, (200, 50, 30), (cx - 13, cy - 6, 26, 14))
    pygame.draw.rect(s, (245, 245, 230), (cx - 9, cy - 3, 6, 8), border_radius=2)
    pygame.draw.rect(s, (245, 245, 230), (cx - 3, cy - 4, 6, 8), border_radius=2)
    pygame.draw.rect(s, (245, 245, 230), (cx + 3, cy - 3, 6, 8), border_radius=2)


def _draw_burger(s, cx, cy):
    pygame.draw.ellipse(s, (205, 150, 80), (cx - 11, cy - 12, 22, 12))
    pygame.draw.rect(s, (130, 200, 90), (cx - 11, cy - 4, 22, 4))
    pygame.draw.rect(s, (110, 60, 30), (cx - 11, cy - 1, 22, 5))
    pygame.draw.ellipse(s, (205, 150, 80), (cx - 11, cy + 3, 22, 10))
    pygame.draw.circle(s, (255, 240, 200), (cx - 4, cy - 9), 1)
    pygame.draw.circle(s, (255, 240, 200), (cx + 3, cy - 10), 1)


def _draw_slushie(s, cx, cy):
    pygame.draw.polygon(s, (220, 240, 250), [
        (cx - 9, cy - 10), (cx + 9, cy - 10),
        (cx + 7, cy + 12), (cx - 7, cy + 12),
    ])
    pygame.draw.polygon(s, (180, 215, 240), [
        (cx - 9, cy - 10), (cx + 9, cy - 10),
        (cx + 7, cy + 12), (cx - 7, cy + 12),
    ], 1)
    pygame.draw.ellipse(s, (100, 170, 230), (cx - 9, cy - 10, 18, 8))
    pygame.draw.line(s, (255, 220, 50), (cx, cy - 12), (cx + 2, cy - 18), 2)


def _draw_cherry_tomato(s, cx, cy):
    pygame.draw.circle(s, (220, 50, 50), (cx, cy + 1), 9)
    pygame.draw.circle(s, (255, 100, 100), (cx - 2, cy - 1), 3)
    leaf_pts = [
        (cx, cy - 12),
        (cx - 3, cy - 9), (cx - 7, cy - 9),
        (cx - 3, cy - 7), (cx - 5, cy - 4),
        (cx, cy - 6),
        (cx + 5, cy - 4), (cx + 3, cy - 7),
        (cx + 7, cy - 9), (cx + 3, cy - 9),
    ]
    pygame.draw.polygon(s, (60, 160, 60), leaf_pts)


def _draw_fruit_juice(s, cx, cy):
    pygame.draw.rect(s, (255, 150, 50), (cx - 9, cy - 10, 18, 22))
    pygame.draw.rect(s, (220, 110, 30), (cx - 9, cy - 10, 18, 22), 1)
    pygame.draw.line(s, (255, 80, 80), (cx - 3, cy - 13), (cx - 3, cy - 3), 2)
    pygame.draw.circle(s, (255, 220, 80), (cx, cy + 3), 4)
    pygame.draw.circle(s, (220, 180, 60), (cx, cy + 3), 4, 1)


def _draw_roasted_sweet_potato(s, cx, cy):
    pygame.draw.ellipse(s, (90, 60, 40), (cx - 13, cy - 6, 26, 14))
    pygame.draw.ellipse(s, (60, 35, 20), (cx - 13, cy - 6, 26, 14), 1)
    pygame.draw.ellipse(s, (180, 130, 200), (cx - 2, cy - 5, 13, 11))
    pygame.draw.line(s, (220, 220, 230), (cx - 5, cy - 9), (cx - 4, cy - 13), 1)
    pygame.draw.line(s, (220, 220, 230), (cx + 3, cy - 9), (cx + 4, cy - 14), 1)


def _draw_cotton_candy(s, cx, cy):
    pygame.draw.circle(s, (255, 180, 220), (cx - 5, cy - 3), 7)
    pygame.draw.circle(s, (255, 200, 230), (cx + 5, cy - 3), 7)
    pygame.draw.circle(s, (255, 220, 240), (cx, cy - 7), 7)
    pygame.draw.circle(s, (255, 200, 230), (cx, cy + 1), 6)
    pygame.draw.rect(s, (160, 110, 60), (cx - 1, cy + 3, 2, 12))


def _draw_ice_cream(s, cx, cy):
    pygame.draw.polygon(s, (180, 120, 60),
                        [(cx - 7, cy - 1), (cx + 7, cy - 1), (cx, cy + 13)])
    pygame.draw.line(s, (140, 90, 40), (cx - 5, cy + 2), (cx + 1, cy + 12), 1)
    pygame.draw.line(s, (140, 90, 40), (cx + 5, cy + 2), (cx - 1, cy + 12), 1)
    pygame.draw.circle(s, (255, 200, 220), (cx, cy - 5), 8)
    pygame.draw.circle(s, (255, 240, 200), (cx - 3, cy - 7), 4)


def _draw_rice_bowl(s, cx, cy):
    pygame.draw.ellipse(s, (250, 250, 245), (cx - 10, cy - 7, 20, 10))
    pygame.draw.ellipse(s, (255, 255, 250), (cx - 7, cy - 9, 14, 6))
    pygame.draw.polygon(s, (240, 240, 250), [
        (cx - 12, cy - 2), (cx + 12, cy - 2),
        (cx + 9,  cy + 10), (cx - 9,  cy + 10),
    ])
    pygame.draw.polygon(s, (180, 180, 200), [
        (cx - 12, cy - 2), (cx + 12, cy - 2),
        (cx + 9,  cy + 10), (cx - 9,  cy + 10),
    ], 1)
    pygame.draw.line(s, (220, 220, 230), (cx - 3, cy - 12), (cx - 2, cy - 16), 1)
    pygame.draw.line(s, (220, 220, 230), (cx + 3, cy - 12), (cx + 4, cy - 17), 1)


def _draw_seaweed_soup(s, cx, cy):
    pygame.draw.polygon(s, (130, 80, 50), [
        (cx - 12, cy - 2), (cx + 12, cy - 2),
        (cx + 9,  cy + 10), (cx - 9,  cy + 10),
    ])
    pygame.draw.ellipse(s, (160, 130, 80), (cx - 11, cy - 4, 22, 7))
    pygame.draw.arc(s, (40, 80, 50), (cx - 8, cy - 4, 12, 7), 0, math.pi, 2)
    pygame.draw.arc(s, (40, 80, 50), (cx - 2, cy - 4, 12, 7), 0, math.pi, 2)
    pygame.draw.line(s, (220, 220, 230), (cx - 3, cy - 8),  (cx - 2, cy - 13), 1)
    pygame.draw.line(s, (220, 220, 230), (cx + 3, cy - 8),  (cx + 4, cy - 14), 1)


def _draw_grilled_fish(s, cx, cy):
    pygame.draw.ellipse(s, (130, 140, 150), (cx - 12, cy - 5, 20, 11))
    pygame.draw.polygon(s, (130, 140, 150),
                        [(cx + 7, cy), (cx + 13, cy - 5), (cx + 13, cy + 5)])
    pygame.draw.line(s, (60, 70, 80), (cx - 6, cy - 4), (cx - 6, cy + 4), 1)
    pygame.draw.line(s, (60, 70, 80), (cx - 1, cy - 4), (cx - 1, cy + 4), 1)
    pygame.draw.line(s, (60, 70, 80), (cx + 4, cy - 4), (cx + 4, cy + 4), 1)
    pygame.draw.circle(s, (30, 30, 30), (cx - 8, cy - 1), 1)


def _draw_instant_ramen(s, cx, cy):
    pygame.draw.polygon(s, (200, 50, 50), [
        (cx - 12, cy - 2), (cx + 12, cy - 2),
        (cx + 9,  cy + 10), (cx - 9,  cy + 10),
    ])
    pygame.draw.ellipse(s, (240, 210, 100), (cx - 12, cy - 7, 24, 9))
    pygame.draw.line(s, (200, 170, 70), (cx - 8, cy - 5), (cx + 8, cy - 3), 1)
    pygame.draw.line(s, (200, 170, 70), (cx - 7, cy - 3), (cx + 7, cy - 1), 1)
    pygame.draw.circle(s, (90, 180, 90), (cx - 3, cy - 5), 1)
    pygame.draw.circle(s, (90, 180, 90), (cx + 4, cy - 3), 1)


def _draw_pizza(s, cx, cy):
    pygame.draw.polygon(s, (240, 200, 130),
                        [(cx, cy - 12), (cx - 12, cy + 10), (cx + 12, cy + 10)])
    pygame.draw.line(s, (180, 130, 60),
                     (cx - 12, cy + 10), (cx + 12, cy + 10), 4)
    pygame.draw.polygon(s, (200, 60, 40),
                        [(cx, cy - 7), (cx - 9, cy + 8), (cx + 9, cy + 8)])
    pygame.draw.circle(s, (160, 30, 30), (cx - 3, cy + 2), 2)
    pygame.draw.circle(s, (160, 30, 30), (cx + 3, cy + 5), 2)
    pygame.draw.circle(s, (255, 240, 220), (cx, cy - 2), 2)


def _draw_snack_bag(s, cx, cy):
    pygame.draw.rect(s, (255, 220, 80), (cx - 10, cy - 10, 20, 22))
    pygame.draw.rect(s, (220, 180, 50), (cx - 10, cy - 10, 20, 22), 1)
    for i in range(-9, 10, 4):
        pygame.draw.polygon(s, (220, 180, 50),
                            [(cx + i, cy - 10), (cx + i + 2, cy - 13), (cx + i + 4, cy - 10)])
    pygame.draw.rect(s, (200, 50, 30), (cx - 7, cy - 2, 14, 5))


def _draw_water_bottle(s, cx, cy):
    # 본체 (투명)
    pygame.draw.rect(s, (220, 240, 250), (cx - 6, cy - 10, 12, 22), border_radius=2)
    pygame.draw.rect(s, (180, 220, 240), (cx - 6, cy - 10, 12, 22), 1, border_radius=2)
    # 물 (아래쪽 파란)
    pygame.draw.rect(s, (100, 180, 255), (cx - 5, cy, 10, 11))
    # 라벨
    pygame.draw.rect(s, (50, 130, 220), (cx - 6, cy - 3, 12, 5))
    # 뚜껑
    pygame.draw.rect(s, (50, 130, 220), (cx - 3, cy - 13, 6, 4))
    # 떠다니는 물방울
    pygame.draw.circle(s, (100, 180, 255), (cx - 9, cy - 8), 1)
    pygame.draw.circle(s, (100, 180, 255), (cx + 9, cy - 5), 1)


DRAW_FN = {
    'cola':                 _draw_cola,
    'milk':                 _draw_milk,
    'apple':                _draw_apple,
    'kimbap':               _draw_kimbap,
    'cup_ramen':            _draw_cup_ramen,
    'chocolate':            _draw_chocolate,
    'candy':                _draw_candy,
    'banana_milk':          _draw_banana_milk,
    'triangle_kimbap':      _draw_triangle_kimbap,
    'soy_milk':             _draw_soy_milk,
    'tteokbokki':           _draw_tteokbokki,
    'burger':               _draw_burger,
    'slushie':              _draw_slushie,
    'cherry_tomato':        _draw_cherry_tomato,
    'fruit_juice':          _draw_fruit_juice,
    'roasted_sweet_potato': _draw_roasted_sweet_potato,
    'cotton_candy':         _draw_cotton_candy,
    'ice_cream':            _draw_ice_cream,
    'rice_bowl':            _draw_rice_bowl,
    'seaweed_soup':         _draw_seaweed_soup,
    'grilled_fish':         _draw_grilled_fish,
    'instant_ramen':        _draw_instant_ramen,
    'pizza':                _draw_pizza,
    'snack_bag':            _draw_snack_bag,
    'water_bottle':         _draw_water_bottle,
}


# ── Food: 단일 음식 인스턴스 ──────────────────────────────
class Food:
    RADIUS = 14

    def __init__(self, x, y, food_id):
        data = FOOD_BY_ID[food_id]
        self.food_id   = food_id
        self.attr      = data['attr']
        self.effect_id = data['effect_id']
        self.duration  = data['duration']
        self.score     = data['score']
        self.x         = float(x)
        self.base_y    = float(y)
        self.collected = False
        self.timer     = random.uniform(0, math.pi * 2)
        d = self.RADIUS * 2
        self.rect = pygame.Rect(0, 0, d, d)
        self._update_rect()

    def _update_rect(self):
        cy = int(self.base_y + math.sin(self.timer) * 5)
        self.rect.x = int(self.x) - self.RADIUS
        self.rect.y = cy - self.RADIUS

    def update(self, speed, magnet_pos=None):
        # 자석은 부정 음식을 끌어당기지 않음 (긍정/무속성만)
        attracted = False
        if magnet_pos and self.attr != ATTR_NEGATIVE:
            dx = magnet_pos[0] - self.x
            dy = magnet_pos[1] - self.base_y
            dist = math.sqrt(dx * dx + dy * dy)
            if 1 < dist < 300:
                pull = min(14.0, 2200 / dist)
                self.x      += dx / dist * pull
                self.base_y += dy / dist * pull * 0.55
                attracted = True
        if not attracted:
            self.x -= speed
        self.timer += 0.08
        self._update_rect()

    def draw(self, screen):
        cx = int(self.x)
        cy = int(self.base_y + math.sin(self.timer) * 5)
        DRAW_FN[self.food_id](screen, cx, cy)


# ── Heart (HP 회복) ────────────────────────────────────────
class Heart:
    def __init__(self, x, y):
        self.x         = float(x)
        self.base_y    = float(y)
        self.collected = False
        self.timer     = 0.0
        self.radius    = 14
        d = self.radius * 2
        self.rect = pygame.Rect(0, 0, d, d)
        self._update_rect()

    def _update_rect(self):
        cy = int(self.base_y + math.sin(self.timer) * 6)
        self.rect.x = int(self.x) - self.radius
        self.rect.y = cy - self.radius

    def update(self, speed):
        self.x -= speed
        self.timer += 0.06
        self._update_rect()

    def draw(self, screen):
        cx = int(self.x)
        cy = int(self.base_y + math.sin(self.timer) * 6)
        r  = self.radius
        color  = (255,  60, 100)
        bright = (255, 170, 185)
        pygame.draw.circle(screen, color, (cx - r // 2, cy - 2), r // 2 + 2)
        pygame.draw.circle(screen, color, (cx + r // 2, cy - 2), r // 2 + 2)
        pygame.draw.polygon(screen, color, [
            (cx - r, cy + 2), (cx + r, cy + 2), (cx, cy + r + 3),
        ])
        pygame.draw.circle(screen, bright, (cx - r // 2 - 2, cy - 5), r // 4)


# ── CollectibleManager ─────────────────────────────────────
class CollectibleManager:
    COMBO_TIMEOUT = 90

    POSITIVE_BIAS = 0.6  # 긍정 음식 클러스터가 나올 확률

    WATER_SPAWN_MIN = 240   # 4초
    WATER_SPAWN_MAX = 360   # 6초

    def __init__(self, screen_width, ground_y):
        self.screen_width   = screen_width
        self.ground_y       = ground_y
        self.foods          = []
        self.water_bottles  = []
        self.spawn_timer    = 0
        self.spawn_interval = 90
        self._water_timer   = 0
        self._next_water    = random.randint(self.WATER_SPAWN_MIN, self.WATER_SPAWN_MAX)
        self._combo         = 0
        self._combo_timer   = 0
        self.current_theme  = 'school'

    def set_theme(self, theme):
        self.current_theme = theme

    @property
    def combo(self):
        return self._combo

    @property
    def multiplier(self):
        if self._combo < 10: return 1
        if self._combo < 25: return 2
        if self._combo < 50: return 3
        return 4

    def add_combo(self, n=1):
        self._combo += n
        self._combo_timer = self.COMBO_TIMEOUT

    # ── 클러스터 생성 ──────────────────────────────────────
    def _pick_cluster_food(self):
        theme     = self.current_theme
        positives = STAGE_FOODS_POS.get(theme, ())
        negatives = STAGE_FOODS_NEG.get(theme, ())
        if positives and negatives:
            pool = positives if random.random() < self.POSITIVE_BIAS else negatives
        else:
            pool = positives or negatives or STAGE_FOODS.get(theme, ())
        return random.choice(pool)['id'] if pool else None

    def _spawn_food_cluster(self):
        food_id = self._pick_cluster_food()
        if food_id is None:
            return
        sx = self.screen_width + 40
        pattern = random.choice(["line_h", "line_v", "arc", "zigzag", "scatter"])
        if pattern == "line_h":
            y = self.ground_y - random.randint(50, 130)
            for i in range(6):
                self.foods.append(Food(sx + i * 30, y, food_id))
        elif pattern == "line_v":
            for i in range(5):
                self.foods.append(Food(sx, self.ground_y - 50 - i * 25, food_id))
        elif pattern == "arc":
            for i in range(7):
                t = (i / 6) * math.pi
                self.foods.append(Food(
                    sx + i * 28,
                    self.ground_y - 60 - math.sin(t) * 70,
                    food_id,
                ))
        elif pattern == "zigzag":
            for i in range(6):
                y = self.ground_y - (100 if i % 2 == 0 else 55)
                self.foods.append(Food(sx + i * 32, y, food_id))
        else:  # scatter
            for _ in range(5):
                self.foods.append(Food(
                    sx + random.randint(0, 100),
                    self.ground_y - random.randint(40, 140),
                    food_id,
                ))

    def _spawn_water(self):
        sx = self.screen_width + 60
        y  = self.ground_y - random.randint(60, 130)
        self.water_bottles.append(Food(sx, y, 'water_bottle'))

    # 스킬: 젤리 파티 — 긍정 음식 3개 즉시 소환
    def spawn_food_burst(self):
        theme     = self.current_theme
        positives = STAGE_FOODS_POS.get(theme, ())
        pool      = positives or STAGE_FOODS.get(theme, ())
        food_id   = random.choice(pool)['id'] if pool else 'water_bottle'
        sx        = self.screen_width - random.randint(50, 250)
        for _ in range(3):
            self.foods.append(Food(
                sx + random.randint(0, 120),
                self.ground_y - random.randint(40, 140),
                food_id,
            ))

    # ── 업데이트 ───────────────────────────────────────────
    def update(self, speed, magnet_pos=None):
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self._spawn_food_cluster()

        self._water_timer += 1
        if self._water_timer >= self._next_water:
            self._water_timer = 0
            self._next_water  = random.randint(self.WATER_SPAWN_MIN, self.WATER_SPAWN_MAX)
            self._spawn_water()

        if self._combo_timer > 0:
            self._combo_timer -= 1
            if self._combo_timer == 0:
                self._combo = 0

        for f in self.foods:
            f.update(speed, magnet_pos)
        for w in self.water_bottles:
            w.update(speed, magnet_pos)

        self.foods         = [f for f in self.foods         if f.x > -30 and not f.collected]
        self.water_bottles = [w for w in self.water_bottles if w.x > -30 and not w.collected]

    def check_collision(self, player_rect):
        """수집된 음식 dict 리스트 반환. game.py에서 효과 처리 + 점수 가산."""
        collected = []
        for f in chain(self.foods, self.water_bottles):
            if not f.collected and player_rect.colliderect(f.rect):
                f.collected = True
                self.add_combo(1)
                collected.append({
                    'food_id':   f.food_id,
                    'attr':      f.attr,
                    'effect_id': f.effect_id,
                    'duration':  f.duration,
                    'score':     f.score,
                })
        return collected

    def reset_combo(self):
        self._combo       = 0
        self._combo_timer = 0

    def draw(self, screen):
        for f in self.foods:
            if not f.collected:
                f.draw(screen)
        for w in self.water_bottles:
            if not w.collected:
                w.draw(screen)
