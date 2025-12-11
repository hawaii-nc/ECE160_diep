import pygame
import math
import random
from config import WORLD_WIDTH, WORLD_HEIGHT, GREY

# Approximate player radius (must match Tank.radius in `core.py`).
# We avoid importing `core` to prevent circular imports.
PLAYER_RADIUS = 20
# Minimum clearance between walls so the player can pass (diameter)
MIN_WALL_CLEARANCE = PLAYER_RADIUS * 2 + 4


class Wall:
    """Axis-aligned rectangular wall."""
    def __init__(self, x, y, w, h, color=GREY):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))

    def draw(self, win, cam_x, cam_y):
        r = self.rect
        draw_rect = pygame.Rect(r.x - cam_x, r.y - cam_y, r.w, r.h)
        pygame.draw.rect(win, self.color, draw_rect)

    def collides_circle(self, cx, cy, radius):
        """Return True if a circle at (cx,cy) with radius intersects this wall."""
        # Find closest point on rect to circle center
        r = self.rect
        closest_x = max(r.left, min(cx, r.right))
        closest_y = max(r.top, min(cy, r.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return dx * dx + dy * dy < radius * radius

    def collides_point(self, x, y):
        r = self.rect
        return r.left <= x <= r.right and r.top <= y <= r.bottom


def resolve_circle_against_wall(entity, wall):
    """Push a circular entity out of the wall if overlapping.
    Entity must have `x`, `y`, and `radius` attributes and will be modified in-place.
    """
    cx, cy, r = entity.x, entity.y, entity.radius
    rect = wall.rect
    # closest point
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - closest_x
    dy = cy - closest_y
    dist2 = dx * dx + dy * dy
    if dist2 == 0:
        # center exactly aligned with corner/edge; nudge out upward
        # choose smallest push: try up, left, right, down
        pushes = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for px, py in pushes:
            entity.x += px * 1.0
            entity.y += py * 1.0
            if not wall.collides_circle(entity.x, entity.y, r):
                return
        return

    dist = math.sqrt(dist2)
    overlap = r - dist
    if overlap > 0:
        # move entity along (dx,dy) direction by overlap
        nx = dx / dist
        ny = dy / dist
        entity.x += nx * overlap
        entity.y += ny * overlap


def resolve_circle_against_walls(entity, walls):
    if not walls:
        return
    for w in walls:
        if w.collides_circle(entity.x, entity.y, entity.radius):
            resolve_circle_against_wall(entity, w)


def create_default_walls():
    """Create a set of walls that separate the map but leave gaps for connectivity."""
    walls = []
    W = WORLD_WIDTH
    H = WORLD_HEIGHT
    # Keep the old default behavior as one deterministic layout
    gap_h = 160
    gap_y = H // 2 - gap_h // 2
    walls.append(Wall(W // 3, 0, 16, gap_y))
    walls.append(Wall(W // 3, gap_y + gap_h, 16, H - (gap_y + gap_h)))

    gap_w = 200
    gap_x = 80
    y = (H * 2) // 3
    walls.append(Wall(0, y, gap_x, 16))
    walls.append(Wall(gap_x + gap_w, y, W - (gap_x + gap_w), 16))

    cx = W // 2 - 80
    cy = H // 2 - 80
    walls.append(Wall(cx, cy, 40, 160))
    walls.append(Wall(cx + 120, cy, 40, 160))

    # Ensure major points remain connected (center and four quadrant centers)
    center = (W // 2, H // 2)
    q1 = (W // 4, H // 4)
    q2 = (W * 3 // 4, H // 4)
    q3 = (W // 4, H * 3 // 4)
    q4 = (W * 3 // 4, H * 3 // 4)
    try:
        walls = ensure_connectivity(walls, [center, q1, q2, q3, q4])
    except Exception:
        # If connectivity enforcement fails for any reason, fall back to generated walls
        pass
    return walls


def create_random_walls(seed: int | None = None, max_vertical: int = 2, max_horizontal: int = 2):
    """Create randomized walls while leaving guaranteed passages so the map remains accessible.

    This function places a small number of long vertical and horizontal walls at random
    positions, and ensures each wall has at least one gap so it can't fully block the map.
    The randomness is seeded for reproducibility.
    """
    if seed is not None:
        random.seed(seed)

    walls = []
    W = WORLD_WIDTH
    H = WORLD_HEIGHT

    wall_thickness = 16

    # Create a few vertical walls
    for i in range(max_vertical):
        placed = False
        attempts = 0
        while not placed and attempts < 30:
            attempts += 1
            # Choose x in safe margins
            x = random.randint(int(W * 0.15), int(W * 0.85))
            gap_h = random.randint(120, 300)
            gap_center = random.randint(int(H * 0.2), int(H * 0.8))
            gap_y = max(20, gap_center - gap_h // 2)
            top_rect = pygame.Rect(x, 0, wall_thickness, gap_y) if gap_y > 8 else None
            bottom_h = H - (gap_y + gap_h)
            bottom_rect = pygame.Rect(x, gap_y + gap_h, wall_thickness, bottom_h) if bottom_h > 8 else None

            def candidate_ok(r):
                if r is None:
                    return True
                for ew in walls:
                    # ensure clearance between r and existing wall rects
                    if rect_min_distance(r, ew.rect) < MIN_WALL_CLEARANCE:
                        return False
                return True

            if candidate_ok(top_rect) and candidate_ok(bottom_rect):
                if top_rect:
                    walls.append(Wall(top_rect.x, top_rect.y, top_rect.w, top_rect.h))
                if bottom_rect:
                    walls.append(Wall(bottom_rect.x, bottom_rect.y, bottom_rect.w, bottom_rect.h))
                placed = True

    # Create a few horizontal walls
    for i in range(max_horizontal):
        placed = False
        attempts = 0
        while not placed and attempts < 30:
            attempts += 1
            y = random.randint(int(H * 0.15), int(H * 0.85))
            gap_w = random.randint(120, 300)
            gap_center = random.randint(int(W * 0.2), int(W * 0.8))
            gap_x = max(20, gap_center - gap_w // 2)
            left_rect = pygame.Rect(0, y, gap_x, wall_thickness) if gap_x > 8 else None
            right_w = W - (gap_x + gap_w)
            right_rect = pygame.Rect(gap_x + gap_w, y, right_w, wall_thickness) if right_w > 8 else None

            def candidate_ok(r):
                if r is None:
                    return True
                for ew in walls:
                    if rect_min_distance(r, ew.rect) < MIN_WALL_CLEARANCE:
                        return False
                return True

            if candidate_ok(left_rect) and candidate_ok(right_rect):
                if left_rect:
                    walls.append(Wall(left_rect.x, left_rect.y, left_rect.w, left_rect.h))
                if right_rect:
                    walls.append(Wall(right_rect.x, right_rect.y, right_rect.w, right_rect.h))
                placed = True

    # Add a couple of small randomized blocks with passages
    for i in range(2):
        bx = random.randint(int(W * 0.3), int(W * 0.7))
        by = random.randint(int(H * 0.3), int(H * 0.7))
        bw = random.randint(40, 120)
        bh = random.randint(40, 160)
        # carve a passage along one side
        passage_side = random.choice(['top', 'bottom', 'left', 'right'])
        # Build candidate rect and ensure clearance from other walls
        if passage_side == 'top':
            cand = pygame.Rect(bx, by + int(bh * 0.3), bw, int(bh * 0.7))
        elif passage_side == 'bottom':
            cand = pygame.Rect(bx, by, bw, int(bh * 0.7))
        elif passage_side == 'left':
            cand = pygame.Rect(bx + int(bw * 0.3), by, int(bw * 0.7), bh)
        else:
            cand = pygame.Rect(bx, by, int(bw * 0.7), bh)

        ok = True
        for ew in walls:
            if rect_min_distance(cand, ew.rect) < MIN_WALL_CLEARANCE:
                ok = False
                break
        if ok:
            walls.append(Wall(cand.x, cand.y, cand.w, cand.h))

    return walls


# Add global visibility flag and setter
WALLS_VISIBLE = True
WALLS_COLLISION = True

def set_walls_visible(v: bool):
    global WALLS_VISIBLE
    WALLS_VISIBLE = bool(v)

# Add setter for wall collision
def set_walls_collision(v: bool):
    global WALLS_COLLISION
    WALLS_COLLISION = bool(v)


def draw_walls(win, walls, cam_x=0, cam_y=0):
    # skip drawing if walls are hidden (e.g. during boss fight)
    if not WALLS_VISIBLE:
        return
    for w in walls:
        w.draw(win, cam_x, cam_y)


def is_position_free(x, y, radius, walls):
    """Return True if a circle at (x,y) with `radius` does not intersect any wall and is inside world bounds."""
    if x - radius < 0 or y - radius < 0 or x + radius > WORLD_WIDTH or y + radius > WORLD_HEIGHT:
        return False
    if not walls:
        return True
    for w in walls:
        if w.collides_circle(x, y, radius):
            return False
    return True


def find_free_position(radius, walls, tries: int = 1000):
    """Try to find a free (x,y) where a circle of `radius` does not intersect walls.

    Uses random sampling then falls back to a local spiral search around center.
    """
    # Random sampling
    for _ in range(tries):
        x = random.randint(radius, WORLD_WIDTH - radius)
        y = random.randint(radius, WORLD_HEIGHT - radius)
        if is_position_free(x, y, radius, walls):
            return x, y

    # Fallback: spiral from center
    cx, cy = WORLD_WIDTH // 2, WORLD_HEIGHT // 2
    max_shift = max(WORLD_WIDTH, WORLD_HEIGHT)
    step = max(8, radius)
    for r in range(step, max_shift, step):
        for dx in range(-r, r + 1, step):
            for dy in (-r, r):
                x = cx + dx
                y = cy + dy
                if 0 <= x - radius and 0 <= y - radius and x + radius <= WORLD_WIDTH and y + radius <= WORLD_HEIGHT:
                    if is_position_free(x, y, radius, walls):
                        return x, y
        for dy in range(-r + step, r - step + 1, step):
            for dx in (-r, r):
                x = cx + dx
                y = cy + dy
                if 0 <= x - radius and 0 <= y - radius and x + radius <= WORLD_WIDTH and y + radius <= WORLD_HEIGHT:
                    if is_position_free(x, y, radius, walls):
                        return x, y

    # As a last resort return center clamped
    return max(radius, min(WORLD_WIDTH - radius, cx)), max(radius, min(WORLD_HEIGHT - radius, cy))


def rect_min_distance(r1: pygame.Rect, r2: pygame.Rect) -> float:
    """Return the minimum distance between two rects (0 if they overlap)."""
    # horizontal gap
    if r1.right < r2.left:
        dx = r2.left - r1.right
    elif r2.right < r1.left:
        dx = r1.left - r2.right
    else:
        dx = 0

    # vertical gap
    if r1.bottom < r2.top:
        dy = r2.top - r1.bottom
    elif r2.bottom < r1.top:
        dy = r1.top - r2.bottom
    else:
        dy = 0

    if dx == 0 and dy == 0:
        return 0.0
    return math.hypot(dx, dy)


def _cell_grid_reachable(start, walls, cell_size=32):
    """Return a set of reachable cell indices (i,j) starting from start=(x,y)."""
    sx, sy = start
    cols = (WORLD_WIDTH + cell_size - 1) // cell_size
    rows = (WORLD_HEIGHT + cell_size - 1) // cell_size

    def cell_rect(i, j):
        return pygame.Rect(i * cell_size, j * cell_size, cell_size, cell_size)

    # build blocked cells from walls
    blocked = set()
    if walls:
        for w in walls:
            r = w.rect
            i0 = max(0, r.left // cell_size)
            j0 = max(0, r.top // cell_size)
            i1 = min(cols - 1, r.right // cell_size)
            j1 = min(rows - 1, r.bottom // cell_size)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    # precise check
                    if r.colliderect(cell_rect(i, j)):
                        blocked.add((i, j))

    # start cell
    si = min(cols - 1, max(0, int(sx) // cell_size))
    sj = min(rows - 1, max(0, int(sy) // cell_size))
    from collections import deque
    q = deque()
    reachable = set()
    if (si, sj) in blocked:
        return reachable
    q.append((si, sj))
    reachable.add((si, sj))
    while q:
        i, j = q.popleft()
        for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
            ni, nj = i+di, j+dj
            if 0 <= ni < cols and 0 <= nj < rows and (ni,nj) not in reachable and (ni,nj) not in blocked:
                reachable.add((ni, nj))
                q.append((ni, nj))
    return reachable


def ensure_connectivity(walls, key_points, cell_size=32, gap_size=120, max_iterations=50):
    """Ensure each point in `key_points` is reachable from the first point by carving gaps if necessary.

    `key_points` should be a list of (x,y) coordinates where connectivity is required.
    This function mutates and returns the `walls` list.
    """
    if not key_points or len(key_points) < 2:
        return walls

    start = key_points[0]
    iterations = 0
    while iterations < max_iterations:
        iterations += 1
        reachable = _cell_grid_reachable(start, walls, cell_size)
        all_reached = True
        unreachable_targets = []
        for pt in key_points[1:]:
            ci = int(pt[0] // cell_size)
            cj = int(pt[1] // cell_size)
            if (ci, cj) not in reachable:
                all_reached = False
                unreachable_targets.append(pt)

        if all_reached:
            break

        # For each unreachable target, try to carve a gap in the first wall intersecting the line
        for target in unreachable_targets:
            # find walls intersecting the line from start->target
            intersecting = [w for w in walls if segment_intersects_rect(start[0], start[1], target[0], target[1], w.rect)]
            if not intersecting:
                # if no wall intersects the straight line, try to remove any wall that blocks connectivity by test removal
                removed = False
                for w in list(walls):
                    temp = [x for x in walls if x is not w]
                    if (int(target[0] // cell_size), int(target[1] // cell_size)) in _cell_grid_reachable(start, temp, cell_size):
                        walls.remove(w)
                        removed = True
                        break
                if removed:
                    continue

            # open a gap in the first intersecting wall
            w = intersecting[0] if intersecting else None
            if w is None:
                continue
            # compute midpoint between start and target as desired gap center
            mx = (start[0] + target[0]) / 2.0
            my = (start[1] + target[1]) / 2.0

            # replace wall with pieces leaving a gap
            new_walls = []
            # vertical wall (taller than wide)
            if w.h > w.w:
                gap_half = gap_size // 2
                gap_center_y = int(max(w.y + gap_half + 4, min(w.y + w.h - gap_half - 4, my)))
                top_h = gap_center_y - gap_half - w.y
                bottom_y = gap_center_y + gap_half
                bottom_h = (w.y + w.h) - bottom_y
                if top_h > 8:
                    new_walls.append(Wall(w.x, w.y, w.w, top_h, w.color))
                if bottom_h > 8:
                    new_walls.append(Wall(w.x, bottom_y, w.w, bottom_h, w.color))
            else:
                # horizontal wall
                gap_half = gap_size // 2
                gap_center_x = int(max(w.x + gap_half + 4, min(w.x + w.w - gap_half - 4, mx)))
                left_w = gap_center_x - gap_half - w.x
                right_x = gap_center_x + gap_half
                right_w = (w.x + w.w) - right_x
                if left_w > 8:
                    new_walls.append(Wall(w.x, w.y, left_w, w.h, w.color))
                if right_w > 8:
                    new_walls.append(Wall(right_x, w.y, right_w, w.h, w.color))

            # replace in walls list
            if new_walls:
                # ensure new walls won't be too close to other existing walls (excluding w)
                conflict = False
                for nw in new_walls:
                    for ew in walls:
                        if ew is w:
                            continue
                        if rect_min_distance(nw.rect, ew.rect) < MIN_WALL_CLEARANCE:
                            conflict = True
                            break
                    if conflict:
                        break

                try:
                    idx = walls.index(w)
                except ValueError:
                    idx = -1

                if conflict:
                    # If carving would create too-close walls, remove the original wall entirely
                    if idx != -1:
                        walls.pop(idx)
                else:
                    if idx != -1:
                        walls.pop(idx)
                        for nw in reversed(new_walls):
                            walls.insert(idx, nw)

        # continue loop to re-evaluate reachability
    return walls


def _seg_seg_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    # Check if segments (x1,y1)-(x2,y2) and (x3,y3)-(x4,y4) intersect
    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)

    return (ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4)) and (
        ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4)
    )


def segment_intersects_rect(x1, y1, x2, y2, rect):
    # If either endpoint inside rect, treat as intersection
    if rect.collidepoint(int(x1), int(y1)) or rect.collidepoint(int(x2), int(y2)):
        return True

    rx1, ry1 = rect.left, rect.top
    rx2, ry2 = rect.right, rect.bottom

    # rect edges
    edges = [
        (rx1, ry1, rx2, ry1),
        (rx2, ry1, rx2, ry2),
        (rx2, ry2, rx1, ry2),
        (rx1, ry2, rx1, ry1),
    ]

    for ex1, ey1, ex2, ey2 in edges:
        if _seg_seg_intersect(x1, y1, x2, y2, ex1, ey1, ex2, ey2):
            return True
    return False


def line_of_sight(x1, y1, x2, y2, walls):
    """Return True if the segment between (x1,y1) and (x2,y2) is not blocked by any wall."""
    if not walls:
        return True
    for w in walls:
        if segment_intersects_rect(x1, y1, x2, y2, w.rect):
            return False
    return True

# Patch all wall objects' collides_circle to respect WALLS_COLLISION
# (Assumes Wall class has a collides_circle method)
def patch_wall_collision():
    from types import MethodType
    def new_collides_circle(self, x, y, r):
        from walls import WALLS_COLLISION
        if not WALLS_COLLISION:
            return False
        # Call the original method
        return self._orig_collides_circle(x, y, r)
    try:
        from walls import Wall
        if not hasattr(Wall, "_orig_collides_circle"):
            Wall._orig_collides_circle = Wall.collides_circle
            Wall.collides_circle = new_collides_circle
    except Exception:
        pass

# Patch on import
patch_wall_collision()

def respawn_walls_avoiding_player(walls, player, min_dist=40):
    """
    Replace the contents of the walls list with new walls,
    ensuring none overlap the player (within min_dist of player center).
    """
    from config import WORLD_WIDTH, WORLD_HEIGHT
    # Remove all current walls
    walls.clear()
    # Recreate walls, avoiding player
    new_walls = create_random_walls()
    safe_walls = []
    for w in new_walls:
        try:
            # If wall has a collides_circle method, use it
            if hasattr(w, "collides_circle"):
                if not w.collides_circle(player.x, player.y, min_dist):
                    safe_walls.append(w)
            else:
                # Fallback: check bounding box distance
                wx, wy, ww, wh = w.x, w.y, w.w, w.h
                if not (wx - min_dist < player.x < wx + ww + min_dist and wy - min_dist < player.y < wy + wh + min_dist):
                    safe_walls.append(w)
        except Exception:
            safe_walls.append(w)
    walls.extend(safe_walls)
