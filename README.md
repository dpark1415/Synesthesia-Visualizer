# Synesthesia Visualizer for TouchDesigner

A minimal MIDI-reactive visualizer. Five simple shapes — one per instrument
— pulse and glow in time with a MIDI file.

This is the **simplified rebuild**: no GLSL, no instancing, no custom
shaders. Just basic SOPs driven by Phong materials, with scale and emission
bound to per-channel activity CHOPs via parameter expressions. The goal is
something that *works* end-to-end before adding visual complexity.

## Requirements

- TouchDesigner 2025.32460 or later
- A `.mid` file

## Setup (3 steps)

Each script is self-contained and idempotent — re-running rebuilds nodes
without leaving duplicates behind.

1. Open TouchDesigner. Open the Textport with **Alt + P**.
2. Paste the entire contents of `synesthesia_part1_setup.py`, press Enter,
   wait for `PART 1 COMPLETE`.
3. Click `/project1/synesthesia/midi_file_in` and set its **File** parameter
   to your `.mid`.
4. Paste `synesthesia_part2_visuals.py`, press Enter.
5. Paste `synesthesia_part3_scene.py`, press Enter.

Middle-click the `OUT` Null TOP inside `/project1/synesthesia` to preview.

## Transport

| Action | Textport command |
|---|---|
| Play | `op('/project1/synesthesia/transport_timer').par.play = True` |
| Pause | `op('/project1/synesthesia/transport_timer').par.play = False` |
| Restart | `op('/project1/synesthesia/transport_timer').par.cue.pulse()` |
| Fullscreen | `op('/project1/synesthesia/window_out').par.winopen.pulse()` |
| Close window | `op('/project1/synesthesia/window_out').par.winclose.pulse()` |
| Change file | `op('/project1/synesthesia/midi_file_in').par.file = 'C:/path/to/song.mid'` |

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
midi_file_in -> select(ch{N}n* ch{N}c*) -> math(max) -> math(/127) -> lag -> rename
```

The `select` pattern matches both note (`n`) and CC (`c`) channels for a
given MIDI channel, so the visualizer responds to either.

## Tweaking

- **Pulse intensity**: edit the `pulse` value in the `VISUALS` table at the
  top of `synesthesia_part2_visuals.py`.
- **Smoothing**: adjust `LAG_RISE` and `LAG_FALL` at the top of
  `synesthesia_part1_setup.py`.
- **Camera speed**: change the `0.18` factor in the `cam_main` orbit
  expressions in `synesthesia_part3_scene.py`.
- **Bloom**: tweak `bloom_threshold.par.blacklevel` and
  `bloom_blur.par.size`.

## Troubleshooting

- **Nothing pulses** — confirm the `.mid` is loaded and the `transport_timer`
  is playing. Watch `activity_drums` etc. in their CHOP viewers; they should
  show non-zero values during playback.
- **Black render** — make sure the `cam_main` look-at points at `cam_target`,
  and that `render_main.par.geometry` resolves to your `*_geo` nodes.
- **Re-run a script** — safe; each script destroys what it owns before
  recreating.
