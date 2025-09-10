import { useEffect, useState } from 'react'
import Login from '@/pages/Login'
import Chat from '@/pages/Chat'
import ThemeToggle from '@/components/ThemeToggle'
import type { User } from '@/lib/types'
import { currentUserApi } from '@/lib/api'

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
    <>
      <div className="fixed top-2 right-2">
        <ThemeToggle />
      </div>
      {user ? <Chat user={user} /> : <Login onLogin={setUser} />}
    </>
  )
}
