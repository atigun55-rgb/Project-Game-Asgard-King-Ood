import pygame
import os
import sys
import random
import math

# --- ตั้งค่าเกม ---
pygame.init()
pygame.mixer.init()
pygame.font.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Asgard King Ood - Sounds & Coins")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont('Arial', 30, bold=True)
SMALL_FONT = pygame.font.SysFont('Arial', 20)

# --- สีและการตั้งค่า ---
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 215, 0)
MAX_LEVELS = 10

# --- Helper: โหลดภาพ ---
def load_safe_image(path, fallback_color=(255, 0, 255), scale=None):
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if scale:
                img = pygame.transform.scale(img, scale)
            return img
        except:
            pass
    
    w, h = scale if scale else (32, 32)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill(fallback_color)
    return surf

# --- Helper: โหลดเสียง (SFX) ---
def load_safe_sound(path):
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except:
            print(f"Error loading sound: {path}")
            return None
    return None

# --- Helper: เล่นเพลงประกอบ (BGM) -> [เพิ่มใหม่] ---
def play_bg_music():
    # ตรวจสอบว่าตอนนี้เพลงกำลังเล่นอยู่ไหม ถ้าเล่นอยู่แล้วไม่ต้องทำอะไร
    if pygame.mixer.music.get_busy():
        return

    # ระบุที่อยู่ไฟล์เพลง (สมมติใช้ไฟล์ .mp3 หรือ .ogg)
    music_path = 'assets/sounds/bgm.mp3' 
    
    if os.path.exists(music_path):
        try:
            pygame.mixer.music.load(music_path)
            # ตั้งค่าความดัง 0.0 - 1.0 (0.3 ถือว่าเบาๆ พอดี)
            pygame.mixer.music.set_volume(0.3) 
            # -1 คือให้วนซ้ำไปเรื่อยๆ
            pygame.mixer.music.play(-1)
            print("Background music started.")
        except Exception as e:
            print(f"Error loading music: {e}")
    else:
        print(f"Music file not found at: {music_path}")

# --- CLASS: Animation ---
class Animation:
    def __init__(self, img, frame_size, frame_count, loop=True, scale_to=None):
        self.frames = []
        self.loop = loop
        self.status = "playing"

        sheet_w, sheet_h = img.get_size()
        frame_w, frame_h = frame_size

        if sheet_w < frame_w or sheet_h < frame_h:
            if scale_to:
                img = pygame.transform.scale(img, scale_to)
            self.frames.append(img)
        else:
            for i in range(frame_count):
                if i * frame_w < sheet_w:
                    rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
                    try:
                        frame = img.subsurface(rect)
                        if scale_to:
                            frame = pygame.transform.scale(frame, scale_to)
                        self.frames.append(frame)
                    except: pass
        
        if not self.frames:
            if scale_to: img = pygame.transform.scale(img, scale_to)
            self.frames.append(img)

        self.index = 0

    def get_frame(self):
        if not self.loop and self.status == "done":
            return self.frames[-1]

        self.index += 0.50
        if self.index >= len(self.frames):
            if self.loop:
                self.index = 0
            else:
                self.index = len(self.frames) - 1
                self.status = "done"
        
        return self.frames[int(self.index)]

    def reset(self):
        self.index = 0
        self.status = "playing"

# --- CLASS: AnimationManager ---
class AnimationManager:
    def __init__(self, animations):
        self.animations = animations
        self.state = 'idle'

    def set_state(self, state):
        if state not in self.animations:
            if 'idle' in self.animations: state = 'idle'
            else: return
                
        if self.state != state:
            self.state = state
            self.animations[self.state].reset()

    def get_frame(self):
        return self.animations[self.state].get_frame()

    def is_done(self):
        return self.animations[self.state].status == "done"

