import { useEffect, useRef, useState } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Send, ChevronLeft, ChevronRight, Pencil } from 'lucide-react'
import {
  listDbConnections,
  listConversations,
  createDbConnection,
  updateDbConnection,
  enableDbConnection,
  disableDbConnection,
  createConversation,
  conversationQuery,
  getConversation,
} from '@/lib/api'
import { cn } from '@/lib/utils'

export type Message = { id: string; role: 'user' | 'assistant'; content: string; pending?: boolean }

type Props = { user: { id: string; username: string } }
type DBConnItem = { id: string; db_name: string; host: string; port: number; user: string; enabled: boolean }

function formatContent(content: { text?: string; response?: string; chart_spec?: Record<string, unknown> }): string {
  if (content?.text) return content.text
  if (content?.response) return content.response
  if (content?.chart_spec) return JSON.stringify(content.chart_spec, null, 2)
  return JSON.stringify(content)
}

function ChatBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex w-full gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback>AI</AvatarFallback>
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
          <AvatarFallback>U</AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}

export default function Chat({ user }: Props) {
  const [dbConns, setDbConns] = useState<DBConnItem[]>([])
  const [convos, setConvos] = useState<{ id: string; title: string | null }[]>([])
  const [selectedConn, setSelectedConn] = useState<string | undefined>()
  const [connOpen, setConnOpen] = useState(false)
  const [editingConn, setEditingConn] = useState<string | null>(null)
  const [connForm, setConnForm] = useState({ db_name: '', host: '', port: 5432, user: '', password: '' })
  const [currentConvo, setCurrentConvo] = useState<string | null>(null)
  const [messagesMap, setMessagesMap] = useState<Record<string, Message[]>>({})
  const [input, setInput] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [connLoading, setConnLoading] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const [dbs, convs] = await Promise.all([
          listDbConnections(),
          listConversations(),
        ])
        setDbConns(dbs)
        setConvos(convs)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
      }
    }
    load()
  }, [])

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
          { id: loadingId, role: 'assistant', content: '', pending: true },
        ],
      }))
      setInput('')
      const res = await conversationQuery(convoId!, {
        prompt: trimmed,
        available_charts: ['bar', 'line', 'pie'],
        model_name: 'gpt-4o-mini',
      })
      const assistantText = formatContent({ response: res.response, chart_spec: res.chart_spec })
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

  const refreshConns = async () => {
    try {
      setDbConns(await listDbConnections())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh connections')
    }
  }

  const handleSaveConn = async () => {
    setError(null)
    setConnLoading(true)
    const body = { ...connForm, user_id: user.id }
    try {
      if (editingConn) {
        await updateDbConnection(editingConn, body)
      } else {
        await createDbConnection(body)
      }
      await refreshConns()
      setConnOpen(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save connection')
    } finally {
      setConnLoading(false)
    }
  }

  const handleToggleConn = async (id: string, enabled: boolean) => {
    setError(null)
    try {
      if (enabled) await disableDbConnection(id, user.id)
      else await enableDbConnection(id, user.id)
      await refreshConns()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update connection')
    }
  }

  const openAddConn = () => {
    setEditingConn(null)
    setConnForm({ db_name: '', host: '', port: 5432, user: '', password: '' })
    setConnOpen(true)
  }

  const openEditConn = (c: DBConnItem) => {
    setEditingConn(c.id)
    setConnForm({ db_name: c.db_name, host: c.host, port: c.port, user: c.user, password: '' })
    setConnOpen(true)
  }

  const handleSelectConvo = async (id: string) => {
    setCurrentConvo(id)
    if (!messagesMap[id]) {
      try {
        const convo = await getConversation(id)
        setMessagesMap((prev) => ({
          ...prev,
          [id]: convo.messages.map((m) => ({
            id: m.id,
            role: m.role as 'user' | 'assistant',
            content: formatContent(m.content as {
              text?: string
              response?: string
              chart_spec?: Record<string, unknown>
            }),
          })),
        }))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load conversation')
      }
    }
  }

  return (
    <div className="flex h-dvh w-full">
      <div className={cn('border-r overflow-y-auto transition-all', sidebarOpen ? 'w-64' : 'w-0')}> 
        <div className={cn('p-2 space-y-2', sidebarOpen ? 'block' : 'hidden')}>
          <div className="flex items-center justify-between">
            <span className="font-semibold">Connections</span>
            <Button size="sm" onClick={openAddConn}>Add</Button>
          </div>
          {dbConns.map((c) => (
            <div key={c.id} className="flex items-center justify-between text-sm">
              <span>{c.db_name}</span>
              <div className="flex gap-1">
                <Button size="sm" variant="outline" onClick={() => handleToggleConn(c.id, c.enabled)}>
                  {c.enabled ? 'Disable' : 'Enable'}
                </Button>
                <Button size="sm" variant="outline" onClick={() => openEditConn(c)}>
                  <Pencil className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ))}
          <Separator className="my-2" />
          <div className="space-y-1">
            {convos.map((c) => (
              <div
                key={c.id}
                className={cn('p-2 cursor-pointer', c.id === currentConvo && 'bg-accent')}
                onClick={() => handleSelectConvo(c.id)}
              >
                {c.title || 'Untitled'}
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="flex flex-1 flex-col relative">
        <Button
          variant="outline"
          size="sm"
          className="absolute top-2 left-2 z-10 h-8 w-8 p-0"
          onClick={() => setSidebarOpen((o) => !o)}
        >
          {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </Button>
        <ScrollArea className="flex-1 px-4 py-4">
          <div className="flex flex-col gap-3">
            {messages.map((m) => (
              <ChatBubble key={m.id} message={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>
        {error && <p className="px-4 text-sm text-red-500">{error}</p>}
        <Separator />
        <div className="px-4 pb-4 pt-2 flex items-center gap-2">
          <Select
            value={selectedConn}
            onValueChange={(v: string) => {
              if (v === 'add') {
                openAddConn()
              } else {
                setSelectedConn(v)
              }
            }}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="DB Connection" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="add">Add connection</SelectItem>
              {dbConns.map((c) => (
                <SelectItem key={c.id} value={c.id} disabled={!c.enabled}>
                  {c.db_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            className="flex-1"
            placeholder="Send a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                handleSend()
              }
            }}
          />
          <Button onClick={handleSend} disabled={sending}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <Dialog open={connOpen} onOpenChange={setConnOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingConn ? 'Edit' : 'Add'} DB Connection</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Input
              placeholder="Database Name"
              value={connForm.db_name}
              onChange={(e) => setConnForm({ ...connForm, db_name: e.target.value })}
            />
            <Input
              placeholder="Host"
              value={connForm.host}
              onChange={(e) => setConnForm({ ...connForm, host: e.target.value })}
            />
            <Input
              placeholder="Port"
              type="number"
              value={connForm.port}
              onChange={(e) => setConnForm({ ...connForm, port: Number(e.target.value) })}
            />
            <Input
              placeholder="Username"
              value={connForm.user}
              onChange={(e) => setConnForm({ ...connForm, user: e.target.value })}
            />
            <Input
              placeholder="Password"
              type="password"
              value={connForm.password}
              onChange={(e) => setConnForm({ ...connForm, password: e.target.value })}
            />
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button onClick={handleSaveConn} disabled={connLoading}>
              {connLoading ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
