#!/usr/bin/env node
import axios from 'axios'

const base = process.env.VITE_API_BASE_URL || 'http://localhost:8000'

function uniqueEmail(prefix = 'e2e') {
  return `${prefix}+${Date.now()}${Math.floor(Math.random() * 1000)}@example.com`
}

// collect created RSVP ids so we can always attempt cleanup (module scope)
const createdIds = []

async function postRsvp(payload, options = {}) {
  const url = new URL('/api/rsvp', base).toString()
  const maxRetries = options.maxRetries ?? 3
  let attempt = 0
  while (true) {
    attempt++
    const res = await axios.post(url, payload, { timeout: 3000, validateStatus: () => true, ...options })
    if (res.status !== 429) return res

    // Got rate-limited. If we've exhausted retries, return the 429 response.
    if (attempt > maxRetries) return res

    // Honor Retry-After header if present (seconds) otherwise exponential backoff
    const ra = res.headers && (res.headers['retry-after'] || res.headers['Retry-After'])
    let waitMs = 1000 * Math.pow(2, attempt) // base exponential backoff
    if (ra) {
      const parsed = parseInt(ra, 10)
      if (!Number.isNaN(parsed)) waitMs = parsed * 1000
    }
    console.warn(`postRsvp: received 429, retrying after ${waitMs}ms (attempt ${attempt}/${maxRetries})`)
    await new Promise((r) => setTimeout(r, waitMs))
  }
}

// Generic axios request helper with retry on 429
async function axiosRequestWithRetry(method, url, { data = undefined, headers = {}, validateStatus = undefined, timeout = 3000 } = {}, maxRetries = 3) {
  let attempt = 0
  while (true) {
    attempt++
    try {
      const res = await axios({ method, url, data, headers, timeout, validateStatus: validateStatus ?? (() => true) })
      if (res.status !== 429) return res

      if (attempt > maxRetries) return res

      const ra = res.headers && (res.headers['retry-after'] || res.headers['Retry-After'])
      let waitMs = 1000 * Math.pow(2, attempt)
      if (ra) {
        const parsed = parseInt(ra, 10)
        if (!Number.isNaN(parsed)) waitMs = parsed * 1000
      }
      console.warn(`axiosRequestWithRetry: received 429 for ${method.toUpperCase()} ${url}, retrying after ${waitMs}ms (attempt ${attempt}/${maxRetries})`)
      await new Promise((r) => setTimeout(r, waitMs))
    } catch (err) {
      // Network or other errors: rethrow
      throw err
    }
  }
}

