import pygame
import sys
import random
import math
import os

# --- CONFIGURACIÓN E INICIALIZACIÓN ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colores (Fallback)
NEON_GREEN = (57, 255, 20)
NEON_RED = (255, 20, 147)
NEON_BLUE = (0, 255, 255)
DARK_SPACE = (10, 10, 25)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galactic Hunter: Alien Crisis")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False) 

# Fuentes
try:
    font_files = pygame.font.match_font('arialblack', 'arial')
    title_font = pygame.font.Font(font_files, 60)
    ui_font = pygame.font.Font(font_files, 24)
    floating_font = pygame.font.Font(font_files, 20)
    combo_font = pygame.font.Font(font_files, 40)
except:
    title_font = pygame.font.SysFont(None, 60)
    ui_font = pygame.font.SysFont(None, 24)
    floating_font = pygame.font.SysFont(None, 20)
    combo_font = pygame.font.SysFont(None, 40)

# Estados
STATE_START = "start"
STATE_MENU = "menu"
STATE_LEVEL = "level"
STATE_GAME_OVER = "game_over"
STATE_LEVEL_WON = "level_won"

current_state = STATE_START
score = 0
current_difficulty_index = 1
DIFFICULTY_MODES = ["Fácil", "Normal", "Difícil"]
current_difficulty = DIFFICULTY_MODES[current_difficulty_index]

# Variables globales de partida
player_health = 0
shots_remaining = 0
combo_count = 0
max_consecutive_combo = 0
levels_completed = {1: False, 2: False, 3: False}

# --- SISTEMA DE ASSETS ---

ASSETS = {
    "images": {
        1: {"aliens": [], "boss": None, "bg": None},
        2: {"aliens": [], "boss": None, "bg": None},
        3: {"aliens": [], "boss": None, "bg": None},
        "kitten": None,
        "combos": {},     
        "crosshair": {}   
    },
    "sounds": {},
    "music": {}
}

def load_image(path, size=None, exact_size=None):
    full_path = os.path.join(*path.split('/'))
    if os.path.exists(full_path):
        try:
            img = pygame.image.load(full_path).convert_alpha()
            if exact_size:
                img = pygame.transform.scale(img, exact_size)
            elif size:
                aspect = img.get_width() / img.get_height()
                img = pygame.transform.scale(img, (int(size * aspect), size))
            return img
        except Exception as e:
            print(f"Error cargando imagen {full_path}: {e}")
            return None
    else:
        return None

def load_game_assets():
    print("Cargando assets...")
    
    ALIEN_SIZE = 90
    BOSS_SIZE = 200
    KITTEN_SIZE = 80
    
    # --- NIVELES ---
    ASSETS["images"][1]["bg"] = load_image("Imagenes/Agua/Escenario_Agua.png", exact_size=(WIDTH, HEIGHT))
    ASSETS["images"][1]["boss"] = load_image("Imagenes/Agua/Boss_agua.png", BOSS_SIZE)
    for i in range(1, 4):
        img = load_image(f"Imagenes/Agua/Alien_agua{i}.png", ALIEN_SIZE)
        if img: ASSETS["images"][1]["aliens"].append(img)
        
    ASSETS["images"][2]["bg"] = load_image("Imagenes/Planta/Escenario_Planta.png", exact_size=(WIDTH, HEIGHT))
    ASSETS["images"][2]["boss"] = load_image("Imagenes/Planta/Boss_planta.png", BOSS_SIZE)
    for i in range(1, 5):
        img = load_image(f"Imagenes/Planta/Alien_planta{i}.png", ALIEN_SIZE)
        if img: ASSETS["images"][2]["aliens"].append(img)
        
    ASSETS["images"][3]["bg"] = load_image("Imagenes/Fuego/escenario.png", exact_size=(WIDTH, HEIGHT))
    ASSETS["images"][3]["boss"] = load_image("Imagenes/Fuego/boss.png", BOSS_SIZE)
    for i in range(1, 4): 
        img = load_image(f"Imagenes/Fuego/enemigo{i}.png", ALIEN_SIZE)
        if img: ASSETS["images"][3]["aliens"].append(img)

    ASSETS["images"]["kitten"] = load_image("Imagenes/Gatitos/gatito_vivo.png", KITTEN_SIZE)

    # --- COMBOS ---
    combo_path = "ImageCombo" 
    ASSETS["images"]["combos"][2] = load_image(f"ImageCombo/ComboX2.png", size=80)
    ASSETS["images"]["combos"][3] = load_image(f"ImageCombo/ComboX3.png", size=100)
    ASSETS["images"]["combos"][5] = load_image(f"ImageCombo/ComboX5.png", size=120)
    ASSETS["images"]["combos"]["super"] = load_image(f"ImageCombo/ComboSuper.png", size=140)

    # --- MIRAS ---
    mira_path = "Imagenes/ImageMira"
    ASSETS["images"]["crosshair"]["normal"] = load_image(f"{mira_path}/MiraAzul1.png", size=60)
    ASSETS["images"]["crosshair"]["shoot"] = load_image(f"{mira_path}/MiraAzul2.png", size=60)

    # --- AUDIO ---
    sfx_files = {
        "shoot": "Audio/Efectos de sonido/disparo2.wav",
        "menu_nav": "Audio/Efectos de sonido/NavMenu.wav",
        "level_select": "Audio/Efectos de sonido/SelecLevel1.wav"
    }
    for key, path in sfx_files.items():
        full_path = os.path.join(*path.split('/'))
        if os.path.exists(full_path):
            ASSETS["sounds"][key] = pygame.mixer.Sound(full_path)
            ASSETS["sounds"][key].set_volume(0.4)

    music_files = {
        "menu": "Audio/Música/Menús.mp3",
        "level_1": "Audio/Música/Nivel 1 (agua).mp3",
        "level_2": "Audio/Música/Nivel 2 (planta).mp3",
        "level_3": "Audio/Música/Nivel 3 (fuego).mp3"
    }
    for key, path in music_files.items():
        full_path = os.path.join(*path.split('/'))
        if os.path.exists(full_path):
            ASSETS["music"][key] = full_path

