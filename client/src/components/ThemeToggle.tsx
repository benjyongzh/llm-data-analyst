import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Moon, Sun } from 'lucide-react'

export default function ThemeToggle() {
  const [enabled, setEnabled] = useState(false)
  const Icon = enabled ? Moon : Sun

  return (
    <Button
      size="icon"
      variant="outline"
      onClick={() => setEnabled(!enabled)}
      aria-label="Toggle dark mode"
    >
      <Icon className="h-4 w-4" />
    </Button>
  )
}
