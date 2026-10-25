# COLLEGE EXPERIMENT RECORD / PROJECT REPORT

**Course Title:** Python Programming for Design  
**Project Title:** WEBLINE: Night Patrol — 2D Side-Scrolling Action Platformer  
**Primary Source File:** [`webline.py`](file:///c:/CODING%20FILES/PYTHON%20PROJECT/webline.py)  
**Documentation:** [`README.md`](file:///c:/CODING%20FILES/PYTHON%20PROJECT/README.md)  
**Programming Language:** Python 3 (Standard Library Only: `tkinter`, `random`, `math`, `os`, `time`)  

---

## 1. AIM & OBJECTIVES

### 1.1 Aim
To design, architect, and implement a complete 2D side-scrolling action platformer game titled **"WEBLINE: Night Patrol"** using Python 3 and Tkinter without third-party game frameworks (e.g., Pygame, Arcade, Pillow), demonstrating principles of event-driven programming, real-time physics simulations, object-oriented software engineering, mathematical vector character rendering, procedural level generation, and canvas-based user interface design.

### 1.2 Learning Objectives
1. **Event-Driven Programming**: Implement an asynchronous, non-blocking render loop running at ~50 FPS using `root.after(20)` with deterministic timer cleanup.
2. **Vector Graphic Synthesis**: Render an articulate superhero character (Spider-Man) solely using mathematical geometry, trigonometric oscillations, and canvas primitives without raster sprite sheets.
3. **Physics & Kinematic Simulation**: Formulate Newtonian gravity, terminal velocity, horizontal acceleration/friction, and pendulum angular dynamics ($d^2\theta = -\frac{g}{L}\sin\theta$) converted into launch kinetic energy.
4. **Collision Detection & Spatial Geometry**: Implement Axis-Aligned Bounding Box (AABB) collisions, radial proximity thresholds, and directional head-stomp logic.
5. **Finite State Machine (FSM)**: Architect a robust state machine managing Title, Controls, Briefing, Gameplay, Pause, Victory, Defeat, and Finale screens.
6. **Procedural Content Generation**: Algorithmatically generate dynamic skyscraper levels with balanced gap spacing, camera boundaries, and safety landing zones.
7. **Predictive Telegraph Mechanics**: Construct a real-time warning system ("Spider-Sense") that calculates impending threats and visually alerts the player before damage occurs.

---

## 2. SYSTEM SPECIFICATIONS & TECH STACK

- **Operating Platform**: Standard PC / Lab workstation running Windows, macOS, or Linux.
- **Language**: Python 3.8+ (Tested on Python 3.14).
- **Required Libraries**: None (Zero external dependencies).
  - `tkinter`: Windowing, Canvas rendering, and event binding.
  - `random`: Procedural seeding and hazard distributions.
  - `math`: Trigonometry (`sin`, `cos`, `atan2`, `hypot`, `radians`).
  - `os`: File system path resolution and directory traversal.
  - `time`: High-resolution mission elapsed time calculations.
- **Display Resolution**: 960 × 540 pixels (16:9 widescreen canvas).
- **Target Frame Rate**: ~50 Updates Per Second (20 ms tick interval).

---

## 3. THEORETICAL BACKGROUND & COMPUTER SCIENCE CONCEPTS

### 3.1 Event-Driven Programming & The Tkinter Loop
Traditional procedural code runs sequentially from top to bottom. In real-time graphical applications, an **event-driven model** is required:
- The Tkinter `root.mainloop()` serves as the core event dispatcher, listening for keyboard presses (`<KeyPress>`, `<KeyRelease>`) and mouse actions (`<Motion>`, `<ButtonPress-1>`, `<ButtonRelease-1>`).
- To achieve smooth animation without freezing the user interface, execution is driven by `root.after(TICK_MS, callback)`.
- **Timer Hygiene**: When transitioning between game states (e.g., Pausing, Restarting, or Completing a Mission), the scheduled callback ID must be explicitly cancelled using `root.after_cancel(self.loop_id)`. Failing to cancel leads to multiple simultaneous game loops running concurrently ("ghost loops"), which causes severe frame drops and velocity duplication.

### 3.2 Physics Simulation & Pendulum Mechanics
The game employs discrete-time Euler integration for character motion:
1. **Linear Kinematics**:
   $$\mathbf{x}_{t+1} = \mathbf{x}_t + \mathbf{v}_x$$
   $$\mathbf{v}_{y, t+1} = \min(\mathbf{v}_{y, t} + g, v_{\text{max}})$$
   $$\mathbf{v}_{x, t+1} = \mathbf{v}_{x, t} \cdot \mu_{\text{decel}}$$
2. **Pendulum Web-Swinging Dynamics**:
   When the player attaches a web to an overhead anchor $(x_a, y_a)$, motion transitions from Cartesian coordinates to polar coordinates:
   $$\theta = \text{atan2}(x_p - x_a, y_p - y_a)$$
   $$L = \sqrt{(x_p - x_a)^2 + (y_p - y_a)^2}$$
   The angular acceleration $\alpha$ is governed by the simple pendulum differential equation:
   $$\alpha = \frac{d^2\theta}{dt^2} = -\frac{g}{L} \sin(\theta)$$
   $$\omega_{t+1} = (\omega_t + \alpha) \cdot \mu_{\text{damping}}$$
   $$\theta_{t+1} = \theta_t + \omega_{t+1}$$
   Cartesian position is reconstructed at every step:
   $$x_p = x_a + L \sin(\theta)$$
   $$y_p = y_a + L \cos(\theta)$$
3. **Launch Momentum Conversion**:
   Upon releasing the web line, tangential linear velocity is calculated and boosted:
   $$v_{\text{tangent}} = L \cdot \omega \cdot \beta_{\text{boost}}$$
   $$v_x = v_{\text{tangent}} \cos(\theta)$$
   $$v_y = -|v_{\text{tangent}} \sin(\theta)| - v_{\text{lift}}$$

### 3.3 Vector Character Animation (Pure Code Rendering)
Rather than relying on static raster bitmap frames, Spider-Man is drawn mathematically via `draw_hero()`:
- **Head & Webbing**: An ellipse with intersecting polar grid lines and angular polygons for the white eye lenses.
- **Sinusoidal Locomotion**: During the running state, limb rotation angles follow sinusoidal curves:
  $$\text{Offset} = A \cdot \sin(\omega \cdot t)$$
  The left and right legs oscillate in anti-phase ($180^\circ$ apart), providing natural running strides.
- **Coordinate Transformation**: Horizontal mirroring is achieved via a localized scalar multiplier $\text{facing} \in \{-1, +1\}$.
- **Rotational Articulation**: During swinging, whole-body rotation is calculated using a 2D rotation matrix:
  $$\begin{bmatrix} x' \\ y' \end{bmatrix} = \begin{bmatrix} \cos(\theta) & -\sin(\theta) \\ \sin(\theta) & \cos(\theta) \end{bmatrix} \begin{bmatrix} x_{\text{local}} \\ y_{\text{local}} \end{bmatrix}$$

### 3.4 Multi-Layer Parallax Scrolling
To create an authentic illusion of spatial depth in a 2D environment, the background is divided into three distinct layers moving at different relative speeds:
- **Layer 1 (Far Skyline)**: $v_{\text{far}} = 0.15 \cdot v_{\text{cam}}$ (distant skyscrapers, glowing moon, stars).
- **Layer 2 (Mid Skyline)**: $v_{\text{mid}} = 0.42 \cdot v_{\text{cam}}$ (rooftop water towers and neon silhouette buildings).
- **Layer 3 (Foreground Platforms)**: $v_{\text{fore}} = 1.0 \cdot v_{\text{cam}}$ (active collision rooftops, interactive objects, and characters).
- **Continuous Tiling Formulation**: To prevent black screen gaps, the horizontal tile offset is computed using:
  $$\text{start}_x = -(\lfloor \mathbf{x}_{\text{cam}} \cdot f \rfloor \pmod W)$$
  The engine renders repeating tiles across $[\text{start}_x, \text{CanvasWidth} + W]$ to ensure 100% continuous coverage.

---

## 4. SYSTEM ARCHITECTURE & CODE MODULES

The application is structured into modular components:

```
┌──────────────────────────────────────────────────────────────┐
│                    Master Tkinter Canvas                     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
       ┌─────────────────┐           ┌─────────────────┐
       │   AssetCache    │           │ Game Controller │
       │ (Auto-Scaling)  │           │ (Finite State)  │
       └─────────────────┘           └────────┬────────┘
                                              │
         ┌───────────────────┬────────────────┼───────────────────┐
         ▼                   ▼                ▼                   ▼
  ┌──────────────┐   ┌──────────────┐  ┌──────────────┐    ┌──────────────┐
  │ Player Class │   │ Enemy Roster │  │ Particle &   │    │  Procedural  │
  │  (Kinematics,│   │  (Subclasses:│  │ Comic Popup  │    │  Generator   │
  │   Swinging)  │   │  Thug, Drone,│  │   Managers   │    │  (Level Gen) │
  └──────────────┘   │  Bomber, etc)│  └──────────────┘    └──────────────┘
                     └──────────────┘
```

### 4.1 `AssetCache` Class
- **Purpose**: Safely loads PNG graphics using standard `tk.PhotoImage` while preventing crashes if an image file is absent.
- **Dynamic Downscaling**: Checks image width and height against target limits (`max_w`, `max_h`). If an asset (such as the 4K `title_art.png` at 3840 × 2160) exceeds the window, it calculates integer subsample factors ($x_f = 4, y_f = 4$) and invokes `img.subsample(xf, yf)` in pure Python.

### 4.2 `Player` Class
- **State Fields**: Position $(x, y)$, Velocity $(v_x, v_y)$, Facing Direction, Coyote Timer, Double-Jump Flag, Invincibility Timer, Pose Identifier.
- **`attach_swing(anchors)`**: Searches for nearest overhead anchor within 440 px. If none exists, dynamically creates an overhead sky anchor so the player can swing from anywhere.
- **`release_swing()`**: Calculates launch velocity with kinetic boost and restores double-jump eligibility.
- **`respawn_at_safe()`**: Catapults the player upward onto the last safe platform if they fall below the buildings without deducting player hearts.

### 4.3 `Enemy` Hierarchy & Subclasses
- **`Enemy` (Base)**: Maintains spatial coordinates, stun state timer, and renders web cocoons when hit by web-shots.
- **`StreetThug`**: Roof-bound patrol adversary that detects player proximity and lunges. Defeated instantly when stomped from above ($v_y > 1.2$).
- **`SentryDrone`**: Aerial hovering drone with trigonometric vertical bobbing. Charges a red targeting laser telegraph for 32 ticks before firing a high-intensity energy beam.
- **`GoblinBomber`**: Oscillates overhead on a jet glider, dropping pumpkin bombs with flashing ground impact danger rings.
- **`HunterDrone`**: Boss pursuer active in Mission 5 that continuously scrolls from the left edge of the screen.

### 4.4 `MissionManager` & Data Schema
Missions are structured as immutable dictionary data structures:
```python
MISSIONS = [
    {
        "id": 1,
        "title": "Rooftop Rescue",
        "length": 5200,
        "desc": "Locate and free 3 trapped civilians by holding [E]...",
        "target_type": "civilian",
        "target_count": 3,
        "thugs": 8, "drones": 0, "bombers": 0, "hunter": False,
        "par_time": 75
    },
    # Missions 2 through 5...
]
```

---

## 5. ALGORITHM & STEP-BY-STEP PROCEDURE

### Step 1: Program Startup & Resource Initialization
1. Initialize Tkinter root window and create the master `tk.Canvas(width=960, height=540)`.
2. Instantiate `AssetCache` and load all available PNG assets (`title_art`, `bg_far`, `bg_mid`, `icons`, `logo`). Apply automatic subsampling if resolution exceeds canvas bounds.
3. Configure default font mappings (fallbacks: `Impact` $\rightarrow$ `Arial Black` $\rightarrow$ `Arial`).

### Step 2: Input Binding & Event Dispatching
1. Bind global keyboard listeners: `<KeyPress>` sets key dictionary flags to `True`; `<KeyRelease>` clears them.
2. Bind mouse motion and click events on Canvas: `<ButtonPress-1>` initiates web-swinging; `<ButtonRelease-1>` triggers swing release.
3. Establish state-dependent hotkeys (`Esc` for menu, `P` for pause, `R` for restart, `F` for web-shot, `E` for interaction).

### Step 3: State Machine & Screen Flow
1. Set initial state to `"TITLE"`.
2. Clear active canvas items and registered interactive button bounds.
3. Draw background artwork, comic title logo, and Canvas-rendered buttons (`[START PATROL]`, `[HOW TO PLAY]`, `[EXIT]`).

### Step 4: Level Generation (Mission Start)
1. Initialize random number generator with a deterministic seed: `seed = 100 + mission_idx * 17`.
2. Build sequential rooftop platform chain $(x, y, w, h)$ with widths between 450 px and 700 px.
3. Place overhead anchor structures (lamp posts, construction cranes, billboards) across gaps.
4. Construct a final 1200 px wide extraction platform with a skyscraper barrier wall.
5. Populate mission objective items (civilians, chips, bombs, gate) and patrol enemies.

### Step 5: Frame Loop Execution (`game_loop`)
1. Increment frame counter: `self.tick_count += 1`.
2. Read player input flags and update kinematics (running acceleration, friction, gravity).
3. If web-swinging is active, solve the pendulum angular acceleration equation and update coordinates.
4. Test rooftop surface collision: if player's feet intersect roof surface while falling ($v_y \ge 0$), snap player to roof height, zero out vertical velocity, and set `on_ground = True`.

### Step 6: Fall Protection & Web Rescue
1. Check if player vertical position exceeds screen bounds ($y > 510$).
2. If true, execute `respawn_at_safe()`: deploy a visual web catch line, emit white web particles, and boost player velocity upward ($v_y = -11.0$) onto the solid ledge.
3. Preserve player hearts (no damage on falling).

### Step 7: Camera Tracking & View Cull
1. Compute target camera position: `target_cam_x = player.x - CANVAS_WIDTH * 0.35`.
2. Apply smooth exponential damping: `cam_x += (target_cam_x - cam_x) * 0.12`.
3. Filter all background and enemy rendering routines to skip items outside `[cam_x - 260, cam_x + CANVAS_WIDTH + 260]`.

### Step 8: Combat & Collision Checks
1. Stomp check: If player downward velocity is positive ($v_y > 1.2$) and intersects the top of a Street Thug, defeat the thug, award +25 points, trigger comic popup `"POW!"`, and bounce player upward ($v_y = -10.0$).
2. Melee & projectile check: If enemy attacks connect and player invincibility timer is zero, deduct 1 heart, initiate 75-tick invincibility blinking, and shake the camera.

### Step 9: Predictive Spider-Sense Detection
1. Scan for incoming threats: Drone laser lock timer $> 12$, falling pumpkin bomb distance $< 120$ px, or charging thug melee distance $< 70$ px.
2. If any condition evaluates to `True`, activate Spider-Sense:
   - Render pulsing concentric red rings around Spider-Man's head.
   - Draw electric spidey-sense lightning arcs.
   - Render directional triangular arrows at screen borders pointing toward off-screen threats.

### Step 10: Canvas-Only UI & Slanted HUD Rendering
1. Render slanted health panel containing 5 Spider-Badge heart icons.
2. Render slanted web-fluid cartridge gauge showing `∞ UNLIMITED`.
3. Render live mission objective tracker panel and countdown timer.
4. Render score tally and multiplier combo badge (`COMBO x2`, `COMBO x3`).
5. Render contextual interaction wheel when holding `[E]` near objectives.

### Step 11: Particle & Comic Popup Updates
1. Update active particle velocities and lifetimes; remove expired particles to maintain budget ($\le 80$).
2. Advance rising comic popups (`"THWIP!"`, `"POW!"`, `"WHAM!"`, `"CLOSE CALL!"`); draw with drop shadows.

### Step 12: Frame Rescheduling
1. Call `root.after(20, self.game_loop)` to schedule the next frame precisely after 20 milliseconds (~50 FPS).

---

## 6. TEST CASES & VALIDATION RESULTS

| Test Case ID | Test Description | Input Condition | Expected Behavior | Observed Result | Pass / Fail |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | Python 3 Lab PC Compatibility | `python webline.py` | Runs with zero external package imports (no Pillow, pygame) | Executed cleanly in standard library Python 3 | **PASS** |
| **TC-02** | 4K Title Art Handling | Load 3840 × 2160 PNG | Auto-downscale to 960 × 540 without UI overflow or crash | Scaled down via `subsample(4, 4)` and centered | **PASS** |
| **TC-03** | Parallax Background Tiling | Continuous horizontal scroll | Sky and mid-skyline repeat seamlessly without black voids | 100% full-screen coverage across all camera coordinates | **PASS** |
| **TC-04** | Dynamic Web-Swinging | Left Click anywhere | Web line attaches to sky/anchor and swings with pendulum physics | Attached smoothly and launched forward | **PASS** |
| **TC-05** | Swing Height Pumping | Hold `W` or `Space` while swinging | Reel in web line and gain vertical height | Spider-Man climbed up web line and soared higher | **PASS** |
| **TC-06** | Web Fluid Availability | Swing and fire web-shot | Fluid never runs out; web-shots always available | Meter displays `∞ UNLIMITED`; shot fires uninterrupted | **PASS** |
| **TC-07** | Fall Safety Net | Player falls below rooftop ledge | Automatic web rescue without heart loss | Catapulted back onto roof ledge; hearts remained intact | **PASS** |
| **TC-08** | Stomp Mechanics | Fall onto thug with $v_y > 1.2$ | Thug knocked out, player bounces up, +25 score | `"POW!"` popup appeared; bounce achieved | **PASS** |
| **TC-09** | Spider-Sense Alert | Drone aims laser at player | Pulsing red rings and edge arrows appear before beam fires | Red warning rings flashed; telegraph visible | **PASS** |
| **TC-10** | Level Boundary Safety | Reach end of Mission | Final extraction roof has barrier wall; no falling off map | Solid wall stopped player; extraction portal active | **PASS** |
| **TC-11** | Reset & State Hygiene | Restart mission 10 times consecutively | No duplicate game loops or frame rate deterioration | Frame rate stable at ~50 FPS with clean timer cleanup | **PASS** |

---

## 7. SAMPLE CORE CODE IMPLEMENTATION

### 7.1 Dynamic Pendulum Web-Swinging Algorithm
```python
def attach_swing(self, anchors):
    """Attaches web to the nearest anchor OR dynamically casts web to the sky."""
    if self.is_swinging:
        return False

    best = None
    best_dist = 999999
    for a in anchors:
        dx = a.x - self.x
        dy = a.y - self.y
        dist = math.hypot(dx, dy)
        if dist <= SWING_ATTACH_RADIUS and dy < 25 and (dx * self.facing >= -60):
            if dist < best_dist:
                best_dist = dist
                best = a

    # If no preset anchor is nearby, shoot web up to the overhead skyline!
    if not best:
        sky_x = self.x + (150 * self.facing)
        sky_y = max(30.0, self.y - 280.0)
        best = AnchorPoint(sky_x, sky_y, kind="sky")

    self.is_swinging = True
    self.swing_anchor = best
    dx = self.x - best.x
    dy = self.y - best.y
    self.swing_len = max(140.0, math.hypot(dx, dy))
    self.swing_angle = math.atan2(dx, dy)
    
    # Initial forward angular velocity
    init_spd = max(4.5, abs(self.vx) + 2.5) * self.facing
    self.swing_dtheta = (init_spd * math.cos(self.swing_angle)) / self.swing_len
    self.can_double_jump = True
    return True
```

### 7.2 Seamless Background Parallax Tiling Formula
```python
# Layer 1: Far Parallax Skyline
bg_far = self.assets.get("bg_far")
if bg_far:
    bg_far_w = bg_far.width()
    start_far = - (int(self.cam_x * 0.15) % bg_far_w)
    for x in range(start_far, CANVAS_WIDTH + bg_far_w, bg_far_w):
        self.canvas.create_image(x + ox, oy, image=bg_far, anchor=tk.NW)

# Layer 2: Mid-Distance City Buildings
bg_mid = self.assets.get("bg_mid")
if bg_mid:
    bg_mid_w = bg_mid.width()
    start_mid = - (int(self.cam_x * 0.42) % bg_mid_w)
    for x in range(start_mid, CANVAS_WIDTH + bg_mid_w, bg_mid_w):
        self.canvas.create_image(x + ox, oy, image=bg_mid, anchor=tk.NW)
```

---

## 8. VIVA-VOCE / PROJECT PRESENTATION Q&A

**Q1: Why did you choose Tkinter instead of Pygame for an action platformer?**  
*Answer:* Standard college lab environments often restrict installing third-party packages like Pygame or Pillow. Building the entire engine directly in standard library Tkinter proves that sophisticated physics simulation, vector character animation, and responsive controls can be achieved purely using core Python without external libraries.

**Q2: How is the game loop maintained without blocking the UI?**  
*Answer:* By utilizing Tkinter's asynchronous scheduling function `root.after(20, callback)`, the engine updates physics and redraws canvas entities every 20 milliseconds (~50 FPS) while allowing the underlying window manager to process input events smoothly.

**Q3: How do you prevent ghost loops or memory leaks when restarting missions?**  
*Answer:* Every state transition explicitly calls `root.after_cancel(self.loop_id)` to cancel pending frame executions before starting a new state. Furthermore, particles are strictly capped at 80 items and off-screen objects are culled beyond 260 px.

**Q4: How does the pendulum web-swinging physics work mathematically?**  
*Answer:* When attached, the player's Cartesian position $(x, y)$ is converted to polar angle $\theta$ and length $L$. Each frame, angular acceleration $\alpha = -\frac{g}{L} \sin(\theta)$ is added to angular velocity with slight damping. Upon release, angular momentum is converted into linear launch velocity using $v_x = L \omega \cos(\theta)$ and $v_y = -|L \omega \sin(\theta)|$.

**Q5: How does the Spider-Sense telegraph system work?**  
*Answer:* The engine scans for impending threats in advance (e.g., drone laser lock timer $> 12$ ticks, falling bomb distance $< 120$ px, or thug attack charge $< 70$ px). When detected, it draws pulsing red warning rings around Spider-Man and screen-edge directional arrows, giving the player a split-second window to dodge before damage occurs.

---

## 9. CONCLUSION & RESULT

The project **"WEBLINE: Night Patrol"** was successfully developed, tested, and validated. It meets all technical, aesthetic, and functional design requirements:
- Runs standalone on any standard Python 3 installation using only built-in modules.
- Employs an authentic 2D comic-book visual design with slanted HUD panels, halftone textures, and floating onomatopoeic popups.
- Demonstrates advanced object-oriented design, discrete event simulation, trigonometric vector rendering, and procedural generation.
- Delivers responsive controls with dynamic web-swinging from anywhere, height pumping, unlimited web fluid, and automated fall safety.
