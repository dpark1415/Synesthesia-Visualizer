# Synesthesia Visualizer for TouchDesigner

A minimal MIDI-reactive visualizer. Five simple shapes — one per instrument
— pulse and glow in time with MIDI input.

No GLSL. No instancing. No DAT scripts. Just SOPs driven by Phong materials,
with scale and emission bound to per-channel activity CHOPs via parameter
expressions.

## Requirements

- TouchDesigner 2025.32460 or later
- A MIDI device, OR a `.mid` file (see *Using a MIDI file* below)

## Setup

The whole project is built by a single script with try/except around every
node creation. A failure in any one step does not stop the rest of the build,
and the script prints a summary report at the end.

1. Open TouchDesigner.
2. Open the Textport with **Alt + P**.
3. Paste the entire contents of [`synesthesia_build.py`](synesthesia_build.py)
   and press Enter.
4. Read the **BUILD REPORT** at the bottom of the Textport output. Every
   step prints `[OK]` or `[FAIL]`. Failures include the exception type,
   message, and full traceback.
5. Set `/project1/synesthesia/midi_in`'s **device** parameter on the
   MIDI Devices Mapper dialog.

Middle-click the `OUT` Null TOP inside `/project1/synesthesia` to preview.

Re-running the script is safe; it destroys `/project1/synesthesia` and
rebuilds it from a clean slate.

## Using a MIDI file instead of a live device

Replace the `midi_in` CHOP with a MIDI File In CHOP after the script
finishes:

```python
b = op('/project1/synesthesia')
b.op('midi_in').destroy()
mf = b.create(midifileinCHOP, 'midi_in')
mf.par.file = 'C:/path/to/song.mid'
```

The downstream `select_*` chains read channel-name globs, so swapping the
source CHOP is enough; nothing else needs to change.

## Transport

| Action | Textport command |
|---|---|
| Fullscreen | `op('/project1/synesthesia/window_out').par.winopen.pulse()` |
| Close window | `op('/project1/synesthesia/window_out').par.winclose.pulse()` |

## Visuals

| Instrument | MIDI channel | Shape | Colour |
|---|:---:|---|---|
| Drums | 10 | Sphere | Red |
| Bass | 1 | Sphere | Blue |
| Melody | 2 | Torus | Gold |
| Pads | 3 | Box | Teal |
| Lead | 4 | Tube | White |

Each shape's scale and emission glow are driven by `activity_<name>`, a
single-channel CHOP (0..1) produced by:

```
midi_in -> select(ch{N}n* ch{N}c*) -> math(max) -> math(/127) -> lag -> rename
```

The `select` pattern matches both note (`n`) and CC (`c`) channels for a
given MIDI channel, so the visualizer responds to either.

## Build phases

The single script is structured in three phases:

1. **Phase 1 — minimum**: container, MIDI input, drums activity chain,
   drums sphere, camera target, orbit camera, key light, render TOP. This
   is the smallest end-to-end pipeline that proves the chain works.
2. **Phase 2 — extra instruments**: bass, melody, pads, lead. Each is
   added in its own protected block.
3. **Phase 3 — extras**: OUT null TOP, window COMP, fill + rim lights.

If Phase 1 fails for any reason, Phases 2 and 3 still attempt to run, and
the **BUILD REPORT** at the end shows exactly which steps succeeded.

## Tweaking

- **Pulse intensity**: edit the per-instrument tuple in `MINIMUM` /
  `EXTRA_INSTRUMENTS` at the top of `synesthesia_build.py` (last value).
- **Smoothing**: adjust `LAG_RISE` and `LAG_FALL` at the top of the script.
- **Camera speed**: change the `0.18` factor in the `cam_main` orbit
  expressions.

## Verified API references

Every parameter name and method used by the script is taken from the
official TouchDesigner documentation:

- [CHOP_Class](https://docs.derivative.ca/CHOP_Class)
- [OP_Class](https://docs.derivative.ca/OP_Class)
- [MidiinCHOP_Class](https://docs.derivative.ca/MidiinCHOP_Class)
- [Geometry_COMP](https://docs.derivative.ca/Geometry_COMP)
- [Camera_COMP](https://docs.derivative.ca/Camera_COMP)
- [Light_COMP](https://docs.derivative.ca/Light_COMP)
- [Render_TOP](https://docs.derivative.ca/Render_TOP)
- [Phong_MAT](https://docs.derivative.ca/Phong_MAT)
