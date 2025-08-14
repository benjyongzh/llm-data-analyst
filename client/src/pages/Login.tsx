import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import { loginApi, registerApi } from '@/lib/api'

type Props = {
  onLogin: (user: { id: string; username: string }) => void
}

export default function Login({ onLogin }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [open, setOpen] = useState(false)
  const [reg, setReg] = useState({ name: '', email: '', password: '' })

  const handleLogin = async () => {
    const user = await loginApi({ username, password })
    onLogin({ id: user.user_id, username: user.username })
  }

  const handleRegister = async () => {
    await registerApi(reg)
    setOpen(false)
  }

  return (
    <div className="flex h-screen w-full items-center justify-center">
      <div className="w-80 space-y-4">
        <Input
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <div className="space-y-2">
          <Button className="w-full" onClick={handleLogin}>
            Login
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => setOpen(true)}
          >
            Create Account
          </Button>
        </div>
      </div>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Account</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Input
              placeholder="Username"
              value={reg.name}
              onChange={(e) => setReg({ ...reg, name: e.target.value })}
            />
            <Input
              placeholder="Email"
              value={reg.email}
              onChange={(e) => setReg({ ...reg, email: e.target.value })}
            />
            <Input
              type="password"
              placeholder="Password"
              value={reg.password}
              onChange={(e) => setReg({ ...reg, password: e.target.value })}
            />
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button onClick={handleRegister}>Register</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
