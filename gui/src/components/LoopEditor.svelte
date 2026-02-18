<script lang="ts">
  import { store } from '../lib/store.svelte.js'
  import type { LoopAction, LoopStyle } from '../lib/types.js'

  let { noteStr } = $props<{ noteStr: string }>()

  const entry = $derived(store.entries[noteStr] as LoopAction)

  const LOOP_STYLES: LoopStyle[] = [
    'cycle', 'bounce', 'reverse', 'once',
    'random', 'random_no_repeat', 'strobe', 'shuffle',
  ]

  function update<K extends keyof LoopAction>(field: K, value: LoopAction[K]) {
    store.update(noteStr, { ...entry, [field]: value })
  }
</script>

<div class="space-y-4">
  <div>
    <label class="block text-xs text-gray-400 mb-1">Scene prefix</label>
    <input
      type="text"
      value={entry.prefix}
      oninput={(e) => update('prefix', (e.target as HTMLInputElement).value)}
      placeholder="e.g. LOOP_A_"
      class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 font-mono"
    />
    <p class="text-xs text-gray-600 mt-1">Matches OBS scenes starting with this prefix</p>
  </div>

  <div>
    <label class="block text-xs text-gray-400 mb-1">Loop style</label>
    <select
      value={entry.style}
      onchange={(e) => update('style', (e.target as HTMLSelectElement).value as LoopStyle)}
      class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200"
    >
      {#each LOOP_STYLES as style}
        <option value={style}>{style}</option>
      {/each}
    </select>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div>
      <label class="block text-xs text-gray-400 mb-1">BPM</label>
      <input
        type="number"
        value={entry.bpm}
        min="1"
        oninput={(e) => update('bpm', parseFloat((e.target as HTMLInputElement).value) || 120)}
        class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200"
      />
    </div>
    <div>
      <label class="block text-xs text-gray-400 mb-1">Steps</label>
      <input
        type="number"
        value={entry.steps}
        min="1"
        oninput={(e) => update('steps', parseFloat((e.target as HTMLInputElement).value) || 1)}
        class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200"
      />
    </div>
  </div>
  <p class="text-xs text-gray-600">
    Switch interval: {((60 / entry.bpm) * entry.steps).toFixed(2)}s
    &nbsp;({entry.bpm} BPM × {entry.steps} step{entry.steps !== 1 ? 's' : ''})
  </p>
</div>
