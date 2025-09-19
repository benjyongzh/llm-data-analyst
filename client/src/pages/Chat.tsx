import { useEffect, useState } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import {
  listDbConnections,
  createDbConnection,
  updateDbConnection,
  enableDbConnection,
  disableDbConnection,
  logoutApi,
} from '@/lib/api'
import { ChatBubble } from '@/components/ChatBubble'
import { AppLayout } from '@/components/AppLayout'
import { ChatSidebar } from '@/components/ChatSidebar'
import { ChatInputBar } from '@/components/ChatInputBar'
import { useConversations } from '@/hooks/useConversations'
import { useMessages } from '@/hooks/useMessages'
import type { DBConnItem, User } from '@/lib/types'
import {cn} from "@/lib/utils.ts";

type Props = { user: User; onLoggedOut: () => void }

export default function Chat({ user, onLoggedOut }: Props) {
  const [dbConns, setDbConns] = useState<DBConnItem[]>([])
  const [selectedConn, setSelectedConn] = useState<string | undefined>()
  const [connOpen, setConnOpen] = useState(false)
  const [editingConn, setEditingConn] = useState<string | null>(null)
  const [useUrl, setUseUrl] = useState(false)
  const [connForm, setConnForm] = useState({
    db_name: '',
    host: '',
    port: 5432,
    user: '',
    password: '',
    url: '',
  })
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
    handleStop,
    streaming,
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
    let body
    try {
      if (useUrl) {
        body = { db_name: connForm.db_name, url: connForm.url, user_id: user.user_id }
      } else {
        const { url, ...rest } = connForm
        void url
        body = { ...rest, user_id: user.user_id }
      }

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

  const handleSelectConversation = (id: string) => {
    const convo = convos.find((c) => c.id === id)
    if (convo?.db_connection_id) {
      setSelectedConn(convo.db_connection_id ?? undefined)
    } else {
      setSelectedConn(undefined)
    }
    selectConvo(id)
  }

  const handleStartNewConversation = () => {
    setCurrentConvo(null)
    setSelectedConn(undefined)
  }

  const handleSelectConnection = (id: string) => {
    if (currentConvo) return
    setSelectedConn(id)
  }

  const openAddConn = () => {
    setEditingConn(null)
    setUseUrl(false)
    setConnForm({ db_name: '', host: '', port: 5432, user: '', password: '', url: '' })
    setConnOpen(true)
  }

  const openEditConn = (c: DBConnItem) => {
    setEditingConn(c.id)
    setUseUrl(false)
    setConnForm({
      db_name: c.db_name,
      host: c.host,
      port: c.port,
      user: c.user,
      password: '',
      url: '',
    })
    setConnOpen(true)
  }

  const handleLogout = async () => {
    setError(null)
    setMsgError(null)
    try {
      await logoutApi()
      onLoggedOut()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to log out')
    }
  }

  useEffect(() => {
    if (!currentConvo) {
      if (selectedConn !== undefined) setSelectedConn(undefined)
      return
    }
    const convo = convos.find((c) => c.id === currentConvo)
    if (convo?.db_connection_id && convo.db_connection_id !== selectedConn) {
      setSelectedConn(convo.db_connection_id ?? undefined)
    }
  }, [currentConvo, convos, selectedConn])

  const allError = error || msgError

  return (
    <AppLayout
      sidebarTitle="Chat"
      sidebar={
        <ChatSidebar
          dbConns={dbConns}
          convos={convos}
          currentConvo={currentConvo}
          onAddConnection={openAddConn}
          onToggleConnection={handleToggleConn}
          onEditConnection={openEditConn}
          onSelectConversation={handleSelectConversation}
          onStartNewConversation={handleStartNewConversation}
          onLogout={handleLogout}
        />
      }
    >
      <div className="flex flex-1 flex-col">
        {currentConvo ? (
          <ScrollArea className="flex-1 px-4 py-4">
            <div className="mx-auto flex w-full max-w-[var(--layout-max-width)] flex-col gap-3">
              {messages.map((m) => (
                <ChatBubble key={m.id} message={m} />
              ))}
              <div ref={bottomRef} />
            </div>
          </ScrollArea>
        ) : null}
        {allError && (
          <p className="mx-auto w-full max-w-[var(--layout-max-width)] px-4 text-sm text-red-500">
            {allError}
          </p>
        )}
        <div
          className={cn(
            'w-full',
            currentConvo ? undefined : 'flex flex-1 items-center justify-center px-4'
          )}
        >
          <ChatInputBar
            dbConns={dbConns}
            selectedConnId={selectedConn}
            onSelectConnection={handleSelectConnection}
            onAddConnection={openAddConn}
            inputValue={input}
            onInputChange={setInput}
            onSend={handleSend}
            onStop={handleStop}
            sending={sending}
            streaming={streaming}
            connectionLocked={currentConvo !== null}
          />
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
              onChange={(e) =>
                setConnForm({ ...connForm, db_name: e.target.value })
              }
            />
            <Separator />
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={useUrl}
                onChange={(e) => setUseUrl(e.target.checked)}
              />
              <span>Use database URL</span>
            </label>
            <Input
              placeholder="Database URL"
              value={connForm.url}
              onChange={(e) => setConnForm({ ...connForm, url: e.target.value })}
              disabled={!useUrl}
            />
            <Input
              placeholder="Host"
              value={connForm.host}
              onChange={(e) => setConnForm({ ...connForm, host: e.target.value })}
              disabled={useUrl}
            />
            <Input
              placeholder="Username"
              value={connForm.user}
              onChange={(e) => setConnForm({ ...connForm, user: e.target.value })}
              disabled={useUrl}
            />
            <Input
              placeholder="Password"
              type="password"
              value={connForm.password}
              onChange={(e) =>
                setConnForm({ ...connForm, password: e.target.value })
              }
              disabled={useUrl}
            />
            <Input
              placeholder="Port"
              type="number"
              value={connForm.port}
              onChange={(e) =>
                setConnForm({ ...connForm, port: Number(e.target.value) })
              }
              disabled={useUrl}
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
