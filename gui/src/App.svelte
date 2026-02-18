<script lang="ts">
  import { onMount } from 'svelte'
  import { store } from './lib/store.svelte.js'
  import type { ActionConfig } from './lib/types.js'
  import NoteList from './components/NoteList.svelte'
  import NoteEditor from './components/NoteEditor.svelte'

  let selectedNote = $state<string | null>(null)
  let midiAccess = $state<MIDIAccess | null>(null)
  let midiInputs = $state<MIDIInput[]>([])
  let selectedInputId = $state('')
  let listenMode = $state(false)
  let filename = $state('config.json')
  let midiError = $state('')

  onMount(async () => {
    if (!navigator.requestMIDIAccess) {
      midiError = 'Web MIDI API not available. Use Chrome or Edge on localhost / HTTPS.'
      return
    }
    try {
      const access = await navigator.requestMIDIAccess()
      midiAccess = access
      updateInputs()
      access.onstatechange = updateInputs
    } catch (e: unknown) {
      midiError = `MIDI access denied: ${e instanceof Error ? e.message : String(e)}`
    }
  })

  function updateInputs() {
    if (!midiAccess) return
    midiInputs = Array.from(midiAccess.inputs.values())
    if (midiInputs.length > 0 && !selectedInputId) {
      selectedInputId = midiInputs[0].id
    }
  }

  $effect(() => {
    if (!midiAccess) return
    for (const input of midiAccess.inputs.values()) {
      input.onmidimessage = null
    }
    if (listenMode && selectedInputId) {
      const input = midiAccess.inputs.get(selectedInputId)
      if (input) input.onmidimessage = handleMidi
    }
  })

  function handleMidi(event: MIDIMessageEvent) {
    const data = event.data
    if (!data || data.length < 3) return
    const [status, note, velocity] = data
    const isNoteOn = (status & 0xf0) === 0x90 && velocity > 0
    if (!isNoteOn) return
    const key = String(note)
    if (!store.entries[key]) {
      store.add(key, { action: 'loop', prefix: 'LOOP_A_', style: 'cycle', bpm: 120, steps: 4 })
    }
    selectedNote = key
  }

  function exportConfig() {
    const output: Record<string, ActionConfig> = {}
    for (const [note, action] of Object.entries(store.entries)) {
      output[note] = cleanAction(action)
    }
    const json = JSON.stringify(output, omitUndefined, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename.trim() || 'config.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  /** JSON replacer that drops undefined values so pause steps stay clean. */
  function omitUndefined(_key: string, value: unknown) {
    return value === undefined ? undefined : value
  }

  function cleanAction(action: ActionConfig): ActionConfig {
    if (action.action === 'sequence') {
      return { ...action, steps: action.steps.map(cleanStep) }
    }
    return action
  }

  function cleanStep(step: ActionConfig): ActionConfig {
    if (step.action === 'pause' && step.resume_note === undefined) {
      return { action: 'pause' }
    }
    return step
  }

  function handleSelect(noteStr: string) {
    selectedNote = noteStr
  }

  function handleRemove(noteStr: string) {
    store.remove(noteStr)
    if (selectedNote === noteStr) selectedNote = null
  }
</script>

<div class="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
  <!-- ── Header ─────────────────────────────────────────────── -->
  <header class="bg-gray-900 border-b border-gray-800 px-5 py-3 flex items-center gap-3 shrink-0">
    <div class="flex items-center gap-2">
      <span class="text-lg font-bold text-white">MIDI OBS</span>
      <span class="text-lg text-gray-500">Config Builder</span>
    </div>

    <div class="flex items-center gap-2 ml-auto">
      <input
        type="text"
        bind:value={filename}
        class="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-300 w-36"
        placeholder="config.json"
        title="Output filename"
      />
      <button
        onclick={exportConfig}
        disabled={Object.keys(store.entries).length === 0}
        class="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white px-4 py-1.5 rounded text-sm font-medium transition-colors"
      >Export JSON</button>
    </div>
  </header>

  <div class="flex flex-1 overflow-hidden">
    <!-- ── Sidebar ─────────────────────────────────────────── -->
    <aside class="w-60 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      <!-- MIDI panel -->
      <div class="p-4 border-b border-gray-800 space-y-3">
        <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">MIDI Input</h2>

        {#if midiError}
          <p class="text-xs text-red-400 leading-relaxed">{midiError}</p>
        {:else if midiInputs.length === 0}
          <p class="text-xs text-gray-500">No MIDI devices found.<br />Plug in a device and refresh.</p>
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

        <label class="flex items-center gap-2.5 cursor-pointer select-none">
          <input
            type="checkbox"
            bind:checked={listenMode}
            disabled={midiInputs.length === 0 || !!midiError}
            class="w-4 h-4 accent-blue-500"
          />
          <span class="text-sm text-gray-300">Listen mode</span>
        </label>
        {#if listenMode}
          <p class="text-xs text-blue-400">Press a pad to map it →</p>
        {/if}
      </div>

      <!-- Note list -->
      <div class="flex-1 overflow-hidden flex flex-col min-h-0">
        <NoteList {selectedNote} onSelect={handleSelect} onRemove={handleRemove} />
      </div>
    </aside>

    <!-- ── Main editor ─────────────────────────────────────── -->
    <main class="flex-1 overflow-y-auto p-6">
      {#if selectedNote !== null && store.entries[selectedNote]}
        <NoteEditor noteStr={selectedNote} />
      {:else}
        <div class="flex flex-col items-center justify-center h-full gap-4 text-center">
          <div class="text-6xl opacity-20">🎹</div>
          <div>
            <p class="text-gray-500 text-sm">Select a note from the sidebar</p>
            <p class="text-gray-600 text-xs mt-1">or turn on listen mode and press a pad</p>
          </div>
        </div>
      {/if}
    </main>
  </div>
</div>
