import { useTranslation } from 'react-i18next'
import { Globe } from 'lucide-react'
import { motion } from 'framer-motion'

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()

  const languages = [
    { code: 'en', label: t('language.english') },
    { code: 'el', label: t('language.greek') },
  ]

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng)
  }

  return (
    <div className="flex items-center gap-2">
      <Globe className="w-5 h-5 text-charcoal/60" />
      <div className="flex items-center gap-1 glass-card rounded-full p-1">
        {languages.map((lang) => (
          <motion.button
            key={lang.code}
            onClick={() => changeLanguage(lang.code)}
            className={`
              px-3 py-1.5 rounded-full text-sm font-medium transition-all
              ${
                i18n.language === lang.code
                  ? 'bg-sage text-white shadow-md'
                  : 'text-charcoal/60 hover:text-charcoal hover:bg-charcoal/5'
              }
            `}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {lang.label}
          </motion.button>
        ))}
      </div>
    </div>
  )
}
