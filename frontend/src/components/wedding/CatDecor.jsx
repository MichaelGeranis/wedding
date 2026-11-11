import { motion, useReducedMotion } from 'framer-motion'

export function CatDecor({ size = 'w-16 h-16' }) {
  const strokeColor = "#AFA088"
  const fillColor = "#AFA088"
  const accentColor = "#D4A5A5"
  const shouldReduceMotion = useReducedMotion()

  // Animation Variants
  const containerVariants = {
    rest: { scale: 1 },
    hover: shouldReduceMotion ? { scale: 1 } : { scale: 1.05, transition: { duration: 0.2 } }
  }

  const earVariants = {
    rest: { rotate: 0 },
    hover: shouldReduceMotion
      ? { rotate: 0 }
      : {
          rotate: [0, -10, 10, -5, 5, 0], // Wiggle effect
          transition: { duration: 0.6, ease: "easeInOut" }
        }
  }

  const tailVariants = {
    rest: shouldReduceMotion
      ? { d: "M 130 160 Q 170 160 160 100" }
      : {
          d: [
            "M 130 160 Q 170 160 160 100",
            "M 130 160 Q 180 140 175 110",
            "M 130 160 Q 170 160 160 100"
          ],
          transition: { duration: 4, repeat: Infinity, ease: "easeInOut", repeatType: "reverse" }
        },
    hover: shouldReduceMotion
      ? { d: "M 130 160 Q 170 160 160 100" }
      : {
          // Speed up the wag on hover
          d: [
            "M 130 160 Q 170 160 160 100",
            "M 130 160 Q 180 140 175 110",
            "M 130 160 Q 170 160 160 100"
          ],
          transition: { duration: 0.8, repeat: Infinity, ease: "easeInOut", repeatType: "reverse" }
        }
  }

  return (
    <motion.div
      className={`relative ${size} cursor-pointer`}
      initial="rest"
      whileHover="hover" // Triggers the 'hover' variant for all children
      animate="rest"
      variants={containerVariants}
      style={{ willChange: 'transform' }}
    >
      <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ transform: 'translateZ(0)' }}>

        {/* --- TAIL --- */}
        <motion.path
          stroke={strokeColor}
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
          opacity="0.6"
          variants={tailVariants} // Uses the fast/slow variant
        />

        {/* --- BODY --- */}
        <path
          d="M 60 170 Q 50 100 90 90 Q 140 100 140 170"
          stroke={strokeColor}
          strokeWidth="2"
          fill={fillColor}
          opacity="0.2"
        />
        <path
          d="M 60 170 Q 50 100 90 90 Q 140 100 140 170"
          stroke={strokeColor}
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
          opacity="0.8"
        />

        {/* --- HEAD --- */}
        <g>
          <circle cx="95" cy="85" r="35" fill={fillColor} opacity="0.2" />
          <circle cx="95" cy="85" r="35" stroke={strokeColor} strokeWidth="2" opacity="0.8" />

          {/* Left Ear (Animated) */}
          {/* We set originX/Y so it rotates around the base of the ear, not the center of the SVG */}
          <motion.path
            d="M 70 60 L 60 30 L 90 55"
            stroke={strokeColor} strokeWidth="2" fill={fillColor} opacity="0.4" strokeLinejoin="round"
            variants={earVariants}
            style={{ originX: "75px", originY: "55px" }}
          />

          {/* Right Ear (Animated) */}
          <motion.path
            d="M 120 60 L 130 30 L 100 55"
            stroke={strokeColor} strokeWidth="2" fill={fillColor} opacity="0.4" strokeLinejoin="round"
            variants={earVariants}
            style={{ originX: "115px", originY: "55px" }}
          />
        </g>

        {/* --- FACE --- */}
        <g>
          {/* Closed Eyes (Visible at Rest) */}
          <motion.g variants={{ rest: { opacity: 1 }, hover: { opacity: 0 } }}>
             <path d="M 80 80 Q 85 75 90 80" stroke={strokeColor} strokeWidth="2" strokeLinecap="round" />
             <path d="M 100 80 Q 105 75 110 80" stroke={strokeColor} strokeWidth="2" strokeLinecap="round" />
          </motion.g>

          {/* Open Eyes (Visible on Hover) */}
          <motion.g variants={{ rest: { opacity: 0, scaleY: 0 }, hover: { opacity: 1, scaleY: 1 } }} style={{ originX: "95px", originY: "80px" }}>
             <circle cx="85" cy="78" r="3" fill="#333" />
             <circle cx="105" cy="78" r="3" fill="#333" />
             {/* Tiny shine in eyes */}
             <circle cx="86" cy="77" r="1" fill="white" />
             <circle cx="106" cy="77" r="1" fill="white" />
          </motion.g>

          {/* Nose & Mouth */}
          <circle cx="95" cy="90" r="3" fill={accentColor} />
          <path d="M 95 93 Q 90 98 85 95" stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" />
          <path d="M 95 93 Q 100 98 105 95" stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" />

          {/* Whiskers */}
          <g opacity="0.5">
            <line x1="75" y1="90" x2="55" y2="85" stroke={strokeColor} strokeWidth="1" />
            <line x1="75" y1="95" x2="55" y2="98" stroke={strokeColor} strokeWidth="1" />
            <line x1="115" y1="90" x2="135" y2="85" stroke={strokeColor} strokeWidth="1" />
            <line x1="115" y1="95" x2="135" y2="98" stroke={strokeColor} strokeWidth="1" />
          </g>
        </g>
      </svg>
    </motion.div>
  )
}
