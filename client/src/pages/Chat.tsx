import { useEffect, useState } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { Send, Pencil } from 'lucide-react'
import {
  listDbConnections,
  createDbConnection,
  updateDbConnection,
  enableDbConnection,
  disableDbConnection,
} from '@/lib/api'
import { cn } from '@/lib/utils'
import { ChatBubble } from '@/components/ChatBubble'
import { AppLayout } from '@/components/AppLayout'
import { useConversations } from '@/hooks/useConversations'
import { useMessages } from '@/hooks/useMessages'
import type { DBConnItem, User } from '@/lib/types'

type Props = { user: User }

export default function Chat({ user }: Props) {
  const [dbConns, setDbConns] = useState<DBConnItem[]>([])
  const [selectedConn, setSelectedConn] = useState<string | undefined>()
  const [connOpen, setConnOpen] = useState(false)
  const [editingConn, setEditingConn] = useState<string | null>(null)
  const [connForm, setConnForm] = useState({ db_name: '', host: '', port: 5432, user: '', password: '' })
  const [connLoading, setConnLoading] = useState(false)

  const {
    convos,
    setConvos,
    currentConvo,
    setCurrentConvo,
    selectConvo,
    messagesMap,
    setMessagesMap,
    error,
    setError,
  } = useConversations()

  const {
    messages,
    input,
    setInput,
    handleSend,
    sending,
    error: msgError,
    setError: setMsgError,
    bottomRef,
  } = useMessages({
    user,
    selectedConn,
    currentConvo,
    setCurrentConvo,
    messagesMap,
    setMessagesMap,
    setConvos,
  })

  useEffect(() => {
    const load = async () => {
      try {
        setDbConns(await listDbConnections())
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
      }
    }
    load()
  }, [setError])

  const refreshConns = async () => {
    try {
      setDbConns(await listDbConnections())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh connections')
    }
  }

  const handleSaveConn = async () => {
    setError(null)
    setMsgError(null)
    setConnLoading(true)
    const body = { ...connForm, user_id: user.user_id }
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
      if (enabled) await disableDbConnection(id, user.user_id)
      else await enableDbConnection(id, user.user_id)
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

  const sidebar = (
    <div className="space-y-2">
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
            onClick={() => selectConvo(c.id)}
          >
            {c.title || 'Untitled'}
          </div>
        ))}
      </div>
    </div>
  )

  const allError = error || msgError

  return (
    <AppLayout sidebar={sidebar}>
      <ScrollArea className="flex-1 px-4 py-4">
        <div className="flex flex-col gap-3">
          {messages.map((m) => (
            <ChatBubble key={m.id} message={m} />
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
      {allError && <p className="px-4 text-sm text-red-500">{allError}</p>}
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
    </AppLayout>
  )
}
