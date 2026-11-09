---
name: Signed Passport
description: A GitHub profile printed as a security document, shown in daylight and under a UV lamp.
colors:
  day-paper: "#E8EEEC"
  day-paper-2: "#DDE6E3"
  day-ink: "#13213A"
  day-label: "#4C5E6E"
  day-guilloche-teal: "#2E8B82"
  day-guilloche-lavender: "#8C79B6"
  day-serial-red: "#C42F2A"
  day-edge: "#C5D2CE"
  day-cover: "#16243F"
  day-stamp-blue: "#1F4FA8"
  day-stamp-violet: "#5B3C9E"
  day-stamp-green: "#1E7A55"
  day-stamp-umber: "#A8531C"
  uv-paper: "#0B0A1A"
  uv-paper-2: "#121129"
  uv-ink: "#E6E8FF"
  uv-label: "#9296CC"
  uv-fluor-mint: "#5CF2C8"
  uv-fluor-periwinkle: "#7FA8FF"
  uv-fluor-vermilion: "#FF6B4A"
  uv-fluor-pink: "#FF5FA8"
  uv-fluor-violet: "#C79BFF"
  uv-fluor-amber: "#FFB04A"
  uv-fibre-yellow: "#FFE45C"
  uv-edge: "#2C2856"
  uv-portrait: "#4A4785"
  uv-cover: "#0F1530"
  emboss-light: "#E9EEF7"
  emboss-mid: "#AEB8CC"
  emboss-dark: "#6C7894"
typography:
  cover-display:
    fontFamily: "Archivo, 'Segoe UI', sans-serif"
    fontSize: "54px"
    fontWeight: 800
    letterSpacing: "22px"
    fontVariation: "'wght' 800, 'wdth' 112"
  headline:
    fontFamily: "Archivo, 'Segoe UI', sans-serif"
    fontSize: "40px"
    fontWeight: 800
    fontVariation: "'wght' 800, 'wdth' 112"
  title:
    fontFamily: "Archivo, 'Segoe UI', sans-serif"
    fontSize: "30px"
    fontWeight: 800
    letterSpacing: "9px"
    fontVariation: "'wght' 800, 'wdth' 112"
  value:
    fontFamily: "Archivo, 'Segoe UI', sans-serif"
    fontSize: "21px"
    fontWeight: 760
    fontVariation: "'wght' 760, 'wdth' 100"
  label:
    fontFamily: "Archivo, 'Segoe UI', sans-serif"
    fontSize: "14.5px"
    fontWeight: 600
    letterSpacing: "1.4px"
    fontVariation: "'wght' 600, 'wdth' 125"
  body:
    fontFamily: "Archivo, 'Segoe UI', sans-serif"
    fontSize: "17px"
    fontWeight: 450
    fontVariation: "'wght' 450, 'wdth' 100"
  mrz:
    fontFamily: "'Azeret Mono', monospace"
    fontSize: "29px"
    fontWeight: 500
    fontVariation: "'wght' 500"
  serial:
    fontFamily: "'Azeret Mono', monospace"
    fontSize: "15px"
    fontWeight: 500
    fontVariation: "'wght' 500"
rounded:
  document: "30px"
  photo-window: "14px"
  stamp-frame: "12px"
  stamp-frame-inner: "7px"
spacing:
  document-margin: "48px"
  field-column: "232px"
  field-row: "52px"
  panel-inset: "40px"
components:
  data-field-label:
    textColor: "{colors.day-label}"
    typography: "{typography.label}"
  data-field-value:
    textColor: "{colors.day-ink}"
    typography: "{typography.value}"
  data-field-value-uv:
    textColor: "{colors.uv-ink}"
    typography: "{typography.value}"
  verified-stamp:
    textColor: "{colors.day-serial-red}"
    rounded: "{rounded.stamp-frame}"
    size: "250px 104px"
  verified-stamp-uv:
    textColor: "{colors.uv-fluor-vermilion}"
    rounded: "{rounded.stamp-frame}"
  visa-stamp:
    textColor: "{colors.day-serial-red}"
    size: "400px 300px"
  portrait-window:
    backgroundColor: "{colors.day-paper-2}"
    rounded: "{rounded.photo-window}"
    size: "262px 338px"
---

# Design System: Signed Passport

