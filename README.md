## Tank Game — Pygame Project

This repository contains a single‑player top‑down tank shooter built with **Python** and **pygame**. The most up‑to‑date implementation lives in `Tank_Game_mkIV/` and includes:

- Player‑controlled tank with upgrades and specializations
- AI‑controlled enemy tanks that orbit, avoid clustering, and shoot at the player
- Projectiles, health, experience, and level progression

Older experimental versions (`Tank_Game_mkI`, `Tank_Game_mkII`, `Tank_Game_mkIII`, `Tank Game/`) have been cleaned up so that `Tank_Game_mkIV` is the main codebase.

---

## 1. Prerequisites

- **Python**: 3.10+ (tested with 3.12 / 3.13 on Windows)
- **pip**: Python package manager
- **pygame**: installed via `pip` (see below)

Optional but recommended:
- A virtual environment to isolate dependencies

---

## 2. Setup Instructions

From the repository root (this folder), run the following in **PowerShell**:

```powershell
cd "C:\Users\kitty\OneDrive\Pictures\Screenshots\New folder\New folder (2)\ECE160_diep.io"

# (Optional) create and activate a virtual environment
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The `requirements.txt` should include at least:

```text
pygame>=2.1
```

If you are not using a virtual environment, you can omit the `venv` lines and run the `pip` commands directly.

---

## 3. How to Run the Game

The main entry point for the latest version is `Tank_Game_mkIV/game.py`.

From the **repository root**:

```powershell
# Using the Windows Python launcher (recommended)
py "Tank_Game_mkIV\game.py"

# Or, using an explicit Python interpreter
python "Tank_Game_mkIV\game.py"
```

If you prefer to run from inside the folder:

```powershell
cd "Tank_Game_mkIV"
py game.py
```

When the window opens:

- Use **WASD** to move
- Use **mouse** to aim and **left click** to shoot
- Follow on‑screen HUD text for upgrades and controls

---

## 4. Project Structure (relevant parts)

- `Tank_Game_mkIV/`
	- `config.py` — screen size, colors, tuning constants
	- `core.py` — `Tank`, `Bullet`, and related gameplay classes
	- `ai_helpers.py` — bot movement and steering behavior
	- `upgrades.py` — data for upgrade and specialization trees
	- `game.py` — main pygame loop, spawning, input, rendering
- `assets/` — images and sounds used by the game (if any)
- `requirements.txt` — Python dependencies (including `pygame`)

Other folders (like `presentation/`, `docs/`) contain documentation and slides used during development and are not required to run the game.

---

## 5. Troubleshooting

**`ModuleNotFoundError: No module named 'pygame'`**
- Ensure you installed requirements:
	```powershell
	python -m pip install -r requirements.txt
	```

**Python not found / Microsoft Store prompt**
- Use the Windows Python launcher instead:
	```powershell
	py "Tank_Game_mkIV\game.py"
	```

**PowerShell blocks venv activation**
- Allow scripts for this session only, then re‑run activate:
	```powershell
	Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
	.\.venv\Scripts\Activate.ps1
	```

If you hit any other error, copy the full traceback and command you ran so it can be debugged quickly.
