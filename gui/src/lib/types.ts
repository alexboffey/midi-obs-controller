export type LoopStyle =
  | 'cycle'
  | 'bounce'
  | 'reverse'
  | 'once'
  | 'random'
  | 'random_no_repeat'
  | 'strobe'
  | 'shuffle'

export interface LoopAction {
  action: 'loop'
  prefix: string
  style: LoopStyle
  bpm: number
  steps: number
  repeats?: number
}

export interface StaticAction {
  action: 'static'
  scene: string
}

export interface StopAction {
  action: 'stop'
}

export interface PauseAction {
  action: 'pause'
  resume_note?: number
}

export type SequenceStepAction =
  | (LoopAction & { repeats: number })
  | StaticAction
  | StopAction
  | PauseAction

export interface SequenceAction {
  action: 'sequence'
  steps: SequenceStepAction[]
}

export type ActionConfig =
  | LoopAction
  | StaticAction
  | StopAction
  | PauseAction
  | SequenceAction
