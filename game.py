import math
import random
import pygame

# SHADOWS OF NOVA — a playable Python/Pygame mini adventure
# Controls: WASD / arrows = move, SPACE = slash, E = Nova burst, R = restart

pygame.init()
WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SHADOWS OF NOVA")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 20)
SMALL = pygame.font.SysFont("consolas", 15)
BIG = pygame.font.SysFont("consolas", 46, bold=True)

BG = (7, 10, 28)
CYAN = (60, 225, 255)
BLUE = (45, 120, 255)
PURPLE = (180, 70, 255)
PINK = (255, 75, 180)
WHITE = (238, 245, 255)
RED = (255, 75, 90)
GOLD = (255, 210, 70)
GREEN = (80, 255, 170)

# Decorative stars
random.seed(14)
stars = [(random.randrange(WIDTH), random.randrange(HEIGHT), random.choice([1, 1, 2]))
         for _ in range(130)]

def text(msg, x, y, color=WHITE, font=FONT, center=False):
    surf = font.render(msg, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def glow_circle(pos, radius, color):
    x, y = int(pos[0]), int(pos[1])
    for r, alpha in [(radius + 9, 25), (radius + 5, 45)]:
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (r, r), r)
        screen.blit(s, (x-r, y-r))
    pygame.draw.circle(screen, color, (x, y), radius)

def make_enemy(level):
    edge = random.choice(["top", "bottom", "left", "right"])
    if edge == "top": pos = [random.randint(35, WIDTH-35), 70]
    elif edge == "bottom": pos = [random.randint(35, WIDTH-35), HEIGHT-35]
    elif edge == "left": pos = [25, random.randint(100, HEIGHT-35)]
    else: pos = [WIDTH-25, random.randint(100, HEIGHT-35)]
    return {"pos": pos, "hp": 2 + level // 2, "speed": random.uniform(0.7, 1.15) + level*0.08,
            "radius": 14 + min(level, 4), "flash": 0}

def reset():
    return {
        "player": pygame.Vector2(WIDTH/2, HEIGHT/2),
        "hp": 100, "energy": 100, "score": 0, "coins": 0, "level": 1,
        "enemies": [make_enemy(1) for _ in range(4)],
        "slashes": [], "bursts": [], "coin_drops": [],
        "hurt_timer": 0, "slash_cd": 0, "burst_cd": 0,
        "message": "Find the Nova shards. Survive the shadows!",
        "message_timer": 180, "game_over": False, "won": False,
    }

game = reset()
running = True

