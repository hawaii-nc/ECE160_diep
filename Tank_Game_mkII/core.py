import math
import pygame
from dataclasses import dataclass
from config import (
    WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WHITE, RED, GREEN, BLUE, YELLOW, ORANGE, CYAN, MAGENTA, GREY, BG_COLOR,
    FPS, BARREL_LENGTH_SCALE, BARREL_WIDTH_BASE, BARREL_WIDTH_DAMAGE_SCALE, BARREL_WIDTH_RADIUS_SCALE,
    DRONE_SPEED, DRONE_DAMAGE, DRONE_SPAWN_INTERVAL_FRAMES, DRONE_LIFETIME_FRAMES, DRONE_RADIUS
)
from upgrades import BulletProfile, GunMount, DroneSpawnerMount, specialization_tree, shotgun_profiles

@dataclass
class Bullet:
    x: float
    y: float
    angle: float
    speed: float
    damage: float
    radius: float
    color: tuple
    owner: str  # "player" or "bot" or "drone"
    owner_id: int | None = None

    def move(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def draw(self, win, cam_x, cam_y):
        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)
        pygame.draw.circle(win, self.color, (screen_x, screen_y), int(self.radius))

class Drone:
    def __init__(self, x, y, owner_id):
        self.x = x
        self.y = y
        self.owner_id = owner_id
        self.speed = DRONE_SPEED
        self.damage = DRONE_DAMAGE
        self.radius = DRONE_RADIUS
        self.life = DRONE_LIFETIME_FRAMES
        self.color = CYAN

    def target_nearest(self, bots):
        if not bots:
            return None
        nearest = min(bots, key=lambda b: (b.x - self.x)**2 + (b.y - self.y)**2)
        return nearest

    def update(self, bots):
        self.life -= 1
        target = self.target_nearest(bots)
        if target is not None:
            ang = math.atan2(target.y - self.y, target.x - self.x)
            self.x += math.cos(ang) * self.speed
            self.y += math.sin(ang) * self.speed
            # simple collision
            if math.hypot(self.x - target.x, self.y - target.y) < target.radius:
                target.health -= self.damage
                self.life = 0  # self-destruct on hit

    def draw(self, win, cam_x, cam_y):
        pygame.draw.circle(win, self.color, (int(self.x - cam_x), int(self.y - cam_y)), int(self.radius))

