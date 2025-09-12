import { useRef, useEffect, useState } from 'react'
import { createConversation, startChat } from '@/lib/api'
import type { Message, User, ConversationListItem } from '@/lib/types'
import type { WorkflowEvent } from '@/lib/eventSchema'
import { useWorkflowStream } from './useWorkflowStream'

type Options = {
  user: User
  selectedConn?: string
  currentConvo: string | null
  setCurrentConvo: (id: string) => void
  messagesMap: Record<string, Message[]>
  setMessagesMap: React.Dispatch<React.SetStateAction<Record<string, Message[]>>>
  setConvos: React.Dispatch<React.SetStateAction<ConversationListItem[]>>
}

export function useMessages({
  user,
  selectedConn,
  currentConvo,
  setCurrentConvo,
  messagesMap,
  setMessagesMap,
  setConvos,
}: Options) {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const [stream, setStream] = useState<
    | { runId: string; sseUrl: string; convoId: string; loadingId: string }
    | null
  >(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messagesMap, currentConvo])

  const messages = messagesMap[currentConvo ?? ''] || []

  const handleStreamEvent = (event: WorkflowEvent) => {
    if (!stream) return
    const { convoId, loadingId } = stream
    if (event.type === 'agent_token') {
      setMessagesMap((prev) => ({
        ...prev,
        [convoId]: prev[convoId].map((m) =>
          m.id === loadingId ? { ...m, content: (m.content || '') + (event.delta || '') } : m
        ),
      }))
    } else if (event.type === 'agent_message') {
      setMessagesMap((prev) => ({
        ...prev,
        [convoId]: prev[convoId].map((m) =>
          m.id === loadingId ? { ...m, content: event.content || '', pending: false } : m
        ),
      }))
    } else if (event.type === 'done') {
      setStream(null)
    }
  }

  useWorkflowStream(stream?.runId ?? null, stream?.sseUrl ?? null, handleStreamEvent)

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed) return
    setError(null)
    setSending(true)
    let convoId = currentConvo
    let loadingId: string | undefined
    try {
      if (!convoId) {
        if (!selectedConn) return
        const newId = crypto.randomUUID()
        const { conversation_id, title } = await createConversation({
          user_id: user.user_id,
          db_connection_id: selectedConn,
          conversation_id: newId,
          prompt: trimmed,
        })
        convoId = conversation_id
        setCurrentConvo(convoId)
        if (title) {
          setConvos((prev) => [{ id: convoId!, title }, ...prev])
        }
      }
      const id = crypto.randomUUID()
      loadingId = crypto.randomUUID()
      setMessagesMap((prev) => ({
        ...prev,
        [convoId!]: [
          ...(prev[convoId!] || []),
          { id, role: 'user', content: trimmed },
          { id: loadingId!, role: 'assistant', content: '', pending: true },
        ],
      }))
      setInput('')
      const { workflow_run_id, sse_url } = await startChat(convoId!, {
        prompt: trimmed,
        available_charts: [],
        model_name: 'gpt-4o-mini',
      })
      setStream({ runId: workflow_run_id, sseUrl: sse_url, convoId: convoId!, loadingId })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
      if (convoId && loadingId) {
        setMessagesMap((prev) => ({
          ...prev,
          [convoId!]: prev[convoId!].filter((m) => m.id !== loadingId),
        }))
      }
    } finally {
      setSending(false)
    }
  }

  return { messages, input, setInput, handleSend, sending, error, setError, bottomRef }
}
