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

export type QueryRequest = {
  prompt: string
  db_connection: DBConnection
  available_charts: string[]
  model_name: string
}

export type QueryResponse = {
  charts: ChartData[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function queryApi(body: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Request failed with ${res.status}`)
  }
  return (await res.json()) as QueryResponse
}

