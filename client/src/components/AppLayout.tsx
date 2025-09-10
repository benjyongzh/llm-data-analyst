import type { ReactNode } from 'react'
import {
  Sidebar,
  SidebarContent,
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'

type Props = {
  sidebar: ReactNode
  children: ReactNode
}

export function AppLayout({ sidebar, children }: Props) {
  return (
    <SidebarProvider>
      <div className="flex h-dvh w-full">
        <Sidebar>
          <SidebarContent>{sidebar}</SidebarContent>
        </Sidebar>
        <SidebarInset>
          <SidebarTrigger className="absolute top-2 left-2 z-10 size-8" />
          {children}
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
