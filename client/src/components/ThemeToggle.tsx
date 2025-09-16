import { Button } from '@/components/ui/button'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/components/ThemeProvider'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const prefersDark =
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches
  const isDark = theme === 'dark' || (theme === 'system' && prefersDark)
  const Icon = isDark ? Moon : Sun

  const handleToggle = () => {
    setTheme(isDark ? 'light' : 'dark')
  }

  return (
    <Button
      size="icon"
      variant="ghost"
      onClick={handleToggle}
      aria-label="Toggle dark mode"
    >
      <Icon className="h-4 w-4" />
    </Button>
  )
}
