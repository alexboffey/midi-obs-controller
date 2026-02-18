<script lang="ts">
  import { store } from '../lib/store.svelte.js'
  import { noteName } from '../lib/noteNames.js'

  let { selectedNote, onSelect, onRemove } = $props<{
    selectedNote: string | null
    onSelect: (noteStr: string) => void
    onRemove: (noteStr: string) => void
  }>()

  let newNote = $state('')

  const sortedNotes = $derived(
    Object.keys(store.entries).map(Number).sort((a, b) => a - b)
  )

  function addNote() {
    const n = parseInt(newNote)
    if (isNaN(n) || n < 0 || n > 127) return
    const key = String(n)
    if (!store.entries[key]) {
      store.add(key, { action: 'loop', prefix: 'LOOP_A_', style: 'cycle', bpm: 120, steps: 4 })
    }
    onSelect(key)
    newNote = ''
  }
</script>

<div class="flex flex-col h-full">
  <div class="px-4 pt-4 pb-2">
    <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Mapped Notes</h2>
    <p class="text-xs text-gray-600">{Object.keys(store.entries).length} note{Object.keys(store.entries).length !== 1 ? 's' : ''}</p>
  </div>

  <ul class="flex-1 overflow-y-auto px-2 py-1">
    {#each sortedNotes as note}
      {@const key = String(note)}
      {@const action = store.entries[key]?.action}
      <li class="group">
        <button
          onclick={() => onSelect(key)}
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm mb-0.5 transition-colors text-left
            {selectedNote === key
              ? 'bg-blue-600 text-white'
              : 'text-gray-300 hover:bg-gray-800'}"
        >
          <span class="flex items-center gap-2 min-w-0">
            <span class="font-mono shrink-0">{note}</span>
            <span class="opacity-60 shrink-0">{noteName(note)}</span>
            <span class="text-xs px-1.5 py-0.5 rounded shrink-0
              {action === 'loop'     ? (selectedNote === key ? 'bg-white/20 text-white' : 'bg-blue-900/60 text-blue-300') :
               action === 'static'   ? (selectedNote === key ? 'bg-white/20 text-white' : 'bg-green-900/60 text-green-300') :
               action === 'sequence' ? (selectedNote === key ? 'bg-white/20 text-white' : 'bg-purple-900/60 text-purple-300') :
               'bg-gray-700 text-gray-400'}"
            >{action}</span>
          </span>
          <span
            role="button"
            tabindex="0"
            onclick={(e) => { e.stopPropagation(); onRemove(key) }}
            onkeydown={(e) => { if (e.key === 'Enter') { e.stopPropagation(); onRemove(key) } }}
            class="opacity-0 group-hover:opacity-100 hover:text-red-400 pl-2 text-lg leading-none shrink-0 transition-opacity"
            aria-label="Remove note {note}"
          >×</span>
        </button>
      </li>
    {/each}

    {#if sortedNotes.length === 0}
      <li class="px-3 py-8 text-center text-gray-600 text-sm leading-relaxed">
        No notes mapped yet.<br />
        Add one below or enable listen mode<br />
        and press a pad.
      </li>
    {/if}
  </ul>

  <div class="p-3 border-t border-gray-800 flex gap-2">
    <input
      type="number"
      bind:value={newNote}
      onkeydown={(e) => { if (e.key === 'Enter') addNote() }}
      min="0"
      max="127"
      placeholder="Note 0–127"
      class="flex-1 min-w-0 bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 placeholder-gray-600"
    />
    <button
      onclick={addNote}
      class="bg-gray-700 hover:bg-gray-600 text-gray-200 px-3 py-1.5 rounded text-sm font-medium shrink-0"
    >Add</button>
  </div>
</div>
