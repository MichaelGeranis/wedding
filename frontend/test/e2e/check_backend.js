#!/usr/bin/env node
/**
 * Simple E2E check: verify frontend can connect to backend by calling /health
 * Usage:
 *   VITE_API_BASE_URL=http://localhost:8000 npm run test:e2e
 */
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
    const url = new URL('/health', base).toString()
    console.log(`Checking backend health at ${url}`)
    const res = await axios.get(url, {timeout: 3000})
    if (res.status === 200 && res.data && res.data.status === 'healthy') {
      console.log('E2E check passed: backend reachable and healthy')
    } else {
      console.error('E2E check failed: unexpected response', res.status, res.data)
      process.exit(2)
    }

    // Next, POST a sample RSVP to /api/rsvp to validate API base path connectivity
    try {
      const rsvpUrl = new URL('/api/rsvp', base).toString()
      const unique = Date.now() + Math.floor(Math.random() * 1000)
      const payload = {
        guest_name: 'E2E Test',
        email: `e2e+${unique}@example.com`,
        attending: false,
      }

      console.log(`Posting sample RSVP to ${rsvpUrl} with email ${payload.email}`)
      const r2 = await axios.post(rsvpUrl, payload, {timeout: 3000, validateStatus: (s) => s === 201 || s === 409})
      // capture created id for cleanup if present
      let createdId = null
      if (r2.status === 201 && r2.data && r2.data.confirmation_number) {
        console.log('E2E RSVP check passed: /api/rsvp accepted sample request')
        if (r2.data.id) createdId = r2.data.id
      } else if (r2.status === 409) {
        console.log('E2E RSVP check: duplicate detected (409) which indicates endpoint is reachable')
      } else {
        console.error('E2E RSVP check failed: unexpected response', r2.status, r2.data)
        process.exit(3)
      }

      // CORS preflight check (OPTIONS)
      try {
        const origin = 'http://localhost:5173'
        console.log(`Sending CORS preflight OPTIONS to ${rsvpUrl} with Origin ${origin}`)
        const opts = await axios.options(rsvpUrl, {
          headers: {
            Origin: origin,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type',
          },
          validateStatus: () => true,
          timeout: 2000,
        })

        const allow = opts.headers['access-control-allow-origin']
        if (!allow) {
          console.error('CORS check failed: no Access-Control-Allow-Origin header')
          process.exit(5)
        }
        console.log('CORS check passed, allowed origin header:', allow)
      } catch (err) {
        console.error('CORS check failed:', err.message || err)
        process.exit(6)
      }

      // Admin auth check: try invalid then valid login
      try {
        const adminUrl = new URL('/api/admin/login', base).toString()
        console.log('Testing admin login incorrect credentials')
        try {
          await axios.post(adminUrl, {password: 'wrongpass'}, {timeout: 3000})
          console.error('Admin login with wrong password unexpectedly succeeded')
          process.exit(7)
        } catch (err) {
          if (err.response && err.response.status === 401) {
            console.log('Admin login rejected invalid credentials (expected)')
          } else {
            console.error('Admin login error (unexpected):', err.message || err)
            process.exit(8)
          }
        }

        console.log('Testing admin login with correct password')
        const E2E_ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'demo-admin'
        const good = await axiosRetry('post', adminUrl, { password: E2E_ADMIN_PASSWORD }, {}, 3000, 3)
        if (good.status === 200 && good.data && good.data.access_token) {
          console.log('Admin auth check passed: received access token')
          // attempt to cleanup the created RSVP if we created one
          if (createdId) {
            try {
              const token = good.data.access_token
              const delUrl = new URL(`/api/admin/guests/${createdId}`, base).toString()
              const d = await axios.delete(delUrl, { headers: { Authorization: `Bearer ${token}` }, validateStatus: () => true })
              if (d.status === 204) console.log(`Cleanup: deleted created RSVP ${createdId}`)
              else console.warn(`Cleanup: failed to delete ${createdId} status=${d.status}`)
            } catch (err) {
              console.warn('Cleanup delete error', err.message || err)
            }
          } else if (payload && payload.email) {
            // fallback: find guest by email via admin list and delete
            try {
              const token = good.data.access_token
              const listUrl = new URL('/api/admin/guests', base).toString()
              const listRes = await axiosRetry('get', listUrl, undefined, { Authorization: `Bearer ${token}` }, 5000, 3)
              if (listRes.status === 200 && Array.isArray(listRes.data.guests)) {
                const matches = listRes.data.guests.filter(g => g.email === payload.email)
                for (const m of matches) {
                  try {
                    const delUrl = new URL(`/api/admin/guests/${m.id}`, base).toString()
                    const d = await axiosRetry('delete', delUrl, undefined, { Authorization: `Bearer ${token}` }, 3000, 3)
                    if (d.status === 204) console.log(`Cleanup: deleted guest ${m.id} (${m.email})`)
                    else console.warn(`Cleanup: failed to delete ${m.id} status=${d.status}`)
                  } catch (err) {
                    console.warn('Cleanup delete error', err.message || err)
                  }
                }
              }
            } catch (err) {
              console.warn('Cleanup by email failed', err.message || err)
            }
          }
          process.exit(0)
        }

        console.error('Admin auth check failed: unexpected response', good.status, good.data)
        process.exit(9)
      } catch (err) {
        console.error('Admin auth check failed:', err.message || err)
        process.exit(10)
      }
    } catch (err) {
      console.error('E2E RSVP check failed:', err.message || err)
      process.exit(4)
    }
  } catch (err) {
    console.error('E2E check failed:', err.message || err)
    process.exit(1)
  }
}

main()
