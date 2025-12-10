import pygame
import sys
import random
import math

# --- CONFIGURACIÓN E INICIALIZACIÓN ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colores (Paleta Neon Space)
NEON_GREEN = (57, 255, 20)
NEON_RED = (255, 20, 147) # Deep Pink
NEON_BLUE = (0, 255, 255)
DARK_SPACE = (10, 10, 25)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galactic Hunter: Alien Crisis")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False) # Ocultamos el ratón para usar nuestra propia mira

# Fuentes
try:
    font_files = pygame.font.match_font('arialblack', 'arial')
    title_font = pygame.font.Font(font_files, 60)
    ui_font = pygame.font.Font(font_files, 24)
    floating_font = pygame.font.Font(font_files, 20)
except:
    title_font = pygame.font.SysFont(None, 60)
    ui_font = pygame.font.SysFont(None, 24)
    floating_font = pygame.font.SysFont(None, 20)

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

# --- CLASES VISUALES (JUICE) ---

class Star:
    """Fondo de estrellas en movimiento para dar profundidad"""
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
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

class Particle(pygame.sprite.Sprite):
    """Efecto de explosión al matar enemigos"""
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((random.randint(3, 6), random.randint(3, 6)))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.life = 40 # Frames de vida

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.life -= 1
        # Efecto de desvanecimiento (shrink)
        if self.life < 10:
            self.image.set_alpha(self.life * 25)
        if self.life <= 0:
            self.kill()

class FloatingText(pygame.sprite.Sprite):
    """Texto que flota hacia arriba (+100, Combo!)"""
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
        if self.life < 20:
            self.image.set_alpha(self.life * 12)
        if self.life <= 0:
            self.kill()

# --- CLASES DEL JUEGO ---

