import sys
import math
import random
import pygame

from config import (
    WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WHITE, RED, GREEN, BG_COLOR, FPS,
    BOT_SPAWN_RATE, MAX_BOTS, UPGRADE_COST, KILLS_PER_LEVEL, LEVELS_PER_SPECIALIZATION
)
from core import Tank, Bullet, render_bullet
from ai_helpers import init_bot_ai, update_bot_ai
from upgrades import specialization_tree, root_defaults

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
    bot.fire_rate = 1.0 + 0.1 * difficulty_level  # bots also get faster fire rates
    # mounts: single aim gun using bot's base profile color
    bot.gun_mounts = bot.gun_mounts[:1]  # keep one mount
    bot.cooldown = 0
    init_bot_ai(bot)
    return bot
#Nathan Chong {
def draw_border(win, cam_x, cam_y, player_x, player_y):
    """Draw dashed slant border lines that fade based on proximity to edges."""
    threshold = 200  # pixels from edge to start fading in
    dash_length = 20
    gap_length = 10
    slant_angle = math.pi / 4  

    # Distances to edges
    dist_left = player_x
    dist_right = WORLD_WIDTH - player_x
    dist_top = player_y
    dist_bottom = WORLD_HEIGHT - player_y

    # Create a surface for the border with alpha
    border_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Helper to draw dashed slant line along an edge
    def draw_dashed_slant(start_x, start_y, end_x, end_y, color, alpha, direction):
        # direction: 1 for /, -1 for \
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.hypot(dx, dy)
        if length == 0:
            return
        num_dashes = int(length / (dash_length + gap_length))
        for i in range(num_dashes):
            pos = i * (dash_length + gap_length) / length
            x1 = start_x + dx * pos
            y1 = start_y + dy * pos
            x2 = x1 + math.cos(slant_angle) * dash_length * direction
            y2 = y1 + math.sin(slant_angle) * dash_length * direction
            pygame.draw.line(border_surf, (*color, alpha), (x1 - cam_x, y1 - cam_y), (x2 - cam_x, y2 - cam_y), 2)

    # Top edge (slanting down-right)
    if dist_top < threshold:
        alpha = int(255 * (1 - dist_top / threshold))
        draw_dashed_slant(0, 0, WORLD_WIDTH, 0, WHITE, alpha, 1)

    # Bottom edge (slanting up-right)
    if dist_bottom < threshold:
        alpha = int(255 * (1 - dist_bottom / threshold))
        draw_dashed_slant(0, WORLD_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WHITE, alpha, -1)

    # Left edge (slanting down-right)
    if dist_left < threshold:
        alpha = int(255 * (1 - dist_left / threshold))
        draw_dashed_slant(0, 0, 0, WORLD_HEIGHT, WHITE, alpha, 1)

    # Right edge (slanting down-left)
    if dist_right < threshold:
        alpha = int(255 * (1 - dist_right / threshold))
        draw_dashed_slant(WORLD_WIDTH, 0, WORLD_WIDTH, WORLD_HEIGHT, WHITE, alpha, -1)

    # Blit the border surface
    win.blit(border_surf, (0, 0))
