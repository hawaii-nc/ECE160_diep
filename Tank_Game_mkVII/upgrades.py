from dataclasses import dataclass
import math

@dataclass
class BulletProfile:
    speed: float
    damage: float
    radius: float
    color: tuple

@dataclass
class GunMount:
    # angle_mode: 'aim' or 'body'
    # 'aim' means angle relative to player aim direction
    # 'body' means fixed absolute angle around tank
    angle_mode: str
    relative_angle: float  # radians
    profile: BulletProfile

@dataclass
class DroneSpawnerMount:
    angle_mode: str  # likely 'body'
    relative_angle: float

def base_profile(color):
    return BulletProfile(speed=7.0, damage=10.0, radius=4.0, color=color)

def heavy_profile(color):
    return BulletProfile(speed=7.0 * 0.6, damage=20.0, radius=6.0, color=color)

def sniper_profile(color):
    return BulletProfile(speed=7.0 * 1.5, damage=15.0, radius=3.0, color=color)

def bigger_faster_profile(color):
    return BulletProfile(speed=10.0, damage=24.0, radius=6.0, color=color)

def shotgun_profiles(color):
    # Return 5 small pellets in a spread pattern (smaller and less damaging than normal)
    pellets = []
    for _ in range(5):
        pellets.append(BulletProfile(speed=6.0, damage=5.0, radius=2.5, color=color))
    return pellets

def specialization_tree(spec_key, color):
    """
    Returns a dict:
      {
        'label': str,
        'options': [
           {'label': str, 'mounts': [GunMount | DroneSpawnerMount | ...], 'shotgun': bool}
        ]
      }
    """
    two_pi_thirds = 2.0 * math.pi / 3.0

    # Root branches: dual_barrel, twin_gun, heavy_cannon, sniper_barrel
    if spec_key == "dual_barrel":
        return {
            'label': "Dual barrel",
            'options': [
                {
                    'label': "Triple barrel",
                    'mounts': [
                        GunMount('aim', 0.0, base_profile(color)),
                        GunMount('aim', 0.2, base_profile(color)),
                        GunMount('aim', -0.2, base_profile(color)),
                    ],
                },
                {
                    'label': "Double barrel + rear gun",
                    'mounts': [
                        # Two forward-facing guns, slightly offset (parallel forwards)
                        GunMount('aim', -0.12, base_profile(color)),
                        GunMount('aim', 0.12, base_profile(color)),
                        # One rear-facing gun (180°)
                        GunMount('aim', math.pi, base_profile(color)),
                    ],
                }
            ]
        }

    if spec_key == "twin_gun":
        return {
            'label': "Twin gun",
            'options': [
                {
                    'label': "Big front + small rear",
                    'mounts': [
                        # Large front gun (similar to heavy cannon) and a normal rear gun
                        GunMount('aim', 0.0, heavy_profile(color)),
                        GunMount('aim', math.pi, base_profile(color)),
                    ],
                },
                {
                    'label': "Three normal guns at 120°",
                    'mounts': [
                        # Use 'aim' mode so these rotate with the player's aim (not fixed world angles)
                        GunMount('aim', 0.0, base_profile(color)),
                        GunMount('aim', two_pi_thirds, base_profile(color)),
                        GunMount('aim', -two_pi_thirds, base_profile(color)),
                    ],
                }
            ]
        }

    if spec_key == "heavy_cannon":
        return {
            'label': "Heavy cannon",
            'options': [
                {
                    'label': "Heavy - bigger & higher damage",
                    'mounts': [
                        # Provide a heavier, higher damage profile (slower base fire characteristics
                        # are handled by overall fire_rate adjustments elsewhere if desired)
                        GunMount('aim', 0.0, heavy_profile(color)),
                    ],
                },
                {
                    'label': "Shotgun cannon",
                    'mounts': [
                        GunMount('aim', -0.6021, BulletProfile(6.0, 5.0, 2.5, color)),
                        GunMount('aim', -0.3011, BulletProfile(6.0, 5.0, 2.5, color)),
                        GunMount('aim', 0.0, BulletProfile(6.0, 5.0, 2.5, color)),
                        GunMount('aim', 0.3011, BulletProfile(6.0, 5.0, 2.5, color)),
                        GunMount('aim', 0.6021, BulletProfile(6.0, 5.0, 2.5, color)),
                    ],
                    'shotgun': True
                }
            ]
        }

    if spec_key == "sniper_barrel":
        return {
            'label': "Sniper barrel",
            'options': [
                {
                    'label': "Longer barrel + faster bullets",
                    'mounts': [
                        GunMount('aim', 0.0, BulletProfile(11.0, 16.0, 3.0, color)),
                    ],
                },
                {
                    'label': "Sniper + drone spawner",
                    'mounts': [
                        # Normal front gun plus a rear drone spawner
                        GunMount('aim', 0.0, base_profile(color)),
                        DroneSpawnerMount('aim', math.pi),  # spawner at rear, rotates with aim
                    ],
                }
            ]
        }

    # Default fallback
    return {
        'label': "None",
        'options': [{'label': "Default", 'mounts': [GunMount('aim', 0.0, base_profile(color))]}]
    }

def root_defaults(spec_key, color):
    """Return a list of GunMounts representing the root-level (first-tier) specialization
    for the given spec_key. These are applied immediately when the player selects a root.
    """
    if spec_key == "dual_barrel":
        return [
            GunMount('aim', -0.12, base_profile(color)),
            GunMount('aim', 0.12, base_profile(color)),
        ], False

    if spec_key == "twin_gun":
        return [
            GunMount('aim', 0.0, base_profile(color)),
            GunMount('aim', math.pi, base_profile(color)),
        ], False

    if spec_key == "heavy_cannon":
        return [
            GunMount('aim', 0.0, heavy_profile(color)),
        ], False

    if spec_key == "sniper_barrel":
        return [
            GunMount('aim', 0.0, sniper_profile(color)),
        ], False

    return [GunMount('aim', 0.0, base_profile(color))], False