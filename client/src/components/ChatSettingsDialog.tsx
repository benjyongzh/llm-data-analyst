import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import type { DBConnItem } from '@/lib/types'

type ChatSettingsDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  dbConns: DBConnItem[]
  onAddConnection: () => void
  onToggleConnection: (id: string, enabled: boolean) => void
  onEditConnection: (connection: DBConnItem) => void
  onLogout: () => Promise<void> | void
}

export function ChatSettingsDialog({
  open,
  onOpenChange,
  dbConns,
  onAddConnection,
  onToggleConnection,
  onEditConnection,
  onLogout,
}: ChatSettingsDialogProps) {
  const handleAddConnection = () => {
    onAddConnection()
    onOpenChange(false)
  }

  const handleEditConnection = (connection: DBConnItem) => {
    onEditConnection(connection)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>Manage your workspace preferences.</DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Connections</h3>
              <Button size="sm" onClick={handleAddConnection}>
                Add
              </Button>
            </div>
            <div className="space-y-2">
              {dbConns.map((connection) => (
                <div
                  key={connection.id}
                  className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                >
                  <div>
                    <p className="font-medium">{connection.db_name}</p>
                    <p className="text-xs text-muted-foreground">{connection.host}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onToggleConnection(connection.id, connection.enabled)}
                    >
                      {connection.enabled ? 'Disable' : 'Enable'}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleEditConnection(connection)}>
                      Edit
                    </Button>
                  </div>
                </div>
              ))}
              {dbConns.length === 0 && (
                <p className="text-sm text-muted-foreground">No connections yet.</p>
              )}
            </div>
          </section>
          <Separator />
          <section className="space-y-3">
            <h3 className="text-sm font-semibold">Session</h3>
            <Button variant="destructive" onClick={() => onLogout()}>
              Log out
            </Button>
          </section>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Close</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