class Tank:
    def __init__(self, x, y, color, is_player=False):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 20
        self.max_health = 100
        self.health = self.max_health
        self.speed = 3.0
        self.is_player = is_player

        # Combat stats
        self.base_bullet_speed = 7.0
        self.base_damage = 10.0
        self.base_radius = 4.0

        # Firing control
        self.fire_rate = 4.0  # shots per second; upgradable
        self.fire_cooldown = 0  # frames until next shot

        self.exp = 0
        self.regen_rate = 0.05

        # Progression
        self.level = 1
        self.bot_kills = 0

        # Specialization
        self.spec_key = None              # current branch root
        self.spec_option_index = None     # chosen option index in tree
        self.specialization_count = 0     # for gating additional branch prompts
        self.specialization_complete = False  # true after completing second-stage specialization

        # Mounts and spawners
        self.gun_mounts = [GunMount('aim', 0.0, BulletProfile(self.base_bullet_speed, self.base_damage, self.base_radius, color))]
        self.drone_spawner_mounts = []  # list of DroneSpawnerMount
        self.drone_spawn_timer = 0
        self.drones = []

        self.cooldown = 0   # used by bots for AI firing cadence
        self.id = None

    def move(self, keys):
        if keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_s]: self.y += self.speed
        if keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_d]: self.x += self.speed
        self.x = max(0, min(WORLD_WIDTH, self.x))
        self.y = max(0, min(WORLD_HEIGHT, self.y))

    def regenerate(self):
        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.regen_rate)

    def can_fire(self):
        return self.fire_cooldown <= 0

    def tick_fire_cooldown(self):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def trigger_fire(self):
        # Reset cooldown based on fire_rate
        if self.fire_rate <= 0:
            self.fire_cooldown = FPS  # prevent divide by zero; effectively disable
        else:
            frames_per_shot = max(1, int(FPS / self.fire_rate))
            self.fire_cooldown = frames_per_shot

    def fire(self, aim_angle, owner_label, owner_id, shotgun=False):
        bullets = []
        for mount in self.gun_mounts:
            # Determine emission angle
            if mount.angle_mode == 'aim':
                emit_angle = aim_angle + mount.relative_angle
            else:
                # body mode: absolute around tank body, use tank's orientation as 0
                emit_angle = mount.relative_angle

            # Shotgun mode: produce multiple pellets from this mount if shotgun=True
            if shotgun:
                pellets = shotgun_profiles(self.color)
                for p in pellets:
                    # add some small random spread
                    spread = (math.pi / 24.0) * (0.5 - (pygame.time.get_ticks() % 1000) / 1000.0)
                    bullets.append(Bullet(self.x, self.y, emit_angle + spread, p.speed, p.damage, p.radius, p.color, owner_label, owner_id))
            else:
                prof = mount.profile
                bullets.append(Bullet(self.x, self.y, emit_angle, prof.speed, prof.damage, prof.radius, prof.color, owner_label, owner_id))

        return bullets

    def integrate_specialization(self, root_key, option_index):
        self.spec_key = root_key
        self.spec_option_index = option_index
        tree = specialization_tree(root_key, self.color)
        option = tree['options'][option_index]

        # Reset mounts to match choice
        new_mounts = []
        shotgun_flag = option.get('shotgun', False)
        spawners = []

        for m in option['mounts']:
            if isinstance(m, GunMount):
                new_mounts.append(m)
            elif isinstance(m, DroneSpawnerMount):
                spawners.append(m)

        self.gun_mounts = new_mounts if new_mounts else self.gun_mounts
        self.drone_spawner_mounts = spawners
        # Store shotgun flag internally for firing logic
        self.is_shotgun = shotgun_flag

    def update_drone_spawners(self):
        if not self.drone_spawner_mounts:
            return
        self.drone_spawn_timer -= 1
        if self.drone_spawn_timer <= 0:
            # spawn a drone at tank position (offset along spawner angle)
            for sp in self.drone_spawner_mounts:
                spawn_x = self.x + math.cos(sp.relative_angle) * (self.radius - 2)
                spawn_y = self.y + math.sin(sp.relative_angle) * (self.radius - 2)
                self.drones.append(Drone(spawn_x, spawn_y, self.id))
            self.drone_spawn_timer = DRONE_SPAWN_INTERVAL_FRAMES

    def update_drones(self, bots, win, cam_x, cam_y):
        for d in self.drones[:]:
            d.update(bots)
            d.draw(win, cam_x, cam_y)
            if d.life <= 0:
                self.drones.remove(d)

    def draw(self, win, cam_x, cam_y, aim_angle):
        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)
        pygame.draw.circle(win, self.color, (screen_x, screen_y), self.radius)

        # Health bar
        bar_width = 40
        bar_height = 5
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.radius - 10
        pygame.draw.rect(win, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(win, GREEN, (bar_x, bar_y, int(bar_width * (self.health / self.max_health)), bar_height))

        # Render barrels for each mount (rectangles scaled by bullet stats)
        for mount in self.gun_mounts:
            prof = mount.profile
            width = int(BARREL_WIDTH_BASE + prof.damage * BARREL_WIDTH_DAMAGE_SCALE + prof.radius * BARREL_WIDTH_RADIUS_SCALE)
            length = int(prof.speed * BARREL_LENGTH_SCALE)
            barrel_surface = pygame.Surface((length, width), pygame.SRCALPHA)
            barrel_surface.fill(self.color)

            if mount.angle_mode == 'aim':
                ang = aim_angle + mount.relative_angle
            else:
                ang = mount.relative_angle

            rotated = pygame.transform.rotate(barrel_surface, -math.degrees(ang))
            rect = rotated.get_rect(center=(screen_x + math.cos(ang) * (self.radius - 2),
                                            screen_y + math.sin(ang) * (self.radius - 2)))
            win.blit(rotated, rect)

        # Render drone spawner as trapezoid (rear by default)
        for sp in self.drone_spawner_mounts:
            ang = sp.relative_angle
            # trapezoid points relative to tank center
            base_len = 18
            top_len = 10
            height = 12
            # oriented along ang; small parallel side attached to tank body
            # construct trapezoid in local coords, then rotate and translate
            pts_local = [
                (-top_len/2, 0), (top_len/2, 0), (base_len/2, height), (-base_len/2, height)
            ]
            cos_a, sin_a = math.cos(ang), math.sin(ang)
            pts_world = []
            for px, py in pts_local:
                wx = self.x + cos_a * px - sin_a * py
                wy = self.y + sin_a * px + cos_a * py
                pts_world.append((int(wx - cam_x), int(wy - cam_y)))
            pygame.draw.polygon(win, GREY, pts_world, 0)

def render_bullet(win, bullet, cam_x, cam_y):
    bullet.draw(win, cam_x, cam_y)