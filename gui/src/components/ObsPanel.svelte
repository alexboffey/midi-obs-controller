<script lang="ts">
  import { obsStore } from '../lib/obs.svelte.js'
  import { store } from '../lib/store.svelte.js'
  import { noteName } from '../lib/noteNames.js'

  let { pendingScene, onSceneClick } = $props<{
    /** The OBS scene queued for the next note press (highlighted in the list). */
    pendingScene: string | null
    onSceneClick: (scene: string) => void
  }>()

  /** Map from scene name → note string for scenes already assigned. */
  const sceneAssignments = $derived(
    Object.entries(store.entries).reduce<Record<string, string>>((acc, [note, action]) => {
      if (action.action === 'static') acc[action.scene] = note
      return acc
    }, {})
  )

  const statusColour = $derived(
    obsStore.status === 'connected'   ? 'bg-green-400'  :
    obsStore.status === 'connecting'  ? 'bg-yellow-400' :
    obsStore.status === 'error'       ? 'bg-red-500'    :
    'bg-gray-600'
  )
</script>

<aside class="w-64 bg-gray-900 border-l border-gray-800 flex flex-col shrink-0 overflow-hidden">

  <!-- Connection panel -->
  <div class="px-4 pt-4 pb-3 border-b border-gray-800 shrink-0">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">OBS Scenes</h2>
      <span class="w-2 h-2 rounded-full {statusColour}"></span>
    </div>

    <div class="space-y-1.5">
      <!-- Host + port on one line -->
      <div class="flex gap-1.5">
        <input
          type="text"
          bind:value={obsStore.host}
          placeholder="localhost"
          class="flex-1 min-w-0 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 placeholder-gray-600"
          title="OBS WebSocket host"
        />
        <input
          type="number"
          bind:value={obsStore.port}
          placeholder="4455"
          class="w-16 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200"
          title="OBS WebSocket port"
        />
      </div>

      <input
        type="password"
        bind:value={obsStore.password}
        placeholder="Password (if set)"
        autocomplete="off"
        class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 placeholder-gray-600"
        title="OBS WebSocket password"
      />

      <!-- Connect / Disconnect + Refresh -->
      <div class="flex gap-1.5 pt-0.5">
        {#if obsStore.status === 'connected'}
          <button
            onclick={() => obsStore.disconnect()}
            class="flex-1 bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1 rounded text-xs font-medium transition-colors"
          >Disconnect</button>
          <button
            onclick={() => obsStore.refreshScenes()}
            class="bg-gray-700 hover:bg-gray-600 text-gray-400 px-2 py-1 rounded text-xs transition-colors"
            title="Refresh scene list"
          >↺</button>
        {:else}
          <button
            onclick={() => obsStore.connect()}
            disabled={obsStore.status === 'connecting'}
            class="flex-1 bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
          >{obsStore.status === 'connecting' ? 'Connecting…' : 'Connect'}</button>
        {/if}
      </div>

      {#if obsStore.error}
        <p class="text-xs text-red-400 leading-relaxed pt-0.5">{obsStore.error}</p>
      {/if}
    </div>
  </div>

  <!-- Scene list -->
  <div class="flex-1 overflow-y-auto">
    {#if obsStore.status !== 'connected'}
      <div class="px-4 py-8 text-center">
        <p class="text-xs text-gray-600 leading-relaxed">
          Connect to OBS to browse<br />available scenes
        </p>
      </div>

    {:else if obsStore.scenes.length === 0}
      <p class="px-4 py-4 text-xs text-gray-600">No scenes found in OBS.</p>

    {:else}
      <ul class="py-1">
        {#each obsStore.scenes as scene}
          {@const assignedNote = sceneAssignments[scene]}
          {@const isPending    = pendingScene === scene}
          <li>
            <button
              onclick={() => onSceneClick(scene)}
              class="w-full flex items-center justify-between px-3 py-2 text-sm text-left transition-colors
                {isPending
                  ? 'bg-blue-600 text-white'
                  : assignedNote
                    ? 'text-gray-400 hover:bg-gray-800'
                    : 'text-gray-200 hover:bg-gray-800'}"
            >
              <span class="truncate min-w-0">{scene}</span>
              {#if assignedNote}
                <span class="text-xs ml-2 shrink-0 tabular-nums
                  {isPending ? 'text-blue-200' : 'text-gray-600'}"
                >{assignedNote} {noteName(Number(assignedNote))}</span>
              {/if}
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </div>

  <!-- Pending assignment hint -->
  {#if pendingScene}
    <div class="px-4 py-2.5 border-t border-gray-800 shrink-0 bg-blue-900/20">
      <p class="text-xs text-blue-400 leading-relaxed">
        Press a pad to assign<br />
        <span class="font-medium text-blue-300">{pendingScene}</span>
      </p>
    </div>
  {/if}

</aside>
