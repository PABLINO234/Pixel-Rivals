import math
import random
import sys
import pygame

# PIXEL RIVALS 2.2 - Arcade local para dos jugadores
# P1: WASD | P2: Flechas | ENTER: jugar | ESC: pausa | R: reiniciar

pygame.init()
pygame.display.set_caption("PIXEL RIVALS 2.3")

WIDTH, HEIGHT = 960, 640
FPS = 60
ROUND_SECONDS = 60
PICKUP_LIMIT = 10

windowed_size = (WIDTH, HEIGHT)
fullscreen = False
window = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
screen = pygame.Surface((WIDTH, HEIGHT))
clock = pygame.time.Clock()

FONT = pygame.font.Font(None, 30)
SMALL = pygame.font.Font(None, 22)
MEDIUM = pygame.font.Font(None, 42)
BIG = pygame.font.Font(None, 70)
TITLE = pygame.font.Font(None, 100)

BG = (6, 9, 23)
GRID = (15, 28, 49)
WHITE = (238, 247, 255)
CYAN = (35, 225, 255)
PINK = (255, 55, 185)
YELLOW = (255, 218, 75)
PURPLE = (183, 105, 255)
GREEN = (90, 255, 160)
ORANGE = (255, 145, 65)
BLUE = (85, 145, 255)

ARENA = pygame.Rect(34, 112, WIDTH - 68, HEIGHT - 148)
OBSTACLES = []
MAP_NAMES = ["CRUZ", "ISLAS", "CARRILES", "FORTALEZA", "LABERINTO"]

def generate_map():
    """Devuelve un diseño aleatorio con zonas libres para jugadores y portales."""
    cx, cy = ARENA.centerx, ARENA.centery
    left, right = ARENA.left, ARENA.right
    top, bottom = ARENA.top, ARENA.bottom
    layouts = [
        [pygame.Rect(cx - 105, cy - 11, 210, 22),
         pygame.Rect(cx - 11, top + 105, 22, 105),
         pygame.Rect(cx - 11, cy + 70, 22, 105)],
        [pygame.Rect(left + 235, top + 95, 22, 115),
         pygame.Rect(left + 235, bottom - 210, 22, 115),
         pygame.Rect(right - 257, top + 95, 22, 115),
         pygame.Rect(right - 257, bottom - 210, 22, 115),
         pygame.Rect(cx - 65, cy - 11, 130, 22)],
        [pygame.Rect(cx - 150, top + 115, 180, 22),
         pygame.Rect(cx - 30, bottom - 137, 180, 22),
         pygame.Rect(left + 330, cy - 55, 22, 110),
         pygame.Rect(right - 352, cy - 55, 22, 110)],
        [pygame.Rect(cx - 95, cy - 95, 190, 18),
         pygame.Rect(cx - 95, cy + 77, 190, 18),
         pygame.Rect(cx - 95, cy - 77, 18, 70),
         pygame.Rect(cx + 77, cy - 77, 18, 70)],
        [pygame.Rect(left + 270, top + 100, 150, 20),
         pygame.Rect(right - 420, bottom - 120, 150, 20),
         pygame.Rect(left + 270, bottom - 120, 20, 90),
         pygame.Rect(right - 290, top + 30, 20, 90),
         pygame.Rect(cx - 11, cy - 45, 22, 90)],
    ]
    index = random.randrange(len(layouts))
    return layouts[index], MAP_NAMES[index]

MAP_NAME = "CRUZ"


def text(surface, value, font, color, center):
    image = font.render(str(value), True, color)
    surface.blit(image, image.get_rect(center=center))

