<script lang="ts">
  import { store } from '../lib/store.svelte.js'
  import { noteName } from '../lib/noteNames.js'

  let { onEditNote } = $props<{
    /** Called when the user clicks "Edit" on a row — switches to single-note view. */
    onEditNote: (noteStr: string) => void
  }>()

  const sortedNotes = $derived(
    Object.keys(store.entries).map(Number).sort((a, b) => a - b)
  )
</script>

<div class="h-full flex flex-col">
  <div class="px-6 pt-5 pb-3 border-b border-gray-800 shrink-0">
    <p class="text-xs text-gray-500">Edit scene and loop names for all mapped notes at once.</p>
  </div>

  {#if sortedNotes.length === 0}
    <div class="flex-1 flex items-center justify-center">
      <p class="text-gray-600 text-sm">No notes mapped yet.</p>
    </div>
  {:else}
    <div class="flex-1 overflow-y-auto">
      <table class="w-full border-collapse">
        <thead>
          <tr class="text-xs text-gray-500 border-b border-gray-800 sticky top-0 bg-gray-950">
            <th class="px-6 py-2 text-left font-medium">Note</th>
            <th class="px-3 py-2 text-left font-medium w-24">Type</th>
            <th class="px-3 py-2 text-left font-medium">Scene / Prefix</th>
            <th class="px-3 py-2 w-14"></th>
          </tr>
        </thead>
        <tbody>
          {#each sortedNotes as note}
            {@const key = String(note)}
            {@const action = store.entries[key]}
            <tr class="border-b border-gray-800/40 hover:bg-gray-900/40 transition-colors group">

              <!-- Note number + name -->
              <td class="px-6 py-2.5">
                <span class="font-mono text-sm text-gray-200">{note}</span>
                <span class="text-xs text-gray-500 ml-1.5">{noteName(note)}</span>
              </td>

              <!-- Action type badge -->
              <td class="px-3 py-2.5">
                <span class="text-xs px-1.5 py-0.5 rounded
                  {action.action === 'loop'     ? 'bg-blue-900/60 text-blue-300'   :
                   action.action === 'static'   ? 'bg-green-900/60 text-green-300' :
                   action.action === 'sequence' ? 'bg-purple-900/60 text-purple-300' :
                   'bg-gray-700 text-gray-400'}"
                >{action.action}</span>
              </td>

              <!-- Editable name field -->
              <td class="px-3 py-2.5">
                {#if action.action === 'static'}
                  <input
                    type="text"
                    value={action.scene}
                    oninput={(e) => store.update(key, { ...action, scene: (e.target as HTMLInputElement).value })}
                    placeholder="Scene name"
                    class="w-full bg-transparent border border-transparent hover:border-gray-700 focus:border-gray-600 focus:bg-gray-800/60 rounded px-2 py-1 text-sm text-gray-200 outline-none transition-colors"
                  />
                {:else if action.action === 'loop'}
                  <input
                    type="text"
                    value={action.prefix}
                    oninput={(e) => store.update(key, { ...action, prefix: (e.target as HTMLInputElement).value })}
                    placeholder="Scene prefix"
                    class="w-full bg-transparent border border-transparent hover:border-gray-700 focus:border-gray-600 focus:bg-gray-800/60 rounded px-2 py-1 text-sm text-gray-200 outline-none transition-colors"
                  />
                {:else if action.action === 'sequence'}
                  <span class="text-sm text-gray-500 px-2">
                    {action.steps.length} step{action.steps.length !== 1 ? 's' : ''}
                  </span>
                {:else}
                  <span class="text-sm text-gray-600 px-2">—</span>
                {/if}
              </td>

              <!-- Edit link -->
              <td class="px-3 py-2.5 text-right">
                <button
                  onclick={() => onEditNote(key)}
                  class="text-xs text-gray-600 hover:text-blue-400 opacity-0 group-hover:opacity-100 transition-all"
                >Edit</button>
              </td>

            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