#Nathan Chong }
def main():
    pygame.init()
    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tank Battle")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    player, bullets, bots, frame_count, game_over, difficulty_level, show_specialization_menu, bot_id_counter = reset_game()

    # Debug / temporary testing toggle: press F2 to enable rapid unlock (kills-per-level = 1)
    rapid_unlock = False

    aim_angle = 0.0
    current_tree = None
    current_options = None
    shotgun_active = False
    # Specialization menu stage: None | 'root' | 'option'
    specialization_stage = None
    pending_root = None
    specializations_shown = 0  # Count how many specialization menus have been shown to the player
    kills_at_last_specialization = 0  # Track kill count when last specialization menu was shown

    while True:
        clock.tick(FPS)
        WIN.fill(BG_COLOR)
        keys = pygame.key.get_pressed()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        cam_x = player.x - WIDTH // 2
        cam_y = player.y - HEIGHT // 2
        draw_border(WIN, cam_x, cam_y, player.x, player.y)

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
                # Reset specialization/menu tracking so restarts don't inherit prior kill counts
                kills_at_last_specialization = 0
                specialization_stage = None
                pending_root = None
                specializations_shown = 0
            if not game_over:
                if show_specialization_menu and event.type == pygame.KEYDOWN:
                    # Two-stage specialization selection:
                    # Stage 'root' -> player picks one of the root branches (1..4)
                    # Stage 'option' -> player picks the chosen branch's option (1..2)
                    root_order = ["dual_barrel", "twin_gun", "heavy_cannon", "sniper_barrel"]

                    # ensure stage set
                    if specialization_stage is None:
                        specialization_stage = 'root'

                    if specialization_stage == 'root':
                        # Root selection uses keys 1..4. Apply the root immediately and resume gameplay.
                        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                            idx = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2, pygame.K_4:3}[event.key]
                            root_key = root_order[idx]
                            # apply root-default mounts immediately
                            mounts, shot_flag = root_defaults(root_key, player.color)
                            # replace player's mounts and clear spawners
                            player.gun_mounts = mounts
                            player.drone_spawner_mounts = []
                            player.spec_key = root_key
                            shotgun_active = shot_flag
                            # Apply shotgun modifier flag to the player (affects firing)
                            player.is_shotgun = shot_flag
                            # close menu and resume gameplay; do not increment specialization_count yet
                            show_specialization_menu = False
                            specialization_stage = None
                            pending_root = None
                            continue

                    elif specialization_stage == 'option':
                        # Option selection uses keys 1..2
                        if event.key in (pygame.K_1, pygame.K_2) and pending_root is not None:
                            chosen = 0 if event.key == pygame.K_1 else 1
                            print(f"DEBUG: CLOSING SPECIALIZATION MENU. kills_at_last_specialization={kills_at_last_specialization}")
                            player.integrate_specialization(pending_root, chosen)
                            shotgun_active = current_options[chosen].get('shotgun', False)
                            # Apply shotgun modifier to the player (affects firing)
                            player.is_shotgun = shotgun_active
                            show_specialization_menu = False
                            specialization_stage = None
                            pending_root = None
                            # clear stored root since we've finalized the option
                            player.spec_key = None
                            # Mark full specialization complete to prevent future branches
                            player.specialization_complete = True
                            # increment specialization count now that selection is finalized
                            player.specialization_count += 1
                            specializations_shown += 1
                            # Consume this event
                            continue

                elif event.type == pygame.KEYDOWN:
                    # Debug: toggle rapid unlock (press F2)
                    if event.key == pygame.K_F2:
                        rapid_unlock = not rapid_unlock
                        continue

                    # Stat upgrades for 5 EXP (only if specialization menu is NOT open)
                    if not show_specialization_menu and player.exp >= UPGRADE_COST:
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
            # Skip gameplay logic if specialization menu is open
            if not show_specialization_menu:
                player.move(keys)
                player.regenerate()
                player.tick_fire_cooldown()
                player.update_drone_spawners()

                # Aim angle from mouse
                aim_angle = math.atan2((mouse_y + cam_y) - player.y, (mouse_x + cam_x) - player.x)

                # Continuous fire: hold left mouse
                mouse_buttons = pygame.mouse.get_pressed()
                if mouse_buttons[0] and player.can_fire():
                    new_bullets = player.fire(aim_angle, "player", player.id, shotgun=player.is_shotgun)
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

                # Bot AI: orbiting movement with randomness and spacing, aim and fire based on fire_rate
                for bot in bots:
                    ang_to_player = update_bot_ai(bot, bots, player)
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
                                    # Check if we should show a specialization menu based purely on kills
                                    # Use a single effective threshold so rapid unlock behaves consistently
                                    effective_kills_threshold = 1 if rapid_unlock else KILLS_PER_LEVEL
                                    kills_since_last_spec = player.bot_kills - kills_at_last_specialization

                                    should_show_menu = (kills_since_last_spec >= effective_kills_threshold)

                                    if should_show_menu and not show_specialization_menu and not player.specialization_complete:
                                        show_specialization_menu = True
                                        # If the player already picked a root previously, show the options
                                        if player.spec_key:
                                            specialization_stage = 'option'
                                            pending_root = player.spec_key
                                            current_tree = specialization_tree(pending_root, player.color)
                                            current_options = current_tree['options']
                                        else:
                                            specialization_stage = 'root'
                                            pending_root = None
                                        kills_at_last_specialization = player.bot_kills
                                    
                                    # Level up for progression display (independent of specialization menus)
                                    effective_kills_per_level = 1 if rapid_unlock else KILLS_PER_LEVEL
                                    if player.bot_kills % effective_kills_per_level == 0:
                                        player.level += 1
                                        difficulty_level += 1
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
            else:
                # When menu is open, still draw the game in background but don't update it
                player.draw(WIN, cam_x, cam_y, aim_angle)
                player.update_drones(bots, WIN, cam_x, cam_y)
                for bot in bots:
                    # Don't call update_bot_ai here - just draw them as-is
                    # Calculate angle for drawing but don't update position
                    ang_to_player = math.atan2(player.y - bot.y, player.x - bot.x)
                    bot.draw(WIN, cam_x, cam_y, ang_to_player)
                for bullet in bullets:
                    render_bullet(WIN, bullet, cam_x, cam_y)

            # HUD
            hud1 = font.render(
                f"EXP: {player.exp} | Kills: {player.bot_kills} | Level: {player.level} | Diff: {difficulty_level}",
                True, WHITE
            )
            hud2 = font.render(
                "Upgrades: 1-Speed 2-BulletSpd 3-Damage 4-Health 5-FireRate (Cost: 5 EXP each)",
                True, WHITE
            )
            # Debug HUD: show whether rapid unlock is active
            debug_text = font.render(f"RapidUnlock: {'ON' if rapid_unlock else 'OFF'} (F2)", True, WHITE)
            WIN.blit(hud1, (10, 10))
            WIN.blit(hud2, (10, 30))
            WIN.blit(debug_text, (10, 50))

            if show_specialization_menu:
                # Render either the root selection (1..4) or the chosen root's options (1..2)
                root_order = ["dual_barrel", "twin_gun", "heavy_cannon", "sniper_barrel"]
                # Color map for each branch
                branch_colors = {
                    "dual_barrel": (255, 200, 100),      # Orange
                    "twin_gun": (100, 200, 255),         # Light blue
                    "heavy_cannon": (255, 100, 100),     # Red
                    "sniper_barrel": (150, 255, 150),    # Light green
                }
                
                if specialization_stage == 'root' or specialization_stage is None:
                    # Root selection menu
                    title_text = font.render("Select Specialization Branch:", True, WHITE)
                    roots_text = "1: Dual Barrel   2: Twin Gun   3: Heavy Cannon   4: Sniper Barrel"
                    root_text = font.render(roots_text, True, WHITE)
                    
                    # Calculate positioning for centered menu
                    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
                    root_rect = root_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
                    
                    # Draw semi-transparent background
                    bg_surf = pygame.Surface((root_rect.width + 40, root_rect.height + 100), pygame.SRCALPHA)
                    bg_surf.fill((0, 0, 0, 180))
                    WIN.blit(bg_surf, (WIDTH // 2 - (root_rect.width + 40) // 2, HEIGHT // 2 - 80))
                    
                    WIN.blit(title_text, title_rect)
                    WIN.blit(root_text, root_rect)
                    
                elif specialization_stage == 'option' and current_tree is not None:
                    # Option selection menu
                    branch_key = pending_root
                    branch_color = branch_colors.get(branch_key, WHITE)
                    
                    title_text = font.render(f"{current_tree['label']} Specialization", True, branch_color)
                    opt1_text = f"1: {current_tree['options'][0]['label']}"
                    opt2_text = f"2: {current_tree['options'][1]['label']}"
                    opt1_render = font.render(opt1_text, True, WHITE)
                    opt2_render = font.render(opt2_text, True, WHITE)
                    
                    # Calculate positioning for centered menu
                    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
                    opt1_rect = opt1_render.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10))
                    opt2_rect = opt2_render.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
                    
                    # Draw semi-transparent background with branch color tint
                    max_width = max(opt1_rect.width, opt2_rect.width, title_rect.width) + 40
                    bg_surf = pygame.Surface((max_width, 130), pygame.SRCALPHA)
                    bg_color = (*branch_color, 180)  # Add alpha channel
                    bg_surf.fill(bg_color)
                    WIN.blit(bg_surf, (WIDTH // 2 - max_width // 2, HEIGHT // 2 - 80))
                    
                    WIN.blit(title_text, title_rect)
                    WIN.blit(opt1_render, opt1_rect)
                    WIN.blit(opt2_render, opt2_rect)
        else:
            over_text = font.render("GAME OVER - Press R to Restart", True, RED)
            WIN.blit(over_text, (WIDTH//2 - 120, HEIGHT//2))

        pygame.display.update()

if __name__ == "__main__":

    main()
