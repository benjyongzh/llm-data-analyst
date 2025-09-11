export type WorkflowEvent = {
  type: 'agent_token' | 'agent_message' | 'step_update' | 'error' | 'done'
  conversation_id: string
  workflow_run_id: string
  step_id: string
  agent_id: string
  delta?: string
  content?: string
  state_patch?: Record<string, unknown>
  metadata?: Record<string, unknown>
}
