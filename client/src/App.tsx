import { useEffect, useState } from 'react'
import Login from '@/pages/Login'
import Chat from '@/pages/Chat'
import ThemeToggle from '@/components/ThemeToggle'
import type { User } from '@/lib/types'
import { currentUserApi } from '@/lib/api'
import { ThemeProvider } from '@/components/ThemeProvider.tsx'

export default function App() {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const checkUser = async () => {
      try {
        const u = await currentUserApi()
        setUser(u)
      } catch {
        setUser(null)
      }
    }
    checkUser()
  }, [])

  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <div className="fixed top-2 right-2">
        <ThemeToggle />
      </div>
      {user ? (
        <Chat
          user={user}
          onLoggedOut={() => {
            setUser(null)
          }}
        />
      ) : (
        <Login onLogin={setUser} />
      )}
    </ThemeProvider>
  )
}
