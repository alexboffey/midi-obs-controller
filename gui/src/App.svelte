<script lang="ts">
  import { onMount } from "svelte";
  import { store } from "./lib/store.svelte.js";
  import { obsStore } from "./lib/obs.svelte.js";
  import { nextUnassignedScene } from "./lib/obsLogic.js";
  import type { ActionConfig, SequenceStepAction } from "./lib/types.js";
  import NoteList from "./components/NoteList.svelte";
  import NoteEditor from "./components/NoteEditor.svelte";
  import BulkEditor from "./components/BulkEditor.svelte";
  import ObsPanel from "./components/ObsPanel.svelte";

  const LS_CONFIG = "midi-obs-config";
  const LS_LISTEN = "midi-obs-listen";
  const LS_FILENAME = "midi-obs-filename";
  const LS_DEVICE = "midi-obs-device";

  let selectedNote = $state<string | null>(null);
  let midiAccess = $state<MIDIAccess | null>(null);
  let midiInputs = $state<MIDIInput[]>([]);
  let selectedInputId = $state("");
  let midiConnected = $state(false);
  let listenMode = $state(false);
  let filename = $state("config.json");
  let midiError = $state("");
  let fileHandle = $state<FileSystemFileHandle | null>(null);
  let view = $state<"edit" | "bulk">("edit");
  let obsOpen = $state(true);
  let pendingObsScene = $state<string | null>(null);
  // Guard so $effects don't overwrite localStorage before onMount restores it
  let restored = $state(false);
  // Snapshot of the config as it was at last file save/import; '' = no file linked yet
  let lastSaved = $state("");
  let isDirty = $state(false);
  // Brief "Saving..." pulse shown while localStorage auto-save is in flight
  let saving = $state(false);
  // Derived JSON — $derived tracks both new-key additions AND value mutations
  const configJson = $derived(JSON.stringify(store.entries));

  onMount(async () => {
    // Restore persisted state
    try {
      const raw = localStorage.getItem(LS_CONFIG);
      if (raw) store.load(JSON.parse(raw));
      const savedListen = localStorage.getItem(LS_LISTEN);
      if (savedListen !== null) listenMode = savedListen === "true";
      const savedFilename = localStorage.getItem(LS_FILENAME);
      if (savedFilename) filename = savedFilename;
    } catch {
      /* ignore corrupt localStorage */
    }
    restored = true;

    obsStore.restoreSettings();

    if (!navigator.requestMIDIAccess) {
      midiError =
        "Web MIDI API not available. Use Chrome or Edge on localhost / HTTPS.";
    }
  });

  async function connectMidi() {
    midiError = "";
    try {
      const access = await navigator.requestMIDIAccess();
      midiAccess = access;
      midiConnected = true;
      updateInputs();
      access.onstatechange = updateInputs;
    } catch (e: unknown) {
      midiError = `MIDI access denied: ${e instanceof Error ? e.message : String(e)}`;
    }
  }

  async function disconnectMidi() {
    listenMode = false;
    if (midiAccess) {
      for (const input of midiAccess.inputs.values()) {
        input.onmidimessage = null;
        await input.close();
      }
    }
    midiAccess = null;
    midiInputs = [];
    midiConnected = false;
  }

  function updateInputs() {
    if (!midiAccess) return;
    midiInputs = Array.from(midiAccess.inputs.values());
    if (!midiInputs.length) return;
    // Restore last-used device by name (more stable than ID across sessions)
    const savedName = localStorage.getItem(LS_DEVICE);
    if (savedName) {
      const match = midiInputs.find((i) => i.name === savedName);
      if (match) {
        selectedInputId = match.id;
        return;
      }
    }
    // Fall back to first available device
    if (!selectedInputId || !midiInputs.some((i) => i.id === selectedInputId)) {
      selectedInputId = midiInputs[0].id;
    }
  }

  // ── Persistence effects ─────────────────────────────────────────────

  $effect(() => {
    if (!restored) return;
    localStorage.setItem(LS_CONFIG, configJson);
    saving = true;
    const timer = setTimeout(() => {
      saving = false;
    }, 800);
    return () => clearTimeout(timer);
  });

  $effect(() => {
    if (!restored) return;
    localStorage.setItem(LS_LISTEN, String(listenMode));
    localStorage.setItem(LS_FILENAME, filename);
  });

  // Remember selected MIDI device by name
  $effect(() => {
    if (!restored) return;
    const input = midiInputs.find((i) => i.id === selectedInputId);
    if (input) localStorage.setItem(LS_DEVICE, input.name);
  });

  // ── Unsaved-changes tracking ─────────────────────────────────────────

  $effect(() => {
    const handle = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handle);
    return () => window.removeEventListener("beforeunload", handle);
  });

  $effect(() => {
    if (lastSaved === "") return;
    const current = configJson;
    const timer = setTimeout(() => {
      isDirty = current !== lastSaved;
    }, 400);
    return () => clearTimeout(timer);
  });

  // ── MIDI ─────────────────────────────────────────────────────────────

  $effect(() => {
    if (!midiAccess) return;
    for (const input of midiAccess.inputs.values()) {
      input.onmidimessage = null;
    }
    if (listenMode && selectedInputId) {
      const input = midiAccess.inputs.get(selectedInputId);
      if (input) input.onmidimessage = handleMidi;
    }
  });

  function handleMidi(event: MIDIMessageEvent) {
    const data = event.data;
    if (!data || data.length < 3) return;
    const [status, note, velocity] = data;
    const isNoteOn = (status & 0xf0) === 0x90 && velocity > 0;
    if (!isNoteOn) return;
    const key = String(note);
    if (!store.entries[key]) {
      if (pendingObsScene) {
        // User clicked a specific OBS scene — assign it, then advance to next unassigned
        const scene = pendingObsScene;
        store.add(key, { action: "static", scene });
        const nextIdx = obsStore.scenes.indexOf(scene) + 1;
        pendingObsScene = nextUnassignedScene(
          obsStore.scenes,
          store.entries,
          nextIdx,
        );
      } else if (
        obsStore.status === "connected" &&
        obsStore.scenes.length > 0
      ) {
        // OBS connected, no scene selected — auto-pick next unassigned OBS scene
        const scene = nextUnassignedScene(obsStore.scenes, store.entries);
        store.add(
          key,
          scene ? { action: "static", scene } : store.defaultAction(),
        );
      } else {
        store.add(key, store.defaultAction());
      }
    }
    selectedNote = key;
    view = "edit";
  }

  // ── Export / Import ──────────────────────────────────────────────────

  async function exportConfig() {
    const output: Record<string, ActionConfig> = {};
    for (const [note, action] of Object.entries(store.entries)) {
      output[note] = cleanAction(action);
    }
    const json = JSON.stringify(output, omitUndefined, 2);

    if ("showSaveFilePicker" in window) {
      try {
        if (!fileHandle) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          fileHandle = await (window as any).showSaveFilePicker({
            suggestedName: filename.trim() || "config.json",
            types: [
              {
                description: "JSON config",
                accept: { "application/json": [".json"] },
              },
            ],
          });
          filename = fileHandle!.name;
        }
        const writable = await fileHandle!.createWritable();
        await writable.write(json);
        await writable.close();
        lastSaved = configJson;
        isDirty = false;
        return;
      } catch (e: unknown) {
        if ((e as DOMException)?.name === "AbortError") return;
        fileHandle = null;
      }
    }

    // Fallback: blob download
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.trim() || "config.json";
    a.click();
    URL.revokeObjectURL(url);
    lastSaved = configJson;
    isDirty = false;
  }

  async function importConfig() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json,application/json";
    await new Promise<void>((resolve) => {
      input.onchange = async () => {
        const file = input.files?.[0];
        if (!file) {
          resolve();
          return;
        }
        try {
          const text = await file.text();
          const data = JSON.parse(text) as Record<string, ActionConfig>;
          store.load(data);
          filename = file.name;
          selectedNote = null;
          lastSaved = JSON.stringify(data);
          isDirty = false;
        } catch {
          alert("Could not parse JSON file — make sure it is a valid config.");
        }
        resolve();
      };
      input.click();
    });
  }

  // ── OBS scene assignment ─────────────────────────────────────────────

  function handleObsSceneClick(scene: string) {
    const entry = selectedNote ? store.entries[selectedNote] : null;
    if (entry?.action === "static") {
      // Only directly assign if this scene isn't already used by a different note.
      // Clicking an already-assigned scene to "see" which note has it is a common
      // mistake that silently overwrites the selected note's scene.
      const takenByOther = Object.entries(store.entries).some(
        ([n, a]) =>
          n !== selectedNote && a.action === "static" && a.scene === scene,
      );
      if (!takenByOther) {
        store.update(selectedNote!, { action: "static", scene });
        return;
      }
    }
    // Toggle pending assignment for the next note press
    pendingObsScene = pendingObsScene === scene ? null : scene;
  }

  function newConfig() {
    store.load({});
    selectedNote = null;
    filename = "config.json";
    fileHandle = null;
    lastSaved = "";
    isDirty = false;
    localStorage.removeItem(LS_CONFIG);
    localStorage.removeItem(LS_FILENAME);
  }

  // ── Helpers ──────────────────────────────────────────────────────────

  function omitUndefined(_key: string, value: unknown) {
    return value === undefined ? undefined : value;
  }

  function cleanAction(action: ActionConfig): ActionConfig {
    if (action.action === "sequence") {
      return { ...action, steps: action.steps.map(cleanStep) };
    }
    return action;
  }

  function cleanStep(step: SequenceStepAction): SequenceStepAction {
    if (step.action === "pause" && step.resume_note === undefined) {
      return { action: "pause" };
    }
    return step;
  }

  function handleSelect(noteStr: string) {
    selectedNote = noteStr;
    view = "edit";
  }

  function handleRemove(noteStr: string) {
    store.remove(noteStr);
    if (selectedNote === noteStr) selectedNote = null;
  }

  function handleEditNote(noteStr: string) {
    selectedNote = noteStr;
    view = "edit";
  }
