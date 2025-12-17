import pygame
import sys
import random

WIDTH, HEIGHT = 800, 600
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Click & Shoot")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 32)

# Estados del juego
STATE_START = "start"
STATE_MENU = "menu"
STATE_LEVEL = "level"
STATE_GAME_OVER = "game_over"
STATE_LEVEL_WON = "level_won"  # << CAMBIO CLAVE >>: Nuevo estado para Victoria

current_state = STATE_START
current_level = 1
max_levels = 3
levels_completed = {1: False, 2: False, 3: False}

# Variables de Juego Globales
score = 0
SCORE_VALUE = 100

DIFFICULTY_MODES = ["Fácil", "Normal", "Difícil"]
current_difficulty_index = 1
current_difficulty = DIFFICULTY_MODES[current_difficulty_index]

player_health = 0
shots_remaining = 0

# << CAMBIO CLAVE >>: Variables de Combo
combo_count = 0  # Número de aciertos seguidos
total_combos = 0  # Total de combos 3x conseguidos en el nivel
max_consecutive_combo = 0  # Máximo combo consecutivo alcanzado


# Clases del juego (Target, BadTarget, Boss - se mantienen igual)
class Target(pygame.sprite.Sprite):
    def __init__(self, level=1):
        super().__init__()
        self.size = 40
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.size)
        self.rect.y = random.randint(0, HEIGHT - self.size)
        self.level = level
        self.speed = 2 + level

        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.choice([-1, 1]) * self.speed

        self.movement_type = level if level < 3 else 2

    def update(self):
        # ... (Movimiento y rebote) ...
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.dx *= -1
            if self.rect.left < 0: self.rect.left = 0
            if self.rect.right > WIDTH: self.rect.right = WIDTH
        if self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.dy *= -1
            if self.rect.top < 0: self.rect.top = 0
            if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT

        if self.movement_type == 2:
            if random.random() < 0.05:
                self.dx = random.choice([-1, 1]) * self.speed
                self.dy = random.choice([-1, 1]) * self.speed


class BadTarget(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 40
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.size)
        self.rect.y = random.randint(0, HEIGHT - self.size)
        self.speed = 3

        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.choice([-1, 1]) * self.speed

    def update(self):
        # ... (Movimiento lineal y rebote) ...
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.dx *= -1
            if self.rect.left < 0: self.rect.left = 0
            if self.rect.right > WIDTH: self.rect.right = WIDTH
        if self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.dy *= -1
            if self.rect.top < 0: self.rect.top = 0
            if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT


class Boss(Target):
    def __init__(self, level=1):
        super().__init__(level)
        self.size = 60
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((0, 0, 255))
        self.rect = self.image.get_rect(center=self.rect.center)
        self.speed = 6 + level

        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.choice([-1, 1]) * self.speed


# Funciones de Dibujo

def draw_text(text, size, color, x, y):
    f = pygame.font.SysFont(None, size)
    t = f.render(text, True, color)
    rect = t.get_rect(center=(x, y))
    screen.blit(t, rect)


def draw_score(score):
    score_text = small_font.render(f"Puntuación: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))


def draw_stats(health, shots):
    # Dibuja Vida (arriba a la derecha)
    health_text = small_font.render(f"Vida: {health}", True, (255, 255, 255))
    health_rect = health_text.get_rect(topright=(WIDTH - 10, 10))
    screen.blit(health_text, health_rect)

    # Dibuja Disparos restantes (debajo de la vida)
    shots_text = small_font.render(f"Disparos: {shots}", True, (255, 255, 255))
    shots_rect = shots_text.get_rect(topright=(WIDTH - 10, 40))
    screen.blit(shots_text, shots_rect)


# << CAMBIO CLAVE >>: Dibuja el botón de Salida
def draw_exit_button():
    # Botón en la esquina inferior izquierda
    btn_text = small_font.render("EXIT", True, (0, 0, 0))
    btn_rect = pygame.Rect(10, HEIGHT - 40, 80, 30)

    # Dibujar el rectángulo del botón
    pygame.draw.rect(screen, (200, 200, 200), btn_rect)

    # Centrar texto en el botón
    text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, text_rect)

    return btn_rect  # Devolver el rectángulo para detección de click


