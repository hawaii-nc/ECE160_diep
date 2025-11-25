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
    # Return multiple small pellets
    pellets = []
    for _ in range(6):
        pellets.append(BulletProfile(speed=8.0, damage=5.0, radius=3.0, color=color))
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
                        GunMount('aim', 0.0, base_profile(color)),
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
                        GunMount('aim', 0.0, BulletProfile(8.5, 18.0, 5.0, color)),
                        GunMount('aim', math.pi, BulletProfile(7.0, 8.0, 3.5, color)),
                    ],
                },
                {
                    'label': "Three normal guns at 120°",
                    'mounts': [
                        GunMount('body', 0.0, base_profile(color)),
                        GunMount('body', two_pi_thirds, base_profile(color)),
                        GunMount('body', -two_pi_thirds, base_profile(color)),
                    ],
                }
            ]
        }

    if spec_key == "heavy_cannon":
        return {
            'label': "Heavy cannon",
            'options': [
                {
                    'label': "Bigger faster bullet",
                    'mounts': [
                        GunMount('aim', 0.0, bigger_faster_profile(color)),
                    ],
                },
                {
                    'label': "Shotgun cannon",
                    'mounts': [
                        # Shotgun is represented by multiple pellets from one mount;
                        # we'll generate bullets per fire using these profiles.
                        GunMount('aim', 0.0, base_profile(color)),  # placeholder for mount direction
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
                        GunMount('aim', 0.0, sniper_profile(color)),
                        DroneSpawnerMount('body', math.pi),  # spawner at rear
                    ],
                }
            ]
        }

    # Default fallback
    return {
        'label': "None",
        'options': [{'label': "Default", 'mounts': [GunMount('aim', 0.0, base_profile(color))]}]
    }