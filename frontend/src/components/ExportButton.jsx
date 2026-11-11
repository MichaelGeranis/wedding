import { useState } from 'react'
import { Download, ChevronDown, FileSpreadsheet, FileText } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { adminAPI } from '../services/api'
import { Button } from './ui/Button'

export function ExportButton() {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = async (type, attending = null) => {
    setIsExporting(true)
    setIsOpen(false)

    try {
      if (type === 'summary') {
        await adminAPI.exportSummaryCSV()
      } else {
        await adminAPI.exportGuestsCSV(attending)
      }
    } catch (error) {
      console.error('Export failed:', error)
      alert(t('errors.export_failed') || 'Export failed. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  const exportOptions = [
    {
      label: t('admin.download_all'),
      icon: FileSpreadsheet,
      action: () => handleExport('guests', null),
    },
    {
      label: t('admin.download_attending'),
      icon: FileSpreadsheet,
      action: () => handleExport('guests', true),
    },
    {
      label: t('admin.download_not_attending'),
      icon: FileSpreadsheet,
      action: () => handleExport('guests', false),
    },
    {
      label: t('admin.export_summary'),
      icon: FileText,
      action: () => handleExport('summary'),
      divider: true,
    },
  ]

  return (
    <div className="relative">
      <Button
        variant="secondary"
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className="flex items-center gap-2"
      >
        {isExporting ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-charcoal border-t-transparent" />
            {t('common.loading')}
          </>
        ) : (
          <>
            <Download className="w-5 h-5" />
            {t('admin.export_csv')}
            <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </>
        )}
      </Button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown Menu */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="absolute right-0 top-full mt-2 w-64 glass-card rounded-xl shadow-xl z-20 overflow-hidden"
            >
              {exportOptions.map((option, index) => {
                const Icon = option.icon
                return (
                  <div key={index}>
                    {option.divider && (
                      <div className="border-t border-charcoal/10 my-1" />
                    )}
                    <button
                      onClick={option.action}
                      className="w-full px-4 py-3 flex items-center gap-3 hover:bg-sage/10 transition-colors text-left group"
                    >
                      <Icon className="w-5 h-5 text-charcoal/60 group-hover:text-sage transition-colors" />
                      <span className="text-sm text-charcoal group-hover:text-charcoal/90">
                        {option.label}
                      </span>
                    </button>
                  </div>
                )
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
