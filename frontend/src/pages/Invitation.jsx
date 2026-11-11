import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router'
import { motion, useReducedMotion } from 'framer-motion'
import { Calendar, Clock, MapPin, Send, TicketsPlane, CalendarPlus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { invitationAPI } from '../services/api'
import { FloralDecor } from '../components/wedding/FloralDecor'
import { CatDecor } from '../components/wedding/CatDecor'
import { CountdownTimer } from '../components/wedding/CountdownTimer'
import { WeatherWidget } from '../components/wedding/WeatherWidget'
import { Button } from '../components/ui/Button'

function Invitation() {
  const { t, i18n } = useTranslation()
  const [searchParams] = useSearchParams()
  const [invitation, setInvitation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const shouldReduceMotion = useReducedMotion()

  // Get token from URL if present
  const token = searchParams.get('token')

  // Get locale for date formatting
  const dateLocale = i18n.language === 'el' ? 'el-GR' : 'en-US'

  useEffect(() => {
    const fetchInvitation = async () => {
      try {
        const data = await invitationAPI.getInvitation()
        setInvitation(data)
      } catch (err) {
        setError(err.message || 'Failed to load invitation')
      } finally {
        setLoading(false)
      }
    }

    fetchInvitation()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen gradient-bg gradient-overlay flex items-center justify-center">
        <motion.div
          initial={shouldReduceMotion ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: shouldReduceMotion ? 0 : 0.3 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-sage border-t-rose-dusty mx-auto mb-4"></div>
          <p className="text-charcoal/60 text-lg">{t('invitation.loading')}</p>
        </motion.div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen gradient-bg gradient-overlay flex items-center justify-center px-6">
        <motion.div
          initial={shouldReduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: shouldReduceMotion ? 0 : 0.3 }}
          className="glass-card rounded-3xl p-8 max-w-md text-center"
        >
          <p className="text-rose-dark text-lg">{error}</p>
        </motion.div>
      </div>
    )
  }

  const weddingDate = invitation?.wedding_date ? new Date(invitation.wedding_date) : null

  // Helper function for animations that respect reduced motion
  const getAnimationProps = (initial, delay = 0) => ({
    initial: shouldReduceMotion ? { opacity: 1, y: 0, scale: 1 } : initial,
    animate: { opacity: 1, y: 0, scale: 1 },
    transition: { duration: shouldReduceMotion ? 0 : 0.6, delay: shouldReduceMotion ? 0 : delay }
  })

  const generateCalendarLink = () => {
    if (!weddingDate || !invitation) return '#'

    const formatDateForCalendar = (date, time) => {
      const d = new Date(date)
      if (time) {
        const [hours, minutes] = time.split(':')
        d.setHours(parseInt(hours), parseInt(minutes), 0, 0)
      }
      return d.toISOString().replace(/-|:|\.\d\d\d/g, '')
    }

    const startDate = formatDateForCalendar(weddingDate, invitation.ceremony_time)
    const endDateTime = new Date(weddingDate)
    if (invitation.ceremony_time) {
      const [hours, minutes] = invitation.ceremony_time.split(':')
      endDateTime.setHours(parseInt(hours) + 5, parseInt(minutes), 0, 0) // Assume 5 hour event
    }
    const endDate = endDateTime.toISOString().replace(/-|:|\.\d\d\d/g, '')

    const brideName = i18n.language === 'el' && invitation.bride_name_gr ? invitation.bride_name_gr : invitation.bride_name
    const groomName = i18n.language === 'el' && invitation.groom_name_gr ? invitation.groom_name_gr : invitation.groom_name
    const title = `${brideName} & ${groomName} Wedding`

    const churchName = i18n.language === 'el' && invitation.church_name_gr ? invitation.church_name_gr : invitation.church_name
    const churchAddress = i18n.language === 'el' && invitation.church_address_gr ? invitation.church_address_gr : invitation.church_address
    const location = churchName && churchAddress
      ? `${churchName}, ${churchAddress}`
      : churchName || churchAddress || ''

    const details = t('invitation.request_pleasure') + ' ' + t('invitation.at_their_wedding')

    const params = new URLSearchParams({
      action: 'TEMPLATE',
      text: title,
      dates: `${startDate}/${endDate}`,
      details: details,
      location: location
    })

    return `https://www.google.com/calendar/render?${params.toString()}`
  }

  return (
    <div className="min-h-screen gradient-bg gradient-overlay">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 pt-32 pb-20">
        <FloralDecor position="top" />

        <div className="max-w-4xl mx-auto text-center space-y-3">
          {/* Pre-heading */}
          <motion.p
            {...getAnimationProps({ opacity: 0, y: 20 }, 0.2)}
            className="text-sage text-sm md:text-base uppercase tracking-widest"
          >
            {t('invitation.pronouncement')}
          </motion.p>

          {/* Couple Names */}
          <div className="space-y-3">
            <motion.h1
              {...getAnimationProps({ opacity: 0, y: 20 }, 0.4)}
              className="font-serif text-5xl md:text-7xl lg:text-8xl text-charcoal font-bold"
            >
              {i18n.language === 'el' && invitation?.bride_name_gr ? invitation.bride_name_gr : invitation?.bride_name}
            </motion.h1>

            <motion.div
              {...getAnimationProps({ opacity: 0, scale: 0.5 }, 0.6)}
              className="flex items-center justify-center gap-4"
            >
              <div className="h-px w-12 md:w-20 bg-rose-dark"></div>
              <CatDecor size="w-10 h-10" className="text-rose-dark fill-rose-dark/30" />
              <div className="h-px w-12 md:w-20 bg-rose-dark"></div>
            </motion.div>

            <motion.h1
              {...getAnimationProps({ opacity: 0, y: 20 }, 0.8)}
              className="font-serif text-5xl md:text-7xl lg:text-8xl text-charcoal font-bold"
            >
              {i18n.language === 'el' && invitation?.groom_name_gr ? invitation.groom_name_gr : invitation?.groom_name}
            </motion.h1>
          </div>

          {/* Invitation Text */}
          <motion.p
            {...getAnimationProps({ opacity: 0 }, 1)}
            className="text-charcoal/80 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed md:leading-7"
          >
            {t('invitation.request_pleasure')} {t('invitation.at_their_wedding')}
          </motion.p>

          {/* Wedding Details */}
          <motion.div
            {...getAnimationProps({ opacity: 0, y: 20 }, 1.4)}
            className="glass-card rounded-3xl p-8 md:p-10"
          >
            <div className="max-w-md mx-auto space-y-6">
              {weddingDate && (
                <div className="flex items-center gap-4 text-charcoal">
                  <Calendar className="w-6 h-6 text-sage shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm uppercase tracking-wider text-charcoal/60 mb-1">
                      {t('invitation.date')}
                    </p>
                    <p className="text-lg md:text-xl font-medium">
                      {weddingDate.toLocaleDateString(dateLocale, {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                  </div>
                </div>
              )}

              {invitation?.ceremony_time && (
                <div className="flex items-center gap-4 text-charcoal">
                  <Clock className="w-6 h-6 text-sage shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm uppercase tracking-wider text-charcoal/60 mb-1">
                      {t('invitation.time')}
                    </p>
                    <p className="text-lg md:text-xl font-medium">
                      {invitation.ceremony_time} <span className="text-base text-charcoal/60">{t('invitation.gr_time')}</span>
                    </p>
                  </div>
                </div>
              )}

              {invitation?.church_name && (
                <a
                  href={invitation.church_maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(invitation.church_name + ' ' + (invitation.church_address || ''))}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 text-charcoal hover:text-sage transition-colors group"
                >
                  <MapPin className="w-6 h-6 text-sage shrink-0 group-hover:text-rose-light" />
                  <div className="flex-1">
                    <p className="text-sm uppercase tracking-wider text-charcoal/60 mb-1">{t('invitation.ceremony')}</p>
                    <p className="text-lg md:text-xl font-medium underline decoration-blue-400/50 group-hover:decoration-blue-600 underline-offset-2">
                      {i18n.language === 'el' && invitation.church_name_gr ? invitation.church_name_gr : invitation.church_name}
                    </p>
                    {(invitation.church_address || invitation.church_address_gr) && (
                      <p className="text-sm underline decoration-blue-300/50 group-hover:decoration-blue-500 underline-offset-2">
                        {i18n.language === 'el' && invitation.church_address_gr ? invitation.church_address_gr : invitation.church_address}
                      </p>
                    )}
                  </div>
                </a>
              )}

              {invitation?.venue_name && (
                <a
                  href={invitation.venue_maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(invitation.venue_name + ' ' + (invitation.venue_address || ''))}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 text-charcoal hover:text-sage transition-colors group"
                >
                  <MapPin className="ww-6 h-6 text-sage shrink-0 group-hover:text-rose-light" />
                  <div className="flex-1">
                    <p className="text-sm uppercase tracking-wider text-charcoal/60 mb-1">{t('invitation.reception')}</p>
                    <p className="text-lg md:text-xl font-medium underline decoration-blue-400/50 group-hover:decoration-blue-600 underline-offset-2">
                      {i18n.language === 'el' && invitation.venue_name_gr ? invitation.venue_name_gr : invitation.venue_name}
                    </p>
                    {(invitation.venue_address || invitation.venue_address_gr) && (
                      <p className="text-sm underline decoration-blue-300/50 group-hover:decoration-blue-500 underline-offset-2">
                        {i18n.language === 'el' && invitation.venue_address_gr ? invitation.venue_address_gr : invitation.venue_address}
                      </p>
                    )}
                  </div>
                </a>
              )}

              {/* Add to Calendar Button */}
              {weddingDate && (
                <div className="pt-4 border-t border-charcoal/10">
                  <a
                    href={generateCalendarLink()}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-sage/10 hover:bg-sage/20 text-sage hover:text-sage-dark rounded-full transition-colors font-medium"
                  >
                    <CalendarPlus className="w-5 h-5" />
                    <span>{t('invitation.add_to_calendar')}</span>
                  </a>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        <FloralDecor position="bottom" />
      </section>

      {/* Countdown Section */}
      {weddingDate && (
        <section className="relative py-12 px-6">
          <div className="max-w-6xl mx-auto">
            <CountdownTimer targetDate={weddingDate} />

            {/* Weather Widget */}
            <div className="max-w-md mx-auto mt-12">
              <WeatherWidget
                weddingDate={weddingDate}
                location={{ lat: 37.9838, lon: 23.7275 }}
              />
            </div>
          </div>

          <FloralDecor position="bottom" />
        </section>
      )}

      {/* RSVP CTA Section */}
      <section className="relative py-12 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={shouldReduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: shouldReduceMotion ? 0 : 0.6 }}
            className="glass-card rounded-3xl p-10 md:p-12 space-y-6"
          >
            <TicketsPlane className="w-12 h-12 md:w-16 md:h-16 text-rose-dark fill-rose-dark/30 mx-auto animate-float" />

            <h2 className="font-serif text-3xl md:text-5xl text-charcoal font-bold">
              {t('invitation.will_you_join')}
            </h2>

            <p className="text-charcoal/70 text-base md:text-lg leading-relaxed md:leading-7 max-w-xl mx-auto">
              {t('invitation.let_us_know')}
            </p>

            {invitation?.rsvp_deadline && (
              <p className="text-sage text-sm md:text-base uppercase tracking-wider">
                {t('invitation.rsvp_by')} {new Date(invitation.rsvp_deadline).toLocaleDateString(dateLocale, {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric'
                })}
              </p>
            )}

            <Link to={token ? `/rsvp?token=${token}` : '/rsvp'}>
              <Button size="lg" className="mt-4">
                <Send className="w-5 h-5" />
                {t('invitation.rsvp_button')}
              </Button>
            </Link>
          </motion.div>
        </div>

      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-charcoal/50 text-sm">
        <p>© {new Date().getFullYear()} {invitation?.bride_name} &amp; {invitation?.groom_name}</p>
      </footer>
    </div>
  )
}

export default Invitation
