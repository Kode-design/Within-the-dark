# WITHIN THE DARK - PROLOGUE PROTOTYPE (NEW ABILITY SYSTEM UPDATE)
# Built with Python & Pygame
# This is a major overhaul of Dread's abilities, replacing the Soul Essence
# system with a new set of four powerful, cooldown-based skills.
# FIX: Corrected TypeError in Player.update() by allowing it to accept extra arguments.

import pygame
import sys
import math
import array
import random

# --- 1. SETUP AND INITIALIZATION ---

pygame.init()
pygame.mixer.init()

# --- Game Window Settings ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Within The Dark - Prologue Prototype")

# --- Colors ---
BLACK = (0, 0, 0); WHITE = (255, 255, 255); PLAYER_COLOR = (150, 150, 255)
PLAYER_BLOCK_COLOR = (200, 200, 255); DREAD_COLOR = (50, 50, 80); ENEMY_COLOR = (255, 100, 100)
TILE_COLOR = (80, 60, 40); HITBOX_COLOR = (255, 255, 0); HEALTH_RED = (200, 0, 0)
HEALTH_GREEN = (0, 200, 0); UI_GRAY = (100, 100, 100); BG_COLOR_DARK = (10, 5, 15)
BG_COLOR_LIGHT = (40, 30, 50); CROSSHAIR_COLOR = (255, 255, 255); TEXT_COLOR = (230, 230, 230)
MENU_OVERLAY_COLOR = (0, 0, 0, 180); INTERACT_COLOR = (255, 223, 100); SPIRIT_COLOR = (200, 255, 255)
BOSS_COLOR = (180, 50, 50); STUN_COLOR = (255, 255, 0); COOLDOWN_COLOR = (180, 180, 180)
STAMINA_COLOR = (100, 180, 255)


# --- Game Clock & Constants ---
clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.8
TILE_SIZE = 40
STAMINA_MAX = 100
STAMINA_REGEN = 20
STAMINA_LIGHT_ATTACK = 5
STAMINA_HEAVY_ATTACK = 15
STAMINA_DASH = 20
STAMINA_BACKSTEP = 10
HAZARD_DAMAGE = 10

# --- Transition Variables ---
transition_phase = None
transition_target_state = None
transition_dialogue = ""
dialogue_timer = 0
transition_alpha = 0
FADE_SPEED = 8

# --- Cutscene Variables ---
cutscene_lines = [
    "Echoes of chains rattle in the darkness...",
    "A heavy coffin lid shifts with a groan.",
    "Khristopher: '...Who dares disturb my rest?'",
    "Khristopher: 'No... I sense the blood of mankind.'",
    "Khristopher: 'Then I shall rise once more.'"
]
cutscene_index = 0
cutscene_timer = 0
CUTSCENE_DELAY = 3500

# --- FONTS ---
font_small = pygame.font.Font(None, 32)
font_medium = pygame.font.Font(None, 50)
font_large = pygame.font.Font(None, 74)

# --- LEVEL MAP DATA ---
level_map = [
'                                                                                                    ',
'                                                                                                    ',
'    S                                                                                               ',
'  XXXXX                                                                                             ',
'                                     E                                                              ',
'       S                         XXXXXXXXX                                                          ',
'     XXXXX                 E                                        B                             X ',
'                          XXXXXX                                     XXX                            X ',
'      L                                                            XXXXXXX                        F X ',
'   P XXXXX                           E                            XXXXXXXXX                       XXX ',
'                                  XXXXXXXXX                      XXXXXXXXXXX                      XXXXX ',
'         E                     S                                XXXXXXXXXXXXX                    XXXXXXX ',
'      XXXXXX               XXXXXXXXXXXXX      GXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ',
'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ',
]
LEVEL_WIDTH = len(level_map[0]) * TILE_SIZE
LEVEL_HEIGHT = len(level_map) * TILE_SIZE

# --- Mini-map ---
MINIMAP_SCALE = 0.1
MINIMAP_WIDTH = int(LEVEL_WIDTH * MINIMAP_SCALE)
MINIMAP_HEIGHT = int(LEVEL_HEIGHT * MINIMAP_SCALE)
minimap_surface = pygame.Surface((MINIMAP_WIDTH, MINIMAP_HEIGHT))
explored_tiles = set()


# --- SOUND MANAGER & UI ---
class SoundManager:
    def __init__(self):
        self.sounds = {
            'light_attack': self.create_placeholder_sound(440, 0.1),
            'heavy_attack': self.create_placeholder_sound(220, 0.3),
            'player_hurt': self.create_placeholder_sound(330, 0.2),
            'interaction': self.create_placeholder_sound(660, 0.1),
            'screech': self.create_placeholder_sound(1200, 0.5),
            'devour': self.create_placeholder_sound(150, 0.8),
            'awakening': self.create_placeholder_sound(60, 0.8, volume=0.6, harmonics=[1,2])
        }
        self.play_music()

    def create_placeholder_sound(self, frequency, duration, volume=0.5, harmonics=None):
        sample_rate = pygame.mixer.get_init()[0]
        num_samples = int(sample_rate * duration)
        buf = array.array('h')
        harmonics = harmonics or [1]
        for i in range(num_samples):
            sample = 0
            for h in harmonics:
                sample += math.sin(2 * math.pi * frequency * h * i / sample_rate) / h
            buf.append(int(32767 * volume * sample / len(harmonics)))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play_music(self):
        self.music = self.create_placeholder_sound(80, 1.0, volume=0.15, harmonics=[1,2,3])
        self.music.play(-1)

    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
