import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

export function CountdownTimer({ targetDate }) {
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
  })

  useEffect(() => {
    const calculateTimeLeft = () => {
      const difference = new Date(targetDate) - new Date()

      if (difference > 0) {
        setTimeLeft({
          days: Math.floor(difference / (1000 * 60 * 60 * 24)),
          hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
          minutes: Math.floor((difference / 1000 / 60) % 60),
          seconds: Math.floor((difference / 1000) % 60),
        })
      }
    }

    calculateTimeLeft()
    const timer = setInterval(calculateTimeLeft, 1000)

    return () => clearInterval(timer)
  }, [targetDate])

  const { t } = useTranslation()

  const timeBlocks = [
    { label: t('common.days'), value: timeLeft.days },
    { label: t('common.hours'), value: timeLeft.hours },
    { label: t('common.minutes'), value: timeLeft.minutes },
    { label: t('common.seconds'), value: timeLeft.seconds },
  ]

  return (
    <div className="flex flex-wrap justify-center gap-4 md:gap-6">
      {timeBlocks.map((block, index) => (
        <motion.div
          key={block.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: index * 0.1 }}
          className="glass-card rounded-2xl p-6 md:p-8 min-w-[100px] md:min-w-[120px]"
        >
          <div className="text-4xl md:text-5xl font-serif font-bold text-rose-dark text-center">
            {String(block.value).padStart(2, '0')}
          </div>
          <div className="text-sm md:text-base text-charcoal/60 text-center mt-2 uppercase tracking-wider">
            {block.label}
          </div>
        </motion.div>
      ))}
    </div>
  )
}
