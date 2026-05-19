import pygame
import sys
import json
import os
import random

import lang
from player import Player
from obstacle import ObstacleManager
from collectible import (CollectibleManager, Heart, PARTICLE_COLOR,
                         ATTR_POSITIVE, ATTR_NEGATIVE, ATTR_NEUTRAL)
from background import Background
from ui import UI
from particles import ParticleManager
from power_up import PowerUpManager, PowerUp
from sound_manager import SoundManager
from achievement import AchievementManager, JUNK_FOODS, SNACK_FOODS
from skill import SkillManager
from debuff import DebuffManager, TIMED_EFFECTS


def _save_path():
    if getattr(sys, 'frozen', False):
        folder = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')),
                              '냠냠건강탐험대')
        os.makedirs(folder, exist_ok=True)
    else:
        folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(folder, 'save_data.json')


def _read_save():
    try:
        with open(_save_path(), 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[save] read failed: {e}")
        return {}


def _write_save(data):
    try:
        with open(_save_path(), 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[save] write failed: {e}")


def _save_kv(**kwargs):
    """save_data.json에 임의 키 부분 업데이트."""
    data = _read_save()
    data.update(kwargs)
    _write_save(data)


class Game:
    MENU         = "menu"
    COUNTDOWN    = "countdown"
    PLAYING      = "playing"
    PAUSED       = "paused"
    GAME_OVER    = "game_over"
    SETTINGS     = "settings"
    DEVINFO      = "devinfo"
    GALLERY      = "gallery"
    ACHIEVEMENTS = "achievements"

    WIDTH    = 800
    HEIGHT   = 450
    GROUND_Y = 385
    FPS      = 60

    INITIAL_SPEED     = 5.0
    MAX_SPEED         = 15.0
    SPEED_UP_INTERVAL = 400
    SPEED_INCREMENT   = 0.35
    METERS_PER_TICK   = 0.05

    # 물게이지
    WATER_MAX        = 100.0
    WATER_DECAY_PER_M = 0.20
    WATER_REFILL     = 20.0

    HEART_SPAWN_INTERVAL = 500.0   # m마다 하트 1개 생성

    def __init__(self, screen):
        self.screen = screen
        self.clock  = pygame.time.Clock()
        self.state  = self.MENU

        saved = _read_save()
        self.high_score        = saved.get('high_score', 0)
        self._bgm_vol          = saved.get('bgm_vol',    0.5)
        self._sfx_vol          = saved.get('sfx_vol',    1.0)
        self._language         = saved.get('language',   'ko')
        self._seen_foods       = set(saved.get('seen_foods', []))
        self._seen_foods_dirty = False

        self.sounds          = SoundManager()
        self.achievement_mgr = AchievementManager(_save_path())
        self.sounds.set_bgm_volume(self._bgm_vol)
        self.sounds.set_sfx_volume(self._sfx_vol)
        self._settings_sel        = 0
        self._devinfo_scroll      = 0
        self._ach_scroll          = 0
        self._drag_scroll_view    = None    # None / 'devinfo' / 'ach'
        self._drag_scroll_offset  = 0
        # 이스터에그: 소희 버튼 24회 클릭 → 데이터 초기화
        self._sohee_clicks        = 0
        self._SOHEE_RESET_THRESHOLD = 24
        # 이스터에그: 타이틀 7회 클릭 → 교복 색 사이클
        self._title_clicks        = 0
        self._TITLE_OUTFIT_THRESHOLD = 7
        lang.set_lang(self._language)
        self._build_objects()

    def _build_objects(self):
        self.speed    = self.INITIAL_SPEED
        self.score    = 0
        self.ticks    = 0
        self.distance = 0.0
        self.player          = Player(150, self.GROUND_Y)
        self.bg              = Background(self.WIDTH, self.HEIGHT, self.GROUND_Y)
        self.obstacle_mgr    = ObstacleManager(self.WIDTH, self.GROUND_Y)
        self.collectible_mgr = CollectibleManager(self.WIDTH, self.GROUND_Y)
        self.powerup_mgr     = PowerUpManager(self.WIDTH, self.GROUND_Y)
        self.particles       = ParticleManager()
        self.ui              = UI(self.WIDTH, self.HEIGHT, self._language)
        self.total_foods          = 0
        self._shield_hit_flag     = False
        self.skill_mgr            = SkillManager()
        self.debuff_mgr           = DebuffManager()
        self.water_gauge          = self.WATER_MAX
        self._last_distance       = 0.0
        self._effect_popup_cooldown = {}   # effect_id -> last shown tick

        # 업적용 메트릭 ────────────────────────────────────
        self.positive_count           = 0
        self.negative_count           = 0
        self.neutral_count            = 0
        self.food_id_set              = set()
        self.water_count              = 0
        self.heart_count              = 0
        self.cola_count               = 0
        self.junk_count               = 0
        self.snack_count              = 0
        self.skill_count              = 0
        self.used_skill_ids           = set()
        self.invincible_used          = False
        self.water_above_50_distance  = 0.0
        self.hp_full_distance         = 0.0
        self.last_breath_distance     = 0.0
        self.thirst_distance          = 0.0
        self.shield_active_distance   = 0.0
        self.visited_stages           = {'school'}
        self.returned_to_school       = False
        self._left_school             = False
        self._prev_theme              = 'school'
        self._stats_last_distance     = 0.0
        self._new_record_flag         = False
        self._game_over_triggered = False
        self._heart           = None
        self._next_heart_dist = self.HEART_SPAWN_INTERVAL
        if hasattr(self, 'achievement_mgr'):
            self.achievement_mgr.reset_session()
        self._countdown_value = 3
        self._countdown_timer = 0
        self._countdown_ticks = self.FPS

    def _start_countdown(self):
        self._build_objects()
        self.sounds.bgm.stop()
        self.state = self.COUNTDOWN

    def _flush_saves(self):
        self.achievement_mgr.flush()
        if self._seen_foods_dirty:
            _save_kv(seen_foods=sorted(self._seen_foods))
            self._seen_foods_dirty = False

    def _reset_save_data(self):
        # 이스터에그: 진행 데이터 초기화. 설정(언어/볼륨)은 보존.
        self.high_score = 0
        self._new_record_flag = False
        self._seen_foods.clear()
        self._seen_foods_dirty = False   # 직접 즉시 기록
        self.achievement_mgr.clear_all()
        _save_kv(high_score=0, seen_foods=[])
        # UI 캐시도 같이 비움 (잠금 흑백 도형 다시 생성)
        self.ui._food_locked_cache.clear()
        self.ui.show_easter_egg_message(lang.T('easter_egg_reset'))

    # ── 이벤트 ────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _save_kv(high_score=self.high_score)
                self._flush_saves()
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEWHEEL:
                if self.state == self.DEVINFO:
                    delta = -event.y * 25
                    self._devinfo_scroll = max(
                        0, min(self._devinfo_scroll + delta,
                               self.ui._devinfo_max_scroll))
                elif self.state == self.ACHIEVEMENTS:
                    delta = -event.y * 30
                    self._ach_scroll = max(
                        0, min(self._ach_scroll + delta,
                               self.ui._ach_max_scroll))

            elif event.type == pygame.MOUSEMOTION and self._drag_scroll_view:
                target_top = event.pos[1] - self._drag_scroll_offset
                new_val = self.ui.scroll_value_for(self._drag_scroll_view, target_top)
                if self._drag_scroll_view == 'devinfo':
                    self._devinfo_scroll = new_val
                elif self._drag_scroll_view == 'ach':
                    self._ach_scroll = new_val

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._drag_scroll_view = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == self.MENU:
                    if (self.ui.gallery_btn_rect and
                            self.ui.gallery_btn_rect.collidepoint(event.pos)):
                        self.state = self.GALLERY
                    elif (self.ui.achievements_btn_rect and
                            self.ui.achievements_btn_rect.collidepoint(event.pos)):
                        self.state = self.ACHIEVEMENTS
                        self._ach_scroll = 0
                        pygame.key.set_repeat(400, 30)
                    elif (self.ui.settings_btn_rect and
                            self.ui.settings_btn_rect.collidepoint(event.pos)):
                        self.state = self.SETTINGS
                    elif (self.ui.devinfo_btn_rect and
                            self.ui.devinfo_btn_rect.collidepoint(event.pos)):
                        self.state = self.DEVINFO
                        self._devinfo_scroll = 0
                        pygame.key.set_repeat(400, 30)
                    elif (self.ui.title_rect and
                            self.ui.title_rect.collidepoint(event.pos)):
                        self._title_clicks += 1
                        if self._title_clicks >= self._TITLE_OUTFIT_THRESHOLD:
                            self._title_clicks = 0
                            from player import cycle_outfit
                            cycle_outfit()
                            self.ui.show_easter_egg_message(lang.T('easter_egg_outfit'))
                elif self.state == self.DEVINFO:
                    offset = self.ui.scroll_thumb_hit('devinfo', event.pos)
                    if offset is not None:
                        self._drag_scroll_view   = 'devinfo'
                        self._drag_scroll_offset = offset
                    elif self.ui.try_cycle_sohee(event.pos):
                        self._sohee_clicks += 1
                        if self._sohee_clicks >= self._SOHEE_RESET_THRESHOLD:
                            self._sohee_clicks = 0
                            self._reset_save_data()
                elif self.state == self.ACHIEVEMENTS:
                    offset = self.ui.scroll_thumb_hit('ach', event.pos)
                    if offset is not None:
                        self._drag_scroll_view   = 'ach'
                        self._drag_scroll_offset = offset
                elif self.state == self.SETTINGS:
                    result = self.ui.handle_settings_click(event.pos)
                    if result is not None:
                        idx, val = result
                        self._settings_sel = idx
                        if idx == 0:
                            self._bgm_vol = val
                            self.sounds.set_bgm_volume(val)
                        elif idx == 1:
                            self._sfx_vol = val
                            self.sounds.set_sfx_volume(val)
                        elif idx == 2:
                            self._cycle_language(1)

            elif event.type == pygame.KEYDOWN:
                if self.state == self.MENU:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self._start_countdown()
                    elif event.key == pygame.K_o:
                        self.state = self.SETTINGS
                    elif event.key == pygame.K_i:
                        self.state = self.DEVINFO
                        self._devinfo_scroll = 0

                elif self.state == self.COUNTDOWN:
                    pass

                elif self.state == self.PLAYING:
                    if event.key in (pygame.K_SPACE, pygame.K_UP):
                        jumped, is_double = self.player.jump()
                        if jumped:
                            self.sounds.play('double_jump' if is_double else 'jump')
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.player.slide_held = True
                        self.player.slide()
                        self.sounds.play('slide')
                    elif event.key == pygame.K_z:
                        result = self.skill_mgr.try_activate()
                        if result:
                            self.sounds.play('skill')
                            self.skill_count += 1
                            self.used_skill_ids.add(result['id'])
                    elif event.key == pygame.K_p:
                        self.state = self.PAUSED
                        self.sounds.bgm.pause()

                elif self.state == self.PAUSED:
                    if event.key == pygame.K_p:
                        self.state = self.PLAYING
                        self.sounds.bgm.unpause()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = self.MENU
                        self._flush_saves()
                        self._build_objects()
                        self.sounds.bgm.stop()

                elif self.state == self.GAME_OVER:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self._start_countdown()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = self.MENU
                        self.sounds.bgm.stop()

                elif self.state == self.GALLERY:
                    if event.key == pygame.K_ESCAPE:
                        self.state = self.MENU

                elif self.state == self.ACHIEVEMENTS:
                    if event.key == pygame.K_ESCAPE:
                        self.state = self.MENU
                        pygame.key.set_repeat()
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self._ach_scroll = min(
                            self._ach_scroll + 30, self.ui._ach_max_scroll)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self._ach_scroll = max(self._ach_scroll - 30, 0)

                elif self.state == self.DEVINFO:
                    if event.key == pygame.K_ESCAPE:
                        self.state = self.MENU
                        pygame.key.set_repeat()
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self._devinfo_scroll = min(
                            self._devinfo_scroll + 25, self.ui._devinfo_max_scroll)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self._devinfo_scroll = max(self._devinfo_scroll - 25, 0)

                elif self.state == self.SETTINGS:
                    if event.key == pygame.K_ESCAPE:
                        _save_kv(bgm_vol=round(self._bgm_vol, 2),
                                 sfx_vol=round(self._sfx_vol, 2),
                                 language=self._language)
                        self.state = self.MENU
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self._settings_sel = (self._settings_sel - 1) % 3
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self._settings_sel = (self._settings_sel + 1) % 3
                    elif event.key == pygame.K_LEFT:
                        if self._settings_sel == 2:
                            self._cycle_language(-1)
                        else:
                            self._adjust_volume(-0.1)
                    elif event.key == pygame.K_RIGHT:
                        if self._settings_sel == 2:
                            self._cycle_language(1)
                        else:
                            self._adjust_volume(0.1)

            elif event.type == pygame.KEYUP:
                if self.state == self.PLAYING:
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        self.player.slide_held = False
                        self.player.end_slide()

    # ── 업데이트 ───────────────────────────────────────────
    def _update(self):
        self.ui.update_popup()           # 칭찬스티커 팝업
        self.ui.update_effect_popups()   # 효과 팝업

        if self.state == self.COUNTDOWN:
            self._update_countdown()
            return
        if self.state != self.PLAYING:
            return

        self.ticks += 1
        if self.ticks % self.SPEED_UP_INTERVAL == 0:
            self.speed = min(self.speed + self.SPEED_INCREMENT, self.MAX_SPEED)
            self.sounds.bgm.update(self.speed)

        self.distance += self.METERS_PER_TICK * (self.speed / self.INITIAL_SPEED)

        self.skill_mgr.update()
        self.debuff_mgr.update()
        self._update_water_gauge()
        self._update_stats()

        # 활성 효과를 player에 반영
        self.player.jump_force_mult     = self.debuff_mgr.jump_force_mult
        self.player.slide_dur_mult      = self.debuff_mgr.slide_dur_mult
        self.player.double_jump_blocked = self.debuff_mgr.double_jump_blocked
        self.player.slide_blocked       = self.debuff_mgr.slide_blocked

        # 시간 감속 스킬: 장애물·배경 속도를 0.4배로
        eff_speed = self.speed
        if self.skill_mgr.active and self.skill_mgr.effect_id == 'slowdown':
            eff_speed *= 0.4
        # 디버프 속도 배율 (slow_freeze)
        eff_speed *= self.debuff_mgr.speed_mult

        pcx = self.player.x + self.player.width  // 2
        pcy = self.player.y + self.player.height // 2

        magnet_pos = (pcx, pcy) if self.powerup_mgr.magnet_active else None

        self.bg.update(eff_speed, self.distance)
        self.obstacle_mgr.set_theme(self.bg.current_theme)
        self.collectible_mgr.set_theme(self.bg.current_theme)
        self.player.update()
        self.obstacle_mgr.update(eff_speed, self.distance)
        self.collectible_mgr.update(eff_speed, magnet_pos)
        self.powerup_mgr.update(eff_speed)

        if self._heart is not None and not self._heart.collected:
            self._heart.update(eff_speed)
            if self._heart.x < -60:
                self._heart = None
            elif self._heart.rect.colliderect(self.player.rect):
                self._heart = None
                self.player.hp += 1
                self.heart_count += 1
                self.sounds.play('collect')
                self.particles.emit_collect(pcx, pcy, (255, 80, 100))

        if self._heart is None and self.distance >= self._next_heart_dist:
            self._heart = Heart(
                self.WIDTH + 80,
                self.GROUND_Y - random.randint(70, 130),
            )
            self._next_heart_dist += self.HEART_SPAWN_INTERVAL

        # 젤리 파티 스킬: 10틱마다 음식 3개 자동 생성
        if self.skill_mgr.active and self.skill_mgr.effect_id == 'jelly_party':
            if self.ticks % 10 == 0:
                self.collectible_mgr.spawn_food_burst()
        self.particles.update()

        if self.player.just_landed:
            self.particles.emit_land_dust(pcx, self.GROUND_Y)

        self.score += 1

        # 음식 수집 — 효과 처리
        collected = self.collectible_mgr.check_collision(self.player.rect)
        if collected:
            self._process_collected(collected, pcx, pcy)

        activated = self.powerup_mgr.check_collision(self.player.rect)
        for kind in activated:
            self.sounds.play('magnet' if kind == 'magnet' else 'shield_on')

        obstacle_hit = self.obstacle_mgr.check_collision(self.player.rect)
        invincible   = (self.skill_mgr.active
                        and self.skill_mgr.effect_id == 'invincible')
        if obstacle_hit and invincible:
            self.invincible_used = True
        if obstacle_hit and not invincible:
            if self.powerup_mgr.use_shield():
                self._shield_hit_flag = True
                self.sounds.play('shield_hit')
                self.particles.emit_hit(pcx, pcy)
                self.player.invincible = self.player.INVINCIBLE_FRAMES
            else:
                hit = self.player.take_hit()
                if hit:
                    self.sounds.play('hit')
                    self.particles.emit_hit(pcx, pcy)
                    if not self.player.alive and not self._game_over_triggered:
                        self._game_over_triggered = True
                        self.sounds.bgm.play_game_over()
                        self.particles.emit_game_over(pcx, pcy)
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self._new_record_flag = True
                            _save_kv(high_score=self.high_score)
                        self.state = self.GAME_OVER

        # ── 칭찬스티커 체크 ──────────────────────────────────
        newly = self.achievement_mgr.check(self._build_stats())
        self._shield_hit_flag = False
        for ach in newly:
            self.ui.push_achievement(ach)

        # 게임 오버로 이번 틱이 전환됐다면 누적된 업적·도감 데이터를 디스크에 기록
        if self.state == self.GAME_OVER:
            self._flush_saves()

    # ── 음식 수집 처리 ─────────────────────────────────────
    def _process_collected(self, collected, pcx, pcy):
        mult       = self.collectible_mgr.multiplier
        skill_mult = 5 if (self.skill_mgr.active and
                           self.skill_mgr.effect_id == 'score_blast') else 1
        score_buff = self.debuff_mgr.score_mult

        # 콤보 정지 디버프 활성 시 콤보 무효화
        if self.debuff_mgr.combo_frozen:
            self.collectible_mgr.reset_combo()

        gauge_total = 0
        for c in collected:
            attr = c['attr']
            eid  = c['effect_id']
            fid  = c['food_id']

            # 점수 가산 (모든 음식)
            self.score += int(c['score'] * mult * skill_mult * score_buff)
            self.total_foods += 1

            # 업적 메트릭
            self.food_id_set.add(fid)
            if fid not in self._seen_foods:
                self._seen_foods.add(fid)
                self._seen_foods_dirty = True
            if attr == ATTR_POSITIVE:
                self.positive_count += 1
            elif attr == ATTR_NEGATIVE:
                self.negative_count += 1
            else:
                self.neutral_count += 1
            if fid == 'water_bottle':
                self.water_count += 1
            if fid == 'cola':
                self.cola_count += 1
            if fid in JUNK_FOODS:
                self.junk_count += 1
            if fid in SNACK_FOODS:
                self.snack_count += 1

            # 게이지 가산 (긍정·무속성 한정) — gauge_freeze 디버프 시 무효
            if attr != ATTR_NEGATIVE and not self.debuff_mgr.gauge_frozen:
                gauge_total += max(1, int(c['score'] / 50))

            # 효과 적용 (즉시 / 지속) — popup 표시 가능 여부 반환
            triggered = self._apply_effect(eid, c.get('duration', 0))
            if triggered:
                self._push_effect_popup(triggered, attr)

            # 파티클
            color = random.choice(PARTICLE_COLOR.get(attr, [(255, 255, 255)]))
            self.particles.emit_collect(pcx, pcy, color)

        if gauge_total > 0:
            self.skill_mgr.add_gauge(normal=gauge_total)

        self.sounds.play('collect')

    # ── 효과 팝업 푸시 (1.5초 쿨다운으로 중복 방지) ─────────
    def _push_effect_popup(self, effect_id, attr):
        last = self._effect_popup_cooldown.get(effect_id, -1000)
        if self.ticks - last < 90:   # 1.5초
            return
        self._effect_popup_cooldown[effect_id] = self.ticks
        text = lang.T(f"effect_{effect_id}_short")
        self.ui.push_effect(text, attr)

    # ── 효과 핸들러 ────────────────────────────────────────
    # 발동된 effect_id를 반환 (팝업에 사용). 발동 안 된 경우 None.
    def _gain_hp_or_score(self):
        if self.player.hp < self.player.MAX_HP:
            self.player.hp += 1
        else:
            self.score += 100

    def _apply_effect(self, effect_id, duration):
        if effect_id == 'hp_or_score':
            self._gain_hp_or_score()
        elif effect_id == 'hp_chance':
            if random.random() >= 0.30:
                return None     # 실패 시 팝업 없음
            self._gain_hp_or_score()
        elif effect_id == 'combo_plus':
            self.collectible_mgr.add_combo(3)
        elif effect_id == 'rice_combo':
            self.skill_mgr.add_gauge(normal=10)
            self.collectible_mgr.add_combo(1)
        elif effect_id == 'gauge_l':
            self.skill_mgr.add_gauge(normal=20)
        elif effect_id == 'gauge_s':
            self.skill_mgr.add_gauge(normal=15)
        elif effect_id == 'gauge_drain':
            self.skill_mgr.gauge = max(0.0, self.skill_mgr.gauge - 25)
        elif effect_id == 'magnet_short':
            self.powerup_mgr.magnet_timer = PowerUp.MAGNET_SHORT_DURATION
            self.powerup_mgr.magnet_total = PowerUp.MAGNET_SHORT_DURATION
        elif effect_id == 'shield_grant':
            self.powerup_mgr.shield_active = True
        elif effect_id == 'cleanse':
            self.debuff_mgr.clear_negative()
        elif effect_id == 'combo_break':
            self.collectible_mgr.reset_combo()
        elif effect_id == 'water_refill':
            self.water_gauge = min(self.WATER_MAX, self.water_gauge + self.WATER_REFILL)
        elif effect_id == 'water_drain':
            self.water_gauge = max(0.0, self.water_gauge - 15)
        elif effect_id in ('score_bonus', 'score_l'):
            pass            # 점수는 c['score']로 이미 가산됨
        elif effect_id in TIMED_EFFECTS:
            self.debuff_mgr.add(effect_id, frames=duration if duration > 0 else None)
        else:
            return None
        return effect_id

    # ── 물게이지 ───────────────────────────────────────────
    def _update_water_gauge(self):
        delta_dist = self.distance - self._last_distance
        self._last_distance = self.distance
        self.water_gauge = max(0.0, self.water_gauge - self.WATER_DECAY_PER_M * delta_dist)
        # 갈증 디버프 토글
        if self.water_gauge <= 0.0:
            self.debuff_mgr.add('thirst', frames=30)  # 매 0.5초 갱신, 자연 소멸

    # ── 업적 메트릭 누적 ──────────────────────────────────
    def _update_stats(self):
        delta = self.distance - self._stats_last_distance
        self._stats_last_distance = self.distance
        if delta <= 0:
            return
        if self.water_gauge >= self.WATER_MAX * 0.5:
            self.water_above_50_distance += delta
        if self.player.hp >= self.player.MAX_HP:
            self.hp_full_distance += delta
        if self.player.hp == 1:
            self.last_breath_distance += delta
        if self.debuff_mgr.is_active('thirst'):
            self.thirst_distance += delta
        if self.powerup_mgr.shield_active:
            self.shield_active_distance += delta

        # 스테이지 변화 추적
        new_theme = self.bg.current_theme
        if new_theme != self._prev_theme:
            self.visited_stages.add(new_theme)
            if self._left_school and new_theme == 'school':
                self.returned_to_school = True
            if new_theme != 'school':
                self._left_school = True
            self._prev_theme = new_theme

    def _build_stats(self):
        return {
            'distance':                   self.distance,
            'score':                      self.score,
            'combo':                      self.collectible_mgr.combo,
            'multiplier':                 self.collectible_mgr.multiplier,
            'theme':                      self.bg.current_theme,
            'total_foods':                self.total_foods,
            'positive_count':             self.positive_count,
            'negative_count':             self.negative_count,
            'food_id_set':                self.food_id_set,
            'water_count':                self.water_count,
            'heart_count':                self.heart_count,
            'cola_count':                 self.cola_count,
            'junk_count':                 self.junk_count,
            'snack_count':                self.snack_count,
            'hp':                         self.player.hp,
            'max_hp':                     self.player.MAX_HP,
            'water_above_50_distance':    self.water_above_50_distance,
            'hp_full_distance':           self.hp_full_distance,
            'last_breath_distance':       self.last_breath_distance,
            'thirst_distance':            self.thirst_distance,
            'shield_active_distance':     self.shield_active_distance,
            'skill_count':                self.skill_count,
            'used_skill_ids':             self.used_skill_ids,
            'invincible_used':            self.invincible_used,
            'shield_block':               self._shield_hit_flag,
            'visited_stages':             self.visited_stages,
            'returned_to_school':         self.returned_to_school,
            'new_record':                 self._new_record_flag,
        }

    def _cycle_language(self, direction):
        langs = ['ko', 'en', 'vi']
        idx = langs.index(self._language) if self._language in langs else 0
        self._language = langs[(idx + direction) % len(langs)]
        lang.set_lang(self._language)
        self.ui.set_language(self._language)
        _save_kv(language=self._language)

    def _adjust_volume(self, delta):
        if self._settings_sel == 0:
            self._bgm_vol = round(max(0.0, min(1.0, self._bgm_vol + delta)), 1)
            self.sounds.set_bgm_volume(self._bgm_vol)
        else:
            self._sfx_vol = round(max(0.0, min(1.0, self._sfx_vol + delta)), 1)
            self.sounds.set_sfx_volume(self._sfx_vol)

    def _update_countdown(self):
        self._countdown_timer += 1
        if self._countdown_timer >= self._countdown_ticks:
            self._countdown_timer = 0
            self._countdown_value -= 1
            if self._countdown_value < 0:
                self.state = self.PLAYING
                self.sounds.bgm.start(self.speed)

    # ── 그리기 ─────────────────────────────────────────────
    def _draw(self):
        self.bg.draw(self.screen)

        if self.state == self.MENU:
            self.ui.draw_menu(self.screen)

        elif self.state == self.SETTINGS:
            self.ui.draw_settings(self.screen, self._bgm_vol, self._sfx_vol,
                                  self._settings_sel, self._language)

        elif self.state == self.GALLERY:
            self.ui.draw_menu(self.screen)   # 메뉴 위에 도감 오버레이
            self.ui.draw_gallery(self.screen, self._seen_foods)

        elif self.state == self.ACHIEVEMENTS:
            self.ui.draw_menu(self.screen)
            self.ui.draw_achievements(
                self.screen, self._ach_scroll, self.achievement_mgr.lifetime_unlocked)

        elif self.state == self.DEVINFO:
            self.ui.draw_gameinfo(self.screen, self._devinfo_scroll)

        elif self.state == self.COUNTDOWN:
            self.player.draw(self.screen)
            self.ui.draw_countdown(self.screen, self._countdown_value)

        elif self.state in (self.PLAYING, self.PAUSED, self.GAME_OVER):
            self.particles.draw(self.screen)
            self.collectible_mgr.draw(self.screen)
            if self._heart is not None and not self._heart.collected:
                self._heart.draw(self.screen)
            self.obstacle_mgr.draw(self.screen)
            self.powerup_mgr.draw(self.screen)
            self.player.draw(self.screen, shield_active=self.powerup_mgr.shield_active)

            warnings = self.obstacle_mgr.get_incoming_warnings()
            thirsty = self.debuff_mgr.is_active('thirst')
            self.ui.draw_hud(
                self.screen, self.score, self.high_score, self.speed,
                self.player.hp,
                self.collectible_mgr.combo,
                self.collectible_mgr.multiplier,
                magnet_timer=self.powerup_mgr.magnet_timer,
                magnet_total=self.powerup_mgr.magnet_total,
                shield_active=self.powerup_mgr.shield_active,
                distance=self.distance,
                warnings=warnings,
                skill_gauge=self.skill_mgr.gauge_ratio,
                skill_active=self.skill_mgr.active,
                skill_effect=self.skill_mgr.effect,
                skill_ratio=self.skill_mgr.skill_ratio,
                water_ratio=self.water_gauge / self.WATER_MAX,
                thirsty=thirsty,
            )
            # 시야 좁힘 / 갈증 오버레이 (HUD 위에 덮음)
            self.ui.draw_overlay_effects(
                self.screen,
                vision_blur=self.debuff_mgr.vision_blur,
                thirsty=thirsty,
            )
            if self.state == self.PAUSED:
                self.ui.draw_paused(self.screen)
            elif self.state == self.GAME_OVER:
                self.ui.draw_game_over(self.screen, self.score,
                                       self.high_score, self.distance)

        if self.state in (self.PLAYING, self.PAUSED, self.GAME_OVER):
            self.ui.draw_effect_popups(self.screen)
        self.ui.draw_achievement_popup(self.screen)
        pygame.display.flip()

    def run(self):
        while True:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(self.FPS)
