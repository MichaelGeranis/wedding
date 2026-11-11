import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth token on unauthorized
      localStorage.removeItem('authToken')
      window.location.href = '/admin'
    }
    return Promise.reject(error)
  }
)

// API methods
export const invitationAPI = {
  getInvitation: async () => {
    const response = await api.get('/invitation')
    return response.data
  },
}

export const rsvpAPI = {
  submitRSVP: async (rsvpData) => {
    const response = await api.post('/rsvp', rsvpData)
    return response.data
  },

  getGuestInfoByToken: async (token) => {
    const response = await api.get('/rsvp/guest-info', {
      params: { token },
    })
    return response.data
  },
}

export const adminAPI = {
  login: async (username, password) => {
    const response = await api.post('/admin/login', { username, password })
    return response.data
  },

  getGuests: async (params = {}) => {
    const response = await api.get('/admin/guests', { params })
    return response.data
  },

  getStats: async () => {
    const response = await api.get('/admin/stats')
    return response.data
  },

  deleteGuest: async (id) => {
    const response = await api.delete(`/admin/guests/${id}`)
    return response.status === 204
  },

  exportGuestsCSV: async (attending = null) => {
    const params = {}
    if (attending !== null) {
      params.attending = attending
    }

    const response = await api.get('/admin/guests/export/csv', {
      params,
      responseType: 'blob', // Important for file download
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url

    // Determine filename from response headers or use default
    const contentDisposition = response.headers['content-disposition']
    let filename = 'guests.csv'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  exportSummaryCSV: async () => {
    const response = await api.get('/admin/guests/export/summary', {
      responseType: 'blob', // Important for file download
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url

    // Determine filename from response headers or use default
    const contentDisposition = response.headers['content-disposition']
    let filename = 'wedding_rsvp_summary.csv'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}

export const invitedGuestsAPI = {
  getInvitedGuests: async () => {
    const response = await api.get('/admin/invited-guests')
    return response.data
  },

  getInvitedGuestsStats: async () => {
    const response = await api.get('/admin/invited-guests/stats')
    return response.data
  },

  createInvitedGuest: async (guestData) => {
    const response = await api.post('/admin/invited-guests', guestData)
    return response.data
  },

  updateInvitedGuest: async (id, guestData) => {
    const response = await api.put(`/admin/invited-guests/${id}`, guestData)
    return response.data
  },

  deleteInvitedGuest: async (id) => {
    const response = await api.delete(`/admin/invited-guests/${id}`)
    return response.status === 204
  },

  exportInvitedGuestsCSV: async () => {
    const response = await api.get('/admin/invited-guests/export/csv', {
      responseType: 'blob', // Important for file download
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url

    // Determine filename from response headers or use default
    const contentDisposition = response.headers['content-disposition']
    let filename = 'invited_guests.csv'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  downloadQRCode: async (guestId, guestName) => {
    const response = await api.get(`/admin/invited-guests/${guestId}/qr-code`, {
      responseType: 'blob', // Important for image download
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url

    // Determine filename from response headers or use default
    const contentDisposition = response.headers['content-disposition']
    let filename = `qr_code_${guestName.replace(/\s+/g, '_')}.png`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  importInvitedGuestsCSV: async (file) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/admin/invited-guests/import/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    return response.data
  },
}

export default api
