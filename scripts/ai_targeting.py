"""
AI Targeting helpers for Tankgame-style bots.

This module provides utilities to:
- select a target for a bot (player prioritized, otherwise nearest enemy)
- predict interception point and aiming angle for leading shots
- simple steering helpers (seek, flee, wander)

How to use in your `Tankgame.py` bot update:

from scripts.ai_targeting import select_target, predict_intercept_angle, should_shoot, seek_vector

# inside bot update loop:
# target = select_target(bot, player, bots)
# if target is not None:
#     aim_angle, time_to_hit = predict_intercept_angle((bot.x, bot.y), bot.bullet_speed, (target.x, target.y), getattr(target, 'vx', 0), getattr(target, 'vy', 0))
#     if should_shoot(bot, target, aim_angle, max_angle_diff=0.3, max_range=800):
#         bullets.append(bot.shoot(target.x, target.y))  # or use aim_angle to fire a led shot

No external dependencies. Contains a simple CLI test when run directly.
"""

import math
import random
from typing import Iterable, Optional, Tuple, Any

Entity = Any  # Expected to have .x and .y attributes; optional .vx and .vy


def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.hypot(dx, dy)


def select_target(bot: Entity, player: Entity, bots: Iterable[Entity], max_range: float = 2000.0) -> Optional[Entity]:
    """
    Select a target for `bot`.

    Priority: player (if in range and alive) else nearest other bot.
    Returns None if no suitable target found.

    Parameters:
    - bot: the bot entity (has x,y)
    - player: the player entity
    - bots: iterable of bot entities (may include `bot` itself)
    - max_range: maximum distance to consider targets
    """
    bot_pos = (bot.x, bot.y)

    # check player first
    if player is not None and getattr(player, 'health', 1) > 0:
        player_pos = (player.x, player.y)
        if distance(bot_pos, player_pos) <= max_range:
            return player

    # find nearest other bot
    nearest = None
    nearest_d = float('inf')
    for other in bots:
        if other is bot:
            continue
        if getattr(other, 'health', 1) <= 0:
            continue
        d = distance(bot_pos, (other.x, other.y))
        if d < nearest_d and d <= max_range:
            nearest = other
            nearest_d = d

    return nearest


def predict_intercept_angle(bot_pos: Tuple[float, float], projectile_speed: float, target_pos: Tuple[float, float],
                            target_vx: float = 0.0, target_vy: float = 0.0) -> Tuple[float, Optional[float]]:
    """
    Compute the aiming angle (radians) from bot_pos to where it should fire to intercept a moving target.

    Returns (angle, time_to_intercept). If no viable intercept (projectile too slow), returns angle pointing to current target_pos and time None.

    Equations based on solving for t in |target_pos + v*t - bot_pos| = projectile_speed * t

    Parameters:
    - bot_pos: (x,y)
    - projectile_speed: scalar > 0
    - target_pos: (x,y)
    - target_vx, target_vy: target velocity components (defaults to 0)
    """
    bx, by = bot_pos
    tx, ty = target_pos
    rx = tx - bx
    ry = ty - by

    rvx = target_vx
    rvy = target_vy

    # solve quadratic: (rvx^2 + rvy^2 - s^2) t^2 + 2 (rx*rvx + ry*rvy) t + (rx^2 + ry^2) = 0
    a = rvx * rvx + rvy * rvy - projectile_speed * projectile_speed
    b = 2 * (rx * rvx + ry * rvy)
    c = rx * rx + ry * ry

    if abs(a) < 1e-6:
        # degenerate -> linear solution
        if abs(b) < 1e-6:
            # target not moving relative or can't solve; aim directly
            angle = math.atan2(ry, rx)
            return angle, None
        t = -c / b
        if t > 0:
            aim_x = tx + rvx * t
            aim_y = ty + rvy * t
            angle = math.atan2(aim_y - by, aim_x - bx)
            return angle, t
        angle = math.atan2(ry, rx)
        return angle, None

    disc = b * b - 4 * a * c
    if disc < 0:
        # no real solution => projectile too slow; aim directly
        angle = math.atan2(ry, rx)
        return angle, None

    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2 * a)
    t2 = (-b + sqrt_disc) / (2 * a)

    t = None
    for candidate in (t1, t2):
        if candidate > 0:
            if t is None or candidate < t:
                t = candidate

    if t is None:
        # no positive intercept time
        angle = math.atan2(ry, rx)
        return angle, None

    aim_x = tx + rvx * t
    aim_y = ty + rvy * t
    angle = math.atan2(aim_y - by, aim_x - bx)
    return angle, t


