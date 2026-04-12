import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

function normalizeApiError(error) {
  const responseMessage = error.response?.data?.message

  if (error.code === 'ECONNABORTED') {
    return new Error('Backend timed out while processing the request.')
  }

  if (!error.response) {
    return new Error('Backend not reachable. Please ensure server is running.')
  }

  return new Error(responseMessage || 'API request failed.')
}

export async function sendQuery(query) {
  console.log('Sending query:', query)

  try {
    const response = await api.post('/query', { query })
    const payload = response.data

    if (!payload || typeof payload !== 'object') {
      throw new Error('Empty response received from backend.')
    }

    return payload
  } catch (error) {
    console.error('API Error:', error)

    if (error instanceof Error && error.message === 'Empty response received from backend.') {
      throw error
    }

    throw normalizeApiError(error)
  }
}
