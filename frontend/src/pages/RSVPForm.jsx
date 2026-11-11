import { useState, useEffect } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSearchParams } from 'react-router'
import { motion, AnimatePresence } from 'framer-motion'
import { Heart, Send, CheckCircle2, Banana, Music, Hamburger, Martini } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { rsvpAPI } from '../services/api'
import { rsvpSchema } from '../lib/validationSchemas'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Textarea } from '../components/ui/Textarea'
import { Label } from '../components/ui/Label'
import { RadioGroup, RadioGroupItem } from '../components/ui/RadioGroup'
import { Select } from '../components/ui/Select'

// Common country codes
const COUNTRY_CODES = [
  { code: '+30', country: 'Greece', flag: '🇬🇷' },
  { code: '+1', country: 'USA/Canada', flag: '🇺🇸' },
  { code: '+44', country: 'UK', flag: '🇬🇧' },
  { code: '+49', country: 'Germany', flag: '🇩🇪' },
  { code: '+33', country: 'France', flag: '🇫🇷' },
  { code: '+39', country: 'Italy', flag: '🇮🇹' },
  { code: '+34', country: 'Spain', flag: '🇪🇸' },
  { code: '+31', country: 'Netherlands', flag: '🇳🇱' },
  { code: '+32', country: 'Belgium', flag: '🇧🇪' },
  { code: '+41', country: 'Switzerland', flag: '🇨🇭' },
  { code: '+46', country: 'Sweden', flag: '🇸🇪' },
  { code: '+47', country: 'Norway', flag: '🇳🇴' },
  { code: '+61', country: 'Australia', flag: '🇦🇺' },
  { code: '+357', country: 'Cyprus', flag: '🇨🇾' },
  { code: '+81', country: 'Japan', flag: '🇯🇵' },
  { code: '+55', country: 'Brazil', flag: '🇧🇷' },
  { code: '+961', country: 'Lebanon', flag: '🇱🇧' },
]

