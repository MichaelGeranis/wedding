#!/usr/bin/env node
import axios from 'axios'

const base = process.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function axiosRetry(method, url, data = undefined, headers = {}, timeout = 3000, maxRetries = 3) {
  let attempt = 0
  while (true) {
    attempt++
    try {
      const res = await axios({ method, url, data, headers, timeout, validateStatus: () => true })
      if (res.status !== 429) return res
      if (attempt > maxRetries) return res
      const ra = res.headers && (res.headers['retry-after'] || res.headers['Retry-After'])
      let waitMs = 1000 * Math.pow(2, attempt)
      if (ra) {
        const parsed = parseInt(ra, 10)
        if (!Number.isNaN(parsed)) waitMs = parsed * 1000
      }
      console.warn(`axiosRetry: received 429 for ${method.toUpperCase()} ${url}, retrying after ${waitMs}ms (attempt ${attempt}/${maxRetries})`)
      await new Promise((r) => setTimeout(r, waitMs))
    } catch (err) {
      throw err
    }
  }
}

async function main() {
  try {
    const E2E_ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'demo-admin'
    const login = await axiosRetry('post', new URL('/api/admin/login', base).toString(), { password: E2E_ADMIN_PASSWORD }, {}, 3000, 3)
    if (!(login.status === 200 && login.data && login.data.access_token)) {
      console.error('Could not obtain admin token')
      process.exit(1)
    }
    const token = login.data.access_token
    const guestsRes = await axiosRetry('get', new URL('/api/admin/guests', base).toString(), undefined, { Authorization: `Bearer ${token}` }, 5000, 3)
    const guests = guestsRes.data.guests || []
    const toDelete = guests.filter(g => typeof g.guest_name === 'string' && g.guest_name.startsWith('E2E'))
    console.log('Found', toDelete.length, 'E2E guests to delete')
    for (const g of toDelete) {
      try {
        const del = await axiosRetry('delete', new URL(`/api/admin/guests/${g.id}`, base).toString(), undefined, { Authorization: `Bearer ${token}` }, 3000, 3)
        if (del.status === 204) console.log('Deleted', g.id, g.guest_name)
        else console.warn('Failed to delete', g.id, 'status=', del.status)
      } catch (err) {
        console.warn('Error deleting', g.id, err.message || err)
      }
    }
    console.log('Cleanup finished')
    process.exit(0)
  } catch (err) {
    console.error('Cleanup failed', err.response ? err.response.data : err.message)
    process.exit(2)
  }
}

main()
