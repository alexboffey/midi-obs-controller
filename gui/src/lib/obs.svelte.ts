/**
 * OBS WebSocket v5 connection store.
 *
 * Implements the protocol using the browser's native WebSocket API and
 * Web Crypto API — no npm dependency required.
 *
 * Protocol flow:
 *   1. Client connects  → Server sends Hello (op 0) with auth challenge
 *   2. Client sends Identify (op 1) with auth string (if password is set)
 *   3. Server sends Identified (op 2) → connection ready
 *   4. Client sends Request (op 6)   → Server sends RequestResponse (op 7)
 */

import { obsAuth } from './obsAuth.js'

const LS_OBS = 'midi-obs-ws-settings'

export type ObsStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

type ObsScene = { sceneName: string; sceneIndex: number }

class ObsStore {
  host     = $state('localhost')
  port     = $state(4455)
  password = $state('')
  status   = $state<ObsStatus>('disconnected')
  /** Scene names ordered top-to-bottom as they appear in OBS. */
  scenes   = $state<string[]>([])
  error    = $state('')

  private ws: WebSocket | null = null
  private pending = new Map<string, (data: unknown) => void>()

  // ── Persistence ─────────────────────────────────────────────────────────

  restoreSettings() {
    try {
      const raw = localStorage.getItem(LS_OBS)
      if (!raw) return
      const s = JSON.parse(raw) as Record<string, unknown>
      if (typeof s.host     === 'string') this.host     = s.host
      if (typeof s.port     === 'number') this.port     = s.port
      if (typeof s.password === 'string') this.password = s.password
    } catch { /* ignore corrupt data */ }
  }

  saveSettings() {
    localStorage.setItem(LS_OBS, JSON.stringify({
      host: this.host, port: this.port, password: this.password,
    }))
  }

  // ── Connection ───────────────────────────────────────────────────────────

  connect() {
    if (this.ws) this.disconnect()
    this.status = 'connecting'
    this.error  = ''
    this.saveSettings()

    let ws: WebSocket
    try {
      ws = new WebSocket(`ws://${this.host}:${this.port}`)
    } catch (e) {
      this.status = 'error'
      this.error  = String(e)
      return
    }
    this.ws = ws

    ws.onmessage = async (e: MessageEvent) => {
      try { await this.handleMessage(JSON.parse(e.data as string)) }
      catch { /* ignore malformed messages */ }
    }
    ws.onerror = () => {
      this.status = 'error'
      this.error  = `Could not connect to OBS at ${this.host}:${this.port}. ` +
                    `Is OBS running with WebSocket Server enabled?`
      this.ws = null
    }
    ws.onclose = () => {
      if (this.status !== 'error') this.status = 'disconnected'
      this.ws     = null
      this.scenes = []
    }
  }

  disconnect() {
    this.ws?.close()
    this.ws     = null
    this.status = 'disconnected'
    this.scenes = []
    this.error  = ''
  }

  async refreshScenes() {
    const data = await this.sendRequest<{ scenes: ObsScene[] }>('GetSceneList')
    if (data?.scenes) {
      // Higher sceneIndex = further down in OBS list; sort descending → top-first
      this.scenes = [...data.scenes]
        .sort((a, b) => b.sceneIndex - a.sceneIndex)
        .map(s => s.sceneName)
    }
  }

  // ── Internal protocol ────────────────────────────────────────────────────

  private async handleMessage(msg: { op: number; d: Record<string, unknown> }) {
    switch (msg.op) {
      case 0: { // Hello
        const d = msg.d as {
          rpcVersion: number
          authentication?: { challenge: string; salt: string }
        }
        let auth = ''
        if (d.authentication && this.password) {
          auth = await obsAuth(this.password, d.authentication.salt, d.authentication.challenge)
        }
        this.ws!.send(JSON.stringify({
          op: 1,
          d: { rpcVersion: 1, ...(auth ? { authentication: auth } : {}), eventSubscriptions: 0 },
        }))
        break
      }
      case 2: { // Identified — fully connected
        this.status = 'connected'
        await this.refreshScenes()
        break
      }
      case 7: { // RequestResponse
        const d = msg.d as {
          requestId: string
          requestStatus: { result: boolean }
          responseData?: unknown
        }
        const resolve = this.pending.get(d.requestId)
        if (resolve) {
          this.pending.delete(d.requestId)
          resolve(d.requestStatus.result ? d.responseData : null)
        }
        break
      }
    }
  }

  private sendRequest<T>(requestType: string): Promise<T | null> {
    return new Promise(resolve => {
      if (!this.ws) { resolve(null); return }
      const requestId = Math.random().toString(36).slice(2)
      this.pending.set(requestId, resolve as (d: unknown) => void)
      this.ws.send(JSON.stringify({ op: 6, d: { requestType, requestId } }))
    })
  }
}

export const obsStore = new ObsStore()
