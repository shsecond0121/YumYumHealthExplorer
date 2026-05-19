import json


# ── 업적 카탈로그 (50개) ──────────────────────────────────
ACHIEVEMENTS = [
    # A. 진행·거리 (8)
    {'id': 'first_run',          'category': 'a'},
    {'id': 'dist_100',           'category': 'a'},
    {'id': 'dist_500',           'category': 'a'},
    {'id': 'dist_1000',          'category': 'a'},
    {'id': 'dist_2000',          'category': 'a'},
    {'id': 'dist_3000',          'category': 'a'},
    {'id': 'dist_5000',          'category': 'a'},
    {'id': 'dist_10000',         'category': 'a'},

    # B. 스테이지 (5)
    {'id': 'stage_street',       'category': 'b'},
    {'id': 'stage_playground',   'category': 'b'},
    {'id': 'stage_home',         'category': 'b'},
    {'id': 'stage_loop',         'category': 'b'},
    {'id': 'all_stages',         'category': 'b'},

    # C. 콤보 (5)
    {'id': 'combo_10',           'category': 'c'},
    {'id': 'combo_30',           'category': 'c'},
    {'id': 'combo_50',           'category': 'c'},
    {'id': 'combo_100',          'category': 'c'},
    {'id': 'max_multiplier',     'category': 'c'},

    # D. 음식 수집 (3)
    {'id': 'jelly_50',           'category': 'd'},
    {'id': 'food_100_run',       'category': 'd'},
    {'id': 'positive_30',        'category': 'd'},

    # E. 음식 카테고리 (7)
    {'id': 'school_master',      'category': 'e'},
    {'id': 'street_master',      'category': 'e'},
    {'id': 'playground_master',  'category': 'e'},
    {'id': 'home_master',        'category': 'e'},
    {'id': 'all_pos_master',     'category': 'e'},
    {'id': 'veggie_lover',       'category': 'e'},
    {'id': 'protein_set',        'category': 'e'},

    # F. 회피·챌린지 (4)
    {'id': 'pure_run',           'category': 'f'},
    {'id': 'no_cola',            'category': 'f'},
    {'id': 'junk_avoider',       'category': 'f'},
    {'id': 'snack_avoider',      'category': 'f'},

    # G. 물게이지 (5)
    {'id': 'water_first',        'category': 'g'},
    {'id': 'water_5_run',        'category': 'g'},
    {'id': 'water_10_run',       'category': 'g'},
    {'id': 'hydration_master',   'category': 'g'},
    {'id': 'thirst_survive',     'category': 'g'},

    # H. HP·생존 (4)
    {'id': 'shield_block',       'category': 'h'},
    {'id': 'hp_full_500',        'category': 'h'},
    {'id': 'last_breath',        'category': 'h'},
    {'id': 'heart_collector',    'category': 'h'},

    # I. 스킬 (5)
    {'id': 'first_skill',        'category': 'i'},
    {'id': 'skill_master',       'category': 'i'},
    {'id': 'invincible_clear',   'category': 'i'},
    {'id': 'all_skills',         'category': 'i'},
    {'id': 'shield_perfect',     'category': 'i'},

    # J. 점수 (4)
    {'id': 'score_5000',         'category': 'j'},
    {'id': 'score_20000',        'category': 'j'},
    {'id': 'score_50000',        'category': 'j'},
    {'id': 'new_record',         'category': 'j'},
]

# 카테고리 순서 (UI에서 헤더 출력 순)
CATEGORY_ORDER = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']

# 카테고리별 업적 목록 (UI 진행도 화면에서 매 프레임 그룹핑하지 않도록 미리 계산)
BY_CATEGORY = {k: [a for a in ACHIEVEMENTS if a['category'] == k]
               for k in CATEGORY_ORDER}

_BY_ID = {a['id']: a for a in ACHIEVEMENTS}

# 음식 카테고리 그룹 (조건 평가용)
SCHOOL_POS_FOODS     = ('milk', 'apple', 'kimbap')
STREET_POS_FOODS     = ('banana_milk', 'triangle_kimbap', 'soy_milk')
PLAYGROUND_POS_FOODS = ('cherry_tomato', 'fruit_juice', 'roasted_sweet_potato')
HOME_POS_FOODS       = ('rice_bowl', 'seaweed_soup', 'grilled_fish')
ALL_POS_FOODS        = (SCHOOL_POS_FOODS + STREET_POS_FOODS
                        + PLAYGROUND_POS_FOODS + HOME_POS_FOODS)
VEGGIE_FOODS         = ('apple', 'cherry_tomato', 'roasted_sweet_potato')
PROTEIN_FOODS        = ('milk', 'soy_milk', 'grilled_fish')
JUNK_FOODS           = ('burger', 'pizza', 'instant_ramen', 'cola')
SNACK_FOODS          = ('candy', 'cotton_candy', 'ice_cream', 'chocolate')
ALL_STAGES           = ('school', 'street', 'playground', 'home')


def _has_all(food_set, required):
    return all(fid in food_set for fid in required)


