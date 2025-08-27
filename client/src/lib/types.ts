export type User = {
  id: string
  username: string
}

export type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  pending?: boolean
}

export type DBConnItem = {
  id: string
  db_name: string
  host: string
  port: number
  user: string
  enabled: boolean
}

export type Conversation = {
  id: string
  title: string | null
}
