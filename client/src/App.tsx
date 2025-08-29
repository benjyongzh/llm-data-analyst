import { useEffect, useState } from 'react'
import Login from '@/pages/Login'
import Chat from '@/pages/Chat'
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

  if (!user) {
    return <Login onLogin={setUser} />
  }

  return <Chat user={user} />
}