class AchievementManager:
    """업적은 두 set으로 관리한다.

    - lifetime: 한 번이라도 달성한 업적 (영구 저장, 진행도 화면용)
    - session : 이번 게임에 달성한 업적 (팝업 중복 방지용, reset_session에서 비움)

    팝업은 session 기준으로 띄워서 같은 게임에 같은 업적은 한 번만 등장하고,
    저장은 lifetime 기준이라 한 번이라도 달성하면 영구 기록된다.

    저장은 dirty flag로 지연시켜 게임 중 disk I/O가 일어나지 않도록 한다.
    flush()를 게임 오버·종료 같은 안전한 지점에서 호출해 실제 기록한다.
    """

    def __init__(self, save_path):
        self._path     = save_path
        self._lifetime = self._load()
        self._session  = set()
        self._dirty    = False

    def _load(self):
        try:
            with open(self._path) as f:
                saved = set(json.load(f).get('achievements', []))
                return {a for a in saved if a in _BY_ID}
        except Exception:
            return set()

    def flush(self):
        if not self._dirty:
            return
        try:
            try:
                with open(self._path) as f:
                    data = json.load(f)
            except Exception:
                data = {}
            data['achievements'] = sorted(self._lifetime)
            with open(self._path, 'w') as f:
                json.dump(data, f)
            self._dirty = False
        except Exception:
            pass

    def reset_session(self):
        self._session = set()

    def clear_all(self):
        """이스터에그용: lifetime/session 업적을 모두 비우고 즉시 디스크 반영."""
        self._lifetime.clear()
        self._session.clear()
        self._dirty = True
        self.flush()

    def check(self, stats):
        fids = stats.get('food_id_set', set())
        cond = {
            # A. 진행·거리
            'first_run':         True,
            'dist_100':          stats['distance'] >=   100,
            'dist_500':          stats['distance'] >=   500,
            'dist_1000':         stats['distance'] >=  1000,
            'dist_2000':         stats['distance'] >=  2000,
            'dist_3000':         stats['distance'] >=  3000,
            'dist_5000':         stats['distance'] >=  5000,
            'dist_10000':        stats['distance'] >= 10000,

            # B. 스테이지
            'stage_street':      stats['theme'] == 'street',
            'stage_playground':  stats['theme'] == 'playground',
            'stage_home':        stats['theme'] == 'home',
            'stage_loop':        stats.get('returned_to_school', False),
            'all_stages':        all(s in stats.get('visited_stages', set())
                                     for s in ALL_STAGES),

            # C. 콤보
            'combo_10':          stats['combo']      >=  10,
            'combo_30':          stats['combo']      >=  30,
            'combo_50':          stats['combo']      >=  50,
            'combo_100':         stats['combo']      >= 100,
            'max_multiplier':    stats['multiplier'] >=   4,

            # D. 음식 수집
            'jelly_50':          stats['total_foods']    >=  50,
            'food_100_run':      stats['total_foods']    >= 100,
            'positive_30':       stats['positive_count'] >=  30,

            # E. 음식 카테고리
            'school_master':     _has_all(fids, SCHOOL_POS_FOODS),
            'street_master':     _has_all(fids, STREET_POS_FOODS),
            'playground_master': _has_all(fids, PLAYGROUND_POS_FOODS),
            'home_master':       _has_all(fids, HOME_POS_FOODS),
            'all_pos_master':    _has_all(fids, ALL_POS_FOODS),
            'veggie_lover':      _has_all(fids, VEGGIE_FOODS),
            'protein_set':       _has_all(fids, PROTEIN_FOODS),

            # F. 회피·챌린지 (1000m / 500m 이상에서만 평가)
            'pure_run':          (stats['distance'] >= 1000
                                  and stats['negative_count'] == 0),
            'no_cola':           (stats['distance'] >= 1000
                                  and stats.get('cola_count', 0) == 0),
            'junk_avoider':      (stats['distance'] >= 1000
                                  and stats.get('junk_count', 0) == 0),
            'snack_avoider':     (stats['distance'] >=  500
                                  and stats.get('snack_count', 0) == 0),

            # G. 물게이지
            'water_first':       stats['water_count'] >= 1,
            'water_5_run':       stats['water_count'] >= 5,
            'water_10_run':      stats['water_count'] >= 10,
            'hydration_master':  (stats['distance'] >= 1000
                                  and stats['water_above_50_distance']
                                      >= 0.95 * stats['distance']),
            'thirst_survive':    stats['thirst_distance'] >= 100,

            # H. HP·생존
            'shield_block':      stats.get('shield_block', False),
            'hp_full_500':       stats['hp_full_distance']     >= 500,
            'last_breath':       stats['last_breath_distance'] >= 100,
            'heart_collector':   stats['heart_count']          >=   3,

            # I. 스킬
            'first_skill':       stats['skill_count'] >= 1,
            'skill_master':      stats['skill_count'] >= 5,
            'invincible_clear':  stats.get('invincible_used', False),
            'all_skills':        len(stats.get('used_skill_ids', set())) >= 4,
            'shield_perfect':    stats['shield_active_distance'] >= 1000,

            # J. 점수
            'score_5000':        stats['score']           >= 5000,
            'score_20000':       stats['score']           >= 20000,
            'score_50000':       stats['score']           >= 50000,
            'new_record':        stats.get('new_record', False),
        }

        newly = []
        for aid, met in cond.items():
            if not met or aid in self._session:
                continue
            self._session.add(aid)
            newly.append(_BY_ID[aid])
            if aid not in self._lifetime:
                self._lifetime.add(aid)
                self._dirty = True
        return newly

    @property
    def lifetime_unlocked(self):
        return self._lifetime
