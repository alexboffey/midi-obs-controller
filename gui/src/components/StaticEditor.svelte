<script lang="ts">
  import { store } from '../lib/store.svelte.js'
  import type { StaticAction } from '../lib/types.js'

  let { noteStr } = $props<{ noteStr: string }>()

  const entry = $derived(store.entries[noteStr] as StaticAction)
</script>

<div class="space-y-4">
  <div>
    <label class="block text-xs text-gray-400 mb-1">Scene name</label>
    <input
      type="text"
      value={entry.scene}
      oninput={(e) => store.update(noteStr, { ...entry, scene: (e.target as HTMLInputElement).value })}
      placeholder="e.g. STATIC_1"
      class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 font-mono"
    />
    <p class="text-xs text-gray-600 mt-1">Stops any running loop and switches to this scene</p>
  </div>
</div>
