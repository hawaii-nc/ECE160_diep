# Pygame Notes & Implementation Guidance

This document contains practical notes for implementing the game with `pygame`.

Environment
- Target Python 3.10+.
- Install with `pip install -r requirements.txt` (contains `pygame`).

Window & rendering
- Prefer a single canvas (pygame.Surface) for the main world.
- Use integer coordinates for blits where possible; keep high-precision positions internally.
- Consider a fixed timestep for physics (e.g., 60 Hz) and variable render updates.

Main loop sketch (conceptual)
- Initialize pygame, load assets
- Create world and entities
- While running:
  - Process input events (keyboard/mouse)
  - Update game logic (fixed ticks)
  - Update AI and projectiles
  - Render the world and HUD
  - Flip the display and cap framerate

Performance tips
- Batch draw calls by grouping layers.
- Use simple shapes for prototype (circles/rects) and swap for sprites later.
- Limit number of active projectiles or implement lifecycle pooling.

Running locally
- A simple run script will call `python -m client.main` (or `python client/main.py`) once implemented.

No implementation code is included here — these are notes to guide later development.
