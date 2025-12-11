import math
import random
import pygame

from config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, FPS, WHITE
from core import Tank, Bullet
from ai_helpers import init_bot_ai, update_bot_ai
from walls import set_walls_visible
from walls import set_walls_collision
from walls import respawn_walls_avoiding_player

class Boss(Tank):
    """A circular boss with 4 guns placed evenly around the rim."""
    def __init__(self, x, y, player):
        super().__init__(x, y, (200, 50, 50), False)
        # visual radius (pixels)
        self.size = 60
        self.radius = self.size

        # scale health from player
        player_max_hp = getattr(player, "max_health", getattr(player, "health", 100))
        self.max_health = int(player_max_hp * 10)
        self.health = self.max_health

        # mirror player's offensive stats for testing/consistency
        self.base_damage = getattr(player, "base_damage", getattr(player, "damage", 10))
        self.bullet_speed = getattr(player, "base_bullet_speed", getattr(player, "bullet_speed", 7))
        # match player's fire rate (shots per second)
        self.fire_rate = max(0.01, getattr(player, "fire_rate", 1.0))
        # move at half speed of normal bots
        self.speed = getattr(player, "speed", 1.6) * 0.5

        # movement / AI / cooldowns
        self.fire_cooldown = 0
        self.special_active = False
        self.special_duration = 5 * FPS
        self.special_cooldown = 20 * FPS
        self._special_timer = random.randint(FPS, self.special_cooldown)

        # guns around rim
        # use 4 guns evenly spaced
        self.gun_count = 4
        self.gun_angles = [i * (2 * math.pi / self.gun_count) for i in range(self.gun_count)]

    def draw(self, win, cam_x, cam_y, alpha=255):
        """Draw boss with optional alpha (0..255)."""
        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)
        if alpha >= 255:
            pygame.draw.circle(win, self.color, (screen_x, screen_y), self.size)
            bar_w = self.size * 2
            pygame.draw.rect(win, (40, 40, 40), (screen_x - self.size, screen_y - self.size - 14, bar_w, 10))
            hp_ratio = max(0.0, self.health / float(max(1, self.max_health)))
            pygame.draw.rect(win, (50, 220, 50), (screen_x - self.size, screen_y - self.size - 14, int(bar_w * hp_ratio), 10))
            for ang in self.gun_angles:
                gx = int(screen_x + math.cos(ang) * (self.size + 6))
                gy = int(screen_y + math.sin(ang) * (self.size + 6))
                pygame.draw.circle(win, (220, 200, 30), (gx, gy), 6)
        else:
            sz = int(self.size * 2 + 24)
            surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
            cx = sz // 2
            cy = sz // 2
            col = (*self.color, alpha)
            pygame.draw.circle(surf, col, (cx, cy), self.size)
            bar_w = self.size * 2
            bg_col = (40, 40, 40, alpha)
            hp_col = (50, 220, 50, alpha)
            pygame.draw.rect(surf, bg_col, (cx - self.size, cy - self.size - 14, bar_w, 10))
            hp_ratio = max(0.0, self.health / float(max(1, self.max_health)))
            pygame.draw.rect(surf, hp_col, (cx - self.size, cy - self.size - 14, int(bar_w * hp_ratio), 10))
            for ang in self.gun_angles:
                gx = int(cx + math.cos(ang) * (self.size + 6))
                gy = int(cy + math.sin(ang) * (self.size + 6))
                pygame.draw.circle(surf, (220, 200, 30, alpha), (gx, gy), 6)
            win.blit(surf, (screen_x - cx, screen_y - cy))

    def move_towards(self, target_x, target_y):
        """Fallback orbit-like movement if AI fails."""
        ang = math.atan2(target_y - self.y, target_x - self.x)
        desired_x = target_x + math.cos(ang + math.pi/2) * 220
        desired_y = target_y + math.sin(ang + math.pi/2) * 220
        dx = desired_x - self.x
        dy = desired_y - self.y
        dist = math.hypot(dx, dy) + 1e-6
        speed = getattr(self, "speed", 1.6)
        self.x += (dx / dist) * speed
        self.y += (dy / dist) * speed
        # clamp inside world
        self.x = max(self.size, min(WORLD_WIDTH - self.size, self.x))
        self.y = max(self.size, min(WORLD_HEIGHT - self.size, self.y))

    def corner_positions(self):
        return [(self.x + math.cos(ang) * (self.size + 6), self.y + math.sin(ang) * (self.size + 6)) for ang in self.gun_angles]


