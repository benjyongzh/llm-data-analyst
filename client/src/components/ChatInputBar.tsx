import { useEffect, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Database, Send, Square } from 'lucide-react'
import type { DBConnItem } from '@/lib/types'
import { cn } from '@/lib/utils'

type ChatInputBarProps = {
  dbConns: DBConnItem[]
  selectedConnId?: string
  onSelectConnection: (id: string) => void
  onAddConnection: () => void
  inputValue: string
  onInputChange: (value: string) => void
  onSend: () => void
  onStop: () => void
  sending: boolean
  streaming: boolean
  connectionLocked: boolean
}

export function ChatInputBar({
  dbConns,
  selectedConnId,
  onSelectConnection,
  onAddConnection,
  inputValue,
  onInputChange,
  onSend,
  onStop,
  sending,
  streaming,
  connectionLocked,
}: ChatInputBarProps) {
  const [connSelectOpen, setConnSelectOpen] = useState(false)

  const selectedConn = useMemo(
    () => dbConns.find((conn) => conn.id === selectedConnId)?.db_name,
    [dbConns, selectedConnId]
  )

  useEffect(() => {
    if (connectionLocked) setConnSelectOpen(false)
  }, [connectionLocked])

  const canSend = Boolean(selectedConnId) && !streaming
  const highlightConnection = !connectionLocked && !canSend
  const connectionLabel = selectedConn
    ? `Connected to ${selectedConn}`
    : connectionLocked
      ? 'Connection locked for current conversation'
      : 'Select database connection'

  const baseWrapper = 'mx-auto w-full max-w-[var(--layout-max-width)] px-4'
  const wrapperClasses = connectionLocked
    ? cn(baseWrapper, 'flex items-center gap-2 pb-4 pt-2')
    : cn(baseWrapper, 'flex flex-col items-center gap-6 py-10 text-center')

  const controlsClasses = connectionLocked
    ? 'flex w-full items-center gap-2'
    : 'flex w-full flex-col items-stretch gap-3 sm:flex-row sm:items-center'

  return (
    <div className={wrapperClasses}>
      {!connectionLocked && (
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold">Start a new chat</h2>
          <p className="text-sm text-muted-foreground">
            Choose a database connection to kick off your next analysis.
          </p>
        </div>
      )}
      <div className={controlsClasses}>
        <Popover
          open={connSelectOpen}
          onOpenChange={(open) => {
            if (connectionLocked) return
            setConnSelectOpen(open)
          }}
        >
          <PopoverTrigger asChild>
            <Button
              variant={highlightConnection ? 'default' : 'outline'}
              className={cn(
                'justify-start gap-2',
                connectionLocked ? 'w-[240px]' : 'w-full sm:w-[280px]',
                highlightConnection ? 'animate-pulse' : undefined
              )}
              aria-label={connectionLabel}
              disabled={connectionLocked}
              title={connectionLabel}
            >
              <Database className={highlightConnection ? 'text-primary-foreground' : undefined} />
              <span className="truncate">
                {selectedConn ?? (connectionLocked ? 'DB Connection' : 'Choose a database connection')}
              </span>
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[240px] p-0">
            <div className="flex flex-col">
              <Button
                variant="ghost"
                className="justify-start"
                onClick={() => {
                  onAddConnection()
                  setConnSelectOpen(false)
                }}
              >
                Add connection
              </Button>
              {dbConns.map((connection) => (
                <Button
                  key={connection.id}
                  variant="ghost"
                  className="justify-start"
                  disabled={!connection.enabled}
                  onClick={() => {
                    onSelectConnection(connection.id)
                    setConnSelectOpen(false)
                  }}
                >
                  {connection.db_name}
                </Button>
              ))}
            </div>
          </PopoverContent>
        </Popover>
        <Input
          className={cn('flex-1', connectionLocked ? '' : 'w-full sm:flex-1')}
          placeholder="Send a message..."
          value={inputValue}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && canSend) {
              event.preventDefault()
              onSend()
            }
          }}
        />
        <Button
          onClick={streaming ? onStop : onSend}
          disabled={streaming ? false : sending || !canSend}
          className={connectionLocked ? undefined : 'w-full sm:w-auto'}
          variant={streaming ? 'destructive' : 'default'}
          aria-label={streaming ? 'Stop response' : 'Send message'}
        >
          {streaming ? (
            <span className="flex items-center gap-2">
              <Square className="h-4 w-4" />
              <span className="hidden sm:inline">Stop</span>
            </span>
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}