def draw_glow(surface, color, center, radius, strength=70):
    glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    c = (radius * 2, radius * 2)
    pygame.draw.circle(glow, (*color, strength // 3), c, radius * 2)
    pygame.draw.circle(glow, (*color, strength), c, radius)
    surface.blit(glow, (center[0] - radius * 2, center[1] - radius * 2))

def circle_rect_collision(x, y, radius, rect):
    closest_x = max(rect.left, min(x, rect.right))
    closest_y = max(rect.top, min(y, rect.bottom))
    return (x - closest_x) ** 2 + (y - closest_y) ** 2 < radius ** 2

def random_position():
    for _ in range(300):
        x = random.randint(ARENA.left + 30, ARENA.right - 30)
        y = random.randint(ARENA.top + 30, ARENA.bottom - 30)
        if not any(circle_rect_collision(x, y, 16, wall.inflate(20, 20)) for wall in OBSTACLES):
            return x, y
    return ARENA.center

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        angle = random.random() * math.tau
        speed = random.uniform(45, 190)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(.25, .55)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 4)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        if self.life > 0:
            radius = max(1, int(self.size * self.life / self.max_life))
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius)

class Player:
    def __init__(self, x, y, color, keys, name):
        self.x, self.y = float(x), float(y)
        self.color = color
        self.keys = keys
        self.name = name
        self.radius = 13
        self.score = 0
        self.base_speed = 245
        self.boost_until = 0
        self.magnet_until = 0
        self.multiplier_until = 0
        self.shield_until = 0
        self.streak = 0
        self.last_pickup = -99
        self.combo_until = 0
        self.dash_until = 0
        self.dash_cooldown_until = 0
        self.facing = (1, 0) if name == "JUGADOR 1" else (-1, 0)
        self.slow_until = 0
        self.hit_cooldown_until = 0
        self.frozen_until = 0
        self.portal_cooldown_until = 0

    def update(self, dt, pressed, now):
        dx = int(pressed[self.keys[1]]) - int(pressed[self.keys[0]])
        dy = int(pressed[self.keys[3]]) - int(pressed[self.keys[2]])
        length = math.hypot(dx, dy)
        if length:
            dx, dy = dx / length, dy / length
            self.facing = (dx, dy)

        speed = self.base_speed * (1.5 if now < self.boost_until else 1)
        if now < self.slow_until:
            speed *= 0.65
        if now < self.frozen_until:
            dx, dy = 0, 0
        if now < self.dash_until:
            speed *= 3.2
        self.move(dx * speed * dt, dy * speed * dt)

    def dash(self, now):
        if now >= self.dash_cooldown_until:
            self.dash_until = now + 0.18
            self.dash_cooldown_until = now + 4.0
            return True
        return False

    def move(self, dx, dy):
        # Separar ejes evita quedar trabado al rozar una pared.
        self.x += dx
        self.x = max(ARENA.left + self.radius, min(ARENA.right - self.radius, self.x))
        if any(circle_rect_collision(self.x, self.y, self.radius, wall) for wall in OBSTACLES):
            self.x -= dx

        self.y += dy
        self.y = max(ARENA.top + self.radius, min(ARENA.bottom - self.radius, self.y))
        if any(circle_rect_collision(self.x, self.y, self.radius, wall) for wall in OBSTACLES):
            self.y -= dy

    def draw(self, surface, now):
        pos = (int(self.x), int(self.y))
        draw_glow(surface, self.color, pos, 22, 75)
        if now < self.shield_until:
            pygame.draw.circle(surface, BLUE, pos, self.radius + 8, 2)
        pygame.draw.circle(surface, self.color, pos, self.radius)
        pygame.draw.circle(surface, WHITE, pos, self.radius, 2)
        pygame.draw.circle(surface, BG, pos, 4)
        if now < self.boost_until:
            pygame.draw.circle(surface, GREEN, pos, self.radius + 4, 1)

    def combo_multiplier(self, now):
        return 2 if now < self.combo_until else 1

