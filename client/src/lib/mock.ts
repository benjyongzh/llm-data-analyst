import type { MessageContent, DBConnItem } from './types'

export const mockUser = {
  user_id: 'mock-user',
  username: 'mockuser',
}

export const mockConversations = [
  {
    id: 'mock-convo-1',
    user_id: mockUser.user_id,
    db_connection_id: 'mock-db-1',
    title: 'First mock conversation',
    model: 'gpt-4',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'mock-convo-2',
    user_id: mockUser.user_id,
    db_connection_id: 'mock-db-1',
    title: 'Second mock conversation',
    model: 'gpt-4',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
]

export const mockDbConnections: DBConnItem[] = [
  {
    id: 'mock-db-1',
    db_name: 'mockdb',
    host: 'localhost',
    port: 5432,
    user: 'postgres',
    enabled: true,
  },
]

type MockMessage = {
  id: string
  conversation_id: string
  author: string
  user_id: string | null
  contents: MessageContent[]
  created_at: string
}

export const mockMessages: MockMessage[] = [
  {
    id: 'mock-msg-1',
    conversation_id: 'mock-convo-1',
    author: 'user',
    user_id: mockUser.user_id,
    contents: [{ type: 'text', content: 'Hello there!' }],
    created_at: '2024-01-01T00:00:01Z',
  },
  {
    id: 'mock-msg-2',
    conversation_id: 'mock-convo-1',
    author: 'assistant',
    user_id: null,
    contents: [{ type: 'text', content: 'Hi! How can I assist you?' }],
    created_at: '2024-01-01T00:00:02Z',
  },
  {
    id: 'mock-msg-3',
    conversation_id: 'mock-convo-1',
    author: 'user',
    user_id: mockUser.user_id,
    contents: [{ type: 'text', content: 'Just testing the mock.' }],
    created_at: '2024-01-01T00:00:03Z',
  },
  {
    id: 'mock-msg-4',
    conversation_id: 'mock-convo-1',
    author: 'assistant',
    user_id: null,
    contents: [{ type: 'text', content: 'Looks good to me.' }],
    created_at: '2024-01-01T00:00:04Z',
  },
  {
    id: 'mock-msg-5',
    conversation_id: 'mock-convo-2',
    author: 'user',
    user_id: mockUser.user_id,
    contents: [{ type: 'text', content: 'What is the weather?' }],
    created_at: '2024-01-02T00:00:01Z',
  },
  {
    id: 'mock-msg-6',
    conversation_id: 'mock-convo-2',
    author: 'assistant',
    user_id: null,
    contents: [{ type: 'text', content: 'Sunny and warm today.' }],
    created_at: '2024-01-02T00:00:02Z',
  },
  {
    id: 'mock-msg-7',
    conversation_id: 'mock-convo-2',
    author: 'user',
    user_id: mockUser.user_id,
    contents: [{ type: 'text', content: 'Great, thanks!' }],
    created_at: '2024-01-02T00:00:03Z',
  },
  {
    id: 'mock-msg-8',
    conversation_id: 'mock-convo-2',
    author: 'assistant',
    user_id: null,
    contents: [{ type: 'text', content: 'Any time.' }],
    created_at: '2024-01-02T00:00:04Z',
  },
]