sound_manager = SoundManager()

def draw_player_health(surface, x, y, health, max_health):
    if health < 0: health = 0
    bar_length = 200; bar_height = 20; fill = (health / max_health) * bar_length
    outline_rect = pygame.Rect(x, y, bar_length, bar_height); fill_rect = pygame.Rect(x, y, fill, bar_height)
    pygame.draw.rect(surface, HEALTH_RED, outline_rect); pygame.draw.rect(surface, HEALTH_GREEN, fill_rect); pygame.draw.rect(surface, UI_GRAY, outline_rect, 2)

def draw_player_stamina(surface, x, y, stamina, max_stamina):
    bar_length = 200; bar_height = 10; fill = (stamina / max_stamina) * bar_length
    outline_rect = pygame.Rect(x, y, bar_length, bar_height)
    fill_rect = pygame.Rect(x, y, fill, bar_height)
    pygame.draw.rect(surface, (40,40,40), outline_rect)
    pygame.draw.rect(surface, STAMINA_COLOR, fill_rect)
    pygame.draw.rect(surface, UI_GRAY, outline_rect, 2)

def draw_boss_health(surface, boss):
    bar_length = 300
    bar_height = 25
    fill = (boss.health / boss.max_health) * bar_length
    outline_rect = pygame.Rect((SCREEN_WIDTH - bar_length)//2, 20, bar_length, bar_height)
    fill_rect = pygame.Rect(outline_rect.x, outline_rect.y, fill, bar_height)
    pygame.draw.rect(surface, HEALTH_RED, outline_rect)
    pygame.draw.rect(surface, HEALTH_GREEN, fill_rect)
    pygame.draw.rect(surface, UI_GRAY, outline_rect, 2)
def draw_text_box(surface, text):
    box_rect = pygame.Rect(50, SCREEN_HEIGHT - 150, SCREEN_WIDTH - 100, 120); pygame.draw.rect(surface, BLACK, box_rect); pygame.draw.rect(surface, UI_GRAY, box_rect, 3)
    text_surface = font_small.render(text, True, TEXT_COLOR); surface.blit(text_surface, (box_rect.x + 15, box_rect.y + 15))

def draw_cooldowns(surface, dread):
    abilities = [('1: Hand', dread.spectral_hand_cooldown, dread.last_hand_use),
                 ('2: Screech', dread.screech_cooldown, dread.last_screech_use),
                 ('3: Devour', dread.devour_cooldown, dread.last_devour_use),
                 ('4: Aspect', dread.aspect_cooldown, dread.last_aspect_use)]
    y_offset = 50
    for name, cooldown, last_use in abilities:
        time_since_use = pygame.time.get_ticks() - last_use
        color = HEALTH_GREEN
        text = f"{name}: Ready"
        if time_since_use < cooldown:
            color = COOLDOWN_COLOR
            text = f"{name}: {((cooldown - time_since_use)/1000):.1f}s"
        
        text_surf = font_small.render(text, True, color)
        surface.blit(text_surf, (SCREEN_WIDTH - text_surf.get_width() - 20, y_offset))
        y_offset += 30

def draw_minimap(surface, player, enemies):
    minimap_surface.fill((20,20,20))
    scale = MINIMAP_SCALE
    for r, row in enumerate(level_map):
        for c, char in enumerate(row):
            if (c, r) in explored_tiles:
                color = TILE_COLOR if char in ('X', 'G') else (40,40,40)
                pygame.draw.rect(minimap_surface, color,
                                 (c*TILE_SIZE*scale, r*TILE_SIZE*scale,
                                  TILE_SIZE*scale, TILE_SIZE*scale))
    pygame.draw.rect(minimap_surface, (0,255,0),
                     (player.rect.centerx*scale-2, player.rect.centery*scale-2,4,4))
    surface.blit(minimap_surface, (SCREEN_WIDTH - MINIMAP_WIDTH - 10, 10))

def create_placeholder_sprites(color, width, height, num_frames=4):
    sprites = []
    for i in range(num_frames):
        surf = pygame.Surface([width, height], pygame.SRCALPHA)
        shade = [max(0, c - i * 25) for c in color]
        pygame.draw.rect(surf, shade, (0, 0, width, height), border_radius=6)
        highlight = [min(255, c + 40) for c in color]
        pygame.draw.rect(surf, highlight, (4, 4, width - 8, height // 2), border_radius=4)
        pygame.draw.rect(surf, (0, 0, 0), (0, 0, width, height), 2, border_radius=6)
        sprites.append(surf)
    return sprites

def start_transition(target_state, dialogue=""):
    global transition_phase, transition_target_state, transition_dialogue, transition_alpha
    transition_phase = 'fade_out'
    transition_target_state = target_state
    transition_dialogue = dialogue
    transition_alpha = 0

def start_cutscene():
    global current_game_state, cutscene_index, cutscene_timer
    cutscene_index = 0
    cutscene_timer = 0
    current_game_state = 'CUTSCENE'
    sound_manager.play('awakening')

# --- 2. PLAYER CLASS ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.animations = {'idle': create_placeholder_sprites(PLAYER_COLOR, 40, 60, 2), 'walk': create_placeholder_sprites(PLAYER_COLOR, 40, 60, 4), 'attack': create_placeholder_sprites(PLAYER_COLOR, 40, 60, 3)}
        self.current_animation = 'idle'; self.animation_frame = 0; self.animation_speed = 0.1
        self.image = self.animations[self.current_animation][self.animation_frame]; self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = pygame.math.Vector2(0, 0); self.move_speed = 5; self.run_speed_multiplier = 1.6
        self.jump_strength = -18; self.is_on_ground = False
        self.facing_right = True; self.is_blocking = False; self.is_dashing = False
        self.max_health = 100; self.health = self.max_health; self.is_invincible = False
        self.invincibility_duration = 1000; self.invincibility_timer = 0
        self.is_attacking = False; self.attack_timer = 0; self.attack_cooldown = 400; self.last_attack_time = -self.attack_cooldown
        self.attack_hitbox = None; self.is_charging = False; self.charge_time = 0; self.charge_threshold = 300
        self.dash_speed = 15; self.dash_duration = 150; self.dash_timer = 0; self.dash_cooldown = 800; self.last_dash_time = -self.dash_cooldown
        self.is_backstepping = False; self.backstep_duration = 120; self.backstep_timer = 0
        self.backstep_cooldown = 600; self.last_backstep_time = -self.backstep_cooldown
        self.max_stamina = STAMINA_MAX; self.stamina = self.max_stamina; self.stamina_regen = STAMINA_REGEN
    def animate(self):
        self.animation_frame += self.animation_speed
        if self.animation_frame >= len(self.animations[self.current_animation]):
            self.animation_frame = 0
            if self.is_attacking: self.is_attacking = False; self.attack_hitbox = None
        self.image = self.animations[self.current_animation][int(self.animation_frame)]
        if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)
    
    # FIX: Added **kwargs to accept and ignore any unexpected arguments.
    def update(self, camera, tiles, **kwargs):
        if self.is_attacking: self.current_animation = 'attack'
        elif self.velocity.x != 0 and self.is_on_ground: self.current_animation = 'walk'
        else: self.current_animation = 'idle'
        self.animate()
        mouse_pos = pygame.mouse.get_pos(); player_screen_x = self.rect.centerx - camera.camera_x
        if not self.is_dashing and not self.is_backstepping:
            if mouse_pos[0] > player_screen_x: self.facing_right = True
            else: self.facing_right = False
        if self.is_invincible and pygame.time.get_ticks() - self.invincibility_timer > self.invincibility_duration: self.is_invincible = False
        if self.is_dashing:
            self.dash_timer -= clock.get_time()
            if self.dash_timer <= 0: self.is_dashing = False; self.velocity.x = 0
        elif self.is_backstepping:
            self.backstep_timer -= clock.get_time()
            if self.backstep_timer <= 0: self.is_backstepping = False; self.velocity.x = 0
        else:
            if self.is_charging: self.charge_time += clock.get_time()
            keys = pygame.key.get_pressed()
            current_speed = self.move_speed
            if keys[pygame.K_LSHIFT]: current_speed *= self.run_speed_multiplier
            if keys[pygame.K_a]: self.velocity.x = -current_speed
            elif keys[pygame.K_d]: self.velocity.x = current_speed
            else: self.velocity.x = 0
            if keys[pygame.K_SPACE] and self.is_on_ground: self.velocity.y = self.jump_strength
        self.rect.x += self.velocity.x
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.velocity.x > 0: self.rect.right = tile.rect.left
                if self.velocity.x < 0: self.rect.left = tile.rect.right
        self.velocity.y += GRAVITY; self.rect.y += self.velocity.y; self.is_on_ground = False
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.velocity.y > 0: self.rect.bottom = tile.rect.top; self.is_on_ground = True; self.velocity.y = 0
                if self.velocity.y < 0: self.rect.top = tile.rect.bottom; self.velocity.y = 0
        self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen * clock.get_time()/1000)
    def start_attack(self, event):
        if event.button == 1 and not (self.is_dashing or self.is_blocking or self.is_attacking): self.is_charging = True; self.charge_time = 0
    def end_attack(self, event):
        if event.button == 1 and self.is_charging:
            self.is_charging = False
            if self.charge_time >= self.charge_threshold: self.heavy_attack()
            else: self.light_attack()
    def light_attack(self):
        if self.stamina < STAMINA_LIGHT_ATTACK: return
        self.stamina -= STAMINA_LIGHT_ATTACK
        sound_manager.play('light_attack'); self.is_attacking = True; self.animation_frame = 0; hitbox_width = 60
        if self.facing_right: self.attack_hitbox = pygame.Rect(self.rect.right, self.rect.top, hitbox_width, self.rect.height)
        else: self.attack_hitbox = pygame.Rect(self.rect.left - hitbox_width, self.rect.top, hitbox_width, self.rect.height)
    def heavy_attack(self):
        if self.stamina < STAMINA_HEAVY_ATTACK: return
        self.stamina -= STAMINA_HEAVY_ATTACK
        sound_manager.play('heavy_attack'); self.is_attacking = True; self.animation_frame = 0; hitbox_width = 90
        if 'camera' in globals(): camera.shake(200, 5)
        if self.facing_right: self.attack_hitbox = pygame.Rect(self.rect.right, self.rect.top, hitbox_width, self.rect.height)
        else: self.attack_hitbox = pygame.Rect(self.rect.left - hitbox_width, self.rect.top, hitbox_width, self.rect.height)
    def dash(self):
        if self.is_dashing or self.stamina < STAMINA_DASH: return
        current_time = pygame.time.get_ticks()
        if current_time - self.last_dash_time > self.dash_cooldown:
            self.stamina -= STAMINA_DASH
            self.is_dashing = True; self.dash_timer = self.dash_duration; self.last_dash_time = current_time
            self.velocity.x = self.dash_speed if self.facing_right else -self.dash_speed; self.velocity.y = 0

    def backstep(self):
        if self.is_backstepping or self.is_dashing or self.stamina < STAMINA_BACKSTEP: return
        current_time = pygame.time.get_ticks()
        if current_time - self.last_backstep_time > self.backstep_cooldown:
            self.stamina -= STAMINA_BACKSTEP
            self.is_backstepping = True; self.backstep_timer = self.backstep_duration; self.last_backstep_time = current_time
            self.velocity.x = -self.dash_speed if self.facing_right else self.dash_speed
            self.velocity.y = 0
    def take_damage(self, amount):
        if self.is_invincible: return
        sound_manager.play('player_hurt');
        if self.is_blocking: amount *= 0.25
        self.health -= amount; self.is_invincible = True; self.invincibility_timer = pygame.time.get_ticks()
        if 'camera' in globals(): camera.shake(150, 4)
        if self.health <= 0: self.kill()

# --- 3. DREAD AND ABILITY CLASSES ---
class Dread(pygame.sprite.Sprite):
    def __init__(self, player_to_follow):
        super().__init__()
        self.player = player_to_follow; self.follow_speed = 0.08
        self.base_size = (80, 120)
        self.image = pygame.Surface(self.base_size); self.image.fill(DREAD_COLOR); self.image.set_alpha(180)
        self.rect = self.image.get_rect()
        self.state = 'FOLLOW'
        self.passive_orb_cooldown = 3000; self.last_passive_orb_time = 0
        self.spectral_hand_cooldown = 5000; self.last_hand_use = -self.spectral_hand_cooldown
        self.screech_cooldown = 10000; self.last_screech_use = -self.screech_cooldown
        self.devour_cooldown = 15000; self.last_devour_use = -self.devour_cooldown
        self.aspect_cooldown = 60000; self.last_aspect_use = -self.aspect_cooldown
        self.aspect_duration = 10000; self.aspect_end_time = 0
        self.aspect_devour_cooldown = 1500; self.last_aspect_devour_time = 0
    def update(self, enemies_group, **kwargs):
        if not self.player.alive():
            if self.image.get_alpha() > 0: self.image.set_alpha(self.image.get_alpha() - 2)
            else: self.kill()
            return
        current_time = pygame.time.get_ticks()
        if self.state == 'ASPECT_OF_DREAD':
            if current_time > self.aspect_end_time or not any(e for e in enemies_group if e.state != 'DYING'):
                self.end_aspect()
            else:
                self.aspect_behavior(enemies_group)
        else:
            self.follow_behavior()
            if current_time - self.last_passive_orb_time > self.passive_orb_cooldown:
                self.passive_orb_attack(enemies_group)
    def follow_behavior(self):
        target_pos_x = self.player.rect.centerx - 80 if self.player.facing_right else self.player.rect.centerx + 80
        target_pos_y = self.player.rect.centery - 80
        self.rect.centerx += (target_pos_x - self.rect.centerx) * self.follow_speed
        self.rect.centery += (target_pos_y - self.rect.centery) * self.follow_speed
    def aspect_behavior(self, enemies_group):
        closest_enemy, min_dist = self.find_closest_enemy(enemies_group)
        if closest_enemy:
            direction = pygame.math.Vector2(closest_enemy.rect.center) - pygame.math.Vector2(self.rect.center)
            if direction.length() > 0: self.rect.move_ip(direction.normalize() * 5)
            if pygame.time.get_ticks() - self.last_aspect_devour_time > self.aspect_devour_cooldown:
                if min_dist < 100 and not closest_enemy.is_boss:
                    closest_enemy.kill()
                    self.last_aspect_devour_time = pygame.time.get_ticks()
    def passive_orb_attack(self, enemies_group):
        closest_enemy, _ = self.find_closest_enemy(enemies_group)
        if closest_enemy:
            self.last_passive_orb_time = pygame.time.get_ticks()
            bolt = SoulBolt(self.rect.center, closest_enemy.rect.center, damage=2)
            all_sprites.add(bolt); projectiles.add(bolt)
    def find_closest_enemy(self, enemies_group):
        closest_enemy = None; min_dist = float('inf')
        for enemy in enemies_group:
            if enemy.state != 'DYING':
                dist = math.hypot(self.rect.centerx - enemy.rect.centerx, self.rect.centery - enemy.rect.centery)
                if dist < min_dist: min_dist = dist; closest_enemy = enemy
        return closest_enemy, min_dist
    def use_spectral_hand(self, target_pos, camera):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hand_use > self.spectral_hand_cooldown:
            self.last_hand_use = current_time
            world_pos = (target_pos[0] + camera.camera_x, target_pos[1] + camera.camera_y)
            hand = SpectralHand(world_pos); all_sprites.add(hand)
    def use_screech(self, enemies_group):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_screech_use > self.screech_cooldown:
            self.last_screech_use = current_time
            sound_manager.play('screech')
            effect = ScreechEffect(self.rect.center); all_sprites.add(effect)
            for enemy in enemies_group:
                if math.hypot(self.rect.centerx - enemy.rect.centerx, self.rect.centery - enemy.rect.centery) < 250:
                    enemy.get_stunned(5000)
                    direction = pygame.math.Vector2(enemy.rect.center) - pygame.math.Vector2(self.rect.center)
                    if direction.length() > 0:
                        enemy.velocity += direction.normalize() * 10
    def use_devour(self, enemies_group):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_devour_use > self.devour_cooldown:
            closest_enemy, _ = self.find_closest_enemy(enemies_group)
            if closest_enemy:
                self.last_devour_use = current_time
                sound_manager.play('devour')
                if closest_enemy.is_boss: closest_enemy.take_damage(50)
                else: closest_enemy.kill()
    def use_aspect_of_dread(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_aspect_use > self.aspect_cooldown:
            self.state = 'ASPECT_OF_DREAD'
            self.aspect_end_time = current_time + self.aspect_duration
            self.image = pygame.Surface((self.base_size[0] * 1.5, self.base_size[1] * 1.5))
            self.image.fill(DREAD_COLOR); self.image.set_alpha(220)
    def end_aspect(self):
        self.state = 'FOLLOW'
        self.last_aspect_use = pygame.time.get_ticks()
        self.image = pygame.Surface(self.base_size)
        self.image.fill(DREAD_COLOR); self.image.set_alpha(180)

class SpectralHand(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos; self.image = pygame.Surface((60, 80), pygame.SRCALPHA)
        self.image.fill((180, 180, 255, 150)); self.rect = self.image.get_rect(center=pos)
        self.slams_left = 3; self.slam_cooldown = 1000; self.last_slam_time = -self.slam_cooldown
    def update(self, **kwargs):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_slam_time > self.slam_cooldown and self.slams_left > 0:
            self.last_slam_time = current_time; self.slams_left -= 1
            hitbox = pygame.Rect(0,0,80,40); hitbox.center = self.pos
            for enemy in enemies:
                if hitbox.colliderect(enemy.rect): enemy.take_damage(10)
            if self.slams_left <= 0: self.kill()

class ScreechEffect(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos; self.max_radius = 250; self.current_radius = 0; self.speed = 20
        self.image = pygame.Surface((self.max_radius * 2, self.max_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
    def update(self, **kwargs):
        self.current_radius += self.speed; self.image.fill((0,0,0,0))
        if self.current_radius < self.max_radius and self.current_radius > 10:
            pygame.draw.circle(self.image, (200,200,255,100), (self.max_radius, self.max_radius), int(self.current_radius), 10)
        elif self.current_radius >= self.max_radius:
            self.kill()

class ShamblingUndead(pygame.sprite.Sprite):
    def __init__(self, x, y, player_ref):
        super().__init__(); self.image = pygame.Surface([40, 55]); self.image.fill(ENEMY_COLOR)
        self.rect = self.image.get_rect(topleft=(x,y))
        self.state = 'PATROL'; self.player = player_ref; self.detection_range = 300; self.attack_range = 30
        self.damage = 10; self.patrol_speed = 1; self.chase_speed = 2.5; self.direction = 1
        self.health = 3; self.max_health = self.health; self.death_timer = 250; self.velocity = pygame.math.Vector2(0,0)
        self.is_stunned = False; self.stun_end_time = 0; self.is_boss = False
    def update(self, tiles, **kwargs):
        current_time = pygame.time.get_ticks()
        if self.is_stunned and current_time > self.stun_end_time: self.is_stunned = False
        if self.state == 'DYING':
            self.death_timer -= clock.get_time(); self.image.set_alpha(255 if self.image.get_alpha() == 0 else 0)
            if self.death_timer <= 0: self.kill()
            return
        if self.is_stunned: self.image.fill(STUN_COLOR); return
        else: self.image.fill(ENEMY_COLOR)
        if not self.player.alive(): self.state = 'PATROL'
        distance_to_player = math.hypot(self.rect.centerx - self.player.rect.centerx, self.rect.centery - self.player.rect.centery)
        if distance_to_player < self.detection_range and self.player.alive(): self.state = 'CHASE'
        else: self.state = 'PATROL'
        if self.state == 'PATROL': self.velocity.x = self.direction * self.patrol_speed
        elif self.state == 'CHASE':
            if distance_to_player > self.attack_range:
                if self.player.rect.centerx > self.rect.centerx: self.velocity.x = self.chase_speed
                else: self.velocity.x = -self.chase_speed
            else: self.velocity.x = 0
        self.rect.x += self.velocity.x
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.state == 'PATROL': self.direction *= -1
                if self.velocity.x > 0: self.rect.right = tile.rect.left
                if self.velocity.x < 0: self.rect.left = tile.rect.right
        self.velocity.y += GRAVITY; self.rect.y += self.velocity.y
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.velocity.y > 0: self.rect.bottom = tile.rect.top; self.velocity.y = 0
                if self.velocity.y < 0: self.rect.top = tile.rect.bottom; self.velocity.y = 0
    def take_damage(self, amount):
        if self.state == 'DYING': return
        self.health -= amount;
        if self.health <= 0: self.state = 'DYING'
    def get_stunned(self, duration):
        self.is_stunned = True; self.stun_end_time = pygame.time.get_ticks() + duration

class TormentedSpirit(pygame.sprite.Sprite):
    def __init__(self, x, y, player_ref):
        super().__init__(); self.image = pygame.Surface([35, 35], pygame.SRCALPHA)
        pygame.draw.circle(self.image, SPIRIT_COLOR, (17, 17), 17); self.image.set_alpha(150)
        self.rect = self.image.get_rect(center=(x,y)); self.player = player_ref
        self.speed = 1.5; self.damage = 15; self.health = 2; self.max_health = self.health
        self.state = 'IDLE'; self.death_timer = 250
        self.is_stunned = False; self.stun_end_time = 0; self.is_boss = False; self.velocity = pygame.math.Vector2(0,0)
    def update(self, **kwargs):
        current_time = pygame.time.get_ticks()
        if self.is_stunned and current_time > self.stun_end_time: self.is_stunned = False
        if self.state == 'DYING':
            self.death_timer -= clock.get_time(); self.image.set_alpha(255 if self.image.get_alpha() == 0 else 0)
            if self.death_timer <= 0: self.kill()
            return
        if self.is_stunned: return
        self.rect.move_ip(self.velocity); self.velocity *= 0.9
        if self.player.alive():
            direction = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
            if direction.length() > 0: self.rect.move_ip(direction.normalize() * self.speed)
    def take_damage(self, amount):
        if self.state == 'DYING': return
        self.health -= amount
        if self.health <= 0: self.state = 'DYING'
    def get_stunned(self, duration):
        self.is_stunned = True; self.stun_end_time = pygame.time.get_ticks() + duration

class CryptGuardian(ShamblingUndead):
    def __init__(self, x, y, player_ref):
        super().__init__(x, y, player_ref); self.image = pygame.Surface([80, 100])
        self.image.fill(BOSS_COLOR); self.rect = self.image.get_rect(topleft=(x,y))
        self.health = 25; self.max_health = self.health; self.damage = 25; self.patrol_speed = 0
        self.chase_speed = 1.8; self.detection_range = 600; self.is_boss = True
    def take_damage(self, amount):
        super().take_damage(amount)
        if self.state == 'DYING':
            for tile in gate_tiles: tile.kill()
    def get_stunned(self, duration): pass

class SoulBolt(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, damage=5):
        super().__init__(); self.image = pygame.Surface([10, 10]); self.image.fill(DREAD_COLOR); self.rect = self.image.get_rect(center=start_pos)
        direction = pygame.math.Vector2(target_pos) - pygame.math.Vector2(start_pos)
        if direction.length() > 0: self.velocity = direction.normalize() * 12
        else: self.velocity = pygame.math.Vector2(0, 0)
        self.damage = damage
    def update(self, **kwargs):
        self.rect.move_ip(self.velocity)
        if not pygame.Rect(0,0,LEVEL_WIDTH, LEVEL_HEIGHT).colliderect(self.rect): self.kill()

class Crosshair(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(); self.image = pygame.Surface([20, 20], pygame.SRCALPHA)
        pygame.draw.line(self.image, CROSSHAIR_COLOR, (0, 10), (20, 10), 2); pygame.draw.line(self.image, CROSSHAIR_COLOR, (10, 0), (10, 20), 2)
        self.rect = self.image.get_rect()
    def update(self, **kwargs): self.rect.center = pygame.mouse.get_pos()

class InteractableObject(pygame.sprite.Sprite):
    def __init__(self, pos, prompt, lore):
        super().__init__(); self.image = pygame.Surface([30, 30]); self.image.fill(INTERACT_COLOR)
        self.rect = self.image.get_rect(center=pos); self.prompt_text = prompt; self.lore_text = lore
    def update(self, **kwargs): pass
    def draw_prompt(self, surface, camera):
        prompt_surf = font_small.render(self.prompt_text, True, TEXT_COLOR)
        x = self.rect.centerx - camera.camera_x - prompt_surf.get_width() / 2; y = self.rect.top - camera.camera_y - 30
        surface.blit(prompt_surf, (x, y))

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(); self.image = pygame.Surface([TILE_SIZE, TILE_SIZE]); self.image.fill(TILE_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
    def update(self, **kwargs): pass

class SpikeTrap(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(); self.image = pygame.Surface([TILE_SIZE, TILE_SIZE]);
        pygame.draw.polygon(self.image, (180,80,80), [(0,TILE_SIZE),(TILE_SIZE/2,0),(TILE_SIZE,TILE_SIZE)])
        self.rect = self.image.get_rect(topleft=(x,y))

class BreakableCrate(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(); self.image = pygame.Surface([TILE_SIZE, TILE_SIZE]); self.image.fill((120,80,40))
        pygame.draw.rect(self.image, (60,40,20), (4,4,TILE_SIZE-8,TILE_SIZE-8),2)
        self.rect = self.image.get_rect(topleft=(x,y)); self.health = 3
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            if 'pickups' in globals() and 'all_sprites' in globals():
                hp = HealthPickup(self.rect.centerx, self.rect.centery)
                pickups.add(hp); all_sprites.add(hp)
            self.kill()

class HealthPickup(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(); self.image = pygame.Surface([15,15]); self.image.fill(HEALTH_GREEN)
        self.rect = self.image.get_rect(center=(x,y))
    def update(self, **kwargs):
        pass

class Camera:
    def __init__(self, target):
        self.target = target; self.camera_x = 0; self.camera_y = 0; self.follow_speed = 0.1
        self.shake_duration = 0; self.shake_intensity = 0; self.shake_offset = pygame.math.Vector2(0,0)
    def update(self):
        if not self.target.alive(): return
        target_x = self.target.rect.centerx - SCREEN_WIDTH / 2
        self.camera_x += (target_x - self.camera_x) * self.follow_speed
        if self.shake_duration > 0:
            self.shake_duration -= clock.get_time()
            self.shake_offset.x = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_offset.y = random.randint(-self.shake_intensity, self.shake_intensity)
        else:
            self.shake_offset.update(0,0)
        if self.camera_x < 0: self.camera_x = 0
        if self.camera_x > LEVEL_WIDTH - SCREEN_WIDTH: self.camera_x = LEVEL_WIDTH - SCREEN_WIDTH

    def shake(self, duration, intensity):
        self.shake_duration = duration
        self.shake_intensity = intensity

# --- 5. GAME SETUP AND MAIN LOOP ---
def game_start():
    global player, dread, all_sprites, enemies, projectiles, ui_sprites, interactables, tiles, gate_tiles
    global hazards, crates, pickups
    global camera, background_rects, current_game_state, final_exit, boss_reference
    explored_tiles.clear()
    all_sprites = pygame.sprite.Group(); enemies = pygame.sprite.Group(); projectiles = pygame.sprite.Group();
    ui_sprites = pygame.sprite.Group(); interactables = pygame.sprite.Group(); tiles = pygame.sprite.Group();
    hazards = pygame.sprite.Group(); crates = pygame.sprite.Group(); pickups = pygame.sprite.Group()
    gate_tiles = pygame.sprite.Group(); boss_reference = None
    for row_index, row in enumerate(level_map):
        for col_index, char in enumerate(row):
            x, y = col_index * TILE_SIZE, row_index * TILE_SIZE
            if char == 'X': tile = Tile(x,y); tiles.add(tile)
            elif char == 'G': tile = Tile(x,y); tiles.add(tile); gate_tiles.add(tile)
            elif char == 'P': player = Player(x, y)
            elif char == 'E': enemies.add(ShamblingUndead(x, y, None))
            elif char == 'S': enemies.add(TormentedSpirit(x, y, None))
            elif char == 'B':
                boss_reference = CryptGuardian(x, y, None)
                enemies.add(boss_reference)
            elif char == 'L': interactables.add(InteractableObject((x,y), "Press 'E'", "Ten thousand years... wasted."))
            elif char == 'F': final_exit = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    hazard_positions = [(500, LEVEL_HEIGHT - TILE_SIZE), (800, LEVEL_HEIGHT - TILE_SIZE * 2)]
    crate_positions = [(600, LEVEL_HEIGHT - TILE_SIZE), (900, LEVEL_HEIGHT - TILE_SIZE)]
    for pos in hazard_positions: hazards.add(SpikeTrap(*pos))
    for pos in crate_positions: crates.add(BreakableCrate(*pos))
    all_sprites.add(tiles, enemies, interactables, hazards, crates)
    for enemy in enemies: enemy.player = player
    dread = Dread(player); camera = Camera(player); crosshair = Crosshair(); ui_sprites.add(crosshair)
    all_sprites.add(player, dread)
    background_rects = []
    for i in range(round(LEVEL_WIDTH / 300)):
        background_rects.append({'rect': pygame.Rect(i * 300, 200 + i % 3 * 50, 80, 150), 'speed': 0.2})
        background_rects.append({'rect': pygame.Rect(i * 450, 300 + i % 2 * 60, 40, 100), 'speed': 0.5})

# --- Main Game Variables & Loop ---
current_game_state = 'MAIN_MENU'
game_over = False; interaction_target = None; showing_lore = False

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
        
        if current_game_state == 'GAMEPLAY':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: player.dash()
                if event.key == pygame.K_c: player.backstep()
                if event.key == pygame.K_1: dread.use_spectral_hand(mouse_pos, camera)
                if event.key == pygame.K_2: dread.use_screech(enemies)
                if event.key == pygame.K_3: dread.use_devour(enemies)
                if event.key == pygame.K_4: dread.use_aspect_of_dread()
                if event.key == pygame.K_p: current_game_state = 'PAUSED'
                if event.key == pygame.K_e and interaction_target and not showing_lore:
                    showing_lore = True; sound_manager.play('interaction')
                elif event.key == pygame.K_e and showing_lore: showing_lore = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if showing_lore: showing_lore = False
                else: player.start_attack(event)
                if event.button == 3: player.is_blocking = True
            if event.type == pygame.MOUSEBUTTONUP:
                if not showing_lore: player.end_attack(event)
                if event.button == 3: player.is_blocking = False
        elif current_game_state == 'PAUSED':
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p: current_game_state = 'GAMEPLAY'; pygame.mouse.set_visible(False)
        elif current_game_state == 'MAIN_MENU':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_button_rect = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 - 25, 200, 50)
                if play_button_rect.collidepoint(mouse_pos) and transition_phase is None:
                    start_transition('CUTSCENE')
        elif current_game_state == 'CUTSCENE':
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                cutscene_index += 1
                cutscene_timer = 0
        elif current_game_state == 'GAME_OVER':
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game_start(); current_game_state = 'GAMEPLAY'; pygame.mouse.set_visible(False)

    # Update
    if current_game_state == 'GAMEPLAY' and not showing_lore:
        all_sprites.update(camera=camera, tiles=tiles, enemies_group=enemies)
        ui_sprites.update(); camera.update()
        explored_tiles.add((player.rect.centerx // TILE_SIZE, player.rect.centery // TILE_SIZE))
        if not player.alive(): game_over = True; current_game_state = 'GAME_OVER'
    elif current_game_state == 'CUTSCENE':
        cutscene_timer += clock.get_time()
        if cutscene_timer > CUTSCENE_DELAY:
            cutscene_index += 1
            cutscene_timer = 0
        if cutscene_index >= len(cutscene_lines) and transition_phase is None:
            start_transition('GAMEPLAY')

    # Handle transitions
    if transition_phase == 'fade_out':
        transition_alpha += FADE_SPEED
        if transition_alpha >= 255:
            transition_alpha = 255
            if transition_dialogue:
                dialogue_timer = 3000
                transition_phase = 'dialogue'
            else:
                if transition_target_state == 'GAMEPLAY':
                    game_start()
                elif transition_target_state == 'CUTSCENE':
                    start_cutscene()
                current_game_state = transition_target_state
                if current_game_state == 'GAMEPLAY':
                    pygame.mouse.set_visible(False)
                transition_phase = 'fade_in'
    elif transition_phase == 'dialogue':
        dialogue_timer -= clock.get_time()
        if dialogue_timer <= 0:
            if transition_target_state == 'GAMEPLAY':
                game_start()
            current_game_state = transition_target_state
            if current_game_state == 'GAMEPLAY':
                pygame.mouse.set_visible(False)
            transition_phase = 'fade_in'
    elif transition_phase == 'fade_in':
        transition_alpha -= FADE_SPEED
        if transition_alpha <= 0:
            transition_alpha = 0
            transition_phase = None

    # Collisions
    if current_game_state == 'GAMEPLAY' and not showing_lore:
        if 'final_exit' in globals() and player.rect.colliderect(final_exit):
            if transition_phase is None:
                start_transition('MAIN_MENU', "The crypt grows silent...")
        interaction_target = pygame.sprite.spritecollideany(player, interactables)
        player_hits = pygame.sprite.spritecollide(player, enemies, False)
        active_hits = [e for e in player_hits if e.state != 'DYING'];
        if active_hits: player.take_damage(active_hits[0].damage)
        if pygame.sprite.spritecollideany(player, hazards):
            player.take_damage(HAZARD_DAMAGE)
        if player.is_attacking and player.attack_hitbox:
            damage = 10 if player.charge_time >= player.charge_threshold else 3
            hit_enemies = [e for e in enemies if player.attack_hitbox.colliderect(e.rect)]
            for enemy in hit_enemies: enemy.take_damage(damage); player.attack_hitbox = None; break
            hit_crates = [c for c in crates if player.attack_hitbox.colliderect(c.rect)]
            for c in hit_crates: c.take_damage(damage); player.attack_hitbox = None; break
        hits = pygame.sprite.groupcollide(projectiles, enemies, True, False);
        for p, e_list in hits.items():
            for enemy in e_list: enemy.take_damage(p.damage)
        for pickup in pygame.sprite.spritecollide(player, pickups, True):
            player.health = min(player.max_health, player.health + 10)

    # --- Draw / Render ---
    screen.fill(BG_COLOR_DARK)
    if current_game_state != 'MAIN_MENU':
        for bg in background_rects:
            bg_x = bg['rect'].x - camera.camera_x * bg['speed'] + camera.shake_offset.x * 0.5
            pygame.draw.rect(screen, BG_COLOR_LIGHT, (bg_x, bg['rect'].y + camera.shake_offset.y * 0.5, bg['rect'].width, bg['rect'].height))
        for sprite in all_sprites:
            screen.blit(sprite.image, (sprite.rect.x - camera.camera_x + camera.shake_offset.x,
                                        sprite.rect.y - camera.camera_y + camera.shake_offset.y))
        if interaction_target and not showing_lore: interaction_target.draw_prompt(screen, camera)
        if player.alive():
            draw_player_health(screen, 20, 20, player.health, player.max_health)
            draw_player_stamina(screen, 20, 45, player.stamina, player.max_stamina)
            if boss_reference and boss_reference.alive() and boss_reference.state != 'DYING':
                draw_boss_health(screen, boss_reference)
            draw_cooldowns(screen, dread)
            draw_minimap(screen, player, enemies)
            ui_sprites.draw(screen)

    # ... (Drawing for states is the same)
    if current_game_state == 'MAIN_MENU':
        pygame.mouse.set_visible(True)
        title_text = font_large.render("Within The Dark", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH/2 - title_text.get_width()/2, SCREEN_HEIGHT/3))
        play_button_rect = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 - 25, 200, 50)
        pygame.draw.rect(screen, UI_GRAY, play_button_rect)
        play_text = font_medium.render("Play", True, WHITE)
        screen.blit(play_text, (play_button_rect.centerx - play_text.get_width()/2, play_button_rect.centery - play_text.get_height()/2))
    elif current_game_state == 'PAUSED':
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill(MENU_OVERLAY_COLOR)
        screen.blit(overlay, (0,0))
        pause_text = font_large.render("PAUSED", True, WHITE)
        screen.blit(pause_text, (SCREEN_WIDTH/2 - pause_text.get_width()/2, SCREEN_HEIGHT/2 - pause_text.get_height()/2))
    elif current_game_state == 'GAME_OVER':
        pygame.mouse.set_visible(True)
        text = font_large.render("YOU DIED", True, HEALTH_RED); text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 40))
        screen.blit(text, text_rect)
        restart_text = font_medium.render("Press 'R' to awaken again", True, WHITE); restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
        screen.blit(restart_text, restart_rect)
    elif current_game_state == 'CUTSCENE':
        pygame.mouse.set_visible(False)
        draw_text_box(screen, cutscene_lines[min(cutscene_index, len(cutscene_lines)-1)])
    if showing_lore:
        draw_text_box(screen, interaction_target.lore_text)

    if transition_phase:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(int(transition_alpha))
        screen.blit(overlay, (0, 0))
        if transition_phase == 'dialogue':
            draw_text_box(screen, transition_dialogue)

    pygame.display.flip()
    clock.tick(FPS)

# --- 6. CLEANUP ---
pygame.quit()
sys.exit()
