import { describe, expect, it } from 'vitest'
import { rsvpSchema } from './validationSchemas'

// What RSVPForm submits for a guest who fills in only the required fields.
const validRsvp = {
  guest_name: 'Maria Papadopoulou',
  email: null,
  country_code: '+30',
  phone: '6912345678',
  attending: true,
  dietary_restrictions: '',
  plus_one: false,
  children_count: 0,
  message: '',
}

const without = (key) => Object.fromEntries(Object.entries(validRsvp).filter(([k]) => k !== key))

// Error messages are i18n keys, keyed by field, as RSVPForm reads them.
const errorsFor = (input) => {
  const result = rsvpSchema.safeParse(input)
  expect(result.success).toBe(false)
  return Object.fromEntries(result.error.issues.map((issue) => [issue.path.join('.'), issue.message]))
}

describe('rsvpSchema', () => {
  it('accepts a complete RSVP', () => {
    const result = rsvpSchema.safeParse({ ...validRsvp, guest_name: '  Maria Papadopoulou  ', children_count: 2 })

    expect(result.success).toBe(true)
    expect(result.data.guest_name).toBe('Maria Papadopoulou')
    expect(result.data.children_count).toBe(2)
  })

  it('requires a name', () => {
    expect(errorsFor(without('guest_name'))).toEqual({ guest_name: 'errors.required' })
    expect(errorsFor({ ...validRsvp, guest_name: '' })).toEqual({ guest_name: 'errors.required' })
    expect(errorsFor({ ...validRsvp, guest_name: ' A ' })).toEqual({ guest_name: 'errors.required' })
  })

  it('rejects a phone number with too few or too many digits', () => {
    expect(errorsFor({ ...validRsvp, phone: '12345' })).toEqual({ phone: 'errors.invalid_phone' })
    expect(errorsFor({ ...validRsvp, phone: '1234567890123456' })).toEqual({ phone: 'errors.invalid_phone' })
    expect(errorsFor({ ...validRsvp, phone: '' })).toEqual({ phone: 'errors.invalid_phone' })
  })

  it('requires a phone number', () => {
    expect(errorsFor(without('phone'))).toEqual({ phone: 'errors.required' })
  })

  it('accepts a phone number written with spaces and punctuation', () => {
    expect(rsvpSchema.safeParse({ ...validRsvp, phone: '(691) 234-5678' }).success).toBe(true)
  })

  // The number input enforces 0-5 in the browser; the schema falls back to 0
  // for anything else that reaches it (an empty input arrives as NaN).
  it.each([-1, 6, 2.5, Number.NaN])('falls back to 0 children for out-of-range value %s', (children_count) => {
    const result = rsvpSchema.safeParse({ ...validRsvp, children_count })

    expect(result.success).toBe(true)
    expect(result.data.children_count).toBe(0)
  })

  it('rejects an invalid email when one is given', () => {
    expect(errorsFor({ ...validRsvp, email: 'not-an-email' })).toEqual({ email: 'errors.invalid_email' })
    expect(rsvpSchema.safeParse({ ...validRsvp, email: '' }).success).toBe(true)
  })
})
