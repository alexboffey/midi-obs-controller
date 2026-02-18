<script lang="ts">
  import { store } from '../lib/store.svelte.js'
  import type { SequenceAction, SequenceStepAction } from '../lib/types.js'
  import SequenceStepEditor from './SequenceStepEditor.svelte'

  let { noteStr } = $props<{ noteStr: string }>()

  const entry = $derived(store.entries[noteStr] as SequenceAction)

  function addStep() {
    const newStep: SequenceStepAction = {
      action: 'loop', prefix: 'LOOP_A_', style: 'cycle', bpm: 120, steps: 4, repeats: 1,
    }
    store.update(noteStr, { ...entry, steps: [...entry.steps, newStep] })
  }

  function removeStep(i: number) {
    const steps = entry.steps.filter((_, idx) => idx !== i)
    store.update(noteStr, { ...entry, steps })
  }

  function moveStep(i: number, dir: -1 | 1) {
    const j = i + dir
    if (j < 0 || j >= entry.steps.length) return
    const steps = [...entry.steps]
    ;[steps[i], steps[j]] = [steps[j], steps[i]]
    store.update(noteStr, { ...entry, steps })
  }

  function updateStep(i: number, newStep: SequenceStepAction) {
    const steps = entry.steps.map((s, idx) => (idx === i ? newStep : s))
    store.update(noteStr, { ...entry, steps })
  }

  const ACTION_COLORS: Record<SequenceStepAction['action'], string> = {
    loop:   'text-blue-400',
    pause:  'text-yellow-400',
    static: 'text-green-400',
    stop:   'text-red-400',
  }
</script>

<div class="space-y-3">
  {#if entry.steps.length === 0}
    <p class="text-sm text-gray-600 py-4 text-center">No steps yet — add one below.</p>
  {/if}

  {#each entry.steps as step, i}
    <div class="border border-gray-700 rounded-lg overflow-hidden">
      <!-- Step header -->
      <div class="flex items-center gap-2 px-3 py-2 bg-gray-800/60">
        <span class="text-xs font-mono text-gray-500 w-6 shrink-0">{i + 1}</span>
        <span class="text-xs font-semibold {ACTION_COLORS[step.action]} flex-1">{step.action}</span>
        <button
          onclick={() => moveStep(i, -1)}
          disabled={i === 0}
          class="text-gray-500 hover:text-gray-300 disabled:opacity-30 px-1 text-sm leading-none"
          title="Move up"
        >↑</button>
        <button
          onclick={() => moveStep(i, 1)}
          disabled={i === entry.steps.length - 1}
          class="text-gray-500 hover:text-gray-300 disabled:opacity-30 px-1 text-sm leading-none"
          title="Move down"
        >↓</button>
        <button
          onclick={() => removeStep(i)}
          class="text-gray-600 hover:text-red-400 px-1 text-sm leading-none"
          title="Remove step"
        >×</button>
      </div>
      <!-- Step editor -->
      <div class="p-3">
        <SequenceStepEditor {step} onUpdate={(s) => updateStep(i, s)} />
      </div>
    </div>
  {/each}

  <button
    onclick={addStep}
    class="w-full border border-dashed border-gray-700 hover:border-gray-500 text-gray-500 hover:text-gray-300 rounded-lg py-2 text-sm transition-colors"
  >+ Add step</button>

  {#if entry.steps.length > 0}
    {@const last = entry.steps[entry.steps.length - 1]}
    {#if last.action === 'loop'}
      <p class="text-xs text-gray-600">Last step is a loop — sequence wraps back to step 1 indefinitely.</p>
    {:else if last.action === 'pause'}
      <p class="text-xs text-yellow-700">Last step is a pause — sequence waits for resume then wraps.</p>
    {:else}
      <p class="text-xs text-gray-600">Sequence ends at the terminal <span class="text-gray-400">{last.action}</span> step.</p>
    {/if}
  {/if}
</div>
