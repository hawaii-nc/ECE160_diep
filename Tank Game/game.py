import sys
import math
import random
import pygame

from config import (
    WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WHITE, RED, GREEN, BG_COLOR, FPS,
    BOT_SPAWN_RATE, MAX_BOTS, UPGRADE_COST
)
from core import Tank, Bullet, render_bullet
from upgrades import specialization_tree

def reset_game():
    player = Tank(WORLD_WIDTH//2, WORLD_HEIGHT//2, WHITE, True)
    player.id = -1
    player.drone_spawn_timer = 0
    bullets = []
    bots = []
    frame_count = 0
    game_over = False
    difficulty_level = 1
    show_specialization_menu = False
    bot_id_counter = 0
    shotgun_mode = False  # toggled based on specialization
    return player, bullets, bots, frame_count, game_over, difficulty_level, show_specialization_menu, bot_id_counter

def spawn_bot(difficulty_level, bot_id):
    bot = Tank(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT), GREEN)
    bot.id = bot_id
    # scale stats with difficulty
    bot.base_bullet_speed += difficulty_level * 0.3
    bot.base_damage += difficulty_level * 2.0
    bot.speed += difficulty_level * 0.2
    bot.fire_rate = 2.0 + 0.2 * difficulty_level  # bots also get faster fire rates
    # mounts: single aim gun using bot's base profile color
    bot.gun_mounts = bot.gun_mounts[:1]  # keep one mount
    bot.cooldown = 0
    return bot

