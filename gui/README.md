# MIDI OBS Config Builder

A browser-based GUI for building and editing `config.json` files for the MIDI OBS Controller.
Built with Svelte 5, Vite, TypeScript, and Tailwind CSS v4.

Available as a live deployment on GitHub Pages, or run locally for development.

## Features

- **Visual config editor** — add/remove notes, pick action types (loop, static, sequence), edit all fields
- **Listen mode** — connect a MIDI device and press a pad to automatically map it
- **Bulk edit view** — table view of all mapped notes for quick scene/prefix renaming across the whole config
- **OBS scene browser** — connect to a live OBS session via WebSocket, browse scenes, and assign them to pads with a click; listen mode auto-assigns the next unassigned scene
- **Sequence builder** — add, reorder, and configure multi-step sequences with full support for loop, pause, static, and stop steps
- **Persistence** — config, listen mode, filename, MIDI device, and OBS connection settings are all saved to `localStorage` and restored on next open
- **Import JSON** — load an existing `config.json` from disk
- **Export / Save** — download the config or save it directly to a file using the browser File System Access API (Chrome/Edge); subsequent saves go to the same file without re-prompting
- **Unsaved changes indicator** — amber label appears when in-memory config differs from the last export/import; native browser leave-page dialog if you navigate away with unsaved changes

## Development

```bash
cd gui
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

> **Browser MIDI permissions**: Web MIDI API requires either `localhost` or an HTTPS origin.
> Chrome and Edge are supported; Firefox requires a flag or extension.

## Tests

```bash
npm test          # run once
npm run test:watch  # watch mode
```

Unit tests cover the pure TypeScript business logic (`obsAuth`, `obsLogic`, `noteNames`).

## Build

```bash
npm run build   # outputs to gui/dist/
npm run preview # preview the build locally
```

The built site is deployed automatically to GitHub Pages on every push to `main`.

## Type checking

```bash
npm run check
```

## Usage

1. Open the app in your browser (dev server or the deployed GitHub Pages URL).
2. **Optional — connect MIDI**: select your device from the dropdown. The last used device is remembered.
3. **Optional — connect OBS**: expand the OBS panel on the right, enter your WebSocket host/port/password, and click Connect. Your scenes will appear in the list.
4. Enable **Listen mode** and press pads to auto-map them. If OBS is connected, each new note is assigned to the next unassigned scene in order.
5. Select a note in the left sidebar to edit its action details in the main area.
6. Use the **Bulk Edit** tab for quick renaming of scene names and loop prefixes across all notes at once.
7. Set the **filename** at the top (default: `config.json`).
8. Click **Export JSON** (or **Save** if you've already picked a file location) to write the config.
9. Place the exported file in your `app/` directory and run the Python script.

## Exported format

The exported JSON matches `app/config.example.json` exactly:

```json
{
  "36": { "action": "loop", "prefix": "LOOP_A_", "style": "cycle", "bpm": 120, "steps": 4 },
  "51": { "action": "static", "scene": "STATIC_1" }
}
```