def create_alien_surface(size, color, type="normal"):
    """Dibuja un alien proceduralmente en una surface"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    if type == "normal":
        # Cuerpo
        pygame.draw.circle(surf, color, (size//2, size//2), size//2)
        # Ojos
        pygame.draw.circle(surf, (0,0,0), (size//3, size//2 - 5), size//8)
        pygame.draw.circle(surf, (0,0,0), (size - size//3, size//2 - 5), size//8)
        # Antenas
        pygame.draw.line(surf, color, (size//2, size//2), (size//4, 0), 3)
        pygame.draw.line(surf, color, (size//2, size//2), (size - size//4, 0), 3)
    
    elif type == "toxic":
        # Forma cuadrada/irregular
        pygame.draw.rect(surf, color, (5, 5, size-10, size-10), border_radius=5)
        # Cruz de peligro
        pygame.draw.line(surf, (0,0,0), (10, 10), (size-10, size-10), 3)
        pygame.draw.line(surf, (0,0,0), (size-10, 10), (10, size-10), 3)
        
    elif type == "boss":
        # Platillo volante
        pygame.draw.ellipse(surf, color, (0, size//3, size, size//2)) # Base
        pygame.draw.circle(surf, (100, 200, 255), (size//2, size//3), size//4) # Cabina
        # Luces
        for i in range(0, size, 15):
            pygame.draw.circle(surf, YELLOW, (i + 10, size//2 + 10), 3)
            
    return surf

class Alien(pygame.sprite.Sprite):
    def __init__(self, level=1):
        super().__init__()
        self.size = 50
        self.color = NEON_RED
        self.image = create_alien_surface(self.size, self.color, "normal")
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.size)
        self.rect.y = random.randint(0, HEIGHT - self.size)
        
        self.speed = 2 + (level * 0.5)
        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.choice([-1, 1]) * self.speed
        
        # Animación de bamboleo
        self.wobble_timer = 0

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        # Rebote
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.dx *= -1
            self.rect.x = max(0, min(self.rect.x, WIDTH - self.size))
        if self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.dy *= -1
            self.rect.y = max(0, min(self.rect.y, HEIGHT - self.size))

        # Movimiento errático para niveles altos
        if random.random() < 0.02:
            self.dx += random.uniform(-0.5, 0.5)
            self.dy += random.uniform(-0.5, 0.5)
            # Normalizar velocidad
            dist = math.hypot(self.dx, self.dy)
            if dist > self.speed * 1.5:
                self.dx = (self.dx / dist) * self.speed
                self.dy = (self.dy / dist) * self.speed

class ToxicAlien(pygame.sprite.Sprite):
    """Enemigos que NO debes matar"""
    def __init__(self):
        super().__init__()
        self.size = 45
        self.image = create_alien_surface(self.size, NEON_GREEN, "toxic")
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
        self.size = 100
        self.image = create_alien_surface(self.size, NEON_BLUE, "boss")
        self.rect = self.image.get_rect(center=self.rect.center)
        self.speed = 5 + level
        self.health = 3 # El jefe necesita 3 disparos
        
    def update(self):
        super().update()
        # El jefe se mueve un poco más rápido de vez en cuando (Dash)
        if random.random() < 0.01:
            self.rect.x += self.dx * 10
            self.rect.y += self.dy * 10
            # Mantener en pantalla
            self.rect.clamp_ip(screen.get_rect())

# --- FUNCIONES DE DIBUJO Y UI ---

def draw_crosshair(surface, pos, ammo):
    """Dibuja una mira futurista en el cursor"""
    x, y = pos
    color = NEON_BLUE if ammo > 0 else (100, 100, 100)
    
    # Círculo central
    pygame.draw.circle(surface, color, (x, y), 5) 
    # Anillo exterior
    pygame.draw.circle(surface, color, (x, y), 20, 2)
    # Líneas
    pygame.draw.line(surface, color, (x - 25, y), (x - 10, y), 2)
    pygame.draw.line(surface, color, (x + 10, y), (x + 25, y), 2)
    pygame.draw.line(surface, color, (x, y - 25), (x, y - 10), 2)
    pygame.draw.line(surface, color, (x, y + 10), (x, y + 25), 2)

def draw_text_centered(text, font, color, y_offset=0):
    t = font.render(text, True, color)
    rect = t.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    screen.blit(t, rect)

def draw_hud():
    # Barra superior semitransparente
    s = pygame.Surface((WIDTH, 50))
    s.set_alpha(128)
    s.fill((0,0,0))
    screen.blit(s, (0,0))
    
    # Score
    score_surf = ui_font.render(f"PUNTOS: {score}", True, YELLOW)
    screen.blit(score_surf, (20, 15))
    
    # Barra de vida
    pygame.draw.rect(screen, (50, 0, 0), (WIDTH - 220, 15, 200, 20)) # Fondo
    hp_pct = max(0, player_health) / 400.0 # Asumimos 400 como base visual max (ajustable)
    pygame.draw.rect(screen, NEON_RED, (WIDTH - 220, 15, 200 * hp_pct, 20))
    hp_text = ui_font.render(f"HP: {player_health}", True, WHITE)
    screen.blit(hp_text, (WIDTH - 220 + 70, 15))
    
    # Disparos
    ammo_color = NEON_BLUE if shots_remaining > 5 else NEON_RED
    ammo_text = ui_font.render(f"BALAS: {shots_remaining}", True, ammo_color)
    screen.blit(ammo_text, (WIDTH // 2 - 40, 15))
    
    # Combo
    if combo_count > 1:
        combo_text = ui_font.render(f"COMBO x{combo_count}!", True, NEON_GREEN)
        screen.blit(combo_text, (WIDTH // 2 - 50, 55))

def draw_exit_button():
    btn_rect = pygame.Rect(10, HEIGHT - 40, 100, 30)
    mouse_pos = pygame.mouse.get_pos()
    color = (255, 50, 50) if btn_rect.collidepoint(mouse_pos) else (200, 200, 200)
    
    pygame.draw.rect(screen, color, btn_rect, border_radius=5)
    pygame.draw.rect(screen, WHITE, btn_rect, 2, border_radius=5)
    
    txt = ui_font.render("ABORTAR", True, (0,0,0))
    screen.blit(txt, (20, HEIGHT - 35))
    return btn_rect

# --- LÓGICA DE JUEGO ---

def initialize_stats(level, num_enemies, difficulty):
    global player_health, shots_remaining, combo_count, max_consecutive_combo
    
    combo_count = 0
    max_consecutive_combo = 0
    

    
    # Munición calculada
    base_ammo = num_enemies + (2 if level == 3 else 0) # Tiros extra para el jefe
    if difficulty == "Fácil":
        shots_remaining = 999
    elif difficulty == "Normal":
        shots_remaining = int(base_ammo * 2)
    else: # Difícil
        shots_remaining = base_ammo * 2 # Margen de error muy bajo


    # Base de vida + bonificación por nivel
    player_health = 100 + (shots_remaining * 20) 
def run_level(level):
    global current_state, score, player_health, shots_remaining, combo_count
    global max_consecutive_combo
    
    score = 0
    
    # Grupos de Sprites
    aliens = pygame.sprite.Group()
    toxics = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    floating_texts = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    
    # Inicializar estrellas
    stars = [Star() for _ in range(50)]
    
    boss = None
    level_targets = 5 + (level * 2)
    
    # Spawner inicial
    for _ in range(level_targets):
        a = Alien(level)
        aliens.add(a)
        all_sprites.add(a)
        
    if level >= 2:
        num_toxics = 3 + level
        for _ in range(num_toxics):
            t = ToxicAlien()
            toxics.add(t)
            all_sprites.add(t)

    # Calcular munición necesaria
    enemies_to_kill = level_targets + (1 if True else 0) # +1 por boss potencial
    initialize_stats(level, enemies_to_kill, current_difficulty)
    
    running = True
    boss_spawned = False
    game_result = None # 'won', 'lost', 'exit'
    
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        
        # --- EVENTOS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Click izquierdo
                    # Check Salida
                    exit_btn = draw_exit_button()
                    if exit_btn.collidepoint(mouse_pos):
                        game_result = 'exit'
                        running = False
                        break
                    
                    if shots_remaining > 0:
                        if current_difficulty != "Fácil":
                            shots_remaining -= 1
                        
                        hit_something = False
                        
                        # 1. Check Aliens Normales
                        clicked_sprites = [s for s in aliens if s.rect.collidepoint(mouse_pos)]
                        for alien in clicked_sprites:
                            # FX: Explosión
                            for _ in range(10):
                                particles.add(Particle(alien.rect.centerx, alien.rect.centery, alien.color))
                            
                            # Logica
                            alien.kill()
                            hit_points = 100 + (combo_count * 20)
                            score += hit_points
                            
                            # Texto flotante
                            txt = FloatingText(f"+{hit_points}", mouse_pos[0], mouse_pos[1], YELLOW)
                            floating_texts.add(txt)
                            
                            hit_something = True
                        
                        # 2. Check Boss
                        if boss and boss.rect.collidepoint(mouse_pos):
                            boss.health -= 1
                            hit_something = True
                            # FX impacto
                            for _ in range(5):
                                particles.add(Particle(mouse_pos[0], mouse_pos[1], WHITE))
                                
                            if boss.health <= 0:
                                # Gran explosión jefe
                                for _ in range(50):
                                    particles.add(Particle(boss.rect.centerx, boss.rect.centery, NEON_BLUE))
                                boss.kill()
                                score += 500
                                levels_completed[level] = True
                                game_result = 'won' # Victoria instantánea al matar jefe
                                running = False
                        
                        # 3. Check Toxicos (Game Over)
                        clicked_toxics = [s for s in toxics if s.rect.collidepoint(mouse_pos)]
                        for t in clicked_toxics:
                            player_health = 0 # Muerte instantánea por tóxico
                            game_result = 'lost'
                            running = False
                        
                        # --- GESTION DE COMBOS ---
                        if hit_something:
                            combo_count += 1
                            if combo_count > max_consecutive_combo:
                                max_consecutive_combo = combo_count
                            
                            # Bonus cada 3 hits
                            if combo_count % 3 == 0:
                                bonus_ammo = 2 if current_difficulty == "Difícil" or current_difficulty == "Normal" else 1
                                shots_remaining += bonus_ammo
                                floating_texts.add(FloatingText(f"AMMO +{bonus_ammo}", mouse_pos[0], mouse_pos[1]-20, NEON_GREEN))
                        else:
                            # Fallo
                            combo_count = 0
                            if current_difficulty == "Difícil":
                                player_health -= 20
                                floating_texts.add(FloatingText("-20 HP", mouse_pos[0], mouse_pos[1], NEON_RED))
        
        # --- UPDATE ---
        # Spawn Boss si no quedan aliens
        if not boss_spawned and len(aliens) == 0:
            boss = Mothership(level)
            boss_spawned = True
            floating_texts.add(FloatingText("¡ALERTA JEFE!", WIDTH//2, HEIGHT//2, NEON_RED, 2.0))
        
        # Update estrellas
        for s in stars: s.update()
        
        # Update entidades
        if boss: boss.update()
        aliens.update()
        toxics.update()
        particles.update()
        floating_texts.update()
        
        # Check condiciones de derrota
        if player_health <= 0:
            game_result = 'lost'; running = False
        if shots_remaining <= 0 and len(aliens) > 0 and current_difficulty != "Fácil":
            game_result = 'lost'; running = False

        # --- DRAW ---
        screen.fill(DARK_SPACE)
        for s in stars: s.draw(screen) # Fondo
        
        aliens.draw(screen)
        toxics.draw(screen)
        if boss: screen.blit(boss.image, boss.rect)
        
        particles.draw(screen)
        floating_texts.draw(screen)
        
        draw_hud()
        draw_exit_button()
        draw_crosshair(screen, mouse_pos, shots_remaining)
        
        pygame.display.flip()

    # --- SALIDA DEL BUCLE ---
    return game_result, {'score': score, 'max_combo': max_consecutive_combo}

# --- PANTALLAS PRINCIPALES ---

def main_loop():
    global current_state, current_difficulty_index, current_difficulty, score
    
    last_stats = {}
    
    running = True
    while running:
        # PANTALLA INICIO
        if current_state == STATE_START:
            screen.fill(DARK_SPACE)
            draw_text_centered("GALACTIC HUNTER", title_font, NEON_BLUE, -50)
            draw_text_centered("Click para iniciar misión", ui_font, WHITE, 50)
            draw_crosshair(screen, pygame.mouse.get_pos(), 99)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    current_state = STATE_MENU
            pygame.display.flip()

        # PANTALLA MENU
        elif current_state == STATE_MENU:
            screen.fill(DARK_SPACE)
            draw_text_centered("SELECTOR DE MISION", title_font, WHITE, -200)
            
            mx, my = pygame.mouse.get_pos()
            
            # Botones de nivel
            for i in range(1, 4):
                btn_color = NEON_GREEN if levels_completed[i] else WHITE
                rect = pygame.Rect(WIDTH//2 - 100, 150 + (i * 70), 200, 50)
                color = NEON_BLUE if rect.collidepoint((mx,my)) else (50, 50, 100)
                
                pygame.draw.rect(screen, color, rect, border_radius=10)
                pygame.draw.rect(screen, btn_color, rect, 2, border_radius=10)
                
                text_surf = ui_font.render(f"NIVEL {i}", True, WHITE)
                screen.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
                
            # Botón Dificultad
            diff_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT - 100, 300, 50)
            d_color = (100, 50, 50) if diff_rect.collidepoint((mx,my)) else (50, 50, 50)
            pygame.draw.rect(screen, d_color, diff_rect, border_radius=10)
            draw_text_centered(f"Dificultad: < {current_difficulty} >", ui_font, YELLOW, 200)

            draw_crosshair(screen, (mx, my), 99)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Click Niveles
                    for i in range(1, 4):
                        rect = pygame.Rect(WIDTH//2 - 100, 150 + (i * 70), 200, 50)
                        if rect.collidepoint((mx, my)):
                            result, stats = run_level(i)
                            last_stats = stats
                            last_stats['difficulty'] = current_difficulty
                            
                            if result == 'won': current_state = STATE_LEVEL_WON
                            elif result == 'lost': current_state = STATE_GAME_OVER
                            elif result == 'exit': current_state = STATE_MENU
                    
                    # Click Dificultad
                    if diff_rect.collidepoint((mx, my)):
                        current_difficulty_index = (current_difficulty_index + 1) % len(DIFFICULTY_MODES)
                        current_difficulty = DIFFICULTY_MODES[current_difficulty_index]

            pygame.display.flip()

        # PANTALLA VICTORIA
        elif current_state == STATE_LEVEL_WON:
            screen.fill((0, 50, 0))
            draw_text_centered("¡MISIÓN CUMPLIDA!", title_font, NEON_GREEN, -150)
            draw_text_centered(f"Puntuación: {last_stats.get('score',0)}", ui_font, WHITE, -50)
            draw_text_centered(f"Mejor Racha: {last_stats.get('max_combo',0)}", ui_font, YELLOW, 50)
            draw_text_centered("Click para volver a la base", ui_font, (200, 200, 200), 150)
            draw_crosshair(screen, pygame.mouse.get_pos(), 99)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN: current_state = STATE_MENU
            pygame.display.flip()

        # PANTALLA GAME OVER
        elif current_state == STATE_GAME_OVER:
            screen.fill((50, 0, 0))
            draw_text_centered("SEÑAL PERDIDA", title_font, NEON_RED, -100)
            draw_text_centered(f"Puntuación Final: {score}", ui_font, WHITE, 0)
            draw_text_centered(f"Max combos: {max_consecutive_combo}", ui_font, WHITE, 0)
            draw_text_centered("Click para reintentar", ui_font, (200, 200, 200), 100)
            draw_crosshair(screen, pygame.mouse.get_pos(), 0)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN: current_state = STATE_MENU
            pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main_loop()