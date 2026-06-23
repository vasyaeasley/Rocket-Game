# Rocket Game — Orbital Launch Simulator

A compact 2D orbital launch simulator made with Pygame. Pilot a rocket from Earth, manage thrust and rotation, and use time-warp to explore orbital mechanics, atmospheres, and spheres-of-influence.

## Demo
This repository contains `main7.py` which runs the simulation. The game features:
- Multiple thruster loadouts (Dual, Quad, Octa)
- Realistic gravity using mu = G * mass
- Atmosphere drag and altitude-dependent air density
- Sphere of influence switching between bodies
- Future trajectory projection
- Minimap, telemetry, zoom, and time warp

## Installation

1. Install Python 3.10+ (recommended).
2. Install dependencies:
```bash
pip install pygame
```

3. Run the game:
```bash
python main7.py
```

## Controls

- Mouse:
  - Left click menu buttons.
  - Mouse wheel: zoom in/out while playing.

- Keyboard (in game):
  - A / D: rotate rocket left / right.
  - W: thrust (also disables time-warp while pressed).
  - < / > keys (Comma / Period): decrease / increase time warp.
  - Close window or press the window close button to exit.

UI:
- Main Menu -> Play -> Select loadout (Dual, Quad, Octa).
- Telemetry on the top-left displays current SoI, altitude, velocity, mass, zoom, and current time-warp.

## Gameplay & Mechanics

- Scaling and units:
  - The simulation converts meters ↔ pixels using a global SCALE value.
  - Gravity is computed using mu = G_CONSTANT * mass of the active body.
  - Atmospheric drag is modeled with a simplified altitude-based density and quadratic drag.

- Time warp:
  - TIME_WARP_LEVELS = [1, 5, 25, 100, 1000] — physics are sub-stepped while time-warped for stability.
  - Thrusting will immediately drop warp to 1x for safety.

- Trajectory prediction:
  - The rocket projects a future trajectory (using the currently active SOI body) and draws a line of predicted positions.

- Minimap:
  - Shows a small overview of the system and the rocket's position.

## Tweakable Constants

At the top of `main7.py` you can adjust game feel and realism:

- WIDTH, HEIGHT — window size.
- FPS — frame rate limit.
- SCALE — map scaling (meters per pixel).
- G_CONSTANT — gravitational constant (default 6.67430e-11).
- TIME_WARP_LEVELS — array of warp multipliers.
- Bodies: modify or add CelestialBody instances in `system_bodies`:
  - CelestialBody(name, x, y, radius_m, mass_kg, soi_radius_m, color, atmo_height_m=0)

Rocket tuning:
- Rocket base_mass, base_thrust, thruster mass scaling, drag_coeff, cross_section_area — see constructor in `Rocket` class.

## Known limitations / notes

- Units are mixed: physics use meters/seconds internally while positions on-screen are pixels after scaling — be careful when modifying SCALE.
- The trajectory predictor currently considers only the active SOI body (it stops when leaving the SOI).
- Atmospheric model is simplified (linear density falloff to the edge of atmosphere).
- No persistent save/menus beyond the main menu and selection screen.

## Contributing

Feel free to:
- Add more bodies (planets, moons) or import system definitions.
- Improve trajectory projection to handle multi-SOI transitions.
- Add UI for configuration and pausing.
- Implement fuel mass reduction and staging for more realistic flight dynamics.

If you'd like, open an issue or a PR with feature requests or bug fixes.

## Credits

- Author: vasyaeasley (project repository)
- Built with: Python and Pygame

## License

Add a LICENSE file for the license you'd like to use (MIT recommended if you want permissive use):

```text
MIT License
Copyright (c) 2026 <your name>

Permission is hereby granted...
```

Replace the placeholder with your preferred license text.

Enjoy piloting and refining your orbital launch simulator — tell me if you want this README committed to the repo, or if you'd like a shorter README or a more detailed developer-oriented one (with code diagrams and explanation of key functions).
