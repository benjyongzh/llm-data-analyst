export type User = {
  user_id: string
  username: string
}

export type DBConnection = {
  db_name?: string
  user?: string
  password?: string
  host?: string
  port?: number
  url?: string
}

export type DBConnItem = {
  id: string
  db_name: string
  host: string
  port: number
  user: string
  enabled: boolean
}

export type XAxisSpec = {
  label: string
  dataType: 'category' | 'date' | 'numeric'
  values: (string | number)[]
  unit?: string
}

export type YAxisSpec = {
  label: string
  values: number[]
  unit?: string
}

export type ChartSpecification = {
  title: string
  xAxis: XAxisSpec
  yAxis: YAxisSpec[]
  chartTypes: string[]
}

export type MessageContent =
  | { type: 'text'; content: string }
  | { type: 'data'; content: ChartSpecification }

export type MessageRecord = {
  id: string
  conversation_id: string
  author: string
  user_id: string | null
  contents: MessageContent[]
  created_at: string
}

export type Conversation = {
  id: string
  user_id: string
  db_connection_id: string
  title: string | null
  model: string | null
  created_at: string
  updated_at: string
}

export type ConversationListItem = {
  id: string
  title: string | null
  db_connection_id?: string | null
}

export type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  pending?: boolean
}

export type QueryResponse = {
  status: string
  code: number
  data: { message: MessageContent[] }
  error?: string
}