def angle_diff(a: float, b: float) -> float:
    """Smallest signed difference between two angles."""
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return d


def should_shoot(bot: Entity, target: Entity, aim_angle: float, max_angle_diff: float = 0.35, max_range: float = 1000.0) -> bool:
    """
    Decide whether the bot should shoot at `target` now.

    Criteria (simple):
    - target is alive and within max_range
    - bot's cooldown == 0 (or attribute not present)
    - aim angle is within `max_angle_diff` radians of direct aim

    This is intentionally conservative; tweak thresholds for difficulty.
    """
    if target is None:
        return False
    if getattr(target, 'health', 1) <= 0:
        return False

    bx, by = bot.x, bot.y
    tx, ty = target.x, target.y
    d = distance((bx, by), (tx, ty))
    if d > max_range:
        return False

    # check cooldown if present
    cooldown = getattr(bot, 'cooldown', 0)
    if cooldown and cooldown > 0:
        return False

    # angle to direct aim
    direct_angle = math.atan2(ty - by, tx - bx)
    if abs(angle_diff(aim_angle, direct_angle)) > max_angle_diff:
        return False

    # simple probabilistic hit chance: farther targets are harder
    # This can be used to vary bot accuracy by difficulty
    return True


def seek_vector(bot_pos: Tuple[float, float], target_pos: Tuple[float, float], max_speed: float) -> Tuple[float, float]:
    """
    Return a velocity vector pointing from bot_pos to target_pos with magnitude up to max_speed.
    """
    dx = target_pos[0] - bot_pos[0]
    dy = target_pos[1] - bot_pos[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return 0.0, 0.0
    scale = min(max_speed, dist) / dist
    return dx * scale, dy * scale


def flee_vector(bot_pos: Tuple[float, float], threat_pos: Tuple[float, float], max_speed: float) -> Tuple[float, float]:
    """Return a flee vector moving away from threat_pos."""
    dx = bot_pos[0] - threat_pos[0]
    dy = bot_pos[1] - threat_pos[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        # random jitter
        angle = random.random() * 2 * math.pi
        return math.cos(angle) * max_speed, math.sin(angle) * max_speed
    scale = max_speed / dist
    return dx * scale, dy * scale


def wander_vector(bot_pos: Tuple[float, float], wander_radius: float, max_speed: float) -> Tuple[float, float]:
    """
    Produce a small wandering velocity. Not physically consistent but fine for simple AI.
    """
    angle = random.uniform(0, 2 * math.pi)
    return math.cos(angle) * max_speed * 0.5, math.sin(angle) * max_speed * 0.5


# Simple test harness when run directly
if __name__ == '__main__':
    # Mock entities
    class E:
        def __init__(self, x, y, vx=0, vy=0, health=100):
            self.x = x
            self.y = y
            self.vx = vx
            self.vy = vy
            self.health = health

    bot = E(100, 100)
    player = E(300, 250, vx=1.5, vy=0.5)
    other = E(400, 400, vx=-1.0, vy=0.2)
    bots = [bot, other]

    print("Select target:", select_target(bot, player, bots))
    angle, t = predict_intercept_angle((bot.x, bot.y), projectile_speed=7.0, target_pos=(player.x, player.y), target_vx=player.vx, target_vy=player.vy)
    print(f"Predicted aim angle: {angle:.3f} rad, time: {t}")
    print("Should shoot?", should_shoot(bot, player, angle, max_angle_diff=0.6, max_range=800))
    print("Seek vector:", seek_vector((bot.x, bot.y), (player.x, player.y), max_speed=3.0))
