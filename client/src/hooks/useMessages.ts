import { useRef, useEffect, useState } from 'react'
import { conversationQuery, createConversation } from '@/lib/api'
import type { Message, User, Conversation } from '@/lib/types'
import { formatMessageContents } from '@/lib/utils'

type Options = {
  user: User
  selectedConn?: string
  currentConvo: string | null
  setCurrentConvo: (id: string) => void
  messagesMap: Record<string, Message[]>
  setMessagesMap: React.Dispatch<React.SetStateAction<Record<string, Message[]>>>
  setConvos: React.Dispatch<React.SetStateAction<Conversation[]>>
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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messagesMap, currentConvo])

  const messages = messagesMap[currentConvo ?? ''] || []

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
        const { conversation_id } = await createConversation({
          user_id: user.id,
          db_connection_id: selectedConn,
          title: trimmed.slice(0, 20),
        })
        convoId = conversation_id
        setCurrentConvo(convoId)
        setConvos((prev) => [{ id: convoId!, title: trimmed.slice(0, 20) }, ...prev])
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
      const res = await conversationQuery(convoId!, {
        prompt: trimmed,
        available_charts: ['bar', 'line', 'pie'],
        model_name: 'gpt-4o-mini',
      })
      const assistantText = formatMessageContents(res.data.message)
      setMessagesMap((prev) => ({
        ...prev,
        [convoId!]: prev[convoId!].map((m) =>
          m.id === loadingId ? { ...m, content: assistantText, pending: false } : m
        ),
      }))
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
