# sheet-contrast-check

Does a screened surface actually lie on a papyrus sheet? A check to run **before** reading ink-model output on
First Letters candidate surfaces, and what it says about 201 surfaces we screened on eligible scrolls.

## In short

- We screened 201 surfaces on 14 First Letters-eligible scrolls with `scrollprize/ink_9um` (seed43, step 50000).
  The surfaces are 173 published clean-sheet patches by Jack and Andrew Gilman
  ([Ahggggg/first-letters-clean-sheets](https://github.com/Ahggggg/first-letters-clean-sheets), commit de78c8b),
  6 published PHerc0800 segments and 22 raw PHerc1203 traces.
  Before counting any of it as a test, we measured whether each surface shows a sheet at all.
- **81 of 201 surfaces have a sheet signal in the range of curated control segments.** The other 120 surfaces (60 %)
  are not a meaningful test of any ink model, whatever the model shows on them.
- **Reading order matters, and our renders are mirrored.** Our `vc_render_tifxyz` renders stack the layers in the
  opposite order to the team's published surface volumes of the same mesh. For `ink_9um` the wrong order drops
  AUC from ~0.75 to ~0.58 on labelled PHerc0841. We therefore chose the order for every surface geometrically, by
  which sheet face looks toward the scroll centre. The rule is calibrated on labelled data, and its numbers are in
  the table below.
- **Our own label-free order heuristic was often wrong.** In our first screening pass we kept, for each surface,
  the order whose `ink_9um` map varies more (larger standard deviation). This heuristic is ours, not a published
  rule. It disagreed with the calibrated geometric order on **35 of 81** surfaces with a sheet signal: 24 of the 60
  surfaces whose order is determined, and 11 of the 21 uncertain ones. On the determined surfaces that is only 60 %
  agreement, close to a coin toss.
  Related: freek_cool's thread "A read-out rule for --direction both" shows that forward and reversed outputs can
  look alike on unread scrolls and proposes reporting their ratio
  ([FreekCool/vesuvius-ink-harness](https://github.com/FreekCool/vesuvius-ink-harness)). Our geometric rule
  complements this by fixing the facing independently of model output.
- With the geometric order, `ink_9um` shows **no rows and no letter shapes** on any of the 81 surfaces with a
  sheet signal (visual inspection of all 81 maps). For the 21 surfaces with an uncertain order we inspected both
  orders. All of them show speckle in both, with no rows and no letter shapes.

## The sheet-contrast measure

The method follows rodriguescarson/eligible-scroll-atlas `scripts/analysis/profile.py` (0c0566c); our
implementation is `code/sheet_contrast.py`.

On a rendered surface volume (28 layers along the normal, native resolution), each 64 × 64 px tile that is at
least 80 % valid gives a mean depth profile. From these we take two numbers:

- `contrast_median`: the median over tiles of (max − min) / mean of the profile;
- `peak_within3`: the share of tiles whose brightest layer is within 3 layers of the centre.

A surface passes if both values reach the **weakest curated control of the same scan protocol**:

| protocol | controls (our own render, 28 layers, native) | threshold |
|---|---|---|
| 9.362 µm / 113 keV | PHerc0841 w00 0.437 / 0.30, ag144 0.440 / 0.26, ag174 0.456 / 0.28; PHerc0139 w043 0.765 / 0.57 | contrast ≥ 0.44, peak ≥ 0.25 |
| 8.64 µm / 116 keV | PHerc1447 w058 0.429 / 0.41, w060 0.351 / 0.23 (central 3000 × 3000 px of each) | contrast ≥ 0.35, peak ≥ 0.22 |

Both thresholds were fixed before any screened surface of that protocol was looked at. The 9.362 µm contrast
threshold is the weakest control rounded to two decimals, so PHerc0841 w00 (0.437) sits just below it. No screened
surface falls between 0.437 and 0.44, so the rounding changes no count.

## Results

By source:

| source | surfaces | with sheet signal |
|---|---|---|
| published clean-sheet patches | 173 | 79 |
| PHerc0800 published segments | 6 | 2 |
| PHerc1203 raw traces | 22 | 0 |

The values for every clean-sheet patch are in [`data/clean_sheets_pass_fail.csv`](data/clean_sheets_pass_fail.csv).

By scroll (`data/counts.json`):

| scroll | voxel µm | surfaces | with sheet signal | order determined | order uncertain |
|---|---|---|---|---|---|
| PHerc0125 | 9.362 | 1 | 0 | 0 | 0 |
| PHerc0175A | 8.64 | 15 | 14 | 9 | 5 |
| PHerc0191 | 9.362 | 5 | 0 | 0 | 0 |
| PHerc0211 | 9.362 | 11 | 1 | 1 | 0 |
| PHerc0257 | 9.362 | 1 | 0 | 0 | 0 |
| PHerc0306B | 8.64 | 7 | 4 | 4 | 0 |
| PHerc0358 | 9.362 | 5 | 3 | 2 | 1 |
| PHerc0483B | 8.64 | 3 | 1 | 1 | 0 |
| PHerc0800 | 8.64 | 6 | 2 | 2 | 0 |
| PHerc0813 | 9.362 | 21 | 10 | 8 | 2 |
| PHerc0826 | 9.362 | 80 | 46 | 33 | 13 |
| PHerc0846B | 9.362 | 2 | 0 | 0 | 0 |
| PHerc1203 | 9.362 | 31 | 0 | 0 | 0 |
| PHerc1545 | 9.362 | 13 | 0 | 0 | 0 |
| **total** | | **201** | **81** | **60** | **21** |

## Reading order: calibration (`code/orient.py`, `data/direction_calibration.json`)

**Earlier work.** Choosing the depth order from geometry was published before us: Matteo Bulloni's
[`auto_order.py`](https://github.com/Bullo27/v8in-12gb) (MIT, posted on the Vesuvius Discord on 2 Oct 2026) uses the
tifxyz grid normal against the scroll axis, taken as the centroid of the masked scan per z-slab. It reported the
right order on 6 of 6 windings (PHerc0841 ×3, PHerc1447 ×3). Our rule below is the same idea, found independently
later. It differs in three points: it measures the render's layer direction from the scan instead of taking a
`--flip-normals` flag; it prefers the published umbilicus where there is one; and it adds a curvature check that
marks surfaces as uncertain.

1. **Layer direction of a render.** At 40–60 random pixels we correlate the render's depth profile with samples of
   the scan taken along +n and −n of the mesh normal. The sign that matches tells which way the layer index grows.
2. **Scroll centre.** We use the published umbilicus where there is one; otherwise the centroid of the papyrus
   mask in the cross-section at that height.
3. **Our renders against the published ones.** On PHerc0841 w00/ag144/ag174, the team's published surface volumes
   grow toward the scroll centre (s = 1.0 / 0.975 / 0.95). Our renders of the same meshes grow away from it
   (s = 0.0 / 0.0 / 0.05).
4. **Rule test on labels.** `ink_9um` on our PHerc0841 renders scores reverse 0.816 / 0.693 / 0.737 against
   forward 0.567 / 0.579 / 0.597 (supervision AUC). The rule predicted reverse. `v8-in` follows the same
   convention (published SV, w00 crop: forward 0.817, reverse 0.545).
5. **Centroid rule on scrolls with a known order.** It holds on PHerc0139 w043 (published SV, s = 1.0) and on
   PHerc1447 w058/w060 (Youssef Nader's layers, which v8-in reads reversed; s = 0.0 / 0.025).
6. **Order per surface.** For each screened surface: if the mesh normal points away from the centre, use reverse;
   if it points toward the centre, use forward. A surface is marked *uncertain* when the local curvature of the
   patch disagrees with that direction.

## Limits

- The patches are small: median 1.6 cm², and only a few are 4 cm² or larger. The sheet check says a sheet is there,
  not that the surface stays on one sheet everywhere.
- A contrast near 1.0 can also come from air gaps next to the sheet.
- For 21 surfaces the order is uncertain: the curvature of the patch disagrees with the centroid rule. Both orders
  look empty, but we do not count these surfaces as a clean test.
- The clean-sheet patches' own `frame_correct_order` (outward → F) is the opposite of what the calibrated rule gives
  for `ink_9um`-family models on `vc_render_tifxyz` renders (outward → reverse). This only matters for readers that
  follow that field.
- This is one model (`ink_9um`) read by eye. It is not evidence that these places carry no ink.
- Our screening heuristic ("suspicion") also responds to sheet texture: median 0.31 with a sheet signal against
  0.21 without. It is a sorting aid, not a detector.

## Files

| path | content |
|---|---|
| `code/sheet_contrast.py` | the measure and the pass rule |
| `code/tile_profile.py` | command-line wrapper for one or more renders |
| `code/orient.py` | layer direction of a render, and the inward/outward test |
| `data/counts.json` | the counts above |
| [`data/clean_sheets_pass_fail.csv`](data/clean_sheets_pass_fail.csv) | per clean-sheet patch (173 rows): scroll, voxel size, `contrast_median`, `peak_within3`, pass/fail, and for passing patches the geometric order and whether it is uncertain |
| `data/controls.json` | control values |
| `data/direction_calibration.json` | the calibration numbers |

The same aggregates are logged as one public W&B run: [sheet-contrast-check / aggregate-results](https://forge.coreweave.com/wandb/lynnhenry-privat/sheet-contrast-check/runs/s27s6fjm).

## Credits and licences

- Clean-sheet patches: Jack Gilman and Andrew Gilman, [Ahggggg/first-letters-clean-sheets](https://github.com/Ahggggg/first-letters-clean-sheets)
  (de78c8b). Their code is MIT; their patches and tables are CC BY-NC 4.0. This repository contains none of their
  files, only numbers measured on our renders of their patches.
- Depth order from geometry, earlier work: Matteo Bulloni, [Bullo27/v8in-12gb](https://github.com/Bullo27/v8in-12gb) `auto_order.py` (MIT).
- Sheet-contrast tile profile: after rodriguescarson, [eligible-scroll-atlas](https://github.com/rodriguescarson/eligible-scroll-atlas) `scripts/analysis/profile.py`.
- PHerc1447 control surfaces and labels: Youssef Nader, [ink-8um-pherc1447-surfaces](https://huggingface.co/datasets/YoussefMoNader/ink-8um-pherc1447-surfaces) (CC BY-NC 4.0).
- Models: [scrollprize/ink_9um](https://huggingface.co/scrollprize/ink_9um), [YoussefMoNader/ink-8um-v8in](https://huggingface.co/YoussefMoNader/ink-8um-v8in) (calibration only).
- Scans, meshes, umbilicus and surface predictions: Vesuvius Challenge open data (CC BY-NC 4.0). Rendering: villa's `vc_render_tifxyz`.

Code in this repository: MIT. Derived numbers: CC BY-NC 4.0, following the scan data. Written with help from Claude Code.
