# Architecture Overview

This document outlines the high-level architecture for the diep.io remake (non-implementation).

Components
- Client: rendering, input, HUD, interpolation, prediction (optional).
- Server: authoritative game world, physics/game loop, collision, leaderboard, matchmaking.
- Shared: message schemas, constants, utilities.
- Networking: use WebSockets or UDP (via WebRTC/data channel) per later decision.

Game loop
- Server runs authoritative tick loop advancing object positions and handling collisions.
- Clients send input deltas; server sends periodic snapshots.

Scaling notes
- Partitioning: rooms/shards per map size.
- Persistence: minimal; ephemeral world state.

Next steps (implementation): choose runtime (Node.js + ws or UDP), state sync strategy, and determinism approach.