# --- CLASS: Platform ---
class Platform:
    def __init__(self, x, y, w, h, image_path='assets/box/idle.png', is_wall=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.is_wall = is_wall
        
        color = (100, 100, 100) if not is_wall else (80, 50, 50)
        img = load_safe_image(image_path, color).convert_alpha()
        img.set_colorkey((0, 0, 0))

        bbox = img.get_bounding_rect()
        if bbox.width > 0 and bbox.height > 0:
            img = img.subsurface(bbox).copy()

        if img.get_height() != h and img.get_height() > 0:
            new_w = int(img.get_width() * (h / img.get_height()))
            img = pygame.transform.scale(img, (new_w, h))

        surf_img = pygame.Surface((w, h), pygame.SRCALPHA)
        iw = img.get_width()

        if w <= iw:
            x0 = (iw - w) // 2
            crop = img.subsurface(pygame.Rect(x0, 0, w, h))
            surf_img.blit(crop, (0, 0))
        else:
            for xx in range(0, w, iw):
                surf_img.blit(img, (xx, 0))

        self.image = surf_img

    def render(self, surf):
        surf.blit(self.image, (self.rect.x, self.rect.y))

# --- CLASS: Decoration ---
class Decoration:
    def __init__(self, x, y, w, h, image_path='assets/environment/decorations.png'):
        self.rect = pygame.Rect(x, y, w, h)
        self.image = load_safe_image(image_path, (50, 50, 200))
        self.image = pygame.transform.scale(self.image, (w, h))

    def render(self, surf):
        surf.blit(self.image, (self.rect.x, self.rect.y))

# --- CLASS: Door ---
class Door:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + 20, y + 20, 50, 80)
        self.draw_x = x
        self.draw_y = y
        self.state = 'idle'

        # โหลดเสียงเปิดประตู
        self.open_sound = load_safe_sound('assets/sounds/door_open.wav')

        idle_img = load_safe_image('assets/door/idle.png')
        opening_img = load_safe_image('assets/door/opening.png', fallback_color=(100,100,100))
        
        opening_frames = 5
        if opening_img.get_width() > 46:
             opening_frames = opening_img.get_width() // 46

        self.anims = {
            'idle': Animation(idle_img, (46, 56), 1, True, (92, 112)),
            'opening': Animation(opening_img, (46, 56), opening_frames, False, (92, 112)),
            'open': Animation(idle_img, (46, 56), 1, True, (92, 112))
        }
        self.manager = AnimationManager(self.anims)

    def open(self):
        if self.state == 'idle':
            self.state = 'opening'
            self.manager.set_state('opening')
            if self.open_sound:
                self.open_sound.set_volume(0.5)
                self.open_sound.play()

    def update(self):
        if self.state == 'opening' and self.manager.is_done():
            self.state = 'open'
            self.manager.set_state('open')

    def render(self, surf):
        frame = self.manager.get_frame()
        surf.blit(frame, (self.draw_x, self.draw_y))

# --- CLASS: Box ---
class Box:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        img = load_safe_image('assets/box/idle.png')
        if img.get_width() >= 22 and img.get_height() >= 16:
            img = img.subsurface(0, 0, 22, 16)
        self.image = pygame.transform.scale(img, (40, 40))

    def render(self, surf):
        surf.blit(self.image, (self.rect.x, self.rect.y))

# --- CLASS: Coin ---
class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 38, 38)
        self.vel_y = -3
        self.gravity = 0.2
        self.collected = False
        self.life_span = 300
        
        self.image = load_safe_image('assets/items/coin.png', YELLOW, (38, 38))
        self.glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.glow_surf, (255, 255, 100, 100), (15, 15), 15)

        self.anim_timer = 0

    def update(self, obstacles):
        if self.collected: return

        self.vel_y += self.gravity
        self.rect.y += int(self.vel_y)
        
        for obj in obstacles:
            if self.rect.colliderect(obj.rect):
                if self.vel_y > 0:
                    self.rect.bottom = obj.rect.top
                    self.vel_y = 0

        self.life_span -= 1
        self.anim_timer += 0.2

    def render(self, surf):
        if self.collected: return
        
        if self.life_span < 60 and int(self.anim_timer) % 2 == 0:
            return

        offset_y = math.sin(self.anim_timer) * 3
        
        surf.blit(self.glow_surf, (self.rect.centerx - 15, self.rect.centery - 15 + offset_y))
        surf.blit(self.image, (self.rect.x, self.rect.y + offset_y))

