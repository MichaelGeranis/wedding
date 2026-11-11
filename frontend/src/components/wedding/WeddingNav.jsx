import { useState } from 'react'
import { Link, useLocation } from 'react-router'
import { Menu, X, AudioLines, Globe } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { cn } from '../../lib/utils'

export function WeddingNav() {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()
  const { t, i18n } = useTranslation()

  const toggleLanguage = () => {
    const newLang = i18n.language === 'el' ? 'en' : 'el'
    i18n.changeLanguage(newLang)
  }

  // Admin is not shown in navigation - access via direct URL only
  const navItems = [
    { path: '/', labelKey: 'nav.invitation' },
    { path: '/rsvp', labelKey: 'nav.rsvp' },
  ]

  const isActive = (path) => {
    if (path === '/admin') {
      return location.pathname === '/admin' || location.pathname.startsWith('/admin/')
    }
    return location.pathname === path
  }

  return (
    <>
      {/* Desktop Navigation */}
      <div className="hidden md:flex fixed top-6 left-0 right-0 justify-center z-50 pointer-events-none">
        <motion.nav
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="pointer-events-auto"
        >
          <div className="glass-card rounded-full px-8 py-3">
            <div className="flex items-center gap-2">
              {navItems.map((item, index) => (
                <div key={item.path} className="flex items-center gap-2">
                  <Link
                    to={item.path}
                    className={cn(
                      "px-5 py-2 rounded-full text-sm font-medium transition-all",
                      isActive(item.path)
                        ? "bg-rose-dark text-white shadow-md"
                        : "text-charcoal hover:text-sage hover:bg-sage/10"
                    )}
                  >
                    {t(item.labelKey)}
                  </Link>
                  {index < navItems.length - 1 && (
                    <AudioLines className="w-3 h-3 text-rose-dark fill-rose-dark/30" />
                  )}
                </div>
              ))}
              <AudioLines className="w-3 h-3 text-rose-dark fill-rose-dark/30" />
              <button
                onClick={toggleLanguage}
                className="px-3 py-2 rounded-full text-sm font-medium transition-all text-charcoal hover:text-sage hover:bg-sage/10 flex items-center gap-1"
                aria-label="Toggle language"
              >
                <Globe className="w-4 h-4" />
                <span>{i18n.language === 'el' ? 'EN' : 'ΕΛ'}</span>
              </button>
            </div>
          </div>
        </motion.nav>
      </div>

      {/* Mobile Navigation */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50">
        <div className="glass-card p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <Link to="/" className="font-serif text-xl text-charcoal hover:text-sage transition-colors">
              {t('nav.wedding')}
            </Link>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleLanguage}
                className="p-2 rounded-lg hover:bg-sage/10 transition-colors flex items-center gap-1"
                aria-label="Toggle language"
              >
                <Globe className="w-5 h-5 text-charcoal" />
                <span className="text-sm font-medium text-charcoal">
                  {i18n.language === 'el' ? 'EN' : 'ΕΛ'}
                </span>
              </button>
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 rounded-lg hover:bg-sage/10 transition-colors"
                aria-label="Toggle menu"
              >
                {isOpen ? (
                  <X className="w-6 h-6 text-charcoal" />
                ) : (
                  <Menu className="w-6 h-6 text-charcoal" />
                )}
              </button>
            </div>
          </div>
        </div>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="glass-card overflow-hidden"
            >
              <div className="p-4 space-y-2">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "block px-4 py-3 rounded-xl text-base font-medium transition-all",
                      isActive(item.path)
                        ? "bg-rose-dark text-white shadow-md"
                        : "text-charcoal hover:bg-sage/10 hover:text-sage"
                    )}
                  >
                    {t(item.labelKey)}
                  </Link>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  )
}
