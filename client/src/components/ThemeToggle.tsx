import { useState } from 'react'
import { Switch } from '@/components/ui/switch'

export default function ThemeToggle() {
  const [enabled, setEnabled] = useState(false)
  return <Switch checked={enabled} onCheckedChange={setEnabled} />
}
