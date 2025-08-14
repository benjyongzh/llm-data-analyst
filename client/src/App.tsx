import { useState } from 'react'
import Login from '@/pages/Login'
import Chat from '@/pages/Chat'

type User = { id: string; username: string }

export default function App() {
  const [user, setUser] = useState<User | null>(() => {
    const id = localStorage.getItem('user_id')
    const username = localStorage.getItem('username')
    return id && username ? { id, username } : null
  })

  if (!user) {
    return (
      <Login
        onLogin={(u) => {
          setUser(u)
          localStorage.setItem('user_id', u.id)
          localStorage.setItem('username', u.username)
        }}
      />
    )
  }

  return <Chat user={user} />
}