while running:
    dt = min(clock.tick(60) / 16.6667, 2.0)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r and (game["game_over"] or game["won"]):
                game = reset()
            if not game["game_over"] and not game["won"]:
                if event.key == pygame.K_SPACE and game["slash_cd"] <= 0:
                    game["slash_cd"] = 20
                    p = game["player"]
                    # Slash hits nearby enemies
                    game["slashes"].append({"pos": p.copy(), "life": 12})
                    hit_any = False
                    for enemy in game["enemies"][:]:
                        if p.distance_to(enemy["pos"]) < 90:
                            enemy["hp"] -= 1
                            enemy["flash"] = 7
                            hit_any = True
                            if enemy["hp"] <= 0:
                                game["score"] += 100
                                game["coins"] += 1
                                game["coin_drops"].append({"pos": enemy["pos"].copy(), "life": 500})
                                game["enemies"].remove(enemy)
                    if hit_any:
                        game["message"] = "NOVA SLASH!"
                        game["message_timer"] = 45
                if event.key == pygame.K_e and game["burst_cd"] <= 0 and game["energy"] >= 35:
                    game["energy"] -= 35
                    game["burst_cd"] = 100
                    p = game["player"]
                    game["bursts"].append({"pos": p.copy(), "radius": 15, "life": 22})
                    for enemy in game["enemies"][:]:
                        if p.distance_to(enemy["pos"]) < 190:
                            enemy["hp"] -= 3
                            enemy["flash"] = 10
                            if enemy["hp"] <= 0:
                                game["score"] += 150
                                game["coins"] += 1
                                game["coin_drops"].append({"pos": enemy["pos"].copy(), "life": 500})
                                game["enemies"].remove(enemy)
                    game["message"] = "NOVA BURST!"
                    game["message_timer"] = 55

    if not game["game_over"] and not game["won"]:
        p = game["player"]
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: move.y += 1
        if move.length_squared() > 0:
            move = move.normalize()
            p += move * 4.1 * dt
        p.x = max(22, min(WIDTH-22, p.x))
        p.y = max(85, min(HEIGHT-22, p.y))

        game["energy"] = min(100, game["energy"] + 0.13*dt)
        game["slash_cd"] = max(0, game["slash_cd"] - dt)
        game["burst_cd"] = max(0, game["burst_cd"] - dt)
        game["hurt_timer"] = max(0, game["hurt_timer"] - dt)
        game["message_timer"] = max(0, game["message_timer"] - dt)

        for enemy in game["enemies"]:
            ep = pygame.Vector2(enemy["pos"])
            delta = p - ep
            if delta.length_squared() > 1:
                ep += delta.normalize() * enemy["speed"] * dt
            enemy["pos"] = [ep.x, ep.y]
            enemy["flash"] = max(0, enemy["flash"] - dt)
            if p.distance_to(ep) < 28 and game["hurt_timer"] <= 0:
                game["hp"] -= 8
                game["hurt_timer"] = 28
                if game["hp"] <= 0:
                    game["hp"] = 0
                    game["game_over"] = True

        for drop in game["coin_drops"][:]:
            drop["life"] -= dt
            if p.distance_to(drop["pos"]) < 30:
                game["score"] += 25
                game["coin_drops"].remove(drop)
            elif drop["life"] <= 0:
                game["coin_drops"].remove(drop)

        for slash in game["slashes"][:]:
            slash["life"] -= dt
            if slash["life"] <= 0: game["slashes"].remove(slash)
        for burst in game["bursts"][:]:
            burst["life"] -= dt
            burst["radius"] += 8*dt
            if burst["life"] <= 0: game["bursts"].remove(burst)

        target_count = min(4 + game["level"], 12)
        if len(game["enemies"]) < target_count:
            if random.random() < 0.018 * dt:
                game["enemies"].append(make_enemy(game["level"]))

        # Every 700 points advances the level
        new_level = min(5, 1 + game["score"] // 700)
        if new_level > game["level"]:
            game["level"] = new_level
            game["hp"] = min(100, game["hp"] + 20)
            game["message"] = f"LEVEL {new_level}! The shadows grow stronger."
            game["message_timer"] = 120
        if game["score"] >= 3500:
            game["won"] = True

    # Draw world
    screen.fill(BG)
    for x, y, r in stars:
        twinkle = (pygame.time.get_ticks() // 350 + x + y) % 3
        color = (65 + twinkle*25, 100 + twinkle*20, 180 + twinkle*20)
        pygame.draw.circle(screen, color, (x, y), r)

    # Horizon / glowing grid
    pygame.draw.rect(screen, (9, 16, 42), (0, 70, WIDTH, HEIGHT-70))
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (14, 35, 67), (x, 70), (x, HEIGHT), 1)
    for y in range(100, HEIGHT, 45):
        pygame.draw.line(screen, (14, 35, 67), (0, y), (WIDTH, y), 1)
    pygame.draw.line(screen, CYAN, (0, 70), (WIDTH, 70), 2)

    # HUD
    text("SHADOWS OF NOVA", 22, 18, CYAN, BIG)
    text("PYGAME EDITION", WIDTH-205, 29, PURPLE, SMALL)
    pygame.draw.rect(screen, (30, 38, 63), (22, 82, 220, 18), border_radius=8)
    pygame.draw.rect(screen, RED, (22, 82, int(220*game["hp"]/100), 18), border_radius=8)
    text(f"HP {game['hp']}/100", 27, 82, WHITE, SMALL)
    pygame.draw.rect(screen, (30, 38, 63), (22, 106, 220, 12), border_radius=6)
    pygame.draw.rect(screen, BLUE, (22, 106, int(220*game["energy"]/100), 12), border_radius=6)
    text(f"ENERGY {int(game['energy'])}", 252, 103, CYAN, SMALL)
    text(f"LEVEL {game['level']}", 22, 129, GOLD, SMALL)
    text(f"SCORE {game['score']}", 150, 129, WHITE, SMALL)
    text(f"SHARDS {game['coins']}", 290, 129, GOLD, SMALL)

    # Coin drops
    for drop in game["coin_drops"]:
        glow_circle(drop["pos"], 6, GOLD)
        pygame.draw.circle(screen, WHITE, (int(drop["pos"][0]), int(drop["pos"][1])), 2)

    # Enemies
    for enemy in game["enemies"]:
        color = WHITE if enemy["flash"] > 0 else PURPLE
        glow_circle(enemy["pos"], enemy["radius"], color)
        pygame.draw.circle(screen, (25, 8, 48), (int(enemy["pos"][0]), int(enemy["pos"][1])), max(3, enemy["radius"]-5))
        pygame.draw.circle(screen, PINK, (int(enemy["pos"][0]-4), int(enemy["pos"][1]-2)), 2)
        pygame.draw.circle(screen, PINK, (int(enemy["pos"][0]+4), int(enemy["pos"][1]-2)), 2)
        # tiny health bar
        pygame.draw.rect(screen, (50, 20, 60), (enemy["pos"][0]-16, enemy["pos"][1]-enemy["radius"]-10, 32, 4))
        pygame.draw.rect(screen, RED, (enemy["pos"][0]-16, enemy["pos"][1]-enemy["radius"]-10,
                                      int(32*max(0, enemy["hp"])/(2+game["level"]//2)), 4))

    # Slash and Nova burst effects
    for slash in game["slashes"]:
        pygame.draw.circle(screen, CYAN, (int(slash["pos"].x), int(slash["pos"].y)), 65, 3)
    for burst in game["bursts"]:
        pygame.draw.circle(screen, PURPLE, (int(burst["pos"].x), int(burst["pos"].y)), int(burst["radius"]), 4)
        pygame.draw.circle(screen, CYAN, (int(burst["pos"].x), int(burst["pos"].y)), max(2, int(burst["radius"]*0.65)), 2)

    # Player
    p = game["player"]
    if game["hurt_timer"] <= 0 or int(game["hurt_timer"]) % 4 < 2:
        glow_circle((p.x, p.y), 16, CYAN)
        pygame.draw.circle(screen, (10, 30, 55), (int(p.x), int(p.y)), 10)
        pygame.draw.circle(screen, WHITE, (int(p.x+3), int(p.y-3)), 3)
        # energy sword
        mouse_dir = pygame.Vector2(pygame.mouse.get_pos()) - p
        if mouse_dir.length_squared() > 1:
            mouse_dir = mouse_dir.normalize()
        else:
            mouse_dir = pygame.Vector2(1, -0.2)
        tip = p + mouse_dir*34
        pygame.draw.line(screen, BLUE, (p.x, p.y), (tip.x, tip.y), 7)
        pygame.draw.line(screen, WHITE, (p.x, p.y), (tip.x, tip.y), 2)

    # Help panel
    panel = pygame.Surface((390, 86), pygame.SRCALPHA)
    panel.fill((3, 8, 22, 205))
    screen.blit(panel, (WIDTH-405, HEIGHT-98))
    text("WASD / ARROWS  MOVE", WIDTH-390, HEIGHT-88, WHITE, SMALL)
    text("SPACE  NOVA SLASH  (nearby enemies)", WIDTH-390, HEIGHT-65, CYAN, SMALL)
    text("E  NOVA BURST  (35 energy)", WIDTH-390, HEIGHT-42, PURPLE, SMALL)

    if game["message_timer"] > 0 and not game["game_over"] and not game["won"]:
        text(game["message"], WIDTH//2, 160, GOLD, FONT, center=True)

    if game["game_over"] or game["won"]:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((2, 4, 18, 205))
        screen.blit(overlay, (0, 0))
        title = "NOVA SAVED!" if game["won"] else "THE SHADOWS WON"
        color = CYAN if game["won"] else RED
        text(title, WIDTH//2, HEIGHT//2-60, color, BIG, center=True)
        text(f"FINAL SCORE: {game['score']}   |   SHARDS: {game['coins']}", WIDTH//2, HEIGHT//2, WHITE, FONT, center=True)
        text("Press R to play again  |  ESC to quit", WIDTH//2, HEIGHT//2+45, GOLD, FONT, center=True)

    pygame.display.flip()

pygame.quit()
