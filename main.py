import pygame
import os
import sys

# ==========================================
# PART 1: GRAPHICS SYSTEM (เดิมคือ graphics.py)
# ==========================================
class Animation:
    def __init__(self, spritesheet, frame_size, frame_count, loop=True):
        self.frames = []
        for i in range(frame_count):
            # ตัดแบ่งภาพจาก Spritesheet ตามแนวนอน
            rect = pygame.Rect(i * frame_size[0], 0, frame_size[0], frame_size[1])
            frame = spritesheet.subsurface(rect)
            self.frames.append(frame)
        self.index = 0
        self.loop = loop
        self.status = "playing"

    def get_frame(self):
        if self.status == "done" and not self.loop:
            return self.frames[-1]
            
        frame = self.frames[int(self.index)]
        self.index += 0.2  # ความเร็วในการเล่น Animation
        if self.index >= len(self.frames):
            if self.loop:
                self.index = 0
            else:
                self.index = len(self.frames) - 1
                self.status = "done"
        return frame

class AnimationManager:
    def __init__(self, animations):
        self.animations = animations
        self.state = 'idle'
        self.animation_status = "playing"

    def set_state(self, state):
        if self.state != state:
            self.state = state
            self.animations[self.state].index = 0
            self.animations[self.state].status = "playing"

    def update(self):
        self.animation_status = self.animations[self.state].status

    def get_current_animation(self):
        return self.animations[self.state]

# ==========================================
# PART 2: ENTITIES (เดิมคือ entities.py)
# ==========================================
class Player:
    def __init__(self, screen, set_state):
        self.health = 3
        self.velocity = 5
        self.direction = pygame.math.Vector2(0, 0)
        self.jump_force = -18
        self.is_in_air = True
        self.screen = screen
        self.width, self.height = (78, 58)
        self.rect = pygame.Rect(520, 500, self.width - 25, self.height - 10)
        self.flip_sprite = False
        self.set_state = set_state

        # โหลดเสียง (ใส่ try-except เผื่อไม่มีไฟล์)
        try:
            self.swing_sound = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'player', 'swing.wav'))
            self.jump_sound = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'player', 'jump.ogg'))
            self.hit_sound = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'player', 'hit.ogg'))
        except:
            print("Warning: Sound files not found.")

        # โหลด Animations
        self.animations = {
            'idle': Animation(pygame.image.load(os.path.join('assets', 'player', 'idle.png')).convert_alpha(), (self.width, self.height), 5),
            'run': Animation(pygame.image.load(os.path.join('assets', 'player', 'run.png')).convert_alpha(), (self.width, self.height), 7),
            'jump': Animation(pygame.image.load(os.path.join('assets', 'player', 'jump.png')).convert_alpha(), (self.width, self.height), 1),
            'fall': Animation(pygame.image.load(os.path.join('assets', 'player', 'fall.png')).convert_alpha(), (self.width, self.height), 1),
            'attack': Animation(pygame.image.load(os.path.join('assets', 'player', 'attack.png')).convert_alpha(), (self.width, self.height), 5, False),
            'hit': Animation(pygame.image.load(os.path.join('assets', 'player', 'hit.png')).convert_alpha(), (self.width, self.height), 5, False),
        }
        self.animation_manager = AnimationManager(self.animations)

    def update(self):
        self.rect.x += self.direction.x * self.velocity
        self.animation_manager.update()
        if self.direction.y > 1: self.animation_manager.set_state('fall')
        elif self.direction.y < 0: self.animation_manager.set_state('jump')
        if self.health <= 0: self.set_state('lose')

    def render(self):
        surface = self.animation_manager.get_current_animation().get_frame()
        if self.flip_sprite:
            surface = pygame.transform.flip(surface, True, False)
            self.screen.blit(surface, (self.rect.x - 70, self.rect.y - 40))
        else:
            self.screen.blit(surface, (self.rect.x - 40, self.rect.y - 40))

    def jump(self):
        self.direction.y = self.jump_force
        self.animation_manager.set_state('jump')

    def gravity(self):
        self.direction.y += 0.9
        self.rect.y += self.direction.y

# ==========================================
# PART 3: MAIN GAME ENGINE
# ==========================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((1200, 700))
    pygame.display.set_caption("King Oink - Integrated Version")
    clock = pygame.time.Clock()

    def dummy_set_state(s): print(f"Change state to: {s}")

    try:
        player = Player(screen, dummy_set_state)
    except Exception as e:
        print(f"Error: {e}")
        print("\nทำตามขั้นตอนนี้: \n1. สร้างโฟลเดอร์ assets\n2. ไปโหลดภาพจาก GitHub KingOink มาใส่ให้ถูกที่\n")
        return

    while True:
        screen.fill((50, 50, 50)) # พื้นหลังเทาเข้ม
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: player.jump()

        # การควบคุมตัวละคร
        keys = pygame.key.get_pressed()
        player.direction.x = 0
        if keys[pygame.K_a]:
            player.direction.x = -1
            player.flip_sprite = True
            player.animation_manager.set_state('run')
        elif keys[pygame.K_d]:
            player.direction.x = 1
            player.flip_sprite = False
            player.animation_manager.set_state('run')
        else:
            if player.animation_manager.state not in ['attack', 'jump', 'fall']:
                player.animation_manager.set_state('idle')

        player.gravity()
        # พื้นดินสมมติ (Collision Simple)
        if player.rect.y > 500:
            player.rect.y = 500
            player.direction.y = 0

        player.update()
        player.render()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()