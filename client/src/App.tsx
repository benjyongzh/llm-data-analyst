import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Send, Bot, User } from 'lucide-react'
import { queryApi, type QueryResponse, type QueryRequest } from '@/lib/api'

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  pending?: boolean
}

function ChatBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex w-full gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback>
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-3 py-2 text-sm shadow-sm',
          isUser
            ? 'bg-primary text-primary-foreground rounded-br-sm'
            : 'bg-secondary text-secondary-foreground rounded-bl-sm'
        )}
      >
        {message.pending ? (
          <span className="inline-flex items-center gap-1 opacity-70">
            <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.2s]"></span>
            <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.1s]"></span>
            <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current"></span>
          </span>
        ) : (
          <pre className="whitespace-pre-wrap break-words font-sans">{message.content}</pre>
        )}
      </div>
      {isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback>
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement | null>(null)

  // Demo defaults; adjust via env/inputs or hook to real settings UI.
  const defaults = useMemo<Pick<QueryRequest, 'db_connection' | 'available_charts' | 'model_name'>>(
    () => ({
      db_connection: {
        db_name: 'example_db',
        user: 'example_user',
        password: 'example_password',
        host: 'localhost',
        port: 5432,
      },
      available_charts: ['bar', 'line', 'pie'],
      model_name: 'gpt-4o-mini',
    }),
    []
  )

  useEffect(() => {
    // Auto-scroll to bottom on new messages
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages])

  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed) return

    const id = crypto.randomUUID()
    const loadingId = crypto.randomUUID()

    setMessages((prev) => [
      ...prev,
      { id, role: 'user', content: trimmed },
      { id: loadingId, role: 'assistant', content: '', pending: true },
    ])
    setInput('')

    try {
      const res: QueryResponse = await queryApi({
        prompt: trimmed,
        ...defaults,
      })

      // Render a compact summary of the response for the chat bubble.
      const assistantText = res.charts
        .map((c, i) => {
          const r = c.reasoning ? `\nReasoning: ${c.reasoning}` : ''
          return `Chart #${i + 1}: ${c.chart_type}${r}\nData: ${JSON.stringify(c.data, null, 2)}`
        })
        .join('\n\n') || 'No charts returned.'

      setMessages((prev) =>
        prev.map((m) => (m.id === loadingId ? { ...m, content: assistantText, pending: false } : m))
      )
    } catch (err: any) {
      const errorText = err?.message ? `Error: ${err.message}` : 'Unexpected error.'
      setMessages((prev) =>
        prev.map((m) => (m.id === loadingId ? { ...m, content: errorText, pending: false } : m))
      )
    }
  }, [input, defaults])

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-dvh w-full items-stretch">
      <div className="flex w-full flex-col">
        <header className="border-b px-4 py-2">
          <div className="mx-auto flex max-w-3xl items-center justify-between">
            <div className="font-semibold">LLM Data Analyst</div>
          </div>
        </header>

        <main className="flex min-h-0 flex-1">
          <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
            <ScrollArea className="flex-1 px-4 py-4">
              <div className="flex flex-col gap-3">
                {messages.length === 0 && (
                  <div className="text-center text-sm text-muted-foreground">
                    Ask a question about your data to get started.
                  </div>
                )}
                {messages.map((m) => (
                  <ChatBubble key={m.id} message={m} />
                ))}
                <div ref={bottomRef} />
              </div>
            </ScrollArea>
            <Separator />
            <div className="px-4 pb-4 pt-2">
              <div className="relative mx-auto flex max-w-3xl items-center gap-2">
                <Input
                  placeholder="Send a message..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                  className="pr-10"
                  aria-label="Chat input"
                />
                <button
                  type="button"
                  onClick={handleSend}
                  className="absolute right-2 inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
                  aria-label="Send"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
