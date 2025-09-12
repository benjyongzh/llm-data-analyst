import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { cn } from '@/lib/utils'
import type { Message } from '@/lib/types'

export function ChatBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex w-full gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      )}
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-3 py-2 text-sm shadow-sm',
          isUser
            ? 'bg-primary text-primary-foreground rounded-br-sm'
            : 'bg-secondary text-secondary-foreground rounded-bl-sm'
        )}
      >
        <pre className="whitespace-pre-wrap break-words font-sans">
          {message.content}
        </pre>
        {message.pending && (
          <span className="inline-flex items-center gap-1 opacity-70">
            <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.2s]"></span>
            <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.1s]"></span>
            <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current"></span>
          </span>
        )}
      </div>
      {isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback>U</AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}
