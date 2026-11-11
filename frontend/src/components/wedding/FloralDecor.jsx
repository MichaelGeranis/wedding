import { motion, useReducedMotion } from 'framer-motion'

export function FloralDecor({ position = 'top' }) {
  const isTop = position === 'top'
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      initial={{ opacity: shouldReduceMotion ? 1 : 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: shouldReduceMotion ? 0 : 1, delay: shouldReduceMotion ? 0 : 0.5 }}
      className={`absolute left-1/2 -translate-x-1/2 ${isTop ? 'top-0' : 'bottom-0'} ${isTop ? '-translate-y-1/2' : 'translate-y-1/2'} w-48 h-24 pointer-events-none`}
      style={{ willChange: 'opacity' }}
    >
      <svg
        viewBox="0 0 200 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={isTop ? '' : 'rotate-180'}
        style={{ transform: 'translateZ(0)' }}
      >
        {/* Decorative leaves and vines */}
        <path
          d="M100 50 Q 80 30, 60 40 Q 50 45, 55 55 Q 60 60, 70 55 Q 85 48, 100 50"
          stroke="#9CAF88"
          strokeWidth="1.5"
          fill="#9CAF88"
          opacity="0.3"
        />
        <path
          d="M100 50 Q 120 30, 140 40 Q 150 45, 145 55 Q 140 60, 130 55 Q 115 48, 100 50"
          stroke="#9CAF88"
          strokeWidth="1.5"
          fill="#9CAF88"
          opacity="0.3"
        />

        {/* Small flowers */}
        <circle cx="70" cy="45" r="3" fill="#D4A5A5" opacity="0.6" />
        <circle cx="130" cy="45" r="3" fill="#D4A5A5" opacity="0.6" />
        <circle cx="100" cy="40" r="4" fill="#D4A5A5" opacity="0.8" />

        {/* Vine stems */}
        <path
          d="M100 50 Q 90 35, 75 42"
          stroke="#9CAF88"
          strokeWidth="1"
          fill="none"
          opacity="0.4"
        />
        <path
          d="M100 50 Q 110 35, 125 42"
          stroke="#9CAF88"
          strokeWidth="1"
          fill="none"
          opacity="0.4"
        />
      </svg>
    </motion.div>
  )
}
