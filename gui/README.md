# MIDI OBS Config Builder

A browser-based GUI for building `config.json` files for the MIDI OBS Controller.
Built with Svelte 5, Vite, TypeScript, and Tailwind CSS v4.

## Features

- **Visual config editor** — add/remove notes, pick action types (loop, static, sequence), edit all fields
- **Listen mode** — connect a MIDI device and press a pad to automatically add it to the config
- **Sequence builder** — add, reorder, and configure multi-step sequences with full support for loop, pause, static, and stop steps
- **Export** — download the config as a properly-formatted `config.json` ready to drop into `app/`

## Development

```bash
cd gui
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

> **Browser MIDI permissions**: Web MIDI API requires either `localhost` or an HTTPS origin.
> Chrome and Edge are supported; Firefox requires a flag or extension.

## Build

```bash
npm run build   # outputs to gui/dist/
npm run preview # preview the build locally
```

The built site is also deployed automatically to GitHub Pages on every push to `main`.

## Type checking

```bash
npm run check
```

## Usage

1. Open the app in your browser (dev or the deployed GitHub Pages URL).
2. Optionally select your MIDI device and enable **Listen mode** — pressing a pad auto-maps it.
3. Select a note in the sidebar and configure its action (loop / static / sequence).
4. Set the **filename** in the top-right (default: `config.json`).
5. Click **Export JSON** to download the file.
6. Copy the downloaded file into your `app/` directory (rename if needed) and run the Python script.

## Exported format

The exported JSON matches `app/config.example.json` exactly:

```json
{
  "36": { "action": "loop", "prefix": "LOOP_A_", "style": "cycle", "bpm": 120, "steps": 4 },
  "51": { "action": "static", "scene": "STATIC_1" }
}
```
