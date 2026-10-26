# RPG Dice TUI

Cinematic Baldur's Gate 3 / D&D style dice roller for the terminal. Pure Python 3 standard library,
24-bit TrueColor, double-buffered rendering. No `pip install`, just `python main.py`.

```
 ╔═ THE TABLE ════════════════════════════╗ ╭─ CHECK ──────────────────╮
 ║        shaded, spinning polyhedron     ║ │ DIE    d20           [D] │
 ║        + shadow + arcane rune ring     ║ │ DC     15          [+/-] │
 ║                                        ║ │ ROLL   Advantage     [A] │
 ║   [big total]  == CRITICAL SUCCESS ==  ║ │ MODIFIERS            [M] │
 ║   d20: 20  +3 Ability  +2 Prof  =  25  ║ │ LAST CHECK / HISTORY     │
 ╚════════════════════════════════════════╝ ╰──────────────────────────╯
```

## Run

```
python main.py          # needs a terminal of at least 90x28 cells
run.bat                 # opens a dedicated, brand-new Windows Terminal window (-w new)
run_split_pane.bat      # opens as a vertical split-pane alongside your active TUI!
.\run.ps1               # same, PowerShell launcher with -w new isolation
python test_rpg.py      # headless tests (no terminal required)
```

Use Windows Terminal (or any VT100 + TrueColor terminal) with a font that has box drawing and block
characters (Cascadia Mono, Consolas). Windows VT mode and UTF-8 are enabled via `ctypes` automatically.

## Controls

| Key | Action |
| --- | --- |
| `Space` / `Enter` | Roll |
| `D` (or `Left`/`Right`) | Cycle die: d20, d12, d10, d8, d6, d4, d100 (resets DC to a sensible default) |
| `+` / `-` (or `Up`/`Down`) | Raise / lower DC (re-evaluates the shown result live) |
| `A` | Normal, Advantage, Disadvantage (rolls two dice, keeps highest / lowest, the other is dimmed) |
| `M` | Edit modifiers: `Up/Down` pick, `Space` toggle, `Left/Right` or `+/-` adjust value / dice count, `M` or `Esc` close |
| `C` | Instant Natural 20 showcase |
| `F` | Instant Natural 1 showcase |
| `Q` / `Esc` | Quit |

## Rules (`mechanics.py`)

* Check passes when `die + modifiers >= DC`.
* Default modifiers: Ability Mod +3, Proficiency +2 (on); Guidance +1d4, Bardic Inspiration +1d6, Bless +1d4 (off).
  Bonus dice are rolled and shown individually.
* d20 only: natural 20 is a critical success (automatic pass), natural 1 a critical failure (automatic fail).
* Advantage / Disadvantage roll two dice and keep the higher / lower one.
* The outcome is decided first, then the animation lands the die exactly on the rolled face.

## Cinematics

* Roll: the die drops from above the table, bounces with decaying restitution (dust, small shake per impact),
  tumbles on a precessing axis and finally slerps onto the winning face with a slow, tense approach.
* Result reveal: natural roll first, then each modifier ticks into the big pixel-font total, then the verdict.
* **Natural 20**: golden particle explosion, shockwave, screen shake, white-gold flash, rotating light rays,
  gold-tinted die, endless sparkles.
* **Natural 1**: red/cyan glitch waves with row tearing and corrupted blocks, falling shards, shake,
  blood-dark aura, cracked red die that jitters.

## Architecture

| File | Role |
| --- | --- |
| `main.py` | `App` state machine (idle, rolling, reveal, result), layout, backdrop, panels, keyboard loop, frame timing |
| `dice_engine.py` | Rotation matrices and quaternions, polyhedra built from vertices with automatic convex-hull faces (d4, d6, d8, d10/d100 trapezohedron, d12, d20), perspective projection, bevelled flat-shaded rasteriser with specular highlight, `DiceBody` roll physics |
| `mechanics.py` | Pure game rules: `Modifier`, `RollMode`, `roll_check` -> immutable `CheckResult` |
| `particles.py` | Particle system, shockwaves, `Aura` (gold / blood), `apply_glitch`, `ScreenShake` |
| `colors.py` | Palette, lerp / gradient / HSV, cached ANSI formatters, `ScreenBuffer`, diffing `FrameWriter` |
| `test_rpg.py` | Geometry, physics, rules, rendering and effect tests |

Rendering pipeline per frame (30 FPS): copy the static backdrop (nebula, floor glow, frames, stars) into a
`ScreenBuffer`, then aura, rune ring, shadows, dice, particles, result zone, panel, glitch, flash tint and
screen shake. `FrameWriter` diffs against the previous frame and emits **one** escape string containing
only the changed cells, so there is no clearing and no flicker. Dice are drawn into a `PixelCanvas`
with two square pixels per cell (`▀` with separate foreground / background colours), doubling the vertical
resolution.
