/**
 * Pure business logic for OBS scene assignment.
 * No Svelte dependencies — safe to import in unit tests.
 */

import type { ActionConfig } from './types.js'

/** Returns the set of scene names currently used as static actions. */
export function assignedScenes(entries: Record<string, ActionConfig>): Set<string> {
  const result = new Set<string>()
  for (const action of Object.values(entries)) {
    if (action.action === 'static') result.add(action.scene)
  }
  return result
}

/**
 * Finds the next OBS scene (from `startIdx` onwards) that is not already
 * assigned as a static action in `entries`.
 * Returns `null` when all scenes from `startIdx` onwards are assigned.
 */
export function nextUnassignedScene(
  scenes: string[],
  entries: Record<string, ActionConfig>,
  startIdx = 0,
): string | null {
  const used = assignedScenes(entries)
  for (let i = startIdx; i < scenes.length; i++) {
    if (!used.has(scenes[i])) return scenes[i]
  }
  return null
}