</script>

<div class="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
  <!-- ── Header ───────────────────────────────────────────────────────── -->
  <header
    class="bg-gray-900 border-b border-gray-800 px-5 py-3 flex items-center gap-3 shrink-0"
  >
    <div class="flex items-center gap-2">
      <span class="text-lg font-bold text-white">MIDI OBS</span>
      <span class="text-lg text-gray-500">Config Builder</span>
    </div>

    <div class="flex items-center gap-2 ml-auto">
      {#if isDirty}
        <span class="text-xs whitespace-nowrap text-amber-400 mr-4"
          >Unsaved changes</span
        >
      {:else if saving}
        <span class="text-xs whitespace-nowrap text-gray-500 mr-4"
          >Saving...</span
        >
      {/if}

      <button
        onclick={newConfig}
        class="bg-gray-700 hover:bg-gray-600 text-gray-200 px-4 py-1.5 rounded text-sm font-medium transition-colors"
        title="Clear all mappings and start fresh">New</button
      >
      <button
        onclick={importConfig}
        class="bg-gray-700 hover:bg-gray-600 text-gray-200 px-4 py-1.5 rounded text-sm font-medium transition-colors"
        >Import JSON</button
      >

      {#if fileHandle}
        <span
          class="text-sm text-gray-300 truncate max-w-44"
          title={fileHandle.name}>{fileHandle.name}</span
        >
        <button
          onclick={() => (fileHandle = null)}
          class="text-xs text-gray-500 hover:text-gray-300 transition-colors px-1"
          title="Change save location">Change</button
        >
      {:else}
        <input
          type="text"
          bind:value={filename}
          class="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-300 w-36"
          placeholder="config.json"
          title="Output filename"
        />
      {/if}

      <button
        onclick={exportConfig}
        disabled={Object.keys(store.entries).length === 0}
        class="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white px-4 py-1.5 rounded text-sm font-medium transition-colors"
        >{fileHandle ? "Save" : "Export JSON"}</button
      >

      <div class="w-px h-5 bg-gray-700 mx-1"></div>

      <!-- OBS panel toggle — dot shows connection status -->
      <button
        onclick={() => {
          obsOpen = !obsOpen;
          if (!obsOpen) pendingObsScene = null;
        }}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors
          {obsOpen
          ? 'bg-gray-600 text-white'
          : 'bg-gray-700 hover:bg-gray-600 text-gray-300'}"
        title="Toggle OBS scene browser"
      >
        OBS
        <span
          class="w-1.5 h-1.5 rounded-full
          {obsStore.status === 'connected'
            ? 'bg-green-400'
            : obsStore.status === 'connecting'
              ? 'bg-yellow-400'
              : obsStore.status === 'error'
                ? 'bg-red-500'
                : 'bg-gray-500'}"
        ></span>
      </button>
    </div>
  </header>

  <div class="flex flex-1 overflow-hidden">
    <!-- ── Left sidebar ──────────────────────────────────────────────── -->
    <aside
      class="w-60 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0"
    >
      <div class="p-4 border-b border-gray-800 space-y-3">
        <div class="flex items-center justify-between">
          <h2
            class="text-xs font-semibold text-gray-400 uppercase tracking-wider"
          >
            MIDI Input
          </h2>
          {#if !midiError}
            {#if midiConnected}
              <button
                onclick={disconnectMidi}
                class="text-xs text-gray-400 hover:text-red-400 transition-colors"
                title="Release MIDI port so other apps (e.g. the Python script) can use it"
                >Disconnect</button
              >
            {:else}
              <button
                onclick={connectMidi}
                class="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >Connect</button
              >
            {/if}
          {/if}
        </div>

        {#if midiError}
          <p class="text-xs text-red-400 leading-relaxed">{midiError}</p>
        {:else if !midiConnected}
          <p class="text-xs text-gray-600 leading-relaxed">
            Disconnected — click Connect to<br />access your MIDI device.
          </p>
        {:else if midiInputs.length === 0}
          <p class="text-xs text-gray-500">
            No MIDI devices found.<br />Plug in a device and refresh.
          </p>
        {:else}
          <select
            bind:value={selectedInputId}
            class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200"
          >
            {#each midiInputs as input}
              <option value={input.id}>{input.name}</option>
            {/each}
          </select>
        {/if}

        {#if midiConnected && midiInputs.length > 0}
          <label class="flex items-center gap-2.5 cursor-pointer select-none">
            <input
              type="checkbox"
              bind:checked={listenMode}
              class="w-4 h-4 accent-blue-500"
            />
            <span class="text-sm text-gray-300">Listen mode</span>
          </label>
          {#if listenMode}
            <p class="text-xs text-blue-400">
              {pendingObsScene
                ? `Next pad → "${pendingObsScene}"`
                : obsStore.status === "connected"
                  ? "Press a pad — OBS scene auto-assigned"
                  : "Press a pad to map it →"}
            </p>
          {/if}
        {/if}
      </div>

      <div class="flex-1 overflow-hidden flex flex-col min-h-0">
        <NoteList
          {selectedNote}
          onSelect={handleSelect}
          onRemove={handleRemove}
        />
      </div>
    </aside>

    <!-- ── Main area ──────────────────────────────────────────────────── -->
    <main class="flex-1 overflow-hidden flex flex-col min-w-0">
      <div class="flex border-b border-gray-800 bg-gray-900/50 shrink-0">
        <button
          onclick={() => (view = "edit")}
          class="px-5 py-2.5 text-sm font-medium border-b-2 transition-colors
            {view === 'edit'
            ? 'border-blue-500 text-white'
            : 'border-transparent text-gray-500 hover:text-gray-300'}"
          >Edit Note</button
        >
        <button
          onclick={() => (view = "bulk")}
          class="px-5 py-2.5 text-sm font-medium border-b-2 transition-colors
            {view === 'bulk'
            ? 'border-blue-500 text-white'
            : 'border-transparent text-gray-500 hover:text-gray-300'}"
          >Bulk Edit</button
        >
      </div>

      <div class="flex-1 overflow-y-auto">
        {#if view === "bulk"}
          <BulkEditor onEditNote={handleEditNote} />
        {:else if selectedNote !== null && store.entries[selectedNote]}
          <div class="p-6">
            <NoteEditor noteStr={selectedNote} />
          </div>
        {:else}
          <div
            class="flex flex-col items-center justify-center h-full gap-4 text-center"
          >
            <div class="text-6xl opacity-20">🎹</div>
            <div>
              <p class="text-gray-500 text-sm">
                Select a note from the sidebar
              </p>
              <p class="text-gray-600 text-xs mt-1">
                or turn on listen mode and press a pad
              </p>
            </div>
          </div>
        {/if}
      </div>
    </main>

    <!-- ── OBS right panel (toggleable) ──────────────────────────────── -->
    {#if obsOpen}
      <ObsPanel
        pendingScene={pendingObsScene}
        onSceneClick={handleObsSceneClick}
      />
    {/if}
  </div>
</div>
