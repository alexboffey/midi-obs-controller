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
}

export const store = new ConfigStore()
