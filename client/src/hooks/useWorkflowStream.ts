import { useEffect } from 'react'
import type { WorkflowEvent } from '@/lib/eventSchema'

export function useWorkflowStream(
  runId: string | null,
  sseUrl: string | null,
  onEvent: (event: WorkflowEvent) => void
) {
  useEffect(() => {
    if (!runId || !sseUrl) return
    const es = new EventSource(sseUrl)
    es.onmessage = (ev) => {
      const data: WorkflowEvent = JSON.parse(ev.data)
      onEvent(data)
    }
    es.onerror = () => {
      es.close()
    }
    return () => {
      es.close()
    }
  }, [runId, sseUrl, onEvent])
}
