import { useState } from 'react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

type Props = {
  sidebar: ReactNode
  children: ReactNode
}

export function AppLayout({ sidebar, children }: Props) {
  const [open, setOpen] = useState(true)
  return (
    <div className="flex h-dvh w-full">
      <div className={cn('border-r overflow-y-auto transition-all', open ? 'w-64' : 'w-0')}>
        <div className={cn('p-2', open ? 'block' : 'hidden')}>{sidebar}</div>
      </div>
      <div className="flex flex-1 flex-col relative">
        <Button
          variant="outline"
          size="sm"
          className="absolute top-2 left-2 z-10 h-8 w-8 p-0"
          onClick={() => setOpen((o) => !o)}
        >
          {open ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </Button>
        {children}
      </div>
    </div>
  )
}