class BossManager:
    """Controls unlock UI, spawning, running, and cleanup of the boss fight."""
    def __init__(self, player, bullets, bots, walls=None):
        self.player = player
        self.bullets = bullets  # main bullets list
        self.bots = bots
        self.walls = walls
        # boss is locked until enough kills
        self.unlocked = False
        self.active = False
        self.boss = None
        self.boss_bullets = []
        self.unlock_kills = 10
        # UI rect (unused for text UI)
        self.btn_w, self.btn_h = 140, 36
        self.btn_rect = pygame.Rect(WIDTH - self.btn_w - 10, 10, self.btn_w, self.btn_h)
        if not hasattr(self.player, "bot_kills"):
            self.player.bot_kills = 0
        self.fade_in = False
        self.fade_timer = 0
        self.boss_alpha = 255

    def check_unlock(self, kills):
        if not self.unlocked and kills >= self.unlock_kills:
            self.unlocked = True

    def handle_event(self, event):
        # keep mouse click support (button rect not used if text UI is used)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.unlocked and not self.active:
                mx, my = event.pos
                if self.btn_rect.collidepoint(mx, my):
                    self.start_boss()

    def start_boss(self):
        # remove regular bots (clears the shared bots list so game.py sees it emptied)
        try:
            self.bots.clear()
        except Exception:
            self.bots = []
        # keep only player bullets
        try:
            self.bullets[:] = [b for b in self.bullets if getattr(b, "owner", None) == "player"]
        except Exception:
            self.bullets = []
        # hide walls during boss fight
        try:
            set_walls_visible(False)
        except Exception:
            pass
        # disable wall collision during boss fight
        try:
            set_walls_collision(False)
        except Exception:
            pass
        # heal player and spawn boss
        self.player.health = getattr(self.player, "max_health", getattr(self.player, "health", 100))
        bx, by = WORLD_WIDTH // 2, WORLD_HEIGHT // 2
        self.boss = Boss(bx, by, self.player)
        # init AI so boss obeys walls and moves like bots
        try:
            init_bot_ai(self.boss)
        except Exception:
            pass
        # ensure boss position is clamped
        self.boss.x = max(self.boss.size, min(WORLD_WIDTH - self.boss.size, self.boss.x))
        self.boss.y = max(self.boss.size, min(WORLD_HEIGHT - self.boss.size, self.boss.y))
        # start fade-in and active state
        self.active = True
        self.fade_in = True
        self.fade_timer = int(3 * FPS)
        self.boss_alpha = 0
        self.boss_bullets.clear()

    def _boss_fire(self):
        if not self.boss:
            return
        # do not fire while fading in
        if getattr(self, "fade_in", False):
            return
        # determine bullet radius to match regular bullets (use player's mount profile if available)
        try:
            bullet_radius = getattr(self.player.gun_mounts[0].profile, "radius", 4)
        except Exception:
            bullet_radius = 4
        for cx, cy in self.boss.corner_positions():
            ang = math.atan2(self.player.y - cy, self.player.x - cx)
            speed = getattr(self.boss, "bullet_speed", 6)
            dmg = getattr(self.boss, "base_damage", 20)
            # try to match Bullet signature used in game.py; if signature differs fall back
            try:
                color = (255, 200, 50)
                b = Bullet(cx, cy, ang, speed, dmg, bullet_radius, color, "boss", None)
            except TypeError:
                # fallback simple object
                class _B:
                    def __init__(self, x, y, ang, sp, dmg):
                        self.x = x; self.y = y; self.angle = ang; self.speed = sp; self.damage = dmg; self.owner = "boss"; self.radius = bullet_radius
                    def move(self): self.x += math.cos(self.angle) * self.speed; self.y += math.sin(self.angle) * self.speed
                    def draw(self, win, cam_x, cam_y): pygame.draw.circle(win, (255,200,50), (int(self.x-cam_x), int(self.y-cam_y)), self.radius)
                b = _B(cx, cy, ang, speed, dmg)
            self.boss_bullets.append(b)

    def _update_boss_bullets(self, win, cam_x, cam_y):
        for b in self.boss_bullets[:]:
            try:
                b.move()
            except Exception:
                pass
            try:
                b.draw(win, cam_x, cam_y)
            except Exception:
                try:
                    pygame.draw.circle(win, (255,200,50), (int(b.x - cam_x), int(b.y - cam_y)), getattr(b, "radius", 4))
                except Exception:
                    pass
            try:
                if math.hypot(b.x - self.player.x, b.y - self.player.y) < getattr(self.player, "radius", 20):
                    self.player.health -= getattr(b, "damage", getattr(b, "dmg", 5))
                    try:
                        self.boss_bullets.remove(b)
                    except ValueError:
                        pass
            except Exception:
                pass
            if getattr(b, "x", 0) < -100 or getattr(b, "x", 0) > WORLD_WIDTH + 100 or getattr(b, "y", 0) < -100 or getattr(b, "y", 0) > WORLD_HEIGHT + 100:
                try:
                    self.boss_bullets.remove(b)
                except ValueError:
                    pass

    def update(self, win, cam_x, cam_y, font):
        # If boss not active don't run fight logic here
        if not self.active:
            return

        # fade-in handling
        if getattr(self, "fade_in", False):
            self.fade_timer -= 1
            total = int(3 * FPS)
            remaining = max(0, self.fade_timer)
            alpha = int(((total - remaining) / total) * 255)
            self.boss_alpha = max(0, min(255, alpha))
            try:
                self.boss.draw(win, cam_x, cam_y, alpha=self.boss_alpha)
            except Exception:
                pass
            if self.fade_timer <= 0:
                self.fade_in = False
                self.boss_alpha = 255
            return

        # Movement: prefer using bot AI so boss obeys walls and spacing
        try:
            try:
                _ = update_bot_ai(self.boss, self.bots, self.player, walls=self.walls)
            except TypeError:
                _ = update_bot_ai(self.boss, self.bots, self.player)
        except Exception:
            try:
                self.boss.move_towards(self.player.x, self.player.y)
            except Exception:
                pass

        # clamp boss inside world bounds as extra safety
        self.boss.x = max(self.boss.size, min(WORLD_WIDTH - self.boss.size, self.boss.x))
        self.boss.y = max(self.boss.size, min(WORLD_HEIGHT - self.boss.size, self.boss.y))

        # special handling (unchanged)
        if getattr(self.boss, "_special_timer", 0) <= 0:
            self.boss.special_active = True
            self.boss._special_left = getattr(self.boss, "special_duration", 5 * FPS)
            self.boss._special_timer = getattr(self.boss, "special_cooldown", 20 * FPS)
        else:
            self.boss._special_timer -= 1

        if getattr(self.boss, "special_active", False):
            if getattr(self.boss, "_special_left", 0) > 0:
                self.boss._special_left -= 1
                current_fire_rate = getattr(self.boss, "fire_rate", 1.0) * 3.0
            else:
                self.boss.special_active = False
                current_fire_rate = getattr(self.boss, "fire_rate", 1.0)
        else:
            current_fire_rate = getattr(self.boss, "fire_rate", 1.0)

        frames_per_shot = max(1, int(FPS / max(0.0001, current_fire_rate)))
        if getattr(self.boss, "fire_cooldown", 0) <= 0:
            self._boss_fire()
            self.boss.fire_cooldown = frames_per_shot
        else:
            self.boss.fire_cooldown -= 1

        # render boss and its bullets
        try:
            self.boss.draw(win, cam_x, cam_y)
        except Exception:
            pass
        self._update_boss_bullets(win, cam_x, cam_y)

        # player bullets hitting boss
        for b in list(self.bullets):
            try:
                if getattr(b, "owner", None) == "player":
                    dist = math.hypot(getattr(b, "x", 0) - self.boss.x, getattr(b, "y", 0) - self.boss.y)
                    if dist < (self.boss.size * 1.4):
                        self.boss.health -= getattr(b, "damage", getattr(b, "dmg", 5))
                        try:
                            self.bullets.remove(b)
                        except ValueError:
                            pass
                        if self.boss.health <= 0:
                            self.end_boss_fight()
                            return
            except Exception:
                continue

    def end_boss_fight(self):
        try:
            self.player.exp += 50
        except Exception:
            pass
        self.boss_bullets.clear()
        self.active = False
        self.boss = None
        # restore walls after boss is defeated
        try:
            set_walls_visible(True)
        except Exception:
            pass
        # re-enable wall collision after boss fight
        try:
            set_walls_collision(True)
        except Exception:
            pass
        # respawn walls, avoiding player position
        try:
            if self.walls is not None and self.player is not None:
                respawn_walls_avoiding_player(self.walls, self.player)
        except Exception:
            pass
        # unlocked remains True for replay

