import pygame
import math
import random
import sys

# Initialize Pygame
pygame.init()

# Screen and world settings
WIDTH, HEIGHT = 800, 600
WORLD_WIDTH, WORLD_HEIGHT = 1600, 1200
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tank Battle")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BG_COLOR = (30, 30, 30)

# Game constants
FPS = 60
BOT_SPAWN_RATE = 50
UPGRADE_COST = 5

# Bullet class
class Bullet:
    def __init__(self, x, y, angle, speed, damage, owner):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.owner = owner
        self.radius = 4

    def move(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def draw(self, win, cam_x, cam_y):
        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)
        pygame.draw.circle(win, RED if self.owner == "player" else GREEN, (screen_x, screen_y), self.radius)

# Tank class
class Tank:
    def __init__(self, x, y, color, is_player=False):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 20
        self.health = 100
        self.speed = 3
        self.bullet_speed = 7
        self.damage = 10
        self.is_player = is_player
        self.exp = 0
        self.cooldown = 0
        self.regen_rate = 0.05  # health per frame
        self.max_health = 100


    def move(self, keys):
        if keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_s]: self.y += self.speed
        if keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_d]: self.x += self.speed
        self.x = max(0, min(WORLD_WIDTH, self.x))
        self.y = max(0, min(WORLD_HEIGHT, self.y))

    def shoot(self, target_x, target_y):
        angle = math.atan2(target_y - self.y, target_x - self.x)
        return Bullet(self.x, self.y, angle, self.bullet_speed, self.damage, "player" if self.is_player else "bot")

    def draw(self, win, cam_x, cam_y):
        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)
        pygame.draw.circle(win, self.color, (screen_x, screen_y), self.radius)
        pygame.draw.rect(win, RED, (screen_x - 20, screen_y - 30, 40, 5))
        pygame.draw.rect(win, GREEN, (screen_x - 20, screen_y - 30, 40 * (self.health / 100), 5))

    def regenerate(self):
        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.regen_rate)
# Reset game function
def reset_game():
    return Tank(WORLD_WIDTH//2, WORLD_HEIGHT//2, WHITE, True), [], [], 0, False

# Main game function
def main():
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    player, bullets, bots, frame_count, game_over = reset_game()

    while True:
        clock.tick(FPS)
        WIN.fill(BG_COLOR)
        keys = pygame.key.get_pressed()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        cam_x = player.x - WIDTH // 2
        cam_y = player.y - HEIGHT // 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                player, bullets, bots, frame_count, game_over = reset_game()
            if not game_over:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    bullets.append(player.shoot(mouse_x + cam_x, mouse_y + cam_y))
                if event.type == pygame.KEYDOWN and player.exp >= UPGRADE_COST:
                    if event.key == pygame.K_1:
                        player.speed += 0.5
                        player.exp -= UPGRADE_COST
                    elif event.key == pygame.K_2:
                        player.bullet_speed += 1
                        player.exp -= UPGRADE_COST
                    elif event.key == pygame.K_3:
                        player.damage += 2
                        player.exp -= UPGRADE_COST
                    elif event.key == pygame.K_4:
                        player.health = min(100, player.health + 20)
                        player.exp -= UPGRADE_COST

        if not game_over:
            player.move(keys)
            player.draw(WIN, cam_x, cam_y)
            player.regenerate()


            frame_count += 1
            if frame_count % BOT_SPAWN_RATE == 0:
                bots.append(Tank(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT), GREEN))

            for bot in bots[:]:
                bot.draw(WIN, cam_x, cam_y)
                if bot.cooldown == 0:
                    bullets.append(bot.shoot(player.x, player.y))
                    bot.cooldown = 120
                else:
                    bot.cooldown -= 1

            for bullet in bullets[:]:
                bullet.move()
                bullet.draw(WIN, cam_x, cam_y)
                if bullet.owner == "player":
                    for bot in bots[:]:
                        if math.hypot(bullet.x - bot.x, bullet.y - bot.y) < bot.radius:
                            bot.health -= bullet.damage
                            bullets.remove(bullet)
                            if bot.health <= 0:
                                bots.remove(bot)
                                player.exp += 5
                            break
                else:
                    if math.hypot(bullet.x - player.x, bullet.y - player.y) < player.radius:
                        player.health -= bullet.damage
                        bullets.remove(bullet)

            if player.health <= 0:
                game_over = True

            # HUD
            hud = font.render(f"EXP: {player.exp} | 1-Speed 2-Bullet 3-Damage 4-Health (Cost: {UPGRADE_COST})", True, WHITE)
            WIN.blit(hud, (10, 10))
        else:
            over_text = font.render("GAME OVER - Press R to Restart", True, RED)
            WIN.blit(over_text, (WIDTH//2 - 100, HEIGHT//2))

        pygame.display.update()

if __name__ == "__main__":
    main()

