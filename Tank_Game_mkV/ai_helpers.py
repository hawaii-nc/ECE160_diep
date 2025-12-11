"""Bot AI helper functions for Tank Game.

Provides utilities to initialize per-bot AI state and to update bot position/orientation
with orbiting, wander, and separation behaviours.
"""

from __future__ import annotations

import math
import random
from typing import Iterable

from config import WORLD_WIDTH, WORLD_HEIGHT
from walls import line_of_sight


def init_bot_ai(bot) -> None:
    """Attach AI metadata to a newly spawned bot."""
    bot.orbit_dir = random.choice([-1, 1])
    bot.wander_angle = random.uniform(0, 2 * math.pi)


def update_bot_ai(
    bot,
    bots: Iterable,
    player,
    preferred_distance: float = 220.0,
    separation_radius: float = 60.0,
    walls: list = None,
) -> float:
    """
    Update the bot's position using orbit, radial, separation, and wander forces.

    Returns the angle (radians) from the bot toward the player for aiming.
    """
    player_speed = getattr(player, "speed", 3.0)
    target_bot_speed = max(0.5, player_speed * 0.75)

    vec_x = player.x - bot.x
    vec_y = player.y - bot.y
    dist = math.hypot(vec_x, vec_y) + 1e-5
    dir_to_player = (vec_x / dist, vec_y / dist)

    tangent = (-dir_to_player[1], dir_to_player[0])
    orbit = (tangent[0] * bot.orbit_dir, tangent[1] * bot.orbit_dir)

    if dist < preferred_distance * 0.8:
        radial = (-dir_to_player[0], -dir_to_player[1])
        radial_scale = 0.6
    elif dist > preferred_distance * 1.2:
        radial = dir_to_player
        radial_scale = 0.5
    else:
        radial = (0.0, 0.0)
        radial_scale = 0.0

    sep_x = 0.0
    sep_y = 0.0
    for other in bots:
        if other is bot:
            continue
        dx = bot.x - getattr(other, "x", bot.x)
        dy = bot.y - getattr(other, "y", bot.y)
        d = math.hypot(dx, dy)
        if 1 < d < separation_radius:
            strength = (separation_radius - d) / separation_radius
            sep_x += dx / d * strength
            sep_y += dy / d * strength

    bot.wander_angle += random.uniform(-0.15, 0.15)
    wander = (math.cos(bot.wander_angle) * 0.3, math.sin(bot.wander_angle) * 0.3)

    move_x = orbit[0] * 1.0 + radial[0] * radial_scale + sep_x * 0.8 + wander[0]
    move_y = orbit[1] * 1.0 + radial[1] * radial_scale + sep_y * 0.8 + wander[1]

    # If walls are present and the bot does NOT have line of sight to the player,
    # the bot should patrol locally (back-and-forth) so it can regain LOS eventually.
    patrol_active = False
    if walls is not None:
        if not line_of_sight(bot.x, bot.y, player.x, player.y, walls):
            # initialize patrol attributes if missing
            if not hasattr(bot, 'patrol_dir'):
                bot.patrol_dir = random.choice([-1, 1])
            if not hasattr(bot, 'patrol_timer'):
                bot.patrol_timer = random.randint(60, 180)
            if not hasattr(bot, 'patrol_axis'):
                # prefer vertical patrol (up/down) but sometimes horizontal
                bot.patrol_axis = random.choice(['y'] * 3 + ['x'])

            # countdown and possibly flip direction
            bot.patrol_timer -= 1
            if bot.patrol_timer <= 0:
                bot.patrol_dir *= -1
                bot.patrol_timer = random.randint(60, 180)

            # Patrol speed is a fraction of target speed
            patrol_speed = max(0.6, target_bot_speed * 0.5)
            if bot.patrol_axis == 'y':
                move_x = 0.0
                move_y = bot.patrol_dir * patrol_speed
            else:
                move_x = bot.patrol_dir * patrol_speed
                move_y = 0.0
            patrol_active = True

    mag = math.hypot(move_x, move_y)
    if mag > 0:
        scale = target_bot_speed / mag
        move_x *= scale
        move_y *= scale

    # Apply movement axis-by-axis so bots can slide along walls if provided
    new_x = bot.x + move_x
    new_y = bot.y + move_y

    # vertical
    prev_x, prev_y = bot.x, bot.y
    bot.y = max(0, min(WORLD_HEIGHT, new_y))
    if walls:
        for w in walls:
            if w.collides_circle(bot.x, bot.y, getattr(bot, 'radius', 20)):
                bot.y = prev_y
                break

    # horizontal
    bot.x = max(0, min(WORLD_WIDTH, new_x))
    if walls:
        for w in walls:
            if w.collides_circle(bot.x, bot.y, getattr(bot, 'radius', 20)):
                bot.x = prev_x
                break

    return math.atan2(player.y - bot.y, player.x - bot.x)