function RSVPForm() {
  const { t, i18n } = useTranslation()
  const [searchParams] = useSearchParams()
  const [submitted, setSubmitted] = useState(false)
  const [confirmationNumber, setConfirmationNumber] = useState('')
  const [apiError, setApiError] = useState(null)
  const [, setLoadingToken] = useState(false)

  const {
    register,
    handleSubmit,
    control,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(rsvpSchema),
    defaultValues: {
      guest_name: '',
      email: null,
      country_code: '+30', // Default to Greece
      phone: '',
      attending: true,
      dietary_restrictions: '',
      plus_one: false,
      children_count: 0,
      message: '',
    },
  })

  const attending = useWatch({ control, name: 'attending' })

  // Scroll to top when component mounts
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  // Check for token parameter and pre-fill guest info
  useEffect(() => {
    const STORAGE_KEY = 'wedding_guest_token'

    // Check URL first, then fall back to localStorage
    let token = searchParams.get('token')
    const storedToken = localStorage.getItem(STORAGE_KEY)

    // If token in URL, save it to localStorage
    if (token) {
      localStorage.setItem(STORAGE_KEY, token)
    } else if (storedToken) {
      // Use stored token if no token in URL
      token = storedToken
    }

    if (!token) return

    const fetchGuestInfo = async () => {
      try {
        setLoadingToken(true)
        const guestInfo = await rsvpAPI.getGuestInfoByToken(token)

        // Pre-fill form fields
        setValue('guest_name', guestInfo.name)

        // Parse phone number to extract country code and number
        if (guestInfo.phone) {
          // Try to extract country code (starts with +)
          const phoneStr = guestInfo.phone.toString().trim()
          let countryCode = '+30' // Default
          let phoneNumber = phoneStr

          // Check if phone starts with + and extract country code
          if (phoneStr.startsWith('+')) {
            // Sort codes by length (longest first) to match longer codes first (e.g., +357 before +35)
            const codes = COUNTRY_CODES.map(c => c.code).sort((a, b) => b.length - a.length)
            const matchedCode = codes.find(code => phoneStr.startsWith(code))
            if (matchedCode) {
              countryCode = matchedCode
              // Extract phone number without country code and trim any spaces
              phoneNumber = phoneStr.substring(matchedCode.length).trim()
            }
          } else {
            // Phone doesn't start with +, try to match it anyway
            // Check if it starts with any country code without the +
            const codes = COUNTRY_CODES.map(c => c.code.substring(1)).sort((a, b) => b.length - a.length)
            const matchedCode = codes.find(code => phoneStr.startsWith(code))
            if (matchedCode) {
              countryCode = '+' + matchedCode
              phoneNumber = phoneStr.substring(matchedCode.length).trim()
            }
          }

          setValue('country_code', countryCode)
          setValue('phone', phoneNumber)
        }
      } catch (error) {
        console.error('Failed to fetch guest info:', error)
        // If token is invalid, remove it from localStorage
        localStorage.removeItem(STORAGE_KEY)
      } finally {
        setLoadingToken(false)
      }
    }

    fetchGuestInfo()
  }, [searchParams, setValue])

  const onSubmit = async (data) => {
    console.log('Form submitted with data:', data)
    setApiError(null)

    try {
      const submitData = { ...data }

      // Convert empty email to null so backend receives None
      if (!submitData.email || submitData.email.trim() === '') {
        submitData.email = null
      }

      // Combine country code with phone number
      if (submitData.phone) {
        // Remove any existing + or country code from phone
        const phoneDigits = submitData.phone.replace(/\D/g, '')
        submitData.phone = submitData.country_code + phoneDigits
      } else {
        submitData.phone = null
      }
      // Remove country_code from submit data (backend doesn't expect it)
      delete submitData.country_code

      // Add current language
      submitData.language = i18n.language

      // Clean up data based on attendance
      if (!submitData.attending) {
        submitData.dietary_restrictions = ''
        submitData.plus_one = false
        submitData.children_count = 0
        submitData.message = ''
      }


      const response = await rsvpAPI.submitRSVP(submitData)
      setConfirmationNumber(response.confirmation_number)
      setSubmitted(true)

      // Clear token from localStorage after successful submission
      localStorage.removeItem('wedding_guest_token')
    } catch (err) {
      if (err.response?.data?.detail) {
        setApiError(err.response.data.detail)
      } else {
        setApiError(err.message || t('errors.submission_failed'))
      }
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen gradient-bg gradient-overlay flex items-center justify-center px-6 py-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="glass-card rounded-3xl p-10 md:p-12 max-w-lg text-center space-y-6"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="w-20 h-20 mx-auto bg-sage/20 rounded-full flex items-center justify-center"
          >
            <CheckCircle2 className="w-12 h-12 text-sage" />
          </motion.div>

          <h2 className="font-serif text-3xl md:text-4xl text-charcoal font-bold">
            {t('rsvp.success_title')}
          </h2>

          <p className="text-charcoal/70 text-lg">
            {t('rsvp.success_message')}
          </p>

          <div className="bg-charcoal/5 rounded-2xl p-4">
            <p className="text-sm text-charcoal/60 uppercase tracking-wider mb-2">
              {t('rsvp.confirmation_number')}
            </p>
            <code className="text-lg font-mono font-bold text-sage">
              {confirmationNumber}
            </code>
          </div>

          <Heart className="w-10 h-10 text-rose-dark fill-rose-dark/30 mx-auto mt-6 animate-float" />
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-bg gradient-overlay px-6 py-20 md:py-28">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-10 space-y-4"
        >
          <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-charcoal font-bold">
            {t('rsvp.title')}
          </h1>
        </motion.div>

        {/* Form Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="glass-card rounded-3xl p-8 md:p-10"
        >
          {apiError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-rose-dusty/10 border-2 border-rose-dusty/30 rounded-xl p-4 mb-6"
            >
              <p className="text-rose-dark text-sm">{apiError}</p>
            </motion.div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            {/* Personal Information */}
            <div className="space-y-5">
              <h3 className="font-serif text-2xl text-charcoal font-semibold flex items-center gap-2">
                {t('rsvp.your_response')}
              </h3>

              <div className="[&>*+*]:mt-2">
                <Label htmlFor="guest_name">{t('rsvp.guest_name')} *</Label>
                <Input
                  id="guest_name"
                  {...register('guest_name')}
                  placeholder={t('rsvp.guest_name_placeholder')}
                />
                {errors.guest_name && (
                  <p className="text-rose-dark text-sm mt-1">{t(errors.guest_name.message)}</p>
                )}
              </div>

              {/* <div className="[&>*+*]:mt-2">
                <Label htmlFor="email">{t('rsvp.email')}</Label>
                <Input
                  id="email"
                  type="email"
                  {...register('email')}
                  placeholder={t('rsvp.email_placeholder')}
                />
                {errors.email && (
                  <p className="text-rose-dark text-sm mt-1">{t(errors.email.message)}</p>
                )}
              </div> */}

              <div className="[&>*+*]:mt-2">
                <Label htmlFor="phone">{t('rsvp.phone')} *</Label>
                <div className="flex gap-2">
                  <Select
                    id="country_code"
                    {...register('country_code')}
                    className="w-32 shrink-0"
                  >
                    {COUNTRY_CODES.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.flag} {item.code}
                      </option>
                    ))}
                  </Select>
                  <Input
                    id="phone"
                    type="tel"
                    {...register('phone')}
                    placeholder="6912345678"
                    className="flex-1"
                  />
                </div>
                {errors.phone && (
                  <p className="text-rose-dark text-sm mt-1">{t(errors.phone.message)}</p>
                )}
              </div>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-charcoal/10"></div>
              <Hamburger className="w-4 h-4 text-violet-500" />
              <div className="h-px flex-1 bg-charcoal/10"></div>
            </div>

            {/* Attendance */}
            <div className="space-y-5">
              <h3 className="font-serif text-2xl text-charcoal font-semibold">
                {t('rsvp.attending')}
              </h3>

              <RadioGroup>
                <RadioGroupItem
                  id="attending-yes"
                  value="true"
                  checked={attending === true}
                  onChange={() => setValue('attending', true)}
                >
                  {t('rsvp.yes_attending')}
                </RadioGroupItem>
                <RadioGroupItem
                  id="attending-no"
                  value="false"
                  checked={attending === false}
                  onChange={() => setValue('attending', false)}
                >
                  {t('rsvp.no_attending')}
                </RadioGroupItem>
              </RadioGroup>
            </div>

            {/* Conditional: Attending Details */}
            <AnimatePresence>
              {attending && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-8 overflow-hidden"
                >
                  {/* Divider */}
                  <div className="flex items-center gap-3">
                    <div className="h-px flex-1 bg-charcoal/10"></div>
                    <Music className="w-4 h-4 text-blue-500" />
                    <div className="h-px flex-1 bg-charcoal/10"></div>
                  </div>

                  {/* Meal Preferences */}
                  <div className="space-y-5">
                    <h3 className="font-serif text-2xl text-charcoal font-semibold">
                      {t('rsvp.dietary_restrictions')}
                    </h3>

                    <div className="space-y-2">
                      <Textarea
                        id="dietary_restrictions"
                        {...register('dietary_restrictions')}
                        placeholder={t('rsvp.dietary_placeholder')}
                        rows={3}
                      />
                    </div>
                  </div>

                  {/* Divider */}
                  <div className="flex items-center gap-3">
                    <div className="h-px flex-1 bg-charcoal/10"></div>
                    <Martini className="w-4 h-4 text-red-500" />
                    <div className="h-px flex-1 bg-charcoal/10"></div>
                  </div>

                  {/* Plus One */}
                  <div className="space-y-5">
                    <h3 className="font-serif text-2xl text-charcoal font-semibold">
                      {t('rsvp.plus_one')}
                    </h3>

                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        id="plus_one"
                        {...register('plus_one')}
                        className="h-5 w-5 rounded-sm border-2 border-charcoal/30 text-sage focus:ring-2 focus:ring-sage focus:ring-offset-2"
                      />
                      <Label htmlFor="plus_one" className="cursor-pointer">
                        {t('rsvp.yes_plus_one')}
                      </Label>
                    </div>

                    {/* No longer collecting plus-one name; only boolean flag is stored */}
                  </div>

                  {/* Divider */}
                  <div className="flex items-center gap-3">
                    <div className="h-px flex-1 bg-charcoal/10"></div>
                    <Heart className="w-4 h-4 text-pink-500" />
                    <div className="h-px flex-1 bg-charcoal/10"></div>
                  </div>

                  {/* Children Count */}
                  <div className="space-y-5">
                    <h3 className="font-serif text-2xl text-charcoal font-semibold">
                      {t('rsvp.children_count_title', 'Number of Children')}
                    </h3>
                    <p className="text-sm text-charcoal/60">
                      {t('rsvp.children_count_description', 'How many children will be joining you? (0-5)')}
                    </p>

                    <div className="[&>*+*]:mt-2">
                      <Label htmlFor="children_count">{t('rsvp.children_count', 'Children')}</Label>
                      <Input
                        id="children_count"
                        type="number"
                        min="0"
                        max="5"
                        {...register('children_count', { valueAsNumber: true })}
                        className="w-32"
                      />
                      {errors.children_count && (
                        <p className="text-rose-dark text-sm mt-1">{t(errors.children_count.message)}</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-charcoal/10"></div>
              <Banana className="w-4 h-4 text-yellow-500" />
              <div className="h-px flex-1 bg-charcoal/10"></div>
            </div>

            {/* Message */}
            <div className="space-y-5">
              <h3 className="font-serif text-2xl text-charcoal font-semibold">
                {t('rsvp.message')}
              </h3>

              <div className="space-y-2">
                <Textarea
                  id="message"
                  {...register('message')}
                  placeholder={t('rsvp.message_placeholder')}
                  rows={4}
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <Button
                type="submit"
                onClick={handleSubmit(onSubmit)}
                disabled={isSubmitting}
                size="lg"
                className="w-full"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    {t('rsvp.submitting')}
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    {t('rsvp.submit')}
                  </>
                )}
              </Button>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  )
}

export default RSVPForm
