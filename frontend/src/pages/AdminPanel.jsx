import { useState, useEffect } from 'react'
import { Link } from 'react-router'
import { motion } from 'framer-motion'
import { LogOut, Search, Filter, UserPlus } from 'lucide-react'
import { useAuth } from '../context/auth'
import { adminAPI } from '../services/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Label } from '../components/ui/Label'
import { Select } from '../components/ui/Select'
import { GuestStatsCards } from '../components/wedding/GuestStatsCards'
import { GuestTable } from '../components/wedding/GuestTable'
import { ExportButton } from '../components/ExportButton'
import { useTranslation } from 'react-i18next'

const PAGE_SIZE = 10

function AdminPanel() {
  const { t } = useTranslation()
  const { isAuthenticated, login, logout } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState(null)
  const [loginLoading, setLoginLoading] = useState(false)

  const [guests, setGuests] = useState([])
  const [stats, setStats] = useState(null)
  const [loadedKey, setLoadedKey] = useState(null)
  const [error, setError] = useState(null)

  const [filter, setFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  // The guest list is loading until the response for this page and filter arrives.
  const requestKey = `${currentPage}:${filter}`
  const loading = loadedKey !== requestKey

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError(null)
    setLoginLoading(true)

    try {
      const response = await adminAPI.login(username, password)
      login(response.access_token)
      setUsername('')
      setPassword('')
    } catch (err) {
      if (err.response?.data?.detail) {
        setLoginError(err.response.data.detail)
      } else {
        setLoginError(t('admin.invalid_credentials'))
      }
    } finally {
      setLoginLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await adminAPI.getStats()
      setStats(response)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  useEffect(() => {
    if (!isAuthenticated) return
    let ignore = false

    const params = {
      limit: PAGE_SIZE,
      offset: (currentPage - 1) * PAGE_SIZE,
    }
    if (filter === 'attending') {
      params.attending = true
    } else if (filter === 'not_attending') {
      params.attending = false
    }

    adminAPI
      .getGuests(params)
      .then((response) => {
        if (ignore) return
        setGuests(response.guests)
        setTotalPages(Math.ceil(response.total / PAGE_SIZE))
        setError(null)
      })
      .catch((err) => {
        if (!ignore) setError(err.message || 'Failed to load guests')
      })
      .finally(() => {
        if (!ignore) setLoadedKey(`${currentPage}:${filter}`)
      })

    adminAPI
      .getStats()
      .then((response) => {
        if (!ignore) setStats(response)
      })
      .catch((err) => console.error('Failed to load stats:', err))

    return () => {
      ignore = true
    }
  }, [isAuthenticated, currentPage, filter])

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter)
    setCurrentPage(1)
  }

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage)
  }

  const handleDelete = async (guest) => {
    if (!window.confirm(t('admin.delete_confirmation', { name: guest.guest_name }))) {
      return
    }

    try {
      const ok = await adminAPI.deleteGuest(guest.id)
      if (ok) {
        setGuests((prev) => prev.filter((g) => g.id !== guest.id))
        // Refresh stats after deletion
        fetchStats()
      } else {
        alert(t('admin.delete_failed'))
      }
    } catch (err) {
      console.error('Delete error', err)
      alert(t('admin.delete_error'))
    }
  }

  // Filter guests by search query
  const filteredGuests = guests.filter((guest) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      guest.guest_name?.toLowerCase().includes(query) ||
      guest.email?.toLowerCase().includes(query) ||
      guest.phone?.includes(query) ||
      guest.confirmation_number?.toLowerCase().includes(query)
    )
  })

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen gradient-bg gradient-overlay flex items-center justify-center px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="glass-card rounded-3xl p-10 md:p-12 w-full max-w-md"
        >
          <h1 className="font-serif text-3xl md:text-4xl text-charcoal font-bold text-center mb-8">
            {t('admin.login_title')}
          </h1>

          {loginError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-rose-dusty/10 border-2 border-rose-dusty/30 rounded-xl p-4 mb-6"
            >
              <p className="text-rose-dark text-sm">{loginError}</p>
            </motion.div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="[&>*+*]:mt-2">
              <Label htmlFor="username">{t('admin.username')}</Label>
              <Input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                placeholder={t('admin.username_placeholder')}
              />
            </div>

            <div className="[&>*+*]:mt-2">
              <Label htmlFor="password">{t('admin.password')}</Label>
              <Input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder={t('admin.password_placeholder')}
              />
            </div>

            <Button type="submit" disabled={loginLoading} size="lg" className="w-full">
              {loginLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  {t('admin.logging_in')}
                </>
              ) : (
                t('admin.login_button')
              )}
            </Button>
          </form>
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
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
          <div>
            <h1 className="font-serif text-3xl md:text-5xl text-charcoal font-bold">

            </h1>
            <p className="text-charcoal/60 mt-2">
              {t('admin.guest_management_subtitle')}
            </p>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <ExportButton />
            <Link to="/admin/invited">
              <Button variant="secondary">
                <UserPlus className="w-5 h-5" />
                {t('admin.invitation_list')}
              </Button>
            </Link>
            <Button variant="ghost" onClick={logout}>
              <LogOut className="w-5 h-5" />
              {t('admin.logout')}
            </Button>
          </div>
        </motion.div>

        {/* Stats Cards */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <GuestStatsCards stats={stats} />
          </motion.div>
        )}

        {/* Filters and Search */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="glass-card rounded-2xl p-6 space-y-4 shadow-lg"
        >
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-charcoal/40" />
                <Input
                  type="text"
                  placeholder={t('admin.search_placeholder')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Filter Dropdown */}
            <div className="md:w-64">
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-charcoal/40 pointer-events-none" />
                <Select
                  value={filter}
                  onChange={(e) => handleFilterChange(e.target.value)}
                  className="pl-10"
                >
                  <option value="all">{t('admin.filter_all')}</option>
                  <option value="attending">{t('admin.filter_attending')}</option>
                  <option value="not_attending">{t('admin.filter_not_attending')}</option>
                </Select>
              </div>
            </div>
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
              <p className="text-charcoal/60">{t('admin.loading_guests')}</p>
            </div>
          ) : (
            <GuestTable guests={filteredGuests} onDelete={handleDelete} />
          )}
        </motion.div>

        {/* Pagination */}
        {totalPages > 1 && !searchQuery && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="flex items-center justify-center gap-4"
          >
            <Button
              variant="outline"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              {t('admin.previous')}
            </Button>

            <span className="text-charcoal/70 min-w-[120px] text-center">
              {t('admin.page_of', { currentPage, totalPages })}
            </span>

            <Button
              variant="outline"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              {t('admin.next')}
            </Button>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default AdminPanel
