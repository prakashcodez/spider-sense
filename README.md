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
| **A / D** or **← / →** | Move / Run along rooftops |
| **W / ↑ / Space** | Jump (Double Jump supported while in air) |
| **Hold Left Mouse** or **Shift** | **Web-Swing from ANYWHERE!** (Attaches to sky/buildings/anchors) |
| **Hold W / Up / Space (while swinging)** | **Pump Upward & Climb Higher** on web line for massive height |
| **F** | Fire **Web-Shot** (Stuns nearest enemy in a web cocoon for 2.5s) |
| **Hold E** | **Interact** (Free trapped civilians / Defuse pumpkin bombs / Enter Extraction) |
| **P** | Pause / Resume patrol |
| **R** | Restart current mission |
| **Esc** | Return to Main Menu |

---

## ⚙️ Core Mechanics & Updates

1. **Dynamic High-Flying Web-Swinging**:
   - Click and hold **Left Mouse** or **Shift** from **anywhere on the map** to shoot a web line into the overhead skyline and swing with authentic pendulum physics.
   - Hold **W** or **Space** while swinging to reel in and gain incredible height, soaring far above city skyscrapers!
   - Releasing the swing converts your angular momentum into an exhilarating high-speed launch jump.
2. **Unlimited Web Fluid**:
   - Web Fluid is now completely **unlimited** (`∞`).
   - Swing as much as you like and fire web-shots freely without running empty.
   - Blue canisters along rooftops now reward **+50 bonus score** and shiny web sparkle particles.
3. **No Fall Damage & Automatic Web Rescue**:
   - Falling off rooftops **never damages Spider-Man or costs hearts**!
   - If you fall below the buildings, an automated safety web instantly fires (`"WEB RESCUE! THWIP!"`) and catapults Spider-Man right back onto the solid rooftop ledge with a heroic flip.
   - Health hearts are **only reduced when enemies attack** (thug melee strikes, drone lasers, and pumpkin bombs).
4. **Auto-Scaled High-Res Title Art**:
   - The title screen dynamically detects image dimensions and cleanly auto-scales high-res and 4K title art (such as 3840×2160) to fit the canvas, centered with comic title banners and buttons.
5. **Seamless Parallax Night Skyline**:
   - Parallax background layers (`bg_far` and `bg_mid`) tile continuously without black voids, providing a living, scrolling comic-book cityscape.
6. **Safe Level Termination**:
   - Every mission ends on a massive 1200 px wide extraction rooftop backed by a towering skyscraper barrier, ensuring players cannot fall off the end of the world.
