export interface ApiErrorPayload {
  code: string
  detail: string
  fields?: Record<string, unknown>
}

export class ApiError extends Error {
  readonly code: string
  readonly fields?: Record<string, unknown>

  constructor(payload: ApiErrorPayload) {
    super(payload.detail)
    this.name = 'ApiError'
    this.code = payload.code
    this.fields = payload.fields
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem('access_token')
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`/api${path}`, { ...options, headers })
  const body: unknown = response.status === 204 ? undefined : await response.json()

  if (!response.ok) {
    const payload = body as Partial<ApiErrorPayload> | null
    throw new ApiError({
      code: payload?.code ?? 'REQUEST_FAILED',
      detail: payload?.detail ?? 'Não foi possível concluir a solicitação.',
      fields: payload?.fields,
    })
  }

  return body as T
}
