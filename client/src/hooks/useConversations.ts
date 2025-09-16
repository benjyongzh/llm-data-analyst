import { useEffect, useState } from 'react'
import { getConversations, getConversation } from '@/lib/api'
import type { ConversationListItem, Message } from '@/lib/types'
import { formatMessageContents } from '@/lib/utils'

export function useConversations() {
  const [convos, setConvos] = useState<ConversationListItem[]>([])
  const [currentConvo, setCurrentConvo] = useState<string | null>(null)
  const [messagesMap, setMessagesMap] = useState<Record<string, Message[]>>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getConversations()
      .then(setConvos)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load conversations')
      )
  }, [])

  const selectConvo = async (id: string) => {
    setCurrentConvo(id)
    if (!messagesMap[id]) {
      try {
        const convo = await getConversation(id)
        setConvos((prev) =>
          prev.map((item) =>
            item.id === id
              ? { ...item, db_connection_id: convo.db_connection_id ?? item.db_connection_id }
              : item
          )
        )
        setMessagesMap((prev) => ({
          ...prev,
          [id]: convo.messages.map((m) => ({
            id: m.id,
            role: m.author === 'assistant' ? 'assistant' : 'user',
            content: formatMessageContents(m.contents),
          })),
        }))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load conversation')
      }
    }
  }

  return {
    convos,
    setConvos,
    currentConvo,
    setCurrentConvo,
    selectConvo,
    messagesMap,
    setMessagesMap,
    error,
    setError,
  }
}