def play_music(track_key):
    if track_key in ASSETS["music"]:
        try:
            pygame.mixer.music.load(ASSETS["music"][track_key])
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
        except: pass

def play_sfx(key):
    if key in ASSETS["sounds"]: ASSETS["sounds"][key].play()

load_game_assets()

# --- CLASES VISUALES ---

class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.choice([0.5, 1, 2])
        self.size = int(self.speed)
        self.color = (random.randint(200, 255), random.randint(200, 255), 255)
    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)
    def draw(self, surface):
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 150), (self.size, self.size), self.size)
        surface.blit(s, (self.x, self.y))

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((random.randint(3, 6), random.randint(3, 6)))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.life = 40
    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.life -= 1
        if self.life < 10: self.image.set_alpha(self.life * 25)
        if self.life <= 0: self.kill()

class FloatingText(pygame.sprite.Sprite):
    def __init__(self, text, x, y, color=WHITE, size_mult=1.0):
        super().__init__()
        font = pygame.font.Font(pygame.font.match_font('arialblack'), int(20 * size_mult)) if pygame.font.match_font('arialblack') else floating_font
        self.image = font.render(text, True, color)
        self.rect = self.image.get_rect(center=(x, y))
        self.dy = -2
        self.life = 60
    def update(self):
        self.rect.y += self.dy
        self.life -= 1
        if self.life < 20: self.image.set_alpha(self.life * 12)
        if self.life <= 0: self.kill()

class ComboImage(pygame.sprite.Sprite):
    def __init__(self, combo_key, x, y):
        super().__init__()
        orig_image = ASSETS["images"]["combos"].get(combo_key)
        if orig_image:
            self.image = orig_image.copy()
        else:
            font = pygame.font.Font(None, 80)
            txt = "SUPER!" if combo_key == "super" else f"COMBO x{combo_key}!"
            self.image = font.render(txt, True, NEON_GREEN)
        self.rect = self.image.get_rect(center=(x, y))
        self.life = 60 
    def update(self):
        self.rect.y -= 2 
        self.life -= 1
        if self.life < 20: self.image.set_alpha(self.life * 12)
        if self.life <= 0: self.kill()