def main():
    pygame.init()
    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tank Battle")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    player, bullets, bots, frame_count, game_over, difficulty_level, show_specialization_menu, bot_id_counter = reset_game()

    aim_angle = 0.0
    current_tree = None
    current_options = None
    shotgun_active = False

    while True:
        clock.tick(FPS)
        WIN.fill(BG_COLOR)
        keys = pygame.key.get_pressed()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        cam_x = player.x - WIDTH // 2
        cam_y = player.y - HEIGHT // 2

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                player, bullets, bots, frame_count, game_over, difficulty_level, show_specialization_menu, bot_id_counter = reset_game()
                shotgun_active = False
                current_tree = None
                current_options = None
            if not game_over:
                if show_specialization_menu and event.type == pygame.KEYDOWN:
                    # Determine current root spec (prompt is generated when level conditions met)
                    # We'll rotate through root branches based on progression count: 0..3 mapping to roots
                    root_order = ["dual_barrel", "twin_gun", "heavy_cannon", "sniper_barrel"]
                    root_index = min(player.specialization_count, len(root_order)-1)
                    root_key = root_order[root_index]
                    tree = specialization_tree(root_key, player.color)
                    current_tree = tree
                    current_options = tree['options']

                    if event.key in (pygame.K_1, pygame.K_2):
                        chosen = 0 if event.key == pygame.K_1 else 1
                        player.integrate_specialization(root_key, chosen)
                        shotgun_active = current_options[chosen].get('shotgun', False)
                        show_specialization_menu = False

                elif event.type == pygame.KEYDOWN:
                    # Stat upgrades for 5 EXP
                    if player.exp >= UPGRADE_COST:
                        if event.key == pygame.K_1:
                            player.speed += 0.5
                            player.exp -= UPGRADE_COST
                        elif event.key == pygame.K_2:
                            # Increase bullet speed across mounts
                            for m in player.gun_mounts:
                                m.profile.speed += 1.0
                            player.exp -= UPGRADE_COST
                        elif event.key == pygame.K_3:
                            # Increase damage across mounts
                            for m in player.gun_mounts:
                                m.profile.damage += 2.0
                            player.exp -= UPGRADE_COST
                        elif event.key == pygame.K_4:
                            player.max_health += 20
                            player.health = min(player.max_health, player.health + 20)
                            player.exp -= UPGRADE_COST
                        elif event.key == pygame.K_5:
                            # New: Fire rate upgrade
                            player.fire_rate += 0.5
                            player.exp -= UPGRADE_COST

        if not game_over:
            player.move(keys)
            player.regenerate()
            player.tick_fire_cooldown()
            player.update_drone_spawners()

            # Aim angle from mouse
            aim_angle = math.atan2((mouse_y + cam_y) - player.y, (mouse_x + cam_x) - player.x)

            # Continuous fire: hold left mouse
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0] and player.can_fire():
                new_bullets = player.fire(aim_angle, "player", player.id, shotgun=shotgun_active)
                bullets.extend(new_bullets)
                player.trigger_fire()

            # Draw player (with barrels and spawners)
            player.draw(WIN, cam_x, cam_y, aim_angle)
            # Update player's drones
            player.update_drones(bots, WIN, cam_x, cam_y)

            # Spawn bots
            frame_count += 1
            if frame_count % BOT_SPAWN_RATE == 0 and len(bots) < MAX_BOTS:
                bot = spawn_bot(difficulty_level, bot_id_counter)
                bot_id_counter += 1
                bots.append(bot)

            # Bot AI: aim and fire based on fire_rate
            for bot in bots:
                # Move a little towards player (optional)
                # Simple line-of-sight approach
                ang_to_player = math.atan2(player.y - bot.y, player.x - bot.x)
                # fire control
                bot.fire_cooldown -= 1
                if bot.fire_cooldown <= 0:
                    # One bullet from the bot's single mount
                    prof = bot.gun_mounts[0].profile
                    bullets.append(Bullet(bot.x, bot.y, ang_to_player, prof.speed, prof.damage, prof.radius, prof.color, "bot", bot.id))
                    # reset cooldown based on bot fire rate
                    frames_per_shot = max(1, int(FPS / bot.fire_rate))
                    bot.fire_cooldown = frames_per_shot

                # draw bot
                bot.draw(WIN, cam_x, cam_y, ang_to_player)

            # Bullets update and collision
            bullets_to_remove = []
            for bullet in bullets:
                bullet.move()
                render_bullet(WIN, bullet, cam_x, cam_y)

                if bullet.owner == "player":
                    for bot in bots[:]:
                        if math.hypot(bullet.x - bot.x, bullet.y - bot.y) < bot.radius:
                            bot.health -= bullet.damage
                            bullets_to_remove.append(bullet)
                            if bot.health <= 0:
                                bots.remove(bot)
                                player.exp += 5
                                player.bot_kills += 1
                                # Level up every 10 kills, increase difficulty
                                if player.bot_kills % 10 == 0:
                                    player.level += 1
                                    difficulty_level += 1
                                    # Specialization every 2 levels (20 kills)
                                    if player.level % 2 == 0:
                                        show_specialization_menu = True
                                        player.specialization_count += 1
                            break

                elif bullet.owner == "bot":
                    # Bot bullets do not hit bots (friendly fire disabled)
                    # Self-hit disabled by owner_id check implicitly by skipping all bot collisions
                    # Check player collision only
                    if math.hypot(bullet.x - player.x, bullet.y - player.y) < player.radius:
                        player.health -= bullet.damage
                        bullets_to_remove.append(bullet)

                elif bullet.owner == "drone":
                    # Drone bullets (not used here, drones do direct contact damage)
                    pass

            # Remove bullets safely
            for b in bullets_to_remove:
                if b in bullets:
                    bullets.remove(b)

            # Game over check
            if player.health <= 0:
                game_over = True

            # HUD
            hud1 = font.render(
                f"EXP: {player.exp} | Kills: {player.bot_kills} | Level: {player.level} | Diff: {difficulty_level}",
                True, WHITE
            )
            hud2 = font.render(
                "Upgrades: 1-Speed 2-BulletSpd 3-Damage 4-Health 5-FireRate (Cost: 5 EXP each)",
                True, WHITE
            )
            WIN.blit(hud1, (10, 10))
            WIN.blit(hud2, (10, 30))

            if show_specialization_menu:
                # Prompt with current branch options
                root_order = ["dual_barrel", "twin_gun", "heavy_cannon", "sniper_barrel"]
                root_index = min(player.specialization_count-1, len(root_order)-1)
                root_key = root_order[root_index] if player.specialization_count > 0 else root_order[0]
                tree = specialization_tree(root_key, player.color)
                opt_text = f"{tree['label']} specialization: 1-{tree['options'][0]['label']} | 2-{tree['options'][1]['label']}"
                spec_text = font.render(opt_text, True, WHITE)
                WIN.blit(spec_text, (WIDTH//2 - 240, HEIGHT//2))
        else:
            over_text = font.render("GAME OVER - Press R to Restart", True, RED)
            WIN.blit(over_text, (WIDTH//2 - 120, HEIGHT//2))

        pygame.display.update()

if __name__ == "__main__":
    main()