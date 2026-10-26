# WEBLINE: Night Patrol

A 2D comic-book side-scrolling action platformer built in Python and Tkinter for the **Python Programming for Design** course.

---

## 🎮 How to Run

Ensure Python 3 is installed. No third-party packages (Pillow, Pygame, etc.) are required.

```bash
python webline.py
```

---

## 🕹️ Hero Controls

| Key / Input | Action |
| :--- | :--- |
| **A / D** or **← / →** | Move / Run along rooftops / Pump swing momentum |
| **W / ↑ / Space** | Jump (Double Jump supported in air) / Reel-in swing for height |
| **Hold Left Mouse** or **Shift** | **Authentic Pendulum Web-Swing** (Hold to swing, Release to launch!) |
| **Right Mouse** or **C / V / Q** | **Direct Combat Attack** (Melee Punch/Kick Combos & Web-Strike Zip Attacks!) |
| **F** | Fire **Web-Shot** (Stuns nearest enemy in a web cocoon for 2.5s) |
| **Hold E** | **Interact** (Free trapped civilians / Defuse pumpkin bombs / Crouch) |
| **P** | Pause / Resume patrol |
| **R** | Restart current mission |
| **Esc** | Return to Main Menu |

---

## ⚙️ Core Mechanics & Features

1. **Direct Combat Attack & Web-Strike (Right Click / C)**:
   - **Melee Combo (within 95 px)**: Execute high-speed punches and roundhouse kicks that stun thugs, shatter drone lock-on systems, deflect aerial hazards, and knock enemies backward with comic popups (`"POW!"`, `"WHAM!"`, `"KAPOW!"`, `"CRUNCH!"`).
   - **Web-Strike Zip Attack (95 to 280 px)**: Target distant enemies with a high-speed web tether and zip directly across gaps to strike them with a flying kick, closing distances instantly.
2. **Dense Physical Rooftop Poles & Authentic Pendulum Swinging**:
   - The city skyline is populated with real, physical structures rooted directly onto rooftops every 120–180 px: **black steel streetlights**, **red construction derrick cranes**, **radio antennas with beacons**, **Art Deco spires**, and **NYC wooden water towers**.
   - Swings simulate real gravitational pendulum physics ($\alpha = -\frac{g}{L} \sin \theta$): Spider-Man dives rapidly down through the arc, builds kinetic speed, and swoops upward toward a high crest.
   - Pumping with **A/D** accelerates swing velocity, while holding **W/Space** reels in the web line for extreme vertical launches.
3. **Level 2 Rebalancing & Dodgeable Laser Telegraph**:
   - Oscorp Sentry Drones track Spider-Man with a dotted red aiming laser, then **lock aim in place** for 14 frames (280ms) with a solid red beam and target reticle, giving players a fair telegraph window to jump or swing out of harm's way.
   - Laser hit detection utilizes true perpendicular point-to-line-segment math, eliminating artificial circular damage hitboxes.
   - Drone density in Mission 2 is rebalanced from 7 down to 4 drones.
4. **Health Medkit Pickups**:
   - Green-glowing emergency first-aid crates are distributed across rooftops.
   - Collecting a medkit restores **+2 health hearts** (up to maximum) with healing sparkle FX and `"+2 HEARTS!"` floating indicators.
5. **Unlimited Web Fluid (`∞`)**:
   - Web Fluid is completely unlimited, allowing non-stop acrobatic web-slinging and rapid web-shots.
   - Canisters along rooftops award **+50 bonus score** and comic sparkles.
6. **No Fall Damage & Automatic Web Rescue**:
   - Falling off rooftops never damages Spider-Man or costs hearts!
   - Automated safety webs catch Spider-Man (`"WEB RESCUE! THWIP!"`) and catapult him back onto the roof with an upward flip.
7. **Auto-Scaled High-Res Title Art**:
   - The title screen dynamically detects image dimensions and cleanly auto-scales high-res and 4K title art (such as 3840×2160) to fit the canvas, centered with comic title banners and buttons.
8. **Seamless Parallax Night Skyline**:
   - Parallax background layers (`bg_far` and `bg_mid`) tile continuously without black voids, providing a living, scrolling comic-book cityscape.
9. **Safe Level Termination**:
   - Every mission ends on a massive 1200 px wide extraction rooftop backed by a towering skyscraper barrier, ensuring players cannot fall off the end of the world.
