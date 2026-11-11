import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Cloud, CloudRain, Sun, CloudSnow, Droplets, ThermometerSun } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function WeatherWidget({ weddingDate, location }) {
  const { i18n } = useTranslation()
  const [weather, setWeather] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchWeather = async () => {
      if (!weddingDate || !location?.lat || !location?.lon) {
        setLoading(false)
        return
      }

      try {
        const date = new Date(weddingDate)
        const today = new Date()
        const daysUntil = Math.ceil((date - today) / (1000 * 60 * 60 * 24))

        // Only fetch if wedding is within 16 days (Open-Meteo forecast limit)
        if (daysUntil < 0 || daysUntil > 16) {
          setError('too_far')
          setLoading(false)
          return
        }

        const formattedDate = date.toISOString().split('T')[0]
        const response = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${location.lat}&longitude=${location.lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weathercode&timezone=auto&start_date=${formattedDate}&end_date=${formattedDate}`
        )

        if (!response.ok) throw new Error('Failed to fetch weather')

        const data = await response.json()

        if (data.daily) {
          setWeather({
            tempMax: Math.round(data.daily.temperature_2m_max[0]),
            tempMin: Math.round(data.daily.temperature_2m_min[0]),
            precipitation: data.daily.precipitation_sum[0],
            precipitationProb: data.daily.precipitation_probability_max[0],
            weatherCode: data.daily.weathercode[0]
          })
        }
      } catch (err) {
        console.error('Weather fetch error:', err)
        setError('fetch_failed')
      } finally {
        setLoading(false)
      }
    }

    fetchWeather()
  }, [weddingDate, location])

  const getWeatherIcon = (code) => {
    // WMO Weather interpretation codes
    if (code === 0) return <Sun className="w-8 h-8 text-yellow-500" />
    if (code >= 1 && code <= 3) return <Cloud className="w-8 h-8 text-gray-400" />
    if (code >= 51 && code <= 67) return <CloudRain className="w-8 h-8 text-blue-500" />
    if (code >= 71 && code <= 77) return <CloudSnow className="w-8 h-8 text-blue-300" />
    if (code >= 80 && code <= 82) return <CloudRain className="w-8 h-8 text-blue-600" />
    if (code >= 95) return <CloudRain className="w-8 h-8 text-purple-600" />
    return <Cloud className="w-8 h-8 text-gray-400" />
  }

  const getWeatherDescription = (code) => {
    if (code === 0) return i18n.language === 'el' ? 'Αίθριος' : 'Clear sky'
    if (code === 1) return i18n.language === 'el' ? 'Κυρίως αίθριος' : 'Mainly clear'
    if (code === 2) return i18n.language === 'el' ? 'Μερικώς νεφελώδης' : 'Partly cloudy'
    if (code === 3) return i18n.language === 'el' ? 'Συννεφιά' : 'Overcast'
    if (code >= 51 && code <= 67) return i18n.language === 'el' ? 'Βροχή' : 'Rain'
    if (code >= 71 && code <= 77) return i18n.language === 'el' ? 'Χιόνι' : 'Snow'
    if (code >= 80 && code <= 82) return i18n.language === 'el' ? 'Βροχόπτωση' : 'Rain showers'
    if (code >= 95) return i18n.language === 'el' ? 'Καταιγίδα' : 'Thunderstorm'
    return i18n.language === 'el' ? 'Μεταβλητός' : 'Variable'
  }

  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-6 text-center">
        <div className="animate-pulse">
          <div className="h-8 w-8 bg-charcoal/20 rounded-full mx-auto mb-2"></div>
          <div className="h-4 w-32 bg-charcoal/20 rounded-sm mx-auto"></div>
        </div>
      </div>
    )
  }

  if (error === 'too_far') {
    return (
      <div className="glass-card rounded-2xl p-6 text-center">
        <Cloud className="w-8 h-8 text-charcoal/40 mx-auto mb-2" />
        <p className="text-sm text-charcoal/60">
          {i18n.language === 'el'
            ? 'Η πρόγνωση θα είναι διαθέσιμη πιο κοντά στην ημερομηνία'
            : 'Weather forecast will be available closer to the date'}
        </p>
      </div>
    )
  }

  if (error || !weather) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="glass-card rounded-2xl p-6"
    >
      <div className="flex items-center gap-4">
        <div className="shrink-0">
          {getWeatherIcon(weather.weatherCode)}
        </div>

        <div className="flex-1">
          <p className="text-sm uppercase tracking-wider text-charcoal/60 mb-1">
            {i18n.language === 'el' ? 'Καιρός' : 'Weather Forecast'}
          </p>
          <p className="text-lg font-medium text-charcoal">
            {getWeatherDescription(weather.weatherCode)}
          </p>
        </div>

        <div className="text-right">
          <div className="flex items-center gap-1 text-charcoal mb-1">
            <ThermometerSun className="w-4 h-4 text-orange-500" />
            <span className="text-xl font-bold">{weather.tempMax}°</span>
            <span className="text-sm text-charcoal/60">/ {weather.tempMin}°C</span>
          </div>

          {weather.precipitationProb > 20 && (
            <div className="flex items-center gap-1 text-sm text-blue-600">
              <Droplets className="w-3 h-3" />
              <span>{weather.precipitationProb}%</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
