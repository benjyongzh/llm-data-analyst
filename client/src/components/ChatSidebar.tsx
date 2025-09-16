import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from '@/components/ui/sidebar'
import { cn } from '@/lib/utils'
import type { ConversationListItem, DBConnItem } from '@/lib/types'
import { ChatSettingsDialog } from '@/components/ChatSettingsDialog'
import { Settings, SquarePen } from 'lucide-react'

type ChatSidebarProps = {
  dbConns: DBConnItem[]
  convos: ConversationListItem[]
  currentConvo: string | null
  onAddConnection: () => void
  onToggleConnection: (id: string, enabled: boolean) => void
  onEditConnection: (connection: DBConnItem) => void
  onSelectConversation: (id: string) => void
  onStartNewConversation: () => void
  onLogout: () => Promise<void> | void
}

export function ChatSidebar({
  dbConns,
  convos,
  currentConvo,
  onAddConnection,
  onToggleConnection,
  onEditConnection,
  onSelectConversation,
  onStartNewConversation,
  onLogout,
}: ChatSidebarProps) {
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <>
      <div className="flex h-full flex-col gap-2">
        <SidebarGroup>
          <Button variant="ghost" className="w-full justify-start gap-2" onClick={onStartNewConversation}>
            <SquarePen className="h-4 w-4" />
            New chat
          </Button>
        </SidebarGroup>
        <SidebarGroup className="flex-1">
          <SidebarGroupLabel>Conversations</SidebarGroupLabel>
          <SidebarGroupContent className="space-y-1">
            {convos.map((conversation) => (
              <Button
                key={conversation.id}
                variant="ghost"
                className={cn(
                  'w-full justify-start gap-2 px-2 py-1 text-sm',
                  conversation.id === currentConvo && 'bg-primary'
                )}
                onClick={() => onSelectConversation(conversation.id)}
              >
                <span className="truncate">{conversation.title || 'Untitled'}</span>
              </Button>
            ))}
            {convos.length === 0 && (
              <p className="px-2 text-sm text-muted-foreground">No conversations yet.</p>
            )}
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <Button
            className="w-full justify-start gap-2"
            variant="outline"
            onClick={() => setSettingsOpen(true)}
          >
            <Settings className="h-4 w-4" />
            Settings
          </Button>
        </SidebarGroup>
      </div>
      <ChatSettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        dbConns={dbConns}
        onAddConnection={onAddConnection}
        onToggleConnection={onToggleConnection}
        onEditConnection={onEditConnection}
        onLogout={onLogout}
      />
    </>
  )
}