## Overview

**Creative North Star: "The Signed Passport"**

Every surface is a page of one security-printed travel document. The data page, the visa stamps, the perforated entry log and the visitor registry are all things a passport physically carries: intaglio ink on tinted security paper, guilloché hairlines, rubber-stamp impressions, laser perforation, a machine-readable zone. Nothing is a card, a widget or a badge. The document is the container; everything else is printed on it or stamped into it.

The system has two lighting states rather than a light and a dark theme. **Daylight** is the document as printed. **UV** is the same document under a 365nm inspection lamp: the paper goes blue-black, security inks fluoresce, fibres and a hidden rosette appear that daylight does not show. Both are generated from the same code path with a swapped palette (`DAY` / `UV` in `.github/scripts/build.py`), so the two states must always carry identical content and geometry.

All sizes are SVG viewBox units (1 unit = 1px at the asset's native width: passport 1200x760, log 1200x330, registry 1200x220, visa 400x300). GitHub scales the whole image to the column, so type size is relative to the artboard, not to the reader's root font size.

**Key Characteristics:**
- One document, two lights: Daylight palette for light mode, UV palette for dark mode, swapped by `<picture>`.
- Hairline and ink, never boxes: structure comes from 1px rules, guilloché, perforation and stamp outlines.
- Expanded caps labels over heavy values, monospace for anything a machine would read.
- Rubber-stamp impressions are procedurally imperfect (bleed, speckle, uneven pressure, occasional double strike).
- One motion moment: only the passport animates.

## Colors

A cool, low-chroma security-paper ground with one dark intaglio ink, two guilloché hairline inks and a single serial red; under UV the same roles become fluorescent.

### Primary
- **Intaglio Navy** (day-ink): all values, names and the header wordmark in daylight; also the engraved portrait and MRZ.
- **UV Ghost White** (uv-ink): the same role under the lamp.

### Secondary
- **Serial Red** (day-serial-red) / **Fluorescent Vermilion** (uv-fluor-vermilion): document number, the VALID UNTIL value, the MRZ scan bar, the VERIFIED stamp, and the first stamp ink. Reserved for what the document asserts about its own validity.

### Tertiary
- **Guilloché Teal** (day-guilloche-teal) and **Guilloché Lavender** (day-guilloche-lavender): rosette rings, the wave underprint pattern and the foil-patch outline. Hairline only (0.6 to 0.8 stroke), never fills.
- **UV Mint** (uv-fluor-mint) and **UV Periwinkle** (uv-fluor-periwinkle): the same rosette and wave roles fluorescing; mint is also the entry-log dot colour under UV.
- **Stamp inks**: six per light, cycled by visa index: day red, blue, violet, green, navy, umber; UV vermilion, periwinkle, violet, mint, ghost white, amber.
- **UV-only security features**: fluorescent pink (uv-fluor-pink) for the hidden rosette and ghost portrait, fibre yellow (uv-fibre-yellow) only among the scattered fibres (pink / mint / periwinkle / yellow, stroke 1.1).
- **Holographic foil**: a linear gradient mint, `#9F86FF`, `#FF7AB8`, `#FFD66B`, mint, clipped to the patch over the portrait corner (opacity 0.38 day, 0.55 UV).

### Neutral
- **Security Paper** (day-paper) / **UV Blue-Black** (uv-paper): the document ground.
- **Photo Tint** (day-paper-2 / uv-paper-2): the portrait window ground only.
- **Field Label Slate** (day-label / uv-label): every field caption, microprint, footer serials, month ticks.
- **Edge** (day-edge / uv-edge): the 1px document border, photo-window border, and the hairline dividers in log and registry.
- **Cover Navy** (day-cover / uv-cover): the closed passport cover, with the **Emboss** gradient (emboss-light to emboss-mid to emboss-dark, radial) for the cover wordmark and rosette.

### Named Rules
**The Two Lights Rule.** Every colour role exists in both DAY and UV. A new surface adds a key to both dicts or to neither; never hardcode a colour into one light.

**The Red Means Valid Rule.** Serial red marks only claims about the document's validity (document number, VALID UNTIL, VERIFIED, scan bar) and the first stamp ink. It is never decoration.

**The UV Reveals Rule.** Fibres, the hidden pink rosette and the strong ghost portrait (opacity 0.75 UV vs 0.16 day) exist only under UV. Daylight never shows them.

## Typography

**Display Font:** Archivo (variable, instanced per role at build time; fallback 'Segoe UI', sans-serif)
**Label/Mono Font:** Azeret Mono (wght 500)

**Character:** Archivo stretched wide for captions and heavy for values reads as government document setting; Azeret Mono carries everything a machine would parse. Each role is a separate static instance of the variable font, subset to the glyphs the SVG uses and embedded as WOFF.

### Hierarchy
- **Cover display** (wght 800 / wdth 112, 54, letter-spacing 22): the PASSPORT wordmark on the cover, filled with the emboss gradient. Cover only.
- **Headline** (wght 800 / wdth 112, 40): surname and given names; registry stamp count.
- **Title** (wght 800 / wdth 112, 30, letter-spacing 9): the PASSPORT header on the data page. The VERIFIED stamp uses the same face at 38 / spacing 4; visa titles at 34 (26 on round stamps), shrinking by 1 to fit, floor 16.
- **Value** (wght 760 / wdth 100, 21): field values. Header values (TYPE, CODE) use the 800/112 face at 23; log statistics at 26.
- **Label** (wght 600 / wdth 125, 14.5, letter-spacing 1.4, uppercase): every field caption. Header captions 13 to 13.5; stamp port and stack lines 15 shrinking to fit, floor 10, spacing 2; arc rim text 14, spacing 2.4.
- **Body** (wght 450 / wdth 100, 17): the only sentence-case running text (log languages 17, registry empty state 19).
- **MRZ** (Azeret Mono 500, 29): the two 44-character lines, forced to `textLength` 1064 with spacing adjust.
- **Serial** (Azeret Mono 500, 15): stamp dates and visitor serials; document number at 24; Merkle root 12.5.

### Named Rules
**The Machine Reads Mono Rule.** Hashes, serials, dates on stamps, MRZ and the document number are Azeret Mono. Human-facing names and values are Archivo.

**The Caption Above Value Rule.** A field is a label-face caption in label colour, then the value baseline at caption y + size + 4. Labels are always uppercase and expanded (wdth 125).

**The Fit By Shrinking Rule.** Stamp text never wraps or truncates; it steps the font size down (0.5 for labels, 1 for titles) using real glyph advances from the instanced font until it fits the stamp's room.

## Layout

The passport data page is a 1200x760 artboard with the document at (20,20) 1160x720. Content sits on a 48-unit inner margin (x 68 to 1132). Left column: the 262x338 portrait window at (68,150). Centre: field grid at x 372 and 604 (232 apart), rows at y 304, 356, 408, 460, 512 (52 apart) below two 40-size name fields 74 apart. Right: the hash-seeded rosette centred at (968,300); the laser-perforated document number runs down x 1128. Bottom 160 units: the MRZ band, separated by a 1px edge rule at y 590.

The entry log and registry are 1200-wide strips with a 40-unit inset: a statistics column at x 40, a 1px vertical edge rule (x 340 log, x 300 registry), then the data. Log dots sit on a 14.9 pitch horizontally and 14.9 x 1.42 vertically; dot radius encodes quartile (0.9, 2.4, 3.3, 4.2, 5.1), empty days at opacity 0.35.

Visa stamps are 400x300 tiles placed three to a row at 32% width in Markdown. Responsive behaviour is GitHub's: every asset scales as a whole image.

## Elevation & Depth

Flat. There are no shadows. Depth is printed, not lit: a 70-unit black gradient at the left edge (opacity 0.16 day, 0.5 UV) reads as the binding gutter, the portrait is an engraving of variable-width lines, and the perforated number is a mask cut through the whole page. The cover's emboss is a radial gradient fill, not a shadow.

**The Printed Depth Rule.** Depth comes from ink, paper and cuts (gutter gradient, engraving, perforation mask). Never add drop shadows or blurs.

## Shapes

Shapes are the physical objects a passport has. The document has 30-unit corners, the photo window 14, the VERIFIED stamp a 12-unit outer and 7-unit inner frame. Stamps take real stamp silhouettes, cycled by visa index: round with rim text, notched rectangle, octagon, oval, arrow-tab exit stamp, shield. Stamp outer strokes are 5 (visas) or 4.5 (VERIFIED) with a 1.4 to 1.6 inner keyline. Everything else is a hairline: 1px edge borders and dividers, 0.6 to 0.8 guilloché strokes.

**The Objects Have Corners Rule.** Radius belongs only to a physical document object (document, photo window, stamp frame). Never round a layout region, panel or text block.

## Components

### Data field
Caption in the label face and label colour, value beneath in the value face and ink colour (serial red for VALID UNTIL). Each field is its own group so it can rise in sequence on the passport.

### Visa stamp
A rubber-stamp impression per project: one stamp ink, one silhouette, rotated by a name-seeded angle (-7 to 6 degrees). Content top to bottom: port (label face), title (title face, shrink to fit), date and star count (mono 15), stack (label face). Group opacity 0.92. About one in three gets a faint double strike (opacity 0.16, offset 1.4, rotation within 1.2 degrees). Static.

### Stamp ink treatment
Every full stamp passes through `ink()`: a displacement filter (fractal noise base frequency 0.035, 2 octaves, scale 3.2) to bleed the edges, composited inside a speckle mask (noise 0.85, alpha matrix -1.15 / 1.42), then masked by a pressure gradient at a seeded angle whose weakest stop falls between 0.35 and 0.6 opacity. In 35% of seeds the far edge drops to 0.05 for a partial strike. Seeds come from the document hash or repo name so the impression is stable between builds. Visitor marks in the registry use a lighter speckle-only filter (noise 0.9, matrix -1.3 / 1.45).

### VERIFIED stamp
Double-framed red rectangle (250x104), rotated -9 degrees, VERIFIED in the title face at 38 with a SIGSTORE date line in the label face at 11. Opacity 0.88 day, 0.95 UV. It is the last thing to land on the passport.

### Guilloché rosette
Two rose-curve rings (base radius 92 and 50, scaled) each repeated 22 and 16 times with a small rotation to make moiré, stroked in the two guilloché inks at 0.65. Lobe counts and phases are seeded by the document hash, so every build prints a different rosette.

### Machine-readable zone
Two ICAO 9303 lines with valid check digits, mono 29, full measure. Followed by a mono 10.5 build line (timestamp and SHA-256) right-aligned at the foot.

### Motion (passport only)
The passport is the page's one motion moment. Cover swings open (1.05s, `cubic-bezier(.55,0,.75,.35)`, from 0.45s) while a shade darkens it; fields and header rise 9 units with `cubic-bezier(.16,1,.3,1)` over 0.7s, staggered from 1.15s; guilloché copies fade in at 0.5s ease-out, staggered 0.035s; the MRZ types on with `steps(44)` and a red scan bar sweeps it (1.1s, from 2.05s); VERIFIED thunks down from scale 1.6 at 3.25s over 0.42s on the same expo ease-out; the foil drifts across its patch on a 7s ease-in-out alternate loop. Every SVG carries `@media (prefers-reduced-motion:reduce){*{animation:none!important}}`.

**The One Motion Moment Rule.** Only the passport animates. Visas, log and registry ship with empty CSS and stay static.

**The Expo Landing Rule.** Things that arrive (fields, stamps) use `cubic-bezier(.16,1,.3,1)`. Only the cover's swing accelerates, because a cover falls open.

## Do's and Don'ts

### Do:
- **Do** add every new colour role to both DAY and UV in `build.py`.
- **Do** set field captions in Archivo wght 600 / wdth 125 at 14.5 with 1.4 spacing, and values in the heavy Archivo instances.
- **Do** put hashes, serials, dates on stamps and machine lines in Azeret Mono 500.
- **Do** pass every new stamp through `ink()` with a stable seed.
- **Do** fit stamp text by shrinking against measured glyph advances, never by wrapping or ellipsis.
- **Do** keep `prefers-reduced-motion` off-switching in every SVG via `finish()`.

### Don't:
- **Don't** animate anything except the passport.
- **Don't** use drop shadows, blurs or glass; depth is printed.
- **Don't** put radius on anything that is not a physical document object.
- **Don't** wrap content in cards, chips or badge rows; use hairline rules and the document itself.
- **Don't** use serial red for decoration; it marks validity.
- **Don't** show UV-only features (fibres, hidden rosette, strong ghost portrait) in daylight.
