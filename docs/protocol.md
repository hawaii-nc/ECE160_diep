# Network Protocol (overview)

This file describes message intent and data shapes at a conceptual level (no code).

Message categories
- Connection: handshake, auth (optional), join/leave.
- Input: client -> server, contains player input (direction, actions) with timestamp or sequence.
- Snapshot: server -> client, periodic world state updates (players, bullets, items).
- Events: spawn, death, leaderboard updates.

Design considerations
- Use simple, compact binary or JSON messages; choose after performance testing.
- Include sequence IDs and timestamps to allow interpolation and reconciliation.