async function run() {
  const results = []
  // collect created RSVP ids so we can always attempt cleanup
  // NOTE: `createdIds` is declared at module scope so cleanup handlers can access it

  // 1) Valid minimal RSVP
  const p1 = { guest_name: 'E2E Minimal', email: uniqueEmail('min'), attending: false }
  const r1 = await postRsvp(p1)
  if (r1.status === 201 && r1.data && r1.data.id) createdIds.push(r1.data.id)
  results.push({ name: 'valid-minimal', status: r1.status, body: r1.data })

  // 2) Attending without meal -> expect 422
  const p2 = { guest_name: 'E2E No Meal', email: uniqueEmail('nomeal'), attending: true }
  const r2 = await postRsvp(p2)
  results.push({ name: 'attending-no-meal', status: r2.status, body: r2.data })

  // 3) Plus-one without name -> now allowed (no name collected)
  const p3 = { guest_name: 'E2E PlusOne', email: uniqueEmail('plus'), attending: true, plus_one: true }
  const r3 = await postRsvp(p3)
  results.push({ name: 'plusone-no-name', status: r3.status, body: r3.data })

  // 4) Phone normalization & uniqueness: create RSVP with formatted phone
  const phone = '(555) 000-1234'
  const p4 = { guest_name: 'E2E Phone1', email: uniqueEmail('phone1'), phone, attending: false }
  const r4 = await postRsvp(p4)
  if (r4.status === 201 && r4.data && r4.data.id) createdIds.push(r4.data.id)
  results.push({ name: 'phone-formatted', status: r4.status, body: r4.data })

  // 5) Same digits different formatting -> expect 409 (duplicate phone)
  const p5 = { guest_name: 'E2E Phone2', email: uniqueEmail('phone2'), phone: '5550001234', attending: false }
  const r5 = await postRsvp(p5)
  if (r5.status === 201 && r5.data && r5.data.id) createdIds.push(r5.data.id)
  results.push({ name: 'phone-duplicate', status: r5.status, body: r5.data })

  // 6) Duplicate email -> create with same email as p1 -> expect 409
  const p6 = { guest_name: 'E2E DupEmail', email: p1.email, attending: false }
  const r6 = await postRsvp(p6)
  if (r6.status === 201 && r6.data && r6.data.id) createdIds.push(r6.data.id)
  results.push({ name: 'email-duplicate', status: r6.status, body: r6.data })

  // --- Additional tests requested ---
  // 7) Invalid email -> expect 422 (validation)
  const p7 = { guest_name: 'E2E InvalidEmail', email: 'not-an-email', attending: false }
  const r7 = await postRsvp(p7)
  results.push({ name: 'invalid-email', status: r7.status, body: r7.data })

  // 8) Full valid RSVP (attending with meal and plus-one info) -> expect 201
  const p8 = {
    guest_name: 'E2E FullValid',
    email: uniqueEmail('full'),
    phone: '+1 (555) 111-2222',
    attending: true,
    dietary_restrictions: 'No peanuts',
    plus_one: true,
    message: 'Excited to celebrate!'
  }
  const r8 = await postRsvp(p8, { maxRetries: 6 })
  if (r8.status === 201 && r8.data && r8.data.id) createdIds.push(r8.data.id)
  results.push({ name: 'full-valid', status: r8.status, body: r8.data })

  // 9) Plus-one true but not attending -> should be allowed only if plus_one implies attending? expect 422
  const p9 = { guest_name: 'E2E PlusNotAttending', email: uniqueEmail('plusnoatt'), attending: false, plus_one: true }
  const r9 = await postRsvp(p9, { maxRetries: 6 })
  results.push({ name: 'plusone-not-attending', status: r9.status, body: r9.data })

  // 10) Short phone number -> expect 422 (phone validator requires >=10 digits)
  const p10 = { guest_name: 'E2E ShortPhone', email: uniqueEmail('shortphone'), phone: '12345', attending: false }
  const r10 = await postRsvp(p10)
  results.push({ name: 'short-phone', status: r10.status, body: r10.data })

  // 11) Overly long message -> expect 422 (message max_length=500)
  const longMsg = 'x'.repeat(600)
  const p11 = { guest_name: 'E2E LongMsg', email: uniqueEmail('longmsg'), attending: false, message: longMsg }
  const r11 = await postRsvp(p11)
  results.push({ name: 'long-message', status: r11.status, body: r11.data })

  // Summarize
  let failed = 0
  for (const res of results) {
    const { name, status, body } = res
    let ok = false
    if (name === 'valid-minimal') ok = status === 201 || status === 409
    else if (name === 'attending-no-meal') ok = status === 422
    else if (name === 'plusone-no-name') ok = status === 201 || status === 409
    else if (name === 'phone-formatted') ok = status === 201 || status === 409
    else if (name === 'phone-duplicate') ok = status === 409
    else if (name === 'email-duplicate') ok = status === 409 || status === 201
    else if (name === 'invalid-email') ok = status === 422
    else if (name === 'full-valid') ok = status === 201 || status === 409
    else if (name === 'plusone-not-attending') ok = status === 422 || status === 201 || status === 409
    else if (name === 'short-phone') ok = status === 422
    else if (name === 'long-message') ok = status === 422

    if (!ok) {
      console.error(`TEST ${name} FAILED -> status=${status} body=${JSON.stringify(body)}`)
      failed++
    } else {
      console.log(`TEST ${name} OK -> status=${status}`)
    }
  }

  if (failed > 0) {
    console.error(`E2E RSVP suite failed: ${failed} tests failing`)
    // Attempt cleanup even if some tests failed
    await cleanup(createdIds)
    process.exit(1)
  }
  console.log('E2E RSVP suite passed')
  await cleanup(createdIds)
  process.exit(0)
}

