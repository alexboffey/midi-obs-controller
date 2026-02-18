import type { ActionConfig } from './types.js'

class ConfigStore {
  entries: Record<string, ActionConfig> = $state({})

  add(noteStr: string, action: ActionConfig) {
    this.entries[noteStr] = action
  }

  remove(noteStr: string) {
    delete this.entries[noteStr]
  }

  update(noteStr: string, action: ActionConfig) {
    this.entries[noteStr] = action
  }

  /** Returns the next auto-incremented scene name, e.g. "Scene 3". */
  nextSceneName(): string {
    const count = Object.values(this.entries).filter(e => e.action === 'static').length
    return `Scene ${count + 1}`
  }

  /** Default action for a newly mapped note. */
  defaultAction(): ActionConfig {
    return { action: 'static', scene: this.nextSceneName() }
  }

  /** Replace all entries (used for import / localStorage restore). */
  load(data: Record<string, ActionConfig>) {
    for (const key of Object.keys(this.entries)) {
      delete this.entries[key]
    }
    for (const [key, value] of Object.entries(data)) {
      this.entries[key] = value
    }
  }
}

export const store = new ConfigStore()
