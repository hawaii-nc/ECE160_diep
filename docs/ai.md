# AI / Bot Design (overview)

This document outlines a compact approach to adding bots to the single-player diep.io-like game.

Goals
- Lightweight AI: predictable, cheap to compute, fun to play against.
- Multiple difficulty tiers via parameter tweaks.
- Behavior driven by simple state machines and steering behaviors.

Bot architecture (conceptual)
- State machine states: Idle, SeekFood, AttackPlayer, Flee, Wander.
- Perception: short-range radial queries against nearby entities.
- Steering: combine seek/evade behaviors for movement; simple velocity integration.
- Shooting: aim at player or nearest enemy with configurable accuracy and fire-rate.

Difficulty tuning
- Reaction time: input delay simulation.
- Aim jitter: introduce angular noise to aiming.
- Aggression: preference for attacking vs farming.

Spawning
- Spawn bots around the player to ensure varied engagements.
- Control population size based on map size and performance.

Notes
- Keep the AI deterministic per tick for easier testing.
- For complex behaviors, consider behavior trees or utility AI later.
