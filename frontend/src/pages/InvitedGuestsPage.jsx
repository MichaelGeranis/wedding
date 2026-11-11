import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router'
import { motion, AnimatePresence } from 'framer-motion'
import { UserPlus, Search, X, Users, ArrowLeft, Download, Upload } from 'lucide-react'
import { useAuth } from '../context/auth'
import { invitedGuestsAPI } from '../services/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Textarea } from '../components/ui/Textarea'
import { Label } from '../components/ui/Label'
import { InvitedGuestsTable } from '../components/wedding/InvitedGuestsTable'
import { t } from 'i18next'

function InvitedGuestsPage() {
  const { isAuthenticated } = useAuth()
  const [guests, setGuests] = useState([])
  const [stats, setStats] = useState(null)
  // Bumped to reload the list; the list is loading until that reload's response arrives.
  const [reloadCount, setReloadCount] = useState(0)
  const [loadedCount, setLoadedCount] = useState(null)
  const loading = loadedCount !== reloadCount
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isExporting, setIsExporting] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [importResult, setImportResult] = useState(null)
  const [showImportResult, setShowImportResult] = useState(false)
  const fileInputRef = useRef(null)

  // Form state
  const [showForm, setShowForm] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState(null)
  const [editingGuest, setEditingGuest] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    notes: '',
    invitation_sent: false,
    rsvp_received: false,
  })

  const fetchStats = async () => {
    try {
      const response = await invitedGuestsAPI.getInvitedGuestsStats()
      setStats(response)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  useEffect(() => {
    if (!isAuthenticated) return
    let ignore = false

    invitedGuestsAPI
      .getInvitedGuests()
      .then((response) => {
        if (ignore) return
        setGuests(response.guests)
        setError(null)
      })
      .catch((err) => {
        if (!ignore) setError(err.message || 'Failed to load invited guests')
      })
      .finally(() => {
        if (!ignore) setLoadedCount(reloadCount)
      })

    invitedGuestsAPI
      .getInvitedGuestsStats()
      .then((response) => {
        if (!ignore) setStats(response)
      })
      .catch((err) => console.error('Failed to load stats:', err))

    return () => {
      ignore = true
    }
  }, [isAuthenticated, reloadCount])

  const resetForm = () => {
    setFormData({ name: '', phone: '', notes: '' })
    setEditingGuest(null)
    setFormError(null)
    setShowForm(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormLoading(true)
    setFormError(null)

    try {
      if (editingGuest) {
        // Update existing guest
        const updated = await invitedGuestsAPI.updateInvitedGuest(editingGuest.id, formData)
        setGuests((prev) =>
          prev.map((g) => (g.id === editingGuest.id ? updated : g))
        )
      } else {
        // Create new guest
        const newGuest = await invitedGuestsAPI.createInvitedGuest(formData)
        setGuests((prev) => [newGuest, ...prev])
      }
      // Refresh stats after create/update
      fetchStats()
      resetForm()
    } catch (err) {
      if (err.response?.data?.detail) {
        setFormError(err.response.data.detail)
      } else {
        setFormError(err.message || 'Failed to save guest')
      }
    } finally {
      setFormLoading(false)
    }
  }

  const handleEdit = (guest) => {
    setEditingGuest(guest)
    setFormData({
      name: guest.name,
      phone: guest.phone,
      notes: guest.notes || '',
      invitation_sent: !!guest.invitation_sent,
      rsvp_received: !!guest.rsvp_received,
    })
    setShowForm(true)
  }

  const handleDelete = async (guest) => {
    if (!window.confirm(t('invited_guests.delete_confirmation_remove', { name: guest.name }))) {
      return
    }

    try {
      const ok = await invitedGuestsAPI.deleteInvitedGuest(guest.id)
      if (ok) {
        setGuests((prev) => prev.filter((g) => g.id !== guest.id))
        // Refresh stats after deletion
        fetchStats()
      } else {
        alert(t('errors.delete_failed'))
      }
    } catch (err) {
      console.error('Delete error', err)
      alert(t('errors.delete_error'))
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      await invitedGuestsAPI.exportInvitedGuestsCSV()
    } catch (error) {
      console.error('Export failed:', error)
      alert(t('errors.export_failed'))
    } finally {
      setIsExporting(false)
    }
  }

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  const handleImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsImporting(true)
    setImportResult(null)

    try {
      const result = await invitedGuestsAPI.importInvitedGuestsCSV(file)
      setImportResult(result)
      setShowImportResult(true)

      // Refresh the guest list and stats if any imports were successful
      if (result.success_count > 0) {
        setReloadCount((count) => count + 1)
      }
    } catch (error) {
      console.error('Import failed:', error)
      const errorMessage = error.response?.data?.detail || t('errors.import_failed')
      setImportResult({
        success_count: 0,
        error_count: 1,
        skipped_count: 0,
        errors: [{ row: '-', error: errorMessage }],
      })
      setShowImportResult(true)
    } finally {
      setIsImporting(false)
      // Reset file input so the same file can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // Filter guests by search query
  const filteredGuests = guests.filter((guest) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      guest.name?.toLowerCase().includes(query) ||
      guest.phone?.includes(query) ||
      guest.notes?.toLowerCase().includes(query)
    )
  })

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen gradient-bg gradient-overlay flex items-center justify-center px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="glass-card rounded-3xl p-10 md:p-12 w-full max-w-md shadow-2xl text-center"
        >
          <h1 className="font-serif text-3xl md:text-4xl text-charcoal font-bold mb-4">
            {t('invited_guests.access_denied')}
          </h1>
          <p className="text-charcoal/70">
            {t('invited_guests.access_denied')}
          </p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-bg gradient-overlay px-6 py-20 md:py-28">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-4"
        >
          <Link
            to="/admin"
            className="inline-flex items-center gap-2 text-charcoal/60 hover:text-charcoal transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {t('invited_guests.back_to_guest_management')}
          </Link>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h1 className="font-serif text-3xl md:text-5xl text-charcoal font-bold">
                {t('invited_guests.title')}
              </h1>
              <p className="text-charcoal/60 mt-2">
                {t('invited_guests.subtitle')}
              </p>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              {/* Hidden file input for CSV import */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleImport}
                className="hidden"
              />
              <Button
                variant="secondary"
                onClick={handleImportClick}
                disabled={isImporting}
              >
                {isImporting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-charcoal border-t-transparent" />
                    {t('common.uploading')}
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    {t('invited_guests.import_csv')}
                  </>
                )}
              </Button>
              <Button
                variant="secondary"
                onClick={handleExport}
                disabled={isExporting || guests.length === 0}
              >
                {isExporting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-charcoal border-t-transparent" />
                    {t('common.exporting')}
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5" />
                    {t('invited_guests.export_csv')}
                  </>
                )}
              </Button>
              <Button onClick={() => setShowForm(true)}>
                <UserPlus className="w-5 h-5" />
                {t('invited_guests.add_guest_title')}
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Stats Card */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="glass-card rounded-2xl p-6 shadow-lg"
          >
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {/* Total Invited */}
              <div className="flex items-center gap-4">
                <div className="bg-sage/20 text-sage p-3 rounded-xl">
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-3xl md:text-4xl font-serif font-bold text-charcoal">
                    {stats.total_invited}
                  </div>
                  <div className="text-sm text-charcoal/60 uppercase tracking-wider">
                    {t('invited_guests.total_invited')}
                  </div>
                </div>
              </div>

              {/* Base Guests */}
              <div className="flex items-center gap-4">
                <div className="bg-blue-500/20 text-blue-600 p-3 rounded-xl">
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-3xl md:text-4xl font-serif font-bold text-charcoal">
                    {stats.total_invited_base}
                  </div>
                  <div className="text-sm text-charcoal/60 uppercase tracking-wider">
                    {t('invited_guests.base_guests')}
                  </div>
                </div>
              </div>

              {/* Children */}
              <div className="flex items-center gap-4">
                <div className="bg-purple-500/20 text-purple-600 p-3 rounded-xl">
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-3xl md:text-4xl font-serif font-bold text-charcoal">
                    {stats.total_children}
                  </div>
                  <div className="text-sm text-charcoal/60 uppercase tracking-wider">
                    {t('invited_guests.children')}
                  </div>
                </div>
              </div>

              {/* Plus Ones */}
              <div className="flex items-center gap-4">
                <div className="bg-rose-dusty/20 text-rose-dark p-3 rounded-xl">
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-3xl md:text-4xl font-serif font-bold text-charcoal">
                    {stats.total_plus_ones}
                  </div>
                  <div className="text-sm text-charcoal/60 uppercase tracking-wider">
                    {t('invited_guests.plus_ones')}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Add/Edit Form Modal */}
        <AnimatePresence>
          {showForm && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-charcoal/50 flex items-center justify-center z-50 p-6"
              onClick={(e) => e.target === e.currentTarget && resetForm()}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="glass-card rounded-3xl p-8 w-full max-w-lg shadow-2xl"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="font-serif text-2xl text-charcoal font-bold">
                    {editingGuest ? t('invited_guests.edit_guest_title') : t('invited_guests.add_guest_title')}
                  </h2>
                  <button
                    onClick={resetForm}
                    className="p-2 rounded-lg hover:bg-charcoal/10 transition-colors"
                  >
                    <X className="w-5 h-5 text-charcoal/60" />
                  </button>
                </div>

                {formError && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-rose-dusty/10 border-2 border-rose-dusty/30 rounded-xl p-4 mb-6"
                  >
                    <p className="text-rose-dark text-sm">{formError}</p>
                  </motion.div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-2">
                    <Label htmlFor="name">{t('invited_guests.guest_name')} *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      placeholder={t('invited_guests.name_placeholder')}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">{t('invited_guests.phone')} *</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={formData.phone}
                      onChange={(e) =>
                        setFormData({ ...formData, phone: e.target.value })
                      }
                      placeholder={t('invited_guests.phone_placeholder')}
                      required
                    />
                    <p className="text-xs text-charcoal/50">
                      {t('invited_guests.phone_verification_note')}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="notes">{t('invited_guests.notes')}</Label>
                    <Textarea
                      id="notes"
                      value={formData.notes}
                      onChange={(e) =>
                        setFormData({ ...formData, notes: e.target.value })
                      }
                      placeholder={t('invited_guests.notes_placeholder')}
                      rows={3}
                    />
                  </div>

                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.invitation_sent}
                        onChange={(e) => setFormData({ ...formData, invitation_sent: e.target.checked })}
                      />
                      <span className="text-sm text-charcoal/70">{t('common.sent')}</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.rsvp_received}
                        onChange={(e) => setFormData({ ...formData, rsvp_received: e.target.checked })}
                      />
                      <span className="text-sm text-charcoal/70">{t('invited_guests.rsvp_received')}</span>
                    </label>
                  </div>

                  <div className="flex gap-3 pt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={resetForm}
                      className="flex-1"
                    >
                      {t('common.cancel')}
                    </Button>
                    <Button
                      type="submit"
                      disabled={formLoading}
                      className="flex-1"
                    >
                      {formLoading ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                          {t('common.saving')}
                        </>
                      ) : editingGuest ? (
                        t('invited_guests.edit_guest')
                      ) : (
                        t('invited_guests.add_guest')
                      )}
                    </Button>
                  </div>
                </form>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Import Result Modal */}
        <AnimatePresence>
          {showImportResult && importResult && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-charcoal/50 flex items-center justify-center z-50 p-6"
              onClick={(e) => e.target === e.currentTarget && setShowImportResult(false)}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="glass-card rounded-3xl p-8 w-full max-w-lg shadow-2xl"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="font-serif text-2xl text-charcoal font-bold">
                    {t('invited_guests.import_results')}
                  </h2>
                  <button
                    onClick={() => setShowImportResult(false)}
                    className="p-2 rounded-lg hover:bg-charcoal/10 transition-colors"
                  >
                    <X className="w-5 h-5 text-charcoal/60" />
                  </button>
                </div>

                <div className="space-y-4">
                  {/* Summary Stats */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-sage/20 rounded-xl p-4 text-center">
                      <div className="text-2xl font-bold text-sage">{importResult.success_count}</div>
                      <div className="text-sm text-charcoal/60">{t('invited_guests.import_success')}</div>
                    </div>
                    <div className="bg-amber-500/20 rounded-xl p-4 text-center">
                      <div className="text-2xl font-bold text-amber-600">{importResult.skipped_count}</div>
                      <div className="text-sm text-charcoal/60">{t('invited_guests.import_skipped')}</div>
                    </div>
                    <div className="bg-rose-dusty/20 rounded-xl p-4 text-center">
                      <div className="text-2xl font-bold text-rose-dark">{importResult.error_count}</div>
                      <div className="text-sm text-charcoal/60">{t('invited_guests.import_errors')}</div>
                    </div>
                  </div>

                  {/* Error Details */}
                  {importResult.errors && importResult.errors.length > 0 && (
                    <div className="bg-rose-dusty/10 border-2 border-rose-dusty/30 rounded-xl p-4">
                      <h3 className="font-semibold text-rose-dark mb-2">
                        {t('invited_guests.import_error_details')}
                      </h3>
                      <ul className="space-y-1 max-h-40 overflow-y-auto text-sm">
                        {importResult.errors.map((err, idx) => (
                          <li key={idx} className="text-charcoal/70">
                            <span className="font-medium">{t('invited_guests.row')} {err.row}:</span> {err.error}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* CSV Format Help */}
                  <div className="bg-charcoal/5 rounded-xl p-4">
                    <h3 className="font-semibold text-charcoal mb-2">
                      {t('invited_guests.csv_format_help')}
                    </h3>
                    <p className="text-sm text-charcoal/60">
                      {t('invited_guests.csv_format_description')}
                    </p>
                  </div>
                </div>

                <div className="mt-6">
                  <Button onClick={() => setShowImportResult(false)} className="w-full">
                    {t('common.close')}
                  </Button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="glass-card rounded-2xl p-6 shadow-lg"
        >
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-charcoal/40" />
            <Input
              type="text"
              placeholder={t('invited_guests.search_placeholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </motion.div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-rose-dusty/10 border-2 border-rose-dusty/30 rounded-xl p-4"
          >
            <p className="text-rose-dark">{error}</p>
          </motion.div>
        )}

        {/* Guest Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          {loading ? (
            <div className="glass-card rounded-2xl p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-sage border-t-rose-dusty mx-auto mb-4"></div>
              <p className="text-charcoal/60">{t('common.loading')}</p>
            </div>
          ) : (
            <InvitedGuestsTable
              guests={filteredGuests}
              onDelete={handleDelete}
              onEdit={handleEdit}
            />
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default InvitedGuestsPage
