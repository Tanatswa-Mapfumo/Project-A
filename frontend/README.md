# App designs — Flutter

Flutter port of the [Figma "welcome" screen](https://www.figma.com/design/1O4CiTmFfVUER3nP06JsUu/App-designs?node-id=33-5) (node `33:5`, 390×844 artboard).

This repo only has `lib/`, `pubspec.yaml`, `analysis_options.yaml` and `assets/` — the platform folders (`android/`, `ios/`, `web/`, etc.) were not generated because the Flutter SDK isn't available in the environment this was built in.

## Setup

1. Scaffold the platform folders into this same directory (it will not overwrite the files already here):
   ```bash
   flutter create --project-name app_designs --org com.example .
   ```
2. Get packages:
   ```bash
   flutter pub get
   ```
3. Run:
   ```bash
   flutter run
   ```

## Notes on fidelity to the Figma frame

- **Colors, spacing, radii, gradient, typography, and the background photo are matched 1:1** to the design (`#FF5A36` / `#FF8166` gradient, 32px headline at line-height 1.2 in Outfit Bold, DM Sans for button/link text, 56px/28-radius primary button, 96px logo tile, etc.). Fonts are pulled live via `google_fonts` (Outfit, DM Sans) — no manual font files needed.
- **The fake iOS status bar (9:41, signal, wifi, battery) was intentionally not hand-drawn.** It's artboard chrome Figma adds so the mockup reads as a real phone — a running app can't show a fake, frozen "9:41"/battery level. Instead the real system status bar is made transparent with light icons over the photo, and the same 44px of vertical space is reserved, so the layout proportions match exactly while the OS shows real info.
- **The home-indicator pill** (the small black rounded bar above the bottom safe area) *is* reproduced, since it's just a decorative shape rather than system-owned chrome.
- **The rounded 32px corner + 1px `#E2DFD9` border on the outer frame was not applied to the Scaffold.** In the Figma file this is the artboard's own presentation styling (so screens look like little phone previews on the canvas) — a real screen runs edge-to-edge on the device, whose corners are already rounded by hardware. If you actually want that border+radius baked into the live screen (e.g. you're embedding this inside another frame/preview), it's a one-line addition — just ask.

## Assets

- `assets/images/welcome_bg.jpg` — background photo exported from Figma (~10MB, uncompressed). Recompress/resize before shipping to production.
- `assets/icons/chart_spline.svg` — logo glyph exported from Figma, tinted white via `ColorFilter`.
