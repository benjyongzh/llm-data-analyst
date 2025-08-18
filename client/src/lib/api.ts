export type DBConnection = {
  db_name: string
  user: string
  password: string
  host?: string
  port: number
}

export type ChartData = {
  chart_type: string
  data: unknown
  reasoning?: string | null
}

export type QueryResponse = {
  charts: ChartData[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function loginApi(body: { username: string; password: string }) {
  const res = await fetch(`${API_BASE}/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Login failed')
  return (await res.json()) as { user_id: string; username: string }
}

export async function registerApi(body: { name: string; email: string; password: string }) {
  const res = await fetch(`${API_BASE}/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error('Register failed')
  return (await res.json()) as { user_id: string }
}

export async function listDbConnections() {
  const res = await fetch(`${API_BASE}/db-connections`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to list connections')
  return (await res.json()) as { id: string; db_name: string; host: string; port: number; user: string; enabled: boolean }[]
}

export async function createDbConnection(body: DBConnection & { user_id: string }) {
  const res = await fetch(`${API_BASE}/db-connections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to create connection')
  return (await res.json()) as { db_connection_id: string }
}

export async function updateDbConnection(id: string, body: DBConnection & { user_id: string }) {
  const res = await fetch(`${API_BASE}/db-connections/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to update connection')
  return (await res.json()) as { status: string }
}

export async function enableDbConnection(id: string, user_id: string) {
  const res = await fetch(`${API_BASE}/db-connections/${id}/enable`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id }),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to enable connection')
  return (await res.json()) as { status: string }
}

export async function disableDbConnection(id: string, user_id: string) {
  const res = await fetch(`${API_BASE}/db-connections/${id}/disable`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id }),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to disable connection')
  return (await res.json()) as { status: string }
}

export async function listConversations() {
  const res = await fetch(`${API_BASE}/conversations`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to list conversations')
  return (await res.json()) as { id: string; title: string | null }[]
}

export async function getConversation(id: string) {
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to get conversation')
  return (await res.json()) as {
    id: string
    title: string | null
    messages: { id: string; role: string; content: unknown }[]
  }
}

export async function createConversation(body: { user_id: string; db_connection_id: string; title?: string; model?: string }) {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to create conversation')
  return (await res.json()) as { conversation_id: string }
}

export async function conversationQuery(conversation_id: string, body: { prompt: string; available_charts: string[]; model_name: string }) {
  const res = await fetch(`${API_BASE}/conversations/${conversation_id}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Query failed')
  return (await res.json()) as QueryResponse
}
