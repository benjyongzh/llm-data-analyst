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

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    let message = 'Request failed'
    try {
      const data = await res.json()
      message = data?.detail || message
    } catch {
      message = res.statusText || message
    }
    throw new Error(message)
  }
  return (await res.json()) as T
}

export async function loginApi(body: { username: string; password: string }) {
  return fetchJson<{ user_id: string; username: string }>(`${API_BASE}/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
}

export async function registerApi(body: { name: string; email: string; password: string }) {
  return fetchJson<{ user_id: string }>(`${API_BASE}/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export async function listDbConnections() {
  return fetchJson<{ id: string; db_name: string; host: string; port: number; user: string; enabled: boolean }[]>(
    `${API_BASE}/db-connections`,
    {
      credentials: 'include',
    }
  )
}

export async function createDbConnection(body: DBConnection & { user_id: string }) {
  return fetchJson<{ db_connection_id: string }>(`${API_BASE}/db-connections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
}

export async function updateDbConnection(id: string, body: DBConnection & { user_id: string }) {
  return fetchJson<{ status: string }>(`${API_BASE}/db-connections/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
}

export async function enableDbConnection(id: string, user_id: string) {
  return fetchJson<{ status: string }>(`${API_BASE}/db-connections/${id}/enable`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id }),
    credentials: 'include',
  })
}

export async function disableDbConnection(id: string, user_id: string) {
  return fetchJson<{ status: string }>(`${API_BASE}/db-connections/${id}/disable`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id }),
    credentials: 'include',
  })
}

export async function listConversations() {
  return fetchJson<{ id: string; title: string | null }[]>(`${API_BASE}/conversations`, {
    credentials: 'include',
  })
}

export async function getConversation(id: string) {
  return fetchJson<{
    id: string
    title: string | null
    messages: { id: string; role: string; content: unknown }[]
  }>(`${API_BASE}/conversations/${id}`, {
    credentials: 'include',
  })
}

export async function createConversation(body: { user_id: string; db_connection_id: string; title?: string; model?: string }) {
  return fetchJson<{ conversation_id: string }>(`${API_BASE}/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
}

export async function conversationQuery(
  conversation_id: string,
  body: { prompt: string; available_charts: string[]; model_name: string }
) {
  return fetchJson<QueryResponse>(`${API_BASE}/conversations/${conversation_id}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
}
