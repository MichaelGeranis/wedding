import { z } from 'zod'

// Error messages are i18n keys; RSVPForm translates them when it shows them,
// so they follow the current language.
const digits = (value) => value.replace(/\D/g, '').length

// Same message as zod 3's required_error: only when the value is missing.
const required = { error: (issue) => (issue.input === undefined ? 'errors.required' : undefined) }

const optionalText = (max) => z.string().max(max).optional().nullable().or(z.literal(''))

// Mirrors the backend's RSVPCreate rules (backend/src/wedding_api/models/rsvp.py);
// the backend stays the authority.
export const rsvpSchema = z.object({
  guest_name: z
    .string(required)
    .trim()
    .min(2, { error: 'errors.required' })
    .max(100),
  email: z.email({ error: 'errors.invalid_email' }).optional().nullable().or(z.literal('')),
  country_code: z.string(),
  phone: z
    .string(required)
    .refine((value) => digits(value) >= 7 && digits(value) <= 15, { error: 'errors.invalid_phone' }),
  attending: z.boolean(),
  dietary_restrictions: optionalText(300),
  plus_one: z.boolean(),
  children_count: z.number().int().min(0).max(5).catch(0),
  message: optionalText(500),
})
