# diep.io — Single-player (local) project skeleton

This repository contains a skeleton layout to recreate a smaller, single-player version of a diep.io-like game. This variant is intended to run locally using Python and pygame, with bots (AI) instead of a networked server.

- Single-player: all game logic, physics, and AI run locally in the client.
- Bots: computer-controlled players (simple AI state machines) to populate matches.
- Shooter: projectile-based combat and simple collision handling.
- Small model: focus on a compact codebase and performance appropriate for educational use or quick prototyping.
Key goals of this skeleton:
- Single-player: all game logic, physics, and AI run locally in the client using a local game loop (pygame).
- Bots: computer-controlled players (simple AI state machines) to populate matches.
- Shooter: projectile-based combat and simple collision handling.
- Small model: focus on a compact codebase and performance appropriate for educational use or quick prototyping.
- Single-player: all game logic, physics, and AI run locally in the client.
- Bots: computer-controlled players (simple AI state machines) to populate matches.
- Shooter: projectile-based combat and simple collision handling.
- Small model: focus on a compact codebase and performance appropriate for educational use or quick prototyping.

Top-level structure (placeholders):
- `client/` — python client using `pygame` (main entry point, game loop, renderer, input, AI manager).
- `server/` — retained for optional headless/local engine experiments or tooling; not required for core single-player experience.
- `shared/` — constants, types and small utilities shared across modules.
- `assets/` — images, sounds, sprites.
- `docs/` — architecture, AI and gameplay design docs (includes pygame-specific notes).
- `tests/` — unit and integration test plans targeting game logic and AI.
- `scripts/` — utility scripts (run helpers, asset packers).
- `tools/` — optional editors or asset conversion tools.

See `docs/` for architecture guidance, AI design and controls and `requirements.txt` for dependencies (pygame). No implementation code is included here — these are placeholders and design notes to guide building the game.
