# Makeup Atelier for Krita

Eleven brushes for painting and blending makeup on portraits. The ten application brushes use grayscale alpha masks and paint with your current foreground color. Soft Focus Blender mixes pigment from the active layer.

## Install and use

Import [Makeup Atelier.bundle](<Makeup Atelier.bundle>) from **Settings → Manage Resource Libraries → Import**. Pick the **Makeup Atelier** tag in the Brush Presets docker, or search for `Makeup -`.

| Preset | Start here | Default size |
| --- | --- | ---: |
| Foundation Sponge | Tap and lift to leave porous coverage where dabs meet. | 145 px |
| Powder Veil | Sweep lightly across a broad area to soften the edge of an application. | 205 px |
| Petal Blush | Build color in short, overlapping sweeps across the cheek. | 195 px |
| Sun Freckles | Place a few staggered dabs. Vary stylus pressure or brush size to change cluster scale. | 155 px |
| Eyeshadow Feather | Sweep along the crease. The elongated tip follows the stroke. | 110 px |
| Wing Liner | Use pen pressure to taper a dark, compact stroke along the lash line or into a wing. | 27 px |
| Velvet Lip Stain | Use short passes to lay down broken color and build depth. | 94 px |
| Mica Dust | Sweep a pale color over a deeper tone to leave scattered flecks. | 165 px |
| Cheek Contour | Sweep under the cheekbone or along the jaw with the broad, tapered tip. | 172 px |
| Detail Contour | Use the narrow tip down the sides of the nose and on smaller planes. | 67 px |
| Soft Focus Blender | Brush across a transition on the layer that holds the pigment. Use short strokes for gradual blending. | 108 px |

Sizes are for the full dab footprint. The narrow eyeliner tip paints a line much thinner than its footprint.

## How the brushes work

Krita's Pixel Brush engine places a series of dabs as you draw. The grayscale brush tip sets each dab's coverage, while spacing and flow determine how much of its texture remains visible through a stroke. The pack uses wide spacing for freckles, tight spacing for continuous liner, and low flow for loose powder. Liner follows the drawing angle and uses size pressure to taper while keeping dark coverage. The other presets use opacity pressure, with size pressure on selected brushes. [Krita Pixel Brush Engine](https://docs.krita.org/en/reference_manual/brushes/brush_engines/pixel_brush_engine.html) · [Brush Tips](https://docs.krita.org/en/reference_manual/brushes/brush_settings/brush_tips.html) · [Opacity and Flow](https://docs.krita.org/en/reference_manual/brushes/brush_settings/opacity_and_flow.html)

Soft Focus Blender uses the Color Smudge engine in Dulling mode, with Color Rate off and a sampling radius to average nearby pigment. [Krita Color Smudge Brush Engine](https://docs.krita.org/en/reference_manual/brushes/brush_engines/color_smudge_engine.html)

The resource bundle packages eleven bitmap tips and eleven `.kpp` presets together so each preset can resolve its tip. [Krita Brush Presets](https://docs.krita.org/en/reference_manual/resource_management/paintoppresets.html) · [Resource Management](https://docs.krita.org/en/reference_manual/resource_management.html)

[View the swatch sheet painted in Krita](swatches.png).

## Rebuild

Run `python build_bundle.py` with Python 3.10+ and Pillow installed. The builder crops and normalizes the source scans, strips light paper tone, and writes the tips, presets, icons, and manifest into the bundle.

The four source scans were made with the built-in ImageGen tool. The [generation prompts](sources/prompts.md) are included for reference.
