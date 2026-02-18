<script lang="ts">
  import { store } from "../lib/store.svelte.js";
  import { noteName } from "../lib/noteNames.js";
  import type { ActionConfig } from "../lib/types.js";
  import LoopEditor from "./LoopEditor.svelte";
  import StaticEditor from "./StaticEditor.svelte";
  import SequenceEditor from "./SequenceEditor.svelte";

  let { noteStr } = $props<{ noteStr: string }>();

  const entry = $derived(store.entries[noteStr]);

  const ACTION_LABELS: Record<ActionConfig["action"], string> = {
    loop: "Loop",
    static: "Static scene",
    sequence: "Sequence",
    stop: "Stop",
    pause: "Pause",
  };

  function setActionType(type: ActionConfig["action"]) {
    if (type === "loop") {
      store.update(noteStr, {
        action: "loop",
        prefix: "LOOP_A_",
        style: "cycle",
        bpm: 120,
        steps: 4,
      });
    } else if (type === "static") {
      store.update(noteStr, { action: "static", scene: "" });
    } else if (type === "sequence") {
      store.update(noteStr, { action: "sequence", steps: [] });
    }
  }
</script>

{#if entry}
  <div class="space-y-6">
    <!-- Note heading -->
    <div class="flex items-baseline gap-3">
      <h2 class="text-2xl font-bold text-white font-mono">{noteStr}</h2>
      <span class="text-gray-400 text-lg">{noteName(parseInt(noteStr))}</span>
    </div>

    <!-- Action type picker -->
    <div>
      <label
        class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2"
        >Action type</label
      >
      <div class="flex gap-2 flex-wrap">
        {#each ["static", "loop", "sequence"] as const as type}
          <button
            onclick={() => setActionType(type)}
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors
              {entry.action === type
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'}"
            >{ACTION_LABELS[type]}</button
          >
        {/each}
      </div>
    </div>

    <!-- Divider -->
    <div class="border-t border-gray-800"></div>

    <!-- Sub-editor -->
    {#if entry.action === "loop"}
      <LoopEditor {noteStr} />
    {:else if entry.action === "static"}
      <StaticEditor {noteStr} />
    {:else if entry.action === "sequence"}
      <SequenceEditor {noteStr} />
    {/if}
  </div>
{:else}
  <div class="flex items-center justify-center h-full">
    <p class="text-gray-600">Select a note to edit it</p>
  </div>
{/if}
