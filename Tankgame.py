import pygame
import math
import random

# Initialize
pygame.init()
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tank Battle")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Game settings
FPS = 60
PLAYER_SPEED = 3
BULLET_SPEED = 7
BOT_SPAWN_RATE = 100  # frames
UPGRADE_COST = 5

# Classes
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

    def draw(self, win):
        pygame.draw.circle(win, RED if self.owner == "player" else GREEN, (int(self.x), int(self.y)), self.radius)

class Tank:
    def __init__(self, x, y, color, is_player=False):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 20
        self.health = 100
        self.speed = PLAYER_SPEED
        self.bullet_speed = BULLET_SPEED
        self.damage = 10
        self.is_player = is_player
        self.exp = 0
        self.upgrades = {"speed": 0, "bullet_speed": 0, "health": 0, "damage": 0}
        self.cooldown = 0

    def move(self, keys):
        if keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_s]: self.y += self.speed
        if keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_d]: self.x += self.speed

    def shoot(self, target_x, target_y):
        angle = math.atan2(target_y - self.y, target_x - self.x)
        return Bullet(self.x, self.y, angle, self.bullet_speed, self.damage, "player" if self.is_player else "bot")

    def draw(self, win):
        pygame.draw.circle(win, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.rect(win, RED, (self.x - 20, self.y - 30, 40, 5))
        pygame.draw.rect(win, GREEN, (self.x - 20, self.y - 30, 40 * (self.health / 100), 5))

# Game loop
def main():
    clock = pygame.time.Clock()
    run = True
    player = Tank(WIDTH//2, HEIGHT//2, WHITE, True)
    bullets = []
    bots = []
    frame_count = 0

    while run:
        clock.tick(FPS)
        WIN.fill((30, 30, 30))
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                bullets.append(player.shoot(*pygame.mouse.get_pos()))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u and player.exp >= UPGRADE_COST:
                    player.exp -= UPGRADE_COST
                    player.speed += 0.5
                    player.bullet_speed += 1
                    player.damage += 2
                    player.health = min(100, player.health + 20)

        player.move(keys)
        player.draw(WIN)

        # Spawn bots
        frame_count += 1
        if frame_count % BOT_SPAWN_RATE == 0:
            bots.append(Tank(random.randint(0, WIDTH), random.randint(0, HEIGHT), GREEN))

        # Bots logic
        for bot in bots[:]:
            bot.draw(WIN)
            if bot.cooldown == 0:
                bullets.append(bot.shoot(player.x, player.y))
                bot.cooldown = 60
            else:
                bot.cooldown -= 1

        # Bullets logic
        for bullet in bullets[:]:
            bullet.move()
            bullet.draw(WIN)
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

        # Display EXP
        font = pygame.font.SysFont(None, 24)
        exp_text = font.render(f"EXP: {player.exp} | Press 'U' to upgrade", True, WHITE)
        WIN.blit(exp_text, (10, 10))

        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()