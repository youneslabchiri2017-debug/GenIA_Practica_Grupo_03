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

current_state = STATE_START
current_level = 1
max_levels = 3
levels_completed = {1: False, 2: False, 3: False}

# >>> NUEVO <<<
# Variables globales de puntuación
score = 0
combo = 0
best_combo = 0

# Clases del juego
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

    def update(self):
        mx, my = pygame.mouse.get_pos()

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

        if self.level == 2:
            if random.random() < 0.05:
                self.dx = random.choice([-1, 1]) * self.speed
                self.dy = random.choice([-1, 1]) * self.speed

        elif self.level == 3:
            if random.random() < 0.5:
                if mx < self.rect.centerx and self.dx < 0: self.dx *= -1
                elif mx > self.rect.centerx and self.dx > 0: self.dx *= -1
                if my < self.rect.centery and self.dy < 0: self.dy *= -1
                elif my > self.rect.centery and self.dy > 0: self.dy *= -1


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


def draw_text(text, size, color, x, y):
    f = pygame.font.SysFont(None, size)
    t = f.render(text, True, color)
    rect = t.get_rect(center=(x, y))
    screen.blit(t, rect)


def start_screen():
    screen.fill((0, 0, 0))
    draw_text("CLICK & SHOOT", 72, (255, 255, 255), WIDTH//2, HEIGHT//2 - 50)
    draw_text("Haz click para comenzar", 36, (200, 200, 200), WIDTH//2, HEIGHT//2 + 20)


def menu_screen():
    screen.fill((30, 30, 30))
    draw_text("SELECCIONA NIVEL", 60, (255, 255, 255), WIDTH//2, 80)

    for i in range(1, max_levels + 1):
        color = (0, 255, 0) if levels_completed[i] else (255, 255, 255)
        text = f"Nivel {i}" + (" ✓" if levels_completed[i] else "")
        draw_text(text, 40, color, WIDTH//2, 180 + (i * 80))


def run_level(level):
    global current_state, levels_completed, score, combo, best_combo

    # Reiniciar puntuación por nivel
    score = 0
    combo = 0
    best_combo = 0

    target_group = pygame.sprite.Group()
    boss = None
    level_targets = 5 + (level * 3)

    for _ in range(level_targets):
        target_group.add(Target(level=level))

    running = True
    boss_spawned = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Detectar click
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                hit = False

                # Enemigos normales
                for t in target_group:
                    if t.rect.collidepoint(pos):
                        t.kill()
                        hit = True
                        score += 100 + (combo * 10)   # >>> NUEVO <<<
                        combo += 1                    # >>> NUEVO <<<
                        best_combo = max(best_combo, combo)
                        break

                # Jefe
                if boss and boss.rect.collidepoint(pos):
                    boss.kill()
                    score += 500 + (combo * 20)      # >>> NUEVO <<<
                    combo += 1
                    best_combo = max(best_combo, combo)
                    levels_completed[level] = True
                    running = False
                    hit = True

                if not hit:
                    combo = 0  # Falla rompe combo

        if not boss_spawned and len(target_group) == 0:
            boss = Boss(level)
            boss_spawned = True

        screen.fill((10, 10, 10))
        target_group.update()
        target_group.draw(screen)

        if boss:
            boss.update()
            screen.blit(boss.image, boss.rect)

        # >>> NUEVO <<<
        # Mostrar puntuación
        score_text = small_font.render(f"Puntuación: {score}", True, (255, 255, 255))
        combo_text = small_font.render(f"Combo: {combo}", True, (200, 200, 50))
        screen.blit(score_text, (10, 10))
        screen.blit(combo_text, (10, 40))

        pygame.display.flip()
        clock.tick(FPS)

    current_state = STATE_MENU


# Loop principal
running = True
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
        menu_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i in range(1, max_levels + 1):
                    ty = 180 + (i * 80)
                    if abs(my - ty) < 40:
                        if i == 1 or levels_completed[i-1]:
                            current_level = i
                            run_level(i)
        pygame.display.flip()

pygame.quit()
