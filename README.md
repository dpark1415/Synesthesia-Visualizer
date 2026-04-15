# Synesthesia Visualizer for TouchDesigner

A MIDI-reactive music visualizer that turns any `.mid` file into a real-time visual experience. Each instrument gets its own visual identity — glowing spheres, shockwaves, particle fields, nebula clouds, and more.

## Requirements

- **TouchDesigner** (2023.11000 or later recommended) — [download free](https://derivative.ca/download)
- A **MIDI file** (`.mid`) of the song you want to visualize

## Quick Setup (3 Steps)

### Step 1 — Build the audio analysis network
1. Open TouchDesigner
2. Open the Textport: press **Alt + P**
3. Copy the entire contents of `synesthesia_part1_setup.py` and paste it into the Textport
4. Press **Enter** and wait for `PART 1 COMPLETE` to appear

### Step 2 — Build the visual generators
1. Copy the entire contents of `synesthesia_part2_visuals.py`
2. Paste into the Textport and press **Enter**
3. Wait for `PART 2 COMPLETE`

### Step 3 — Build the scene and output
1. Copy the entire contents of `synesthesia_part3_scene.py`
2. Paste into the Textport and press **Enter**
3. Wait for `PART 3 COMPLETE`

## Loading Your Music

1. Navigate into the `/project1/synesthesia` container
2. Click on the `midi_file_in` node
3. In the parameters panel, set the **File** path to your `.mid` file
4. Press play on TouchDesigner's timeline

## Transport Controls

Paste these one-liners into the Textport:

| Action | Command |
|--------|---------|
| **Play** | `op('/project1/synesthesia/transport_timer').par.play = True` |
| **Pause** | `op('/project1/synesthesia/transport_timer').par.play = False` |
| **Restart** | `op('/project1/synesthesia/transport_timer').par.cue = True` |
| **Fullscreen** | `op('/project1/synesthesia/window_out').par.winopen = True` |
| **Exit fullscreen** | `op('/project1/synesthesia/window_out').par.winclose = True` |
| **Change file** | `op('/project1/synesthesia/midi_file_in').par.file = 'C:/path/to/song.mid'` |

## What Each Instrument Looks Like

| MIDI Channel | Instrument | Visual |
|:---:|---|---|
| 10 | Drums (kick) | Red pressure sphere with bloom |
| 10 | Drums (snare) | Cyan shockwave torus ring |
| 10 | Drums (hi-hat) | 30 bright spark particles |
| 1 | Bass | Deep blue/purple bioluminescent sphere |
| 2 | Melody | 50 gold particles in arc paths |
| 3 | Pads | 3 layered teal/violet nebula planes |
| 4 | Lead | White/gold noise-displaced ribbon |
| — | Background | 200 twinkling star particles |

## Tweaking the Visuals

- **Bloom intensity**: Adjust `bloom_threshold` Level TOP opacity
- **Trail length**: Adjust `feedback_decay` Level TOP opacity (0.85–0.95)
- **Camera speed**: Edit the orbit expressions on `cam_orbit`
- **Colour palette**: Edit the GLSL fragment shader DATs for any instrument
- **Smoothing**: Adjust lag rise/fall times on the Lag CHOPs

## Troubleshooting

- **Nothing renders**: Make sure your `.mid` file is loaded and the timeline is playing
- **Script errors**: Run the scripts in order — Part 1, then 2, then 3
- **Performance**: Lower MSAA from 4x to 2x on `render_main`, or reduce instance counts