def start_screen():
    screen.fill((0, 0, 0))
    draw_text("CLICK & SHOOT", 72, (255, 255, 255), WIDTH // 2, HEIGHT // 2 - 50)
    draw_text("Haz click para comenzar", 36, (200, 200, 200), WIDTH // 2, HEIGHT // 2 + 20)


def menu_screen():
    global current_difficulty_index, current_difficulty

    screen.fill((30, 30, 30))
    draw_text("SELECCIONA NIVEL", 60, (255, 255, 255), WIDTH // 2, 80)

    # Dibujar niveles
    for i in range(1, max_levels + 1):
        color = (255, 255, 255)  # << CAMBIO CLAVE >>: Ya no se usan los tics, ni el color verde
        text = f"Nivel {i}"
        draw_text(text, 40, color, WIDTH // 2, 180 + (i * 80))

    # Dibujar desplegable de dificultad
    diff_text = f"Dificultad: < {current_difficulty} >"
    draw_text(diff_text, 40, (255, 100, 100), WIDTH // 2, HEIGHT - 80)

    diff_area_x = WIDTH // 2
    diff_area_y = HEIGHT - 80

    return diff_area_x, diff_area_y


# << CAMBIO CLAVE >>: Nueva pantalla de Victoria
def level_won_screen(final_score, combos, max_combo, difficulty):
    screen.fill((0, 80, 0))  # Fondo verde de victoria
    draw_text("¡NIVEL COMPLETADO!", 72, (255, 255, 255), WIDTH // 2, 100)

    draw_text(f"Puntuación Total: {final_score}", 48, (255, 255, 0), WIDTH // 2, 250)
    draw_text(f"Dificultad: {difficulty}", 40, (255, 255, 255), WIDTH // 2, 320)
    draw_text(f"Combos (3x) Realizados: {combos}", 40, (200, 200, 255), WIDTH // 2, 380)
    draw_text(f"Racha de Combo Máxima: {max_combo}", 40, (200, 200, 255), WIDTH // 2, 430)

    draw_text("Click para volver al menú", 36, (200, 200, 200), WIDTH // 2, HEIGHT - 80)


def game_over_screen():
    screen.fill((100, 0, 0))
    draw_text("GAME OVER", 72, (255, 255, 255), WIDTH // 2, HEIGHT // 2 - 50)
    draw_text(f"Puntuación Final: {score}", 48, (255, 255, 255), WIDTH // 2, HEIGHT // 2)
    draw_text("Click para volver al menú", 36, (200, 200, 200), WIDTH // 2, HEIGHT // 2 + 70)


# Funciones de Gestión

def initialize_stats(level, num_enemies, difficulty):
    global player_health, shots_remaining, combo_count, total_combos, max_consecutive_combo

    # Resetear contadores de la partida
    combo_count = 0
    total_combos = 0
    max_consecutive_combo = 0

    # 1. Vida: 100 puntos base por nivel
    player_health = 100 + (level * 100)

    # 2. Disparos
    if difficulty == "Fácil" or difficulty == "Normal":
        shots_remaining = num_enemies
    elif difficulty == "Difícil":
        shots_remaining = num_enemies * 2


def apply_penalty(hit):
    global player_health, shots_remaining, current_difficulty, combo_count, total_combos, max_consecutive_combo

    if current_difficulty == "Fácil":
        # Sin penalización y sin disparos limitados
        return

    # Reducir el disparo si no es modo Fácil
    shots_remaining -= 1

    if hit:
        # El jugador acierta
        combo_count += 1

        # Actualizar el máximo combo consecutivo
        if combo_count > max_consecutive_combo:
            max_consecutive_combo = combo_count

        # << CAMBIO CLAVE >>: Recompensa por Combo 3x en modo Difícil
        if current_difficulty == "Difícil" and combo_count >= 3:
            player_health += 40
            shots_remaining += 2
            total_combos += 1
            combo_count = 0  # Resetear el contador de combo después de la recompensa

    else:
        # El jugador falla

        # Resetear el contador de combo si falla
        combo_count = 0

        # Reducir vida solo en modo Difícil por disparo fallado
        if current_difficulty == "Difícil":
            player_health -= 20
            if player_health < 0:
                player_health = 0


def run_level(level):
    global current_state, levels_completed, score, player_health, shots_remaining, current_difficulty
    global total_combos, max_consecutive_combo  # Para que se actualicen las estadísticas

    # << CAMBIO CLAVE >>: La puntuación se resetea al empezar CUALQUIER nivel
    score = 0

    target_group = pygame.sprite.Group()
    bad_target_group = pygame.sprite.Group()
    boss = None

    level_targets = 5 + (level * 3)
    num_enemies_total = level_targets

    for _ in range(level_targets):
        target_group.add(Target(level=level))

    if level == 3:
        num_bad_targets = level_targets // 2
        for _ in range(num_bad_targets):
            bad_target_group.add(BadTarget())
        num_enemies_total += num_bad_targets

    initialize_stats(level, num_enemies_total, current_difficulty)

    running = True
    boss_spawned = False
    game_lost = False
    exit_to_menu = False  # << CAMBIO CLAVE >>: Nueva bandera para salir

    while running:
        # Comprobar si el jugador ha ganado/perdido por stats
        if player_health <= 0 or (shots_remaining <= 0 and current_difficulty != "Fácil" and len(target_group) > 0):
            game_lost = True
            running = False

        # Lógica de aparición del Jefe
        if not boss_spawned and len(target_group) == 0 and len(bad_target_group) == 0:
            boss = Boss(level)
            boss_spawned = True

        if not boss_spawned and len(target_group) == 0 and len(bad_target_group) > 0:
            boss = Boss(level)
            boss_spawned = True

        # Bucle de Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                # Comprobar click en botón EXIT
                exit_button_rect = draw_exit_button()
                if exit_button_rect.collidepoint(pos):
                    exit_to_menu = True
                    running = False
                    break  # Salir del bucle for para ir al while exit

                # Procesar disparo solo si hay munición (o es fácil)
                if shots_remaining > 0 or current_difficulty == "Fácil":
                    hit = False

                    # Intentar eliminar objetivos ROJOS (acierto)
                    for t in target_group:
                        if t.rect.collidepoint(pos):
                            t.kill()
                            score += SCORE_VALUE
                            hit = True

                    # Comprobar objetivos VERDES (causa Game Over)
                    for bt in bad_target_group:
                        if bt.rect.collidepoint(pos):
                            game_lost = True
                            running = False
                            hit = True

                    # Intentar eliminar al Jefe (acierto)
                    if boss and boss.rect.collidepoint(pos):
                        boss.kill()
                        levels_completed[level] = True
                        running = False
                        hit = True

                    # Aplicar penalización/recompensa
                    apply_penalty(hit)

        # Dibujo
        screen.fill((10, 10, 10))
        target_group.update()
        target_group.draw(screen)
        bad_target_group.update()
        bad_target_group.draw(screen)

        if boss:
            boss.update()
            screen.blit(boss.image, boss.rect)

        draw_score(score)
        draw_stats(player_health, shots_remaining)
        draw_exit_button()  # Dibuja el botón de salida

        pygame.display.flip()
        clock.tick(FPS)

    # Transición de estado después de salir del bucle
    if exit_to_menu:
        current_state = STATE_MENU
    elif game_lost:
        current_state = STATE_GAME_OVER
    else:
        current_state = STATE_LEVEL_WON  # << CAMBIO CLAVE >>: Va a la pantalla de victoria


# Loop principal del juego
running = True
# Variables para almacenar los datos al ganar, para mostrarlos en la pantalla de victoria
win_stats = {}

while running:
    if current_state == STATE_START:
        start_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                current_state = STATE_MENU
        pygame.display.flip()

    elif current_state == STATE_MENU:
        diff_area_x, diff_area_y = menu_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                # Comprobar clicks en los niveles (acceso libre)
                for i in range(1, max_levels + 1):
                    ty = 180 + (i * 80)
                    if abs(my - ty) < 40:
                        current_level = i
                        current_state = STATE_LEVEL
                        run_level(i)

                        # Al volver de run_level, guardar las estadísticas si se ganó
                        if current_state == STATE_LEVEL_WON:
                            win_stats = {
                                'score': score,
                                'combos': total_combos,
                                'max_combo': max_consecutive_combo,
                                'difficulty': current_difficulty
                            }
                            # Y pasar a la pantalla de victoria
                            continue

                # Comprobar clicks en el desplegable de dificultad
                if abs(my - diff_area_y) < 20 and abs(mx - diff_area_x) < 75:
                    current_difficulty_index = (current_difficulty_index + 1) % len(DIFFICULTY_MODES)
                    current_difficulty = DIFFICULTY_MODES[current_difficulty_index]

        pygame.display.flip()

    elif current_state == STATE_LEVEL_WON:  # << CAMBIO CLAVE >>: Nuevo estado de victoria
        level_won_screen(win_stats['score'], win_stats['combos'], win_stats['max_combo'], win_stats['difficulty'])
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                current_state = STATE_MENU  # Volver al menú
        pygame.display.flip()

    elif current_state == STATE_GAME_OVER:
        game_over_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                current_state = STATE_MENU
        pygame.display.flip()

pygame.quit()