import {
  DBConnection,
  MessageContent,
  QueryResponse,
  DBConnItem,
} from './types'
import {
  mockUser,
  mockConversations,
  mockMessages,
  mockDbConnections,
} from './mock'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const USE_MOCK_USER = import.meta.env.VITE_USE_MOCK_USER === 'true'
const USE_MOCK_CONVERSATIONS =
  import.meta.env.VITE_USE_MOCK_CONVERSATIONS === 'true'
const USE_MOCK_DB_CONNECTIONS =
  import.meta.env.VITE_USE_MOCK_DB_CONNECTIONS === 'true'

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
  if (USE_MOCK_USER) {
    return { user_id: mockUser.user_id, username: mockUser.username }
  }
  return fetchJson<{ user_id: string; username: string }>(`${API_BASE}/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
}

export async function logoutApi() {
  if (USE_MOCK_USER) {
    return { status: 'ok' }
  }
  return fetchJson<{ status: string }>(`${API_BASE}/users/logout`, {
    method: 'POST',
    credentials: 'include',
  })
}

export async function currentUserApi() {
  if (USE_MOCK_USER) {
    return { user_id: mockUser.user_id, username: mockUser.username }
  }
  return fetchJson<{ user_id: string; username: string }>(`${API_BASE}/users/me`, {
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
  if (USE_MOCK_DB_CONNECTIONS) {
    return mockDbConnections
  }
  return fetchJson<DBConnItem[]>(`${API_BASE}/db-connections`, {
    credentials: 'include',
  })
}

export async function createDbConnection(body: DBConnection & { user_id: string }) {
  if (USE_MOCK_DB_CONNECTIONS) {
    const id = crypto.randomUUID()
    mockDbConnections.push({
      id,
      db_name: body.db_name,
      host: body.host ?? 'localhost',
      port: body.port,
      user: body.user,
      enabled: true,
    })
    return { db_connection_id: id }
  }
  return fetchJson<{ db_connection_id: string }>(`${API_BASE}/db-connections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
}

export async function updateDbConnection(id: string, body: DBConnection & { user_id: string }) {
  if (USE_MOCK_DB_CONNECTIONS) {
    const conn = mockDbConnections.find((c) => c.id === id)
    if (conn) {
      conn.db_name = body.db_name
      conn.host = body.host ?? 'localhost'
      conn.port = body.port
      conn.user = body.user
    }
    return { status: 'ok' }
  }
  return fetchJson<{ status: string }>(`${API_BASE}/db-connections/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  })
}

export async function enableDbConnection(id: string, user_id: string) {
  if (USE_MOCK_DB_CONNECTIONS) {
    const conn = mockDbConnections.find((c) => c.id === id)
    if (conn) conn.enabled = true
    return { status: 'ok' }
  }
  return fetchJson<{ status: string }>(`${API_BASE}/db-connections/${id}/enable`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id }),
    credentials: 'include',
  })
}

export async function disableDbConnection(id: string, user_id: string) {
  if (USE_MOCK_DB_CONNECTIONS) {
    const conn = mockDbConnections.find((c) => c.id === id)
    if (conn) conn.enabled = false
    return { status: 'ok' }
  }
  return fetchJson<{ status: string }>(`${API_BASE}/db-connections/${id}/disable`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id }),
    credentials: 'include',
  })
}

export async function deleteDbConnection(id: string, user_id: string) {
  if (USE_MOCK_DB_CONNECTIONS) {
    const idx = mockDbConnections.findIndex((c) => c.id === id)
    if (idx !== -1) mockDbConnections.splice(idx, 1)
    return { status: 'ok' }
  }
  return fetchJson<{ status: string }>(`${API_BASE}/db-connections/${id}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id }),
    credentials: 'include',
  })
}

export async function getConversations() {
  if (USE_MOCK_CONVERSATIONS) {
    return mockConversations.map(({ id, title }) => ({ id, title }))
  }
  return fetchJson<{ id: string; title: string | null }[]>(`${API_BASE}/conversations`, {
    credentials: 'include',
  })
}

export async function getConversation(id: string) {
  if (USE_MOCK_CONVERSATIONS) {
    const convo = mockConversations.find((c) => c.id === id)
    const messages = mockMessages
      .filter((m) => m.conversation_id === id)
      .map(({ id, author, user_id, contents }) => ({ id, author, user_id, contents }))
    return { id, title: convo?.title ?? null, messages }
  }
  return fetchJson<{
    id: string
    title: string | null
    messages: { id: string; author: string; user_id: string | null; contents: MessageContent[] }[]
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
