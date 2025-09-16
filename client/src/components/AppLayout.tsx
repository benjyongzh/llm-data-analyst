import type { ReactNode } from 'react'
import {
  Sidebar,
  SidebarContent,
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
  SidebarHeader,
} from '@/components/ui/sidebar'

type Props = {
  sidebar: ReactNode
  children: ReactNode
  sidebarTitle?: ReactNode
}

export function AppLayout({ sidebar, children, sidebarTitle }: Props) {
  return (
    <SidebarProvider>
      <div className="flex h-dvh w-full">
        <Sidebar>
          {sidebarTitle ? (
            <SidebarHeader className="px-4 py-4 text-lg font-semibold">
              {sidebarTitle}
            </SidebarHeader>
          ) : null}
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
