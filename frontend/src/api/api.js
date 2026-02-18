import axios from 'axios'

const API = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

export async function getSchemes({ page = 1, limit = 20, category, state, status } = {}) {
  const params = { page, limit }
  if (category) params.category = category
  if (state) params.state = state
  if (status) params.status = status
  const res = await API.get('/schemes', { params })
  return res.data
}

export async function getScheme(id) {
  const res = await API.get(`/schemes/${id}`)
  return res.data
}

export async function searchSchemes(query) {
  const res = await API.get('/search', { params: { q: query } })
  return res.data
}

export async function getCategories() {
  const res = await API.get('/categories')
  return res.data
}

export async function checkEligibility(profile) {
  const res = await API.post('/eligibility-check', profile)
  return res.data
}