class Crosshair(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.img_normal = ASSETS["images"]["crosshair"].get("normal")
        self.img_shoot = ASSETS["images"]["crosshair"].get("shoot")
        
        if not self.img_normal:
            self.img_normal = self._create_geometric_crosshair(NEON_BLUE)
        if not self.img_shoot:
            self.img_shoot = self._create_geometric_crosshair(NEON_RED)
            
        self.image = self.img_normal
        self.rect = self.image.get_rect()
        self.cooldown_timer = 0
        self.COOLDOWN_TIME = 30 
        
    def _create_geometric_crosshair(self, color):
        s = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (30, 30), 28, 2)
        pygame.draw.line(s, color, (0, 30), (60, 30), 2)
        pygame.draw.line(s, color, (30, 0), (30, 60), 2)
        return s

    def update(self):
        pos = pygame.mouse.get_pos()
        self.rect.center = pos
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
            self.image = self.img_shoot 
        else:
            self.image = self.img_normal 

    def try_shoot(self):
        if self.cooldown_timer > 0: return False
        self.cooldown_timer = self.COOLDOWN_TIME 
        return True

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# --- CLASES DEL JUEGO (ENEMIGOS) ---

def create_alien_surface(size, color, type="normal"):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    if type == "normal": pygame.draw.circle(surf, color, (size//2, size//2), size//2)
    elif type == "toxic": pygame.draw.rect(surf, color, (5, 5, size-10, size-10), border_radius=5)
    elif type == "boss": pygame.draw.ellipse(surf, color, (0, size//3, size, size//2))
    return surf

class Alien(pygame.sprite.Sprite):
    def __init__(self, level=1, speed_mult=1.0):
        super().__init__()
        self.size = 90
        self.color = NEON_RED
        loaded_imgs = ASSETS["images"].get(level, {}).get("aliens", [])
        self.image = random.choice(loaded_imgs) if loaded_imgs else create_alien_surface(self.size, self.color, "normal")
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.size)
        self.rect.y = random.randint(0, HEIGHT - self.size)
        
        # Velocidad base + multiplicador del modo infinito
        self.speed = (2 + (level * 0.5)) * speed_mult
        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.choice([-1, 1]) * self.speed

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.left < 0 or self.rect.right > WIDTH: self.dx *= -1; self.rect.x = max(0, min(self.rect.x, WIDTH - self.size))
        if self.rect.top < 0 or self.rect.bottom > HEIGHT: self.dy *= -1; self.rect.y = max(0, min(self.rect.y, HEIGHT - self.size))

class Kitten(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 80
        kitten_img = ASSETS["images"].get("kitten")
        self.image = kitten_img if kitten_img else create_alien_surface(self.size, NEON_GREEN, "toxic")
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.size)
        self.rect.y = random.randint(0, HEIGHT - self.size)
        self.speed = 3
        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.choice([-1, 1]) * self.speed

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.left < 0 or self.rect.right > WIDTH: self.dx *= -1
        if self.rect.top < 0 or self.rect.bottom > HEIGHT: self.dy *= -1

class Mothership(Alien):
    def __init__(self, level=1):
        super().__init__(level)
        self.size = 200
        boss_img = ASSETS["images"].get(level, {}).get("boss")
        self.image = boss_img if boss_img else create_alien_surface(self.size, NEON_BLUE, "boss")
        self.rect = self.image.get_rect(center=self.rect.center)
        self.speed = 5 + level
        self.health = 5 + level 
    def update(self):
        super().update()
        if random.random() < 0.01:
            self.rect.x += self.dx * 10
            self.rect.y += self.dy * 10
            self.rect.clamp_ip(screen.get_rect())

# --- UI ---

def draw_text_centered(text, font, color, y_offset=0):
    t = font.render(text, True, color)
    rect = t.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    screen.blit(t, rect)

def draw_hud():
    s = pygame.Surface((WIDTH, 50))
    s.set_alpha(150)
    s.fill((0,0,0))
    screen.blit(s, (0,0))
    
    score_surf = ui_font.render(f"PUNTOS: {score}", True, YELLOW)
    screen.blit(score_surf, (20, 15))
    
    pygame.draw.rect(screen, (50, 0, 0), (WIDTH - 220, 15, 200, 20))
    hp_pct = max(0, player_health) / 400.0
    pygame.draw.rect(screen, NEON_RED, (WIDTH - 220, 15, 200 * hp_pct, 20))
    hp_text = ui_font.render(f"HP: {player_health}", True, WHITE)
    screen.blit(hp_text, (WIDTH - 220 + 70, 15))
    
    ammo_color = NEON_BLUE if shots_remaining > 5 else NEON_RED
    ammo_text = ui_font.render(f"BALAS: {shots_remaining}", True, ammo_color)
    screen.blit(ammo_text, (WIDTH // 2 - 40, 15))

    if combo_count > 1:
        c_color = NEON_GREEN if combo_count < 5 else NEON_BLUE
        if combo_count >= 10: c_color = YELLOW
        combo_txt = combo_font.render(f"COMBO x{combo_count}!", True, c_color)
        screen.blit(combo_txt, (WIDTH // 2 - combo_txt.get_width() // 2, 70))

def draw_exit_button():
    btn_rect = pygame.Rect(10, HEIGHT - 40, 100, 30)
    mouse_pos = pygame.mouse.get_pos()
    color = (255, 50, 50) if btn_rect.collidepoint(mouse_pos) else (200, 200, 200)
    pygame.draw.rect(screen, color, btn_rect, border_radius=5)
    pygame.draw.rect(screen, WHITE, btn_rect, 2, border_radius=5)
    txt = ui_font.render("ABORTAR", True, (0,0,0))
    screen.blit(txt, (20, HEIGHT - 35))
    return btn_rect

# --- LOGICA DEL MODO NORMAL ---

def initialize_stats(level, num_enemies, difficulty):
    global player_health, shots_remaining, combo_count, max_consecutive_combo
    combo_count = 0
    max_consecutive_combo = 0
    base_ammo = num_enemies + (5 if level == 3 else 3) 
    if difficulty == "Fácil": shots_remaining = 999
    elif difficulty == "Normal": shots_remaining = int(base_ammo * 2.5)
    else: shots_remaining = base_ammo * 2
    player_health = 100 + (shots_remaining * 20) 

def run_level(level):
    global current_state, score, player_health, shots_remaining, combo_count, max_consecutive_combo
    
    play_music(f"level_{level}")
    score = 0
    
    aliens = pygame.sprite.Group()
    kittens = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    floating_texts = pygame.sprite.Group()
    combo_sprites = pygame.sprite.Group() 
    all_sprites = pygame.sprite.Group()
    
    stars = [Star() for _ in range(30)]
    crosshair = Crosshair() 
    level_bg = ASSETS["images"][level]["bg"]
    boss = None
    
    level_targets = 5 + (level * 2)
    for _ in range(level_targets):
        a = Alien(level)
        aliens.add(a)
    
    if level >= 2:
        for _ in range(3 + level):
            k = Kitten()
            kittens.add(k)

    enemies_to_kill = level_targets + 1
    initialize_stats(level, enemies_to_kill, current_difficulty)
    
    running = True
    boss_spawned = False
    game_result = None 
    
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        crosshair.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    exit_btn = draw_exit_button()
                    if exit_btn.collidepoint(mouse_pos):
                        play_sfx("menu_nav")
                        game_result = 'exit'; running = False; break
                    
                    if shots_remaining > 0:
                        if not crosshair.try_shoot(): continue 
                        
                        play_sfx("shoot")
                        if current_difficulty != "Fácil": shots_remaining -= 1
                        
                        hit_something = False
                        
                        for alien in [s for s in aliens if s.rect.collidepoint(mouse_pos)]:
                            for _ in range(10): particles.add(Particle(alien.rect.centerx, alien.rect.centery, alien.color))
                            alien.kill()
                            score += 100 + (combo_count * 20)
                            floating_texts.add(FloatingText(f"+{100+(combo_count*20)}", mouse_pos[0], mouse_pos[1], YELLOW))
                            hit_something = True
                        
                        if boss and boss.rect.collidepoint(mouse_pos):
                            boss.health -= 1
                            hit_something = True
                            for _ in range(5): particles.add(Particle(mouse_pos[0], mouse_pos[1], WHITE))
                            if boss.health <= 0:
                                for _ in range(50): particles.add(Particle(boss.rect.centerx, boss.rect.centery, NEON_BLUE))
                                boss.kill()
                                score += 1000
                                levels_completed[level] = True
                                game_result = 'won'; running = False
                        
                        for k in [s for s in kittens if s.rect.collidepoint(mouse_pos)]:
                            player_health = 0; game_result = 'lost'; running = False
                        
                        if hit_something:
                            combo_count += 1
                            if combo_count > max_consecutive_combo: max_consecutive_combo = combo_count
                            
                            c_img = None
                            spawn_x, spawn_y = mouse_pos
                            
                            if combo_count == 2: c_img = ComboImage(2, spawn_x, spawn_y)
                            elif combo_count == 3: c_img = ComboImage(3, spawn_x, spawn_y)
                            elif combo_count == 5: c_img = ComboImage(5, spawn_x, spawn_y)
                            elif combo_count > 5: c_img = ComboImage("super", spawn_x, spawn_y)
                            
                            if c_img: combo_sprites.add(c_img)

                            if combo_count % 3 == 0:
                                shots_remaining += 2
                                floating_texts.add(FloatingText("AMMO +2", mouse_pos[0], mouse_pos[1]-20, NEON_GREEN))
                        else:
                            combo_count = 0
                            if current_difficulty == "Difícil":
                                player_health -= 20
                                floating_texts.add(FloatingText("-20 HP", mouse_pos[0], mouse_pos[1], NEON_RED))
        
        if not boss_spawned and len(aliens) == 0:
            boss = Mothership(level)
            boss_spawned = True
            floating_texts.add(FloatingText("¡ALERTA JEFE!", WIDTH//2, HEIGHT//2, NEON_RED, 2.0))
        
        for s in stars: s.update()
        if boss: boss.update()
        aliens.update(); kittens.update()
        particles.update(); floating_texts.update()
        combo_sprites.update()
        
        if player_health <= 0 or (shots_remaining <= 0 and len(aliens) > 0 and current_difficulty != "Fácil"):
            game_result = 'lost'; running = False

        screen.fill(DARK_SPACE)
        if level_bg: screen.blit(level_bg, (0,0))
        for s in stars: s.draw(screen)
        
        aliens.draw(screen); kittens.draw(screen)
        if boss: screen.blit(boss.image, boss.rect)
        
        particles.draw(screen); floating_texts.draw(screen)
        combo_sprites.draw(screen)
        
        draw_hud() 
        draw_exit_button()
        crosshair.draw(screen)
        
        pygame.display.flip()

    return game_result, {'score': score, 'max_combo': max_consecutive_combo}

# --- LÓGICA MODO INFINITO ---

def run_infinite_mode():
    global current_state, score, player_health, shots_remaining, combo_count, max_consecutive_combo
    
    # Seleccionamos música aleatoria al inicio
    current_music_track = random.choice([1, 2, 3])
    play_music(f"level_{current_music_track}")
    
    score = 0
    combo_count = 0
    max_consecutive_combo = 0
    
    # Stats Iniciales Modo Infinito
    player_health = 800
    shots_remaining = 30 # Empiezas con munición limitada
    
    aliens = pygame.sprite.Group()
    kittens = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    floating_texts = pygame.sprite.Group()
    combo_sprites = pygame.sprite.Group() 
    
    stars = [Star() for _ in range(30)]
    crosshair = Crosshair() 
    
    # Variables de progresión
    monsters_killed = 0
    monster_speed_mult = 1.0
    
    running = True
    game_result = None
    
    # Usamos un fondo base inicial
    current_bg_index = 1
    level_bg = ASSETS["images"][current_bg_index]["bg"]
    
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        crosshair.update()
        
        # --- SPAWN LOGIC ---
        # 1. Monstruos: Máximo 15 en pantalla
        if len(aliens) < 15:
            # Elegimos tipo visual aleatorio entre los niveles 1, 2 y 3
            visual_level = random.randint(1, 3)
            # Pasamos el multiplicador de velocidad
            a = Alien(visual_level, speed_mult=monster_speed_mult)
            aliens.add(a)
        
        # 2. Gatitos: Aumentan progresivamente hasta máx 20
        # Formula: Base 3 + 1 por cada 10 kills, tope 20
        max_kittens = min(20, 3 + (monsters_killed // 10))
        if len(kittens) < max_kittens:
            if random.random() < 0.05: # Chance pequeño de spawn por frame para no llenar de golpe
                k = Kitten()
                kittens.add(k)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    exit_btn = draw_exit_button()
                    if exit_btn.collidepoint(mouse_pos):
                        play_sfx("menu_nav")
                        game_result = 'exit'; running = False; break
                    
                    if shots_remaining > 0:
                        if not crosshair.try_shoot(): continue 
                        
                        play_sfx("shoot")
                        shots_remaining -= 1
                        
                        hit_something = False
                        
                        # Hit Alien
                        for alien in [s for s in aliens if s.rect.collidepoint(mouse_pos)]:
                            for _ in range(10): particles.add(Particle(alien.rect.centerx, alien.rect.centery, alien.color))
                            alien.kill()
                            hit_something = True
                            
                            # PROGRESIÓN MODO INFINITO
                            monsters_killed += 1
                            score += 100 + (combo_count * 20)
                            floating_texts.add(FloatingText(f"+{100+(combo_count*20)}", mouse_pos[0], mouse_pos[1], YELLOW))
                            
                            
                            
                            # 1. Velocidad: Aumenta cada 10 kills
                            if monsters_killed % 10 == 0:
                                monster_speed_mult += 0.05
                                floating_texts.add(FloatingText("¡ENEMIGOS MÁS RÁPIDOS!", WIDTH//2, 100, NEON_RED, 1.5))
                            
                            # 2. Balas: Se recargan cada 20 kills
                            if monsters_killed % 20 == 0:
                                shots_remaining += 20 # Recarga generosa
                                floating_texts.add(FloatingText("¡RECARGA DE ARMA!", WIDTH//2, HEIGHT//2, NEON_BLUE, 2.0))
                                play_sfx("level_select") # Sonido de confirmación

                            # 3. Cambio de escenario (Visual) cada 50 kills
                            if monsters_killed % 50 == 0:
                                current_bg_index = (current_bg_index % 3) + 1
                                level_bg = ASSETS["images"][current_bg_index]["bg"]
                                # Cambiar música también
                                play_music(f"level_{current_bg_index}")
                        
                        # Hit Gatito (Game Over directo)
                        for k in [s for s in kittens if s.rect.collidepoint(mouse_pos)]:
                            player_health = 0; game_result = 'lost'; running = False
                        
                        if hit_something:
                            combo_count += 1
                            if combo_count > max_consecutive_combo: max_consecutive_combo = combo_count
                            
                            c_img = None
                            spawn_x, spawn_y = mouse_pos
                            if combo_count % 3 ==0:
                                shots_remaining += 2
                            if combo_count == 2: c_img = ComboImage(2, spawn_x, spawn_y)
                            elif combo_count == 3: c_img = ComboImage(3, spawn_x, spawn_y)
                            elif combo_count == 5: c_img = ComboImage(5, spawn_x, spawn_y)
                            elif combo_count > 5: c_img = ComboImage("super", spawn_x, spawn_y)
                            
                            if c_img: combo_sprites.add(c_img)
                        else:
                            combo_count = 0
                            # En modo infinito fallar quita vida
                            player_health -= 20
                            floating_texts.add(FloatingText("-20 HP", mouse_pos[0], mouse_pos[1], NEON_RED))

        for s in stars: s.update()
        aliens.update(); kittens.update()
        particles.update(); floating_texts.update()
        combo_sprites.update()
        
        if player_health <= 0 or (shots_remaining <= 0 and len(aliens) > 0):
            game_result = 'lost'; running = False

        screen.fill(DARK_SPACE)
        if level_bg: screen.blit(level_bg, (0,0))
        for s in stars: s.draw(screen)
        
        aliens.draw(screen); kittens.draw(screen)
        
        particles.draw(screen); floating_texts.draw(screen)
        combo_sprites.draw(screen)
        
        # UI Personalizada para Modo Infinito
        draw_hud()
        # Mostrar contador de muertes
        kills_txt = ui_font.render(f"KILLS: {monsters_killed}", True, WHITE)
        screen.blit(kills_txt, (WIDTH - 150, 45))
        
        draw_exit_button()
        crosshair.draw(screen)
        
        pygame.display.flip()

    return game_result, {'score': score, 'max_combo': max_consecutive_combo}

# --- MENU PRINCIPAL ---

def main_loop():
    global current_state, current_difficulty_index, current_difficulty, score
    last_stats = {}
    play_music("menu")
    menu_crosshair = Crosshair() 
    
    running = True
    while running:
        menu_crosshair.update() 
        
        if current_state == STATE_START:
            screen.fill(DARK_SPACE)
            draw_text_centered("GALACTIC HUNTER", title_font, NEON_BLUE, -50)
            draw_text_centered("Click para iniciar misión", ui_font, WHITE, 50)
            menu_crosshair.draw(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    play_sfx("menu_nav")
                    current_state = STATE_MENU

        elif current_state == STATE_MENU:
            if not pygame.mixer.music.get_busy(): play_music("menu")
            screen.fill(DARK_SPACE)
            draw_text_centered("SELECTOR DE MISION", title_font, WHITE, -200)
            mx, my = pygame.mouse.get_pos()
            
            # Botones Niveles 1-3
            for i in range(1, 4):
                rect = pygame.Rect(WIDTH//2 - 100, 120 + (i * 70), 200, 50)
                color = NEON_BLUE if rect.collidepoint((mx,my)) else (50, 50, 100)
                pygame.draw.rect(screen, color, rect, border_radius=10)
                pygame.draw.rect(screen, NEON_GREEN if levels_completed[i] else WHITE, rect, 2, border_radius=10)
                text_surf = ui_font.render(f"NIVEL {i}", True, WHITE)
                screen.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
            
            # Botón MODO INFINITO (Ajustado)
            inf_rect = pygame.Rect(WIDTH//2 - 100, 420, 200, 50) # Coordenada Y cambiada a 420
            inf_color = NEON_RED if inf_rect.collidepoint((mx,my)) else (100, 0, 50)
            pygame.draw.rect(screen, inf_color, inf_rect, border_radius=10)
            pygame.draw.rect(screen, YELLOW, inf_rect, 2, border_radius=10)
            inf_txt = ui_font.render("MODO INFINITO", True, WHITE)
            screen.blit(inf_txt, (inf_rect.centerx - inf_txt.get_width()//2, inf_rect.centery - inf_txt.get_height()//2))

            # Selector Dificultad
            diff_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT - 80, 300, 50)
            pygame.draw.rect(screen, (100, 50, 50) if diff_rect.collidepoint((mx,my)) else (50, 50, 50), diff_rect, border_radius=10)
            draw_text_centered(f"Dificultad: < {current_difficulty} >", ui_font, YELLOW, 240)

            menu_crosshair.draw(screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Click Niveles 1-3
                    for i in range(1, 4):
                        if pygame.Rect(WIDTH//2 - 100, 120 + (i * 70), 200, 50).collidepoint((mx, my)):
                            play_sfx("level_select")
                            pygame.mixer.music.stop()
                            result, stats = run_level(i)
                            last_stats = stats; last_stats['difficulty'] = current_difficulty
                            play_music("menu")
                            if result == 'won': current_state = STATE_LEVEL_WON
                            elif result == 'lost': current_state = STATE_GAME_OVER
                            elif result == 'exit': current_state = STATE_MENU
                    
                    # Click Modo Infinito
                    if inf_rect.collidepoint((mx, my)):
                        play_sfx("level_select")
                        pygame.mixer.music.stop()
                        result, stats = run_infinite_mode()
                        last_stats = stats
                        play_music("menu")
                        if result == 'lost': current_state = STATE_GAME_OVER
                        elif result == 'exit': current_state = STATE_MENU

                    # Click Dificultad
                    if diff_rect.collidepoint((mx, my)):
                        play_sfx("menu_nav")
                        current_difficulty_index = (current_difficulty_index + 1) % len(DIFFICULTY_MODES)
                        current_difficulty = DIFFICULTY_MODES[current_difficulty_index]

        elif current_state == STATE_LEVEL_WON:
            screen.fill((0, 50, 0))
            draw_text_centered("¡MISIÓN CUMPLIDA!", title_font, NEON_GREEN, -150)
            draw_text_centered(f"Puntuación: {last_stats.get('score',0)}", ui_font, WHITE, -50)
            draw_text_centered(f"Mejor Racha: {last_stats.get('max_combo',0)}", ui_font, YELLOW, 50)
            draw_text_centered("Click para volver a la base", ui_font, (200, 200, 200), 150)
            menu_crosshair.draw(screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN: play_sfx("menu_nav"); current_state = STATE_MENU

        elif current_state == STATE_GAME_OVER:
            screen.fill((50, 0, 0))
            draw_text_centered("SEÑAL PERDIDA", title_font, NEON_RED, -100)
            draw_text_centered(f"Puntuación Final: {score}", ui_font, WHITE, 0)
            draw_text_centered("¡Mataste un gatito!" if player_health == 0 and shots_remaining > 0 else "Misión Fallida", ui_font, YELLOW, 50)
            draw_text_centered("Click para reintentar", ui_font, (200, 200, 200), 150)
            menu_crosshair.draw(screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN: play_sfx("menu_nav"); current_state = STATE_MENU
        
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main_loop()