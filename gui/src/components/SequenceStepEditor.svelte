<script lang="ts">
  import type { SequenceStepAction, LoopStyle } from '../lib/types.js'

  let { step, onUpdate } = $props<{
    step: SequenceStepAction
    onUpdate: (s: SequenceStepAction) => void
  }>()

  const LOOP_STYLES: LoopStyle[] = [
    'cycle', 'bounce', 'reverse', 'once',
    'random', 'random_no_repeat', 'strobe', 'shuffle',
  ]

  function setType(type: SequenceStepAction['action']) {
    if (type === 'loop') {
      onUpdate({ action: 'loop', prefix: 'LOOP_A_', style: 'cycle', bpm: 120, steps: 4, repeats: 1 })
    } else if (type === 'pause') {
      onUpdate({ action: 'pause' })
    } else if (type === 'static') {
      onUpdate({ action: 'static', scene: '' })
    } else {
      onUpdate({ action: 'stop' })
    }
  }
</script>

<div class="space-y-3">
  <div>
    <label class="block text-xs text-gray-500 mb-1">Step type</label>
    <select
      value={step.action}
      onchange={(e) => setType((e.target as HTMLSelectElement).value as SequenceStepAction['action'])}
      class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300"
    >
      <option value="loop">loop</option>
      <option value="pause">pause</option>
      <option value="static">static</option>
      <option value="stop">stop</option>
    </select>
  </div>

  {#if step.action === 'loop'}
    <div class="grid grid-cols-2 gap-2">
      <div class="col-span-2">
        <label class="block text-xs text-gray-500 mb-1">Prefix</label>
        <input
          type="text"
          value={step.prefix}
          oninput={(e) => onUpdate({ ...step, prefix: (e.target as HTMLInputElement).value })}
          placeholder="LOOP_A_"
          class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300 font-mono placeholder-gray-700"
        />
      </div>
      <div class="col-span-2">
        <label class="block text-xs text-gray-500 mb-1">Style</label>
        <select
          value={step.style}
          onchange={(e) => onUpdate({ ...step, style: (e.target as HTMLSelectElement).value as LoopStyle })}
          class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300"
        >
          {#each LOOP_STYLES as s}
            <option value={s}>{s}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">BPM</label>
        <input
          type="number" min="1" value={step.bpm}
          oninput={(e) => onUpdate({ ...step, bpm: parseFloat((e.target as HTMLInputElement).value) || 120 })}
          class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300"
        />
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">Steps</label>
        <input
          type="number" min="1" value={step.steps}
          oninput={(e) => onUpdate({ ...step, steps: parseFloat((e.target as HTMLInputElement).value) || 1 })}
          class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300"
        />
      </div>
      <div class="col-span-2">
        <label class="block text-xs text-gray-500 mb-1">Repeats</label>
        <input
          type="number" min="1" value={step.repeats ?? 1}
          oninput={(e) => onUpdate({ ...step, repeats: parseInt((e.target as HTMLInputElement).value) || 1 })}
          class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300"
        />
      </div>
    </div>

  {:else if step.action === 'pause'}
    <div>
      <label class="block text-xs text-gray-500 mb-1">Resume note <span class="text-gray-600">(optional — defaults to trigger note)</span></label>
      <input
        type="number"
        min="0"
        max="127"
        value={step.resume_note ?? ''}
        placeholder="Leave blank to use trigger note"
        oninput={(e) => {
          const v = (e.target as HTMLInputElement).value
          onUpdate(v === '' ? { action: 'pause' } : { action: 'pause', resume_note: parseInt(v) })
        }}
        class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300 placeholder-gray-700"
      />
    </div>

  {:else if step.action === 'static'}
    <div>
      <label class="block text-xs text-gray-500 mb-1">Scene name</label>
      <input
        type="text"
        value={step.scene}
        oninput={(e) => onUpdate({ action: 'static', scene: (e.target as HTMLInputElement).value })}
        placeholder="e.g. STATIC_1"
        class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300 font-mono placeholder-gray-700"
      />
      <p class="text-xs text-gray-700 mt-1">Terminal — sequence ends here</p>
    </div>

  {:else if step.action === 'stop'}
    <p class="text-xs text-gray-600">Ends the sequence silently without changing the current scene.</p>
  {/if}
</div>