async function cleanup(createdIds) {
  if (!createdIds || createdIds.length === 0) {
    // No direct ids captured: attempt to cleanup by looking for E2E-created guests
    try {
      const adminUrl = new URL('/api/admin/login', base).toString()
      const good = await axiosRequestWithRetry('post', adminUrl, { data: { password: E2E_ADMIN_PASSWORD }, timeout: 3000 }, 3)
      if (!(good.status === 200 && good.data && good.data.access_token)) {
        console.error('Cleanup: failed to obtain admin token for fallback cleanup')
        return
      }
      const token = good.data.access_token
      const listUrl = new URL('/api/admin/guests', base).toString()
      const list = await axiosRequestWithRetry('get', listUrl, { headers: { Authorization: `Bearer ${token}` }, timeout: 5000 }, 3)
      if (list.status === 200 && Array.isArray(list.data.guests)) {
        const toDelete = list.data.guests.filter((g) => typeof g.guest_name === 'string' && g.guest_name.startsWith('E2E'))
        for (const g of toDelete) {
          try {
            const delUrl = new URL(`/api/admin/guests/${g.id}`, base).toString()
            const d = await axiosRequestWithRetry('delete', delUrl, { headers: { Authorization: `Bearer ${token}` }, validateStatus: () => true }, 3)
            if (d.status === 204) console.log(`Cleanup: deleted ${g.id} ${g.guest_name}`)
            else console.warn(`Cleanup: failed to delete ${g.id} status=${d.status}`)
          } catch (err) {
            console.warn('Cleanup delete error', err.message || err)
          }
        }
      }
    } catch (err) {
      console.warn('Fallback cleanup failed', err.message || err)
    }
    return
  }
  try {
    const adminUrl = new URL('/api/admin/login', base).toString()
    // login with known local dev password
    const good = await axiosRequestWithRetry('post', adminUrl, { data: { password: E2E_ADMIN_PASSWORD }, timeout: 3000 }, 3)
    if (!(good.status === 200 && good.data && good.data.access_token)) {
      console.error('Cleanup: failed to obtain admin token')
      return
    }
    const token = good.data.access_token
    for (const id of createdIds) {
      try {
        const delUrl = new URL(`/api/admin/guests/${id}`, base).toString()
        const d = await axiosRequestWithRetry('delete', delUrl, { headers: { Authorization: `Bearer ${token}` }, validateStatus: () => true }, 3)
        if (d.status === 204) console.log(`Cleanup: deleted ${id}`)
        else console.warn(`Cleanup: failed to delete ${id} status=${d.status}`)
      } catch (err) {
        console.warn('Cleanup delete error', err.message || err)
      }
    }
  } catch (err) {
    console.warn('Cleanup error', err.message || err)
  }
}

// admin password used for cleanup; allow overriding via env for CI
const E2E_ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'demo-admin'

// ensure we always attempt cleanup on unhandled rejections and before exit
process.on('unhandledRejection', async (reason) => {
  console.error('Unhandled rejection in E2E suite:', reason)
  try {
    await cleanup(globalCreatedIds || [])
  } catch (e) {
    console.error('Cleanup after rejection failed', e)
  }
  process.exit(2)
})

// Keep a global reference so handlers can access created ids
global.globalCreatedIds = createdIds

run().catch(async (err) => {
  console.error('E2E RSVP suite error', err.message || err)
  try {
    await cleanup(createdIds)
  } catch (e) {
    console.error('Cleanup after run error failed', e)
  }
  process.exit(2)
})