# --- CLASS: FloatingText ---
class FloatingText:
    def __init__(self, x, y, text, color=WHITE):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 40
        self.vel_y = -2

    def update(self):
        self.y += self.vel_y
        self.life -= 1
        return self.life <= 0

    def render(self, surf):
        alpha = min(255, self.life * 6)
        txt_surf = SMALL_FONT.render(self.text, True, self.color)
        txt_surf.set_alpha(alpha)
        surf.blit(txt_surf, (self.x - txt_surf.get_width()//2, self.y))

# --- CLASS: Player ---
class Player:
    def __init__(self):
        self.rect = pygame.Rect(100, 400, 34, 40)
        self.vel_y = 0
        self.on_ground = False
        self.flip = False
        self.is_attacking = False
        self.entering_door = False
        self.door_target = None
        
        self.max_hp = 3
        self.hp = 3
        self.invincible_timer = 0
        self.is_dead = False
        self.knockback_timer = 0 
        self.knockback_dir = 0 
        self.door_delay = 0
        self.DOOR_DELAY_FRAMES = 10
        self.door_open_tick = None
        self.DOOR_DELAY_MS = 0

        # --- โหลดเสียง Player ---
        self.swing_sound = load_safe_sound('assets/sounds/player/swing.wav')
        self.jump_sound = load_safe_sound('assets/sounds/player/jump.wav')
        self.hit_sound = load_safe_sound('assets/sounds/player/hit.wav') 

        anim_data = {
            'idle': ('idle.png', 11, True),
            'run': ('idle.png', 8, True),
            'jump': ('idle.png', 1, True),
            'fall': ('idle.png', 1, True),
            'attack': ('attack.png', 3, False),
            'door_in': ('door_in.png', 8, False),
            'hit': ('idle.png', 2, False),
            'die': ('idle.png', 10, False)
        }

        self.anims = {}
        DRAW_SIZE = (70, 58)
        
        temp_anims = {}
        for name, data in anim_data.items():
            fname, frames, loop = data
            path = f'assets/player/{fname}'
            
            if not os.path.exists(path):
                if name == 'die': path = 'assets/player/idle.png'
                elif name == 'door_in': path = 'assets/player/dooraa.png'
                else: path = 'assets/player/door_enter.png'
                if name == 'door_in': frames = 6
            
            img = load_safe_image(path)
            temp_anims[name] = Animation(img, (78, 58), frames, loop, scale_to=DRAW_SIZE)

        self.anims = temp_anims
        self.draw_h = DRAW_SIZE[1]
        self.manager = AnimationManager(self.anims)

    def reset(self):
        self.rect.topleft = (100, 400)
        self.entering_door = False
        self.is_attacking = False
        self.door_target = None
        self.vel_y = 0
        self.hp = self.max_hp
        self.invincible_timer = 0
        self.is_dead = False
        self.flip = False
        self.knockback_timer = 0
        self.manager.set_state('idle')
        self.door_delay = 0
        self.door_open_tick = None

    def take_damage(self, source_rect):
        if self.invincible_timer > 0 or self.is_dead: return

        self.hp -= 1
        self.invincible_timer = 90
        self.manager.set_state('hit')
        self.is_attacking = False      
        self.door_target = None        

        KB_FORCE = 6
        KB_TIME  = 10     

        if self.rect.centerx < source_rect.centerx:
            self.knockback_dir = -KB_FORCE
        else:
            self.knockback_dir = KB_FORCE

        self.knockback_timer = KB_TIME
        self.vel_y = -6       

        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.manager.set_state('die')

    def attack(self, enemies):
        if not self.is_attacking and not self.entering_door and not self.is_dead and self.knockback_timer == 0:
            self.is_attacking = True
            self.manager.set_state('attack')
            
            if self.swing_sound: self.swing_sound.play()

            att_rect = self.rect.copy()
            att_rect.width += 40
            if self.flip: att_rect.x -= 40

            hit_count = 0
            for e in enemies:
                if not e.is_dying and att_rect.colliderect(e.rect):
                    e.die()
                    hit_count += 1
            
            if hit_count > 0 and self.hit_sound:
                self.hit_sound.play()

    def start_enter_door(self, door):
        if not self.entering_door and not self.door_target and not self.is_dead and self.knockback_timer == 0:
            self.door_target = door
            self.door_open_tick = None
            door.open()

    def move(self, obstacles):
        if self.entering_door or self.door_target or self.is_dead: return

        dx = 0

        if self.knockback_timer > 0:
            dx = self.knockback_dir
            self.knockback_timer -= 1
        else:
            keys = pygame.key.get_pressed()
            if not self.is_attacking:
                if keys[pygame.K_a]:
                    dx = -5
                    self.flip = True
                    if self.on_ground: self.manager.set_state('run')
                elif keys[pygame.K_d]:
                    dx = 5
                    self.flip = False
                    if self.on_ground: self.manager.set_state('run')
                else:
                    if self.on_ground: self.manager.set_state('idle')

                if keys[pygame.K_w] and self.on_ground:
                    self.vel_y = -20
                    self.on_ground = False
                    self.manager.set_state('jump')
                    if self.jump_sound:
                        self.jump_sound.set_volume(0.4) 
                        self.jump_sound.play()

        self.vel_y += 0.8
        if self.vel_y > 15: self.vel_y = 15
        dy = int(round(self.vel_y))
        if dy == 0:
            if self.vel_y > 0: dy = 1
            elif self.vel_y < 0: dy = -1

        self.rect.x += dx
        for obj in obstacles:
            if self.rect.colliderect(obj.rect):
                if dx > 0: self.rect.right = obj.rect.left
                if dx < 0: self.rect.left = obj.rect.right

        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

        self.rect.y += dy
        self.on_ground = False
        for obj in obstacles:
            if self.rect.colliderect(obj.rect):
                if dy > 0:
                    self.rect.bottom = obj.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif dy < 0:
                    self.rect.top = obj.rect.bottom
                    self.vel_y = 0

        if self.rect.top < 0:
            self.rect.top = 0
            if self.vel_y < 0: self.vel_y = 0

        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.vel_y = 0
            self.on_ground = True

        if not self.on_ground and not self.is_attacking:
            if self.vel_y > 0: self.manager.set_state('fall')

    def update(self):
        if self.invincible_timer > 0: self.invincible_timer -= 1

        if self.is_dead:
            if self.manager.is_done() and self.manager.state == 'die':
                return "dead"
            return None

        if self.is_attacking and self.manager.is_done() and self.manager.state == 'attack':
            self.is_attacking = False

        if self.door_target:
            if self.door_target.state == 'open' and not self.entering_door:
                if self.door_open_tick is None:
                    self.door_open_tick = pygame.time.get_ticks()

                self.manager.set_state('idle')
                self.vel_y = 0
                self.rect.centerx = self.door_target.rect.centerx

                if pygame.time.get_ticks() - self.door_open_tick >= self.DOOR_DELAY_MS:
                    self.entering_door = True
                    self.manager.set_state('door_in')

            if self.entering_door and self.manager.is_done():
                self.door_open_tick = None
                return "next_level"
        
        if self.manager.state == 'hit' and self.manager.is_done():
             if self.on_ground: self.manager.set_state('idle')

        return None

    def render(self, surf):
        if self.invincible_timer > 0 and (self.invincible_timer // 4) % 2 == 0: return

        frame = self.manager.get_frame()
        if self.flip:
            frame = pygame.transform.flip(frame, True, False)

        draw_x = self.rect.centerx - frame.get_width() // 2
        draw_y = self.rect.bottom - self.draw_h

        surf.blit(frame, (draw_x, draw_y))

# --- CLASS: Enemy ---
class Enemy:
    def __init__(self, x, y, dist):
        self.rect = pygame.Rect(x, y, 34, 30)
        self.start_x = x
        self.dist = dist
        self.dir = random.choice([-1, 1])
        self.speed = random.uniform(1.5, 2.5)
        self.is_dying = False

        self.death_sound = load_safe_sound('assets/sounds/enemy/death.wav')

        img = load_safe_image('assets/pig/run.png')
        self.run_anim = Animation(img, (34, 28), 6, True, (44, 38))

        die_img = load_safe_image('assets/pig/dead.png', fallback_color=(200, 50, 50))
        self.die_anim = Animation(die_img, (34, 28), 6, False, (44, 38))

    def is_dead_finished(self):
        return self.is_dying and self.die_anim.status == "done"

    def die(self):
        if not self.is_dying:
            self.is_dying = True
            if self.death_sound:
                self.death_sound.set_volume(0.4)
                self.death_sound.play()

    def update(self, player_rect, obstacles):
        if self.is_dying: return None

        dx = self.dir * self.speed
        self.rect.x += dx

        for obj in obstacles:
            if self.rect.colliderect(obj.rect):
                if dx > 0:
                    self.rect.right = obj.rect.left
                    self.dir = -1
                elif dx < 0:
                    self.rect.left = obj.rect.right
                    self.dir = 1
                break

        if self.rect.left < 0:
            self.rect.left = 0
            self.dir = 1
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.dir = -1

        ground_check = pygame.Rect(self.rect.x, self.rect.bottom + 2, self.rect.width, 6)
        on_ground = False
        for obj in obstacles:
            if ground_check.colliderect(obj.rect):
                on_ground = True
                break
        if not on_ground:
            self.dir *= -1

        if self.rect.x > self.start_x + self.dist:
            self.dir = -1
        elif self.rect.x < self.start_x:
            self.dir = 1

        if self.rect.colliderect(player_rect):
            return "hit"

        return None

    def render(self, surf):
        if self.is_dying:
            frame = self.die_anim.get_frame()
        else:
            frame = self.run_anim.get_frame()
            if self.dir == 1:
                frame = pygame.transform.flip(frame, True, False)

        draw_x = self.rect.centerx - frame.get_width() // 2
        draw_y = self.rect.bottom - frame.get_height()
        surf.blit(frame, (draw_x, draw_y))

# --- Helper ตรวจสอบการซ้อนทับ ---
def check_overlap(new_rect, existing_rects, margin=40):
    check_rect = new_rect.inflate(margin * 2, margin * 2)
    for r in existing_rects:
        if check_rect.colliderect(r):
            return True
    return False

# --- ฟังก์ชันสร้างด่าน ---
def build_level(lvl):
    random.seed(lvl * 100)
    platforms = []
    boxes = []
    decorations = []
    enemies = []
    walls = []

    def clamp(v, lo, hi):
        return lo if v < lo else hi if v > hi else v

    bg_image = load_safe_image('assets/bg/background.png', (40, 40, 50))
    bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    floor_y = 600
    floor = Platform(0, floor_y, SCREEN_WIDTH, SCREEN_HEIGHT - floor_y, 'assets/bg/pp.png')
    platforms.append(floor)

    existing_rects = [floor.rect]
    spawn_safe_zone = pygame.Rect(50, 350, 200, 150)
    existing_rects.append(spawn_safe_zone)
    decor_rects = []

    # ประตู
    zone = lvl % 3
    if zone == 1: door_x = random.randint(880, SCREEN_WIDTH - 160)   
    elif zone == 2: door_x = random.randint(700, 880)                  
    else: door_x = random.randint(520, 720)                  

    if door_x < 520: door_x = 520
    min_tier = 1 if lvl <= 2 else 2
    door_tier = random.randint(min_tier, 3)
    door_y = floor_y - (120 + door_tier * 100)

    DOOR_PLAT_W, DOOR_PLAT_H = 150, 20
    door_plat_left = door_x - 29
    door_plat_top  = door_y + 105
    door_plat_rect = pygame.Rect(door_plat_left, door_plat_top, DOOR_PLAT_W, DOOR_PLAT_H)

    LOG_H = 28
    PATH_H = LOG_H
    path_platforms = []

    start_w = random.randint(120, 370)
    start_x = random.randint(100, 250)
    start_y = floor_y - random.randint(100, 320)
    start_rect = pygame.Rect(start_x, start_y, start_w, PATH_H)
    
    if check_overlap(start_rect, [spawn_safe_zone], margin=10):
        start_y = spawn_safe_zone.bottom + 20
        start_rect.y = start_y

    if not check_overlap(start_rect, existing_rects, margin=20):
        p0 = Platform(start_x, start_y, start_w, PATH_H, 'assets/bg/oo.png')
        platforms.append(p0)
        path_platforms.append(p0)
        existing_rects.append(start_rect)

    approach_w = random.randint(180, 260)
    gap_to_door = random.randint(150, 450)
    approach_x = door_plat_left - gap_to_door - approach_w
    approach_x = clamp(approach_x, 80, SCREEN_WIDTH - approach_w - 30)
    approach_y = door_plat_top - random.randint(10, 250)
    approach_y = clamp(approach_y, 340, floor_y - 80)

    if path_platforms:
        last = path_platforms[-1].rect
        dist_x = max(0, door_plat_left - last.right)
    else:
        dist_x = max(0, door_plat_left - 160)

    total_steps = clamp((dist_x // 200) + 3 + door_tier, 4, 8) 
    intermediate_count = max(0, total_steps - 2)

    for i in range(intermediate_count):
        attempts = 0
        placed = False
        while attempts < 14 and not placed:
            w = random.randint(100, 300)
            gap = random.randint(180, 350) 
            if path_platforms:
                prev = path_platforms[-1].rect
                x = prev.right + gap
                if x + w > approach_x - 100: x = (approach_x - 20) - w
            else:
                x = random.randint(160, 360)
            x = clamp(x, 20, SCREEN_WIDTH - w - 20)
            prev_y = path_platforms[-1].rect.y if path_platforms else (floor_y - 100)
            MAX_Y_STEP = 75
            MIN_Y_STEP = 30 
            remaining = (intermediate_count - i + 1)
            ideal_step = (approach_y - prev_y) / max(1, remaining)
            ideal_step = clamp(ideal_step, -MAX_Y_STEP, MAX_Y_STEP)
            if abs(ideal_step) < MIN_Y_STEP: ideal_step = MIN_Y_STEP * (1 if ideal_step >= 0 else -1)
            desired_y = int(round(prev_y + ideal_step + random.randint(-5, 5)))
            desired_y = int(round(desired_y / 10) * 10)
            desired_y = clamp(desired_y, 150, floor_y - 80)
            new_rect = pygame.Rect(x, desired_y, w, PATH_H)
            
            if not check_overlap(new_rect, existing_rects, margin=40):
                p = Platform(x, desired_y, w, PATH_H, 'assets/bg/oo.png')
                platforms.append(p)
                path_platforms.append(p)
                existing_rects.append(new_rect)
                placed = True
            attempts += 1

    attempts = 0
    while attempts < 18:
        new_rect = pygame.Rect(approach_x, approach_y, approach_w, PATH_H)
        if not check_overlap(new_rect, existing_rects, margin=40):
            pA = Platform(approach_x, approach_y, approach_w, PATH_H, 'assets/bg/oo.png')
            platforms.append(pA)
            path_platforms.append(pA)
            existing_rects.append(new_rect)
            break
        approach_x = clamp(approach_x + random.randint(-40, 40), 30, SCREEN_WIDTH - approach_w - 30)
        approach_y = clamp(approach_y + random.randint(-20, 20), 140, floor_y - 80)
        attempts += 1

    platforms.append(Platform(door_plat_left, door_plat_top, DOOR_PLAT_W, DOOR_PLAT_H, 'assets/bg/mm.png'))
    existing_rects.append(door_plat_rect)
    door = Door(door_x, door_y)

    # Platforms เสริม
    num_platforms = random.randint(2, 4)
    for _ in range(num_platforms):
        attempts = 0
        while attempts < 10:
            w = random.randint(120, 220)
            x = random.randint(100, SCREEN_WIDTH - w - 50)
            tiers = [floor_y - 100, floor_y - 220, floor_y - 280]
            y = random.choice(tiers) + random.randint(-10, 10)
            PLAT_H = LOG_H
            cx = x + w // 2
            if abs(cx - door_x) < 180 and y > (door_plat_top - 120):
                attempts += 1
                continue
            new_rect = pygame.Rect(x, y, w, PLAT_H)
            if not check_overlap(new_rect, existing_rects, margin=40):
                p = Platform(x, y, w, PLAT_H, 'assets/bg/oo.png')
                platforms.append(p)
                existing_rects.append(new_rect)
                if random.random() > 0.6: boxes.append(Box(x + w // 2 - 20, y - 40))
                break
            attempts += 1

    # Walls
    num_walls = random.randint(1, 2)
    for _ in range(num_walls):
        attempts = 0
        while attempts < 10:
            w = random.randint(40, 60)
            h = random.randint(100, 140)
            x = random.randint(350, 850)
            y = floor_y - h
            new_rect = pygame.Rect(x, y, w, h)
            if not check_overlap(new_rect, existing_rects, margin=30):
                walls.append(Platform(x, y, w, h, 'assets/box/idle.png', is_wall=True))
                existing_rects.append(new_rect)
                break
            attempts += 1

    # ศัตรู
    for idx, plat in enumerate(path_platforms):
        if idx == 0 and random.random() < 0.6: continue
        if random.random() < 0.75:
            ex_min = plat.rect.x + 20
            ex_max = plat.rect.right - 100
            if ex_max > ex_min:
                ex = random.randint(ex_min, ex_max)
                ey = plat.rect.top - 30
                edist = min(150, max(60, plat.rect.width - 60))
                e_rect = pygame.Rect(ex, ey, 34, 30)
                if not check_overlap(e_rect, [e.rect for e in enemies], margin=10):
                    enemies.append(Enemy(ex, ey, edist))

    if path_platforms:
        plat = path_platforms[-1]
        ex_min = plat.rect.x + 20
        ex_max = plat.rect.right - 100
        if ex_max > ex_min:
            ex = random.randint(ex_min, ex_max)
            ey = plat.rect.top - 30
            edist = min(160, max(70, plat.rect.width - 70))
            e_rect = pygame.Rect(ex, ey, 34, 30)
            if not check_overlap(e_rect, [e.rect for e in enemies], margin=10):
                enemies.append(Enemy(ex, ey, edist))

    num_enemies = min(2 + lvl, 8)
    spawnable_platforms = platforms
    safety = 0
    while len(enemies) < num_enemies and safety < 50:
        chosen_plat = random.choice(spawnable_platforms)
        ex_min = chosen_plat.rect.x + 20
        ex_max = chosen_plat.rect.right - 100
        if ex_max <= ex_min:
            safety += 1
            continue
        ex = random.randint(ex_min, ex_max)
        ey = chosen_plat.rect.top - 30
        edist = min(100, max(60, chosen_plat.rect.width - 60))
        e_rect = pygame.Rect(ex, ey, 34, 30)
        if not check_overlap(e_rect, [e.rect for e in enemies], margin=10):
            enemies.append(Enemy(ex, ey, edist))
        safety += 1

    # Decorations
    for _ in range(4):
        attempts = 0
        while attempts < 10:
            w, h = 100, 100
            x = random.randint(10, SCREEN_WIDTH - w - 10)
            y = random.randint(180, 190)
            new_rect = pygame.Rect(x, y, w, h)
            if not check_overlap(new_rect, decor_rects, margin=10):
                decorations.append(Decoration(x, y, w, h, 'assets/environment/decorations.png'))
                decor_rects.append(new_rect)
                break
            attempts += 1

    all_platforms = platforms + walls
    random.seed()
    return all_platforms, boxes, decorations, enemies, door, bg_image

# --- Main Game Setup ---
player = Player()
cur_level = 1
game_state = "MENU" 
score = 0
coins_list = []
floating_texts = []

heart_img = load_safe_image('assets/lives_coins/health_bar.png', (255, 0, 0), (30, 30))
COIN_SOUND = load_safe_sound('assets/sounds/coin.wav')

platforms, boxes, decorations, enemies, door_obj, bg_img = [], [], [], [], None, None

def start_game(level):
    global cur_level, platforms, boxes, decorations, enemies, door_obj, bg_img, score, coins_list, floating_texts
    cur_level = level
    platforms, boxes, decorations, enemies, door_obj, bg_img = build_level(cur_level)
    player.reset()
    player.rect.topleft = (100, 400)
    coins_list = []
    floating_texts = []

start_game(1)

# --- Main Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.KEYDOWN:
            if game_state == "MENU":
                if event.key == pygame.K_RETURN:
                    game_state = "PLAYING"
                    score = 0
                    start_game(1)
            
            elif game_state == "PLAYING":
                if event.key == pygame.K_j:
                    player.attack(enemies)
                if event.key == pygame.K_SPACE:
                    if player.rect.colliderect(door_obj.rect):
                        player.start_enter_door(door_obj)
            
            elif game_state == "GAMEOVER":
                if event.key == pygame.K_r:
                    game_state = "PLAYING"
                    start_game(cur_level)
                elif event.key == pygame.K_q:
                    game_state = "MENU"

    screen.fill(BLACK)

    if game_state == "MENU":
        # --- [เพิ่มใหม่] เล่นเพลงตอนอยู่หน้าเมนู ---
        play_bg_music()
        
        title_txt = FONT.render("Asgard King Ood", True, (255, 215, 0))
        sub_txt = SMALL_FONT.render("Press ENTER to Start", True, WHITE)
        screen.blit(title_txt, (SCREEN_WIDTH//2 - title_txt.get_width()//2, SCREEN_HEIGHT//2 - 50))
        screen.blit(sub_txt, (SCREEN_WIDTH//2 - sub_txt.get_width()//2, SCREEN_HEIGHT//2 + 20))

    elif game_state == "PLAYING" or game_state == "GAMEOVER" or game_state == "END_DEMO":
        if bg_img: screen.blit(bg_img, (0, 0))

        for dec in decorations: dec.render(screen)

        if game_state == "PLAYING":
            # --- [เพิ่มใหม่] เล่นเพลงตอนเล่นเกม (ถ้าหยุดไป) ---
            play_bg_music()
            
            door_obj.update()
            
            obstacles = platforms + boxes
            player.move(obstacles)

            new_enemies = []
            for e in enemies:
                res = e.update(player.rect, obstacles)
                if res == "hit":
                    player.take_damage(e.rect)
                
                if e.is_dead_finished():
                    coins_list.append(Coin(e.rect.centerx - 12, e.rect.centery - 12))
                else:
                    new_enemies.append(e)
            
            enemies = new_enemies

            for c in coins_list:
                c.update(obstacles)
                if not c.collected and player.rect.colliderect(c.rect):
                    c.collected = True
                    score += 1
                    floating_texts.append(FloatingText(c.rect.centerx, c.rect.y, "+1", YELLOW))
                    if COIN_SOUND:
                        COIN_SOUND.play()
            
            coins_list = [c for c in coins_list if not c.collected and c.life_span > 0]

            new_texts = []
            for t in floating_texts:
                if t.update():
                    pass
                else:
                    new_texts.append(t)
            floating_texts = new_texts

            res = player.update()
            
            if res == "dead":
                game_state = "GAMEOVER"
            
            if res == "next_level":
                cur_level += 1
                if cur_level > MAX_LEVELS:
                    game_state = "END_DEMO"
                else:
                    start_game(cur_level)

        for p in platforms: p.render(screen)
        for b in boxes: b.render(screen)
        door_obj.render(screen)
        
        for c in coins_list: c.render(screen)

        for e in enemies: e.render(screen)
        player.render(screen)

        for t in floating_texts: t.render(screen)

        for i in range(player.hp):
            screen.blit(heart_img, (SCREEN_WIDTH - 40 - (i * 35), 20))
        
        score_txt = FONT.render(f"Coins: {score}", True, YELLOW)
        screen.blit(score_txt, (20, 20))
        
        lvl_txt = SMALL_FONT.render(f"Level: {cur_level}/{MAX_LEVELS}", True, WHITE)
        screen.blit(lvl_txt, (20, 55))

        if game_state == "PLAYING" and player.rect.colliderect(door_obj.rect) and not player.door_target:
            help_txt = FONT.render("Press SPACEBAR", True, (255, 255, 0))
            screen.blit(help_txt, (door_obj.rect.x - 50, door_obj.rect.y - 40))

        if game_state == "GAMEOVER":
            # --- [เพิ่มใหม่] หยุดเพลงตอนตาย ---
            pygame.mixer.music.stop()
            
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(200)
            s.fill((0, 0, 0))
            screen.blit(s, (0, 0))
            
            msg1 = FONT.render("YOU DIED", True, (255, 50, 50))
            msg2 = SMALL_FONT.render("Press 'R' to Respawn", True, WHITE)
            msg3 = SMALL_FONT.render("Press 'Q' to Quit", True, (200, 200, 200))
            
            screen.blit(msg1, (SCREEN_WIDTH//2 - msg1.get_width()//2, SCREEN_HEIGHT//2 - 60))
            screen.blit(msg2, (SCREEN_WIDTH//2 - msg2.get_width()//2, SCREEN_HEIGHT//2))
            screen.blit(msg3, (SCREEN_WIDTH//2 - msg3.get_width()//2, SCREEN_HEIGHT//2 + 40))

        if game_state == "END_DEMO":
            # --- [เพิ่มใหม่] หยุดเพลงตอนจบเกม ---
            pygame.mixer.music.stop()
            
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(220)
            s.fill((0, 0, 0))
            screen.blit(s, (0, 0))
            
            end_msg = FONT.render("END DEMO", True, (255, 215, 0))
            sub_msg = SMALL_FONT.render(f"Total Coins: {score}", True, YELLOW)
            quit_msg = SMALL_FONT.render("Press 'Q' to Quit", True, (200, 200, 200))
            
            screen.blit(end_msg, (SCREEN_WIDTH//2 - end_msg.get_width()//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(sub_msg, (SCREEN_WIDTH//2 - sub_msg.get_width()//2, SCREEN_HEIGHT//2 + 10))
            screen.blit(quit_msg, (SCREEN_WIDTH//2 - quit_msg.get_width()//2, SCREEN_HEIGHT//2 + 50))
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_q]:
                game_state = "MENU"

    pygame.display.flip()
    clock.tick(60)