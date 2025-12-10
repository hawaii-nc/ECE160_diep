# Screen and world settings
WIDTH, HEIGHT = 800, 600
WORLD_WIDTH, WORLD_HEIGHT = 1600, 1200

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (50, 150, 255)
YELLOW = (245, 235, 66)
ORANGE = (255, 165, 0)
CYAN = (0, 200, 200)
MAGENTA = (220, 30, 220)
GREY = (120, 120, 120)
BG_COLOR = (30, 30, 30)

# Game constants
FPS = 60
BOT_SPAWN_RATE = 50  # frames between bot spawns
UPGRADE_COST = 5
MAX_BOTS = 5
KILLS_PER_LEVEL = 10
LEVELS_PER_SPECIALIZATION = 2

# Drone settings
DRONE_SPEED = 4.0
DRONE_DAMAGE = 4
DRONE_SPAWN_INTERVAL_FRAMES = FPS * 1.5  # every ~1.5 seconds (2x frequency)
DRONE_LIFETIME_FRAMES = FPS * 20       # ~20 seconds
DRONE_RADIUS = 6

# Barrel rendering scale factors
BARREL_LENGTH_SCALE = 5.0   # pixels per bullet_speed
BARREL_WIDTH_BASE = 3       # base width in pixels
BARREL_WIDTH_DAMAGE_SCALE = 0.2  # adds width per damage
BARREL_WIDTH_RADIUS_SCALE = 0.8  # adds width per bullet radius