class Pickup:
    VALUES = {"coin": 10, "gem": 25, "star": 50,
              "boost": 0, "magnet": 0, "x2": 0, "shield": 0, "freeze": 0}
    COLORS = {"coin": YELLOW, "gem": PURPLE, "star": WHITE,
              "boost": GREEN, "magnet": ORANGE, "x2": CYAN, "shield": BLUE, "freeze": PINK}

    def __init__(self):
        self.kind = random.choices(
            ["coin", "gem", "star", "boost", "magnet", "x2", "shield", "freeze"],
            [45, 22, 7, 8, 5, 4, 4, 5]
        )[0]
        self.x, self.y = random_position()
        self.phase = random.random() * math.tau
        self.radius = 9 if self.kind == "coin" else 11

    def draw(self, surface, elapsed):
        pulse = math.sin(elapsed * 5 + self.phase) * 2
        r = max(5, int(self.radius + pulse))
        pos = (int(self.x), int(self.y))
        color = self.COLORS[self.kind]
        draw_glow(surface, color, pos, r + 4, 45)
        pygame.draw.circle(surface, color, pos, r, 2)
        if self.kind == "coin":
            pygame.draw.circle(surface, color, pos, max(3, r // 2))
        elif self.kind == "gem":
            pygame.draw.polygon(surface, color, [(pos[0], pos[1]-r), (pos[0]+r, pos[1]),
                                                  (pos[0], pos[1]+r), (pos[0]-r, pos[1])])
        elif self.kind == "star":
            points = []
            for i in range(10):
                a = -math.pi / 2 + i * math.pi / 5
                rr = r if i % 2 == 0 else r * .45
                points.append((pos[0] + math.cos(a)*rr, pos[1] + math.sin(a)*rr))
            pygame.draw.polygon(surface, color, points)
        else:
            symbol = {"boost": ">", "magnet": "M", "x2": "2", "shield": "S", "freeze": "F"}[self.kind]
            text(surface, symbol, SMALL, color, pos)

class Mine:
    """Mina de energía: resta puntos si el jugador la toca."""
    def __init__(self):
        self.x, self.y = random_position()
        self.phase = random.random() * math.tau
        self.radius = 13
        self.life = 12.0
        self.drift_angle = random.random() * math.tau
        self.drift_speed = random.uniform(12, 24)

    def update(self, dt):
        self.life -= dt
        self.x += math.cos(self.drift_angle + self.life * .5) * self.drift_speed * dt
        self.y += math.sin(self.drift_angle + self.life * .5) * self.drift_speed * dt
        self.x = max(ARENA.left + 20, min(ARENA.right - 20, self.x))
        self.y = max(ARENA.top + 20, min(ARENA.bottom - 20, self.y))

    def draw(self, surface, elapsed):
        pulse = math.sin(elapsed * 7 + self.phase) * 3
        r = int(self.radius + pulse)
        pos = (int(self.x), int(self.y))
        draw_glow(surface, ORANGE, pos, r + 5, 65)
        pygame.draw.circle(surface, (255, 65, 75), pos, r, 3)
        pygame.draw.line(surface, WHITE, (pos[0]-6, pos[1]-6), (pos[0]+6, pos[1]+6), 2)
        pygame.draw.line(surface, WHITE, (pos[0]-6, pos[1]+6), (pos[0]+6, pos[1]-6), 2)


def new_pickup():
    return Pickup()

def reset_game():
    global OBSTACLES, PORTALS, MAP_NAME
    OBSTACLES, MAP_NAME = generate_map()
    PORTALS = [
        (ARENA.left + 72, ARENA.top + 70),
        (ARENA.right - 72, ARENA.bottom - 70),
    ]
    p1 = Player(ARENA.left + 75, ARENA.centery, CYAN,
                (pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s), "JUGADOR 1")
    p2 = Player(ARENA.right - 75, ARENA.centery, PINK,
                (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN), "JUGADOR 2")
    return p1, p2, [new_pickup() for _ in range(8)], ROUND_SECONDS, "countdown", 0, 3.0, [], [], 5.0


def draw_portals(surface, elapsed):
    for i, (x, y) in enumerate(PORTALS):
        pulse = math.sin(elapsed * 5 + i) * 3
        radius = int(18 + pulse)
        color = CYAN if i == 0 else PURPLE
        draw_glow(surface, color, (x, y), radius + 5, 55)
        pygame.draw.circle(surface, color, (x, y), radius, 3)
        pygame.draw.circle(surface, WHITE, (x, y), max(5, radius - 7), 1)

def update_portals(player, now):
    if now < player.portal_cooldown_until:
        return
    for index, (x, y) in enumerate(PORTALS):
        if math.hypot(player.x - x, player.y - y) < player.radius + 17:
            destination = PORTALS[1 - index]
            player.x, player.y = destination[0], destination[1]
            player.portal_cooldown_until = now + 3.0
            break

def draw_background(surface, elapsed):
    surface.fill(BG)
    offset = int((elapsed * 12) % 32)
    for x in range(-32 + offset, WIDTH, 32):
        pygame.draw.line(surface, GRID, (x, 0), (x, HEIGHT), 1)
    for y in range(-32 + offset, HEIGHT, 32):
        pygame.draw.line(surface, GRID, (0, y), (WIDTH, y), 1)
    pygame.draw.rect(surface, (20, 95, 120), ARENA, 2, border_radius=9)
    pygame.draw.rect(surface, (20, 42, 68), ARENA.inflate(-8, -8), 1, border_radius=7)
    for wall in OBSTACLES:
        pygame.draw.rect(surface, (24, 42, 68), wall, border_radius=5)
        pygame.draw.rect(surface, (60, 135, 165), wall, 2, border_radius=5)
        pygame.draw.line(surface, (40, 95, 125), wall.topleft, wall.bottomright, 1)

def draw_hud(surface, p1, p2, seconds, now):
    pygame.draw.rect(surface, (10, 16, 35), (0, 0, WIDTH, 96))
    pygame.draw.line(surface, (30, 75, 100), (0, 95), (WIDTH, 95), 2)
    text(surface, f"P1  {p1.score}", FONT, CYAN, (125, 34))
    text(surface, f"COMBO x{p1.combo_multiplier(now)}", SMALL, CYAN, (125, 67))
    text(surface, "PIXEL RIVALS", FONT, WHITE, (WIDTH // 2, 25))
    text(surface, f"{max(0, math.ceil(seconds)):02d}", BIG, YELLOW, (WIDTH // 2, 66))
    text(surface, f"P2  {p2.score}", FONT, PINK, (WIDTH - 125, 34))
    text(surface, f"COMBO x{p2.combo_multiplier(now)}", SMALL, PINK, (WIDTH - 125, 67))

def apply_pickup(player, item, now, particles, golden_rush=False, opponent=None):
    color = Pickup.COLORS[item.kind]
    for _ in range(12):
        particles.append(Particle(item.x, item.y, color))

    if item.kind == "boost":
        player.boost_until = now + 5
    elif item.kind == "magnet":
        player.magnet_until = now + 6
    elif item.kind == "x2":
        player.multiplier_until = now + 7
    elif item.kind == "shield":
        player.shield_until = now + 7
    elif item.kind == "freeze":
        if opponent is not None:
            opponent.frozen_until = now + 1.8
    else:
        combo_active = now - player.last_pickup <= 2.5
        if combo_active:
            player.streak += 1
        else:
            player.streak = 1
        player.last_pickup = now
        multiplier = 2 if combo_active else 1
        player.combo_until = now + 2.5
        if now < player.multiplier_until:
            multiplier *= 2
        if golden_rush:
            multiplier *= 2
        player.score += item.VALUES[item.kind] * multiplier
        if player.streak >= 3:
            player.score += 5 * multiplier

def draw_status(surface, player, now, x, color):
    active = []
    if now < player.boost_until: active.append("VELOCIDAD")
    if now < player.magnet_until: active.append("IMAN")
    if now < player.multiplier_until: active.append("PUNTOS x2")
    if now < player.shield_until: active.append("ESCUDO")
    if now < player.slow_until: active.append("LENTO")
    if now < player.frozen_until: active.append("CONGELADO")
    if now < player.dash_cooldown_until:
        active.append(f"DASH {player.dash_cooldown_until - now:.1f}s")
    else:
        active.append("DASH LISTO")
    if active:
        text(surface, " | ".join(active), SMALL, color, (x, HEIGHT - 15))

def main():
    p1, p2, pickups, time_left, state, elapsed, countdown, particles, mines, mine_timer = reset_game()
    running = True
    golden_rush = False
    final_rush = False

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.04)
        now = pygame.time.get_ticks() / 1000.0
        elapsed += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                windowed_size = (max(640, event.w), max(480, event.h))
                window = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    if fullscreen:
                        fullscreen = False
                        window = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                    else:
                        windowed_size = window.get_size()
                        fullscreen = True
                        info = pygame.display.Info()
                        window = pygame.display.set_mode(
                            (info.current_w, info.current_h), pygame.FULLSCREEN
                        )
                elif event.key == pygame.K_ESCAPE:
                    if state in ("playing", "countdown"):
                        state = "paused"
                    elif state == "paused":
                        state = "playing"
                    elif state in ("menu", "finished"):
                        running = False
                elif event.key == pygame.K_RETURN and state in ("menu", "finished"):
                    p1, p2, pickups, time_left, state, elapsed, countdown, particles, mines, mine_timer = reset_game()
                elif event.key == pygame.K_SPACE and state == "paused":
                    state = "playing"
                elif event.key == pygame.K_f and state == "playing":
                    p1.dash(now)
                elif event.key == pygame.K_RCTRL and state == "playing":
                    p2.dash(now)
                elif event.key == pygame.K_r and state in ("playing", "paused", "countdown"):
                    p1, p2, pickups, time_left, state, elapsed, countdown, particles, mines, mine_timer = reset_game()

        pressed = pygame.key.get_pressed()
        draw_background(screen, elapsed)

        if state == "menu":
            text(screen, "PIXEL", TITLE, CYAN, (WIDTH//2, 190))
            text(screen, "RIVALS", TITLE, PINK, (WIDTH//2, 275))
            text(screen, "DOS JUGADORES  /  UNA ARENA", FONT, WHITE, (WIDTH//2, 350))
            text(screen, "COLECCIONA, USA PORTALES Y SABOTEA A TU RIVAL", SMALL, (170, 195, 215), (WIDTH//2, 395))
            text(screen, "P1: WASD", FONT, CYAN, (WIDTH//2 - 120, 455))
            text(screen, "P2: FLECHAS", FONT, PINK, (WIDTH//2 + 120, 455))
            text(screen, "ENTER PARA JUGAR", MEDIUM, YELLOW, (WIDTH//2, 530))
            text(screen, "60 SEGUNDOS | DASH: F / CTRL DER. | F11: PANTALLA COMPLETA", SMALL, (150, 170, 195), (WIDTH//2, 570))

        elif state in ("countdown", "playing", "paused"):
            if state == "countdown":
                countdown -= dt
                if countdown <= 0:
                    state = "playing"
            elif state == "playing":
                p1.update(dt, pressed, now)
                p2.update(dt, pressed, now)
                time_left -= dt
                mine_timer -= dt

                # Cada cierto tiempo aparece una mina nueva; desaparece sola.
                if mine_timer <= 0 and len(mines) < 4:
                    mines.append(Mine())
                    mine_timer = 7.0
                elif mine_timer <= 0:
                    mine_timer = 3.0

                for mine in mines[:]:
                    mine.update(dt)
                    if mine.life <= 0:
                        mines.remove(mine)

                # Eventos temporales: sobrecarga cada 20 s y x2 en los últimos 10 s.
                match_elapsed = ROUND_SECONDS - time_left
                golden_rush = (int(match_elapsed // 20) % 2 == 1 and match_elapsed % 20 < 5)
                final_rush = time_left <= 10

                # El iman atrae objetos cercanos, sin alterar el control del jugador.
                for player in (p1, p2):
                    update_portals(player, now)
                    if now < player.magnet_until:
                        for item in pickups:
                            vx, vy = player.x - item.x, player.y - item.y
                            distance = math.hypot(vx, vy)
                            if 25 < distance < 115:
                                item.x += vx / distance * 95 * dt
                                item.y += vy / distance * 95 * dt

                for player in (p1, p2):
                    for item in pickups[:]:
                        if math.hypot(player.x-item.x, player.y-item.y) < player.radius + item.radius + 4:
                            apply_pickup(player, item, now, particles, golden_rush or final_rush, p2 if player is p1 else p1)
                            pickups.remove(item)
                            break

                # Las minas penalizan una sola vez por contacto. El escudo las bloquea.
                for player in (p1, p2):
                    for mine in mines[:]:
                        if math.hypot(player.x - mine.x, player.y - mine.y) < player.radius + mine.radius:
                            if now >= player.hit_cooldown_until:
                                if now < player.shield_until:
                                    player.shield_until = 0
                                    color = BLUE
                                else:
                                    player.score = max(0, player.score - 15)
                                    player.slow_until = now + 1.2
                                    color = ORANGE
                                player.hit_cooldown_until = now + 1.0
                                for _ in range(18):
                                    particles.append(Particle(mine.x, mine.y, color))
                                mines.remove(mine)
                                break

                while len(pickups) < PICKUP_LIMIT:
                    pickups.append(new_pickup())

                if time_left <= 0:
                    time_left = 0
                    state = "finished"

            draw_hud(screen, p1, p2, time_left, now)
            draw_portals(screen, elapsed)
            for item in pickups:
                item.draw(screen, elapsed)
            for mine in mines:
                mine.draw(screen, elapsed)
            if state == "playing" and golden_rush:
                text(screen, "SOBRECARGA DORADA: PUNTOS x2", SMALL, YELLOW, (WIDTH//2, 112))
            elif state == "playing" and final_rush:
                text(screen, "RECTA FINAL: TODOS LOS PUNTOS x2", SMALL, YELLOW, (WIDTH//2, 112))
            for particle in particles[:]:
                particle.update(dt)
                particle.draw(screen)
                if particle.life <= 0:
                    particles.remove(particle)
            p1.draw(screen, now)
            p2.draw(screen, now)
            draw_status(screen, p1, now, 160, CYAN)
            draw_status(screen, p2, now, WIDTH - 160, PINK)

            if state == "countdown":
                number = max(1, math.ceil(countdown))
                text(screen, str(number), TITLE, YELLOW, (WIDTH//2, HEIGHT//2))
            elif state == "paused":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                text(screen, "PAUSA", TITLE, WHITE, (WIDTH//2, HEIGHT//2 - 25))
                text(screen, "ESPACIO PARA CONTINUAR  |  R PARA REINICIAR", SMALL, WHITE, (WIDTH//2, HEIGHT//2 + 40))
            else:
                text(screen, "DASH: F / CTRL DER. | PORTALES: TELETRANSPORTE | ESC: PAUSA | R: RESET", SMALL, (150, 170, 195), (WIDTH//2, HEIGHT - 15))

        elif state == "finished":
            draw_hud(screen, p1, p2, 0, now)
            if p1.score > p2.score:
                winner, color = "GANA JUGADOR 1", CYAN
            elif p2.score > p1.score:
                winner, color = "GANA JUGADOR 2", PINK
            else:
                winner, color = "EMPATE", YELLOW
            text(screen, "FIN DE PARTIDA", FONT, WHITE, (WIDTH//2, 190))
            text(screen, winner, BIG, color, (WIDTH//2, 280))
            text(screen, f"{p1.score}  -  {p2.score}", TITLE, WHITE, (WIDTH//2, 370))
            text(screen, "ENTER: NUEVA PARTIDA", MEDIUM, YELLOW, (WIDTH//2, 470))
            text(screen, "ESC: SALIR", SMALL, (160, 180, 205), (WIDTH//2, 515))

        window.fill((0, 0, 0))
        ww, wh = window.get_size()
        scale = min(ww / WIDTH, wh / HEIGHT)
        scaled_size = (max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale)))
        frame = pygame.transform.scale(screen, scaled_size)
        window.blit(frame, ((ww - scaled_size[0]) // 2, (wh - scaled_size[1]) // 2))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
