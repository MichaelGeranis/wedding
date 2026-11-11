import { motion } from 'framer-motion'
import { Trash2, Phone, Edit2, StickyNote, QrCode, Copy } from 'lucide-react'
import { Button } from '../ui/Button'
import { useTranslation } from 'react-i18next'
import { invitedGuestsAPI } from '../../services/api'
import { useState } from 'react'

export function InvitedGuestsTable({ guests, onDelete, onEdit }) {
  const { t } = useTranslation()
  const [downloadingQR, setDownloadingQR] = useState(null)
  const [copiedId, setCopiedId] = useState(null)

  const handleDownloadQR = async (guest) => {
    try {
      setDownloadingQR(guest.id)
      await invitedGuestsAPI.downloadQRCode(guest.id, guest.name)
    } catch (error) {
      console.error('Failed to download QR code:', error)
      alert(t('errors.qr_download_failed'))
    } finally {
      setDownloadingQR(null)
    }
  }

  const handleCopyURL = async (guest) => {
    try {
      const frontendUrl = window.location.origin
      const invitationUrl = `${frontendUrl}/?token=${guest.token}`
      await navigator.clipboard.writeText(invitationUrl)
      setCopiedId(guest.id)
      setTimeout(() => setCopiedId(null), 2000) // Reset after 2 seconds
    } catch (error) {
      console.error('Failed to copy URL:', error)
      alert(t('errors.copy_url_failed'))
    }
  }

  if (!guests || guests.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center">
        <p className="text-charcoal/60 text-lg">{t('invited_guests.no_guests')}</p>
        <p className="text-charcoal/40 text-sm mt-2">{t('invited_guests.add_guests')}</p>
      </div>
    )
  }

  return (
    <>
      {/* Desktop Table View */}
      <div className="hidden md:block glass-card rounded-2xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-charcoal/5">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('invited_guests.name')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('invited_guests.phone')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('invited_guests.notes')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('invited_guests.invitation_sent')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('invited_guests.rsvp')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('invited_guests.added_on')}
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('invited_guests.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-charcoal/10">
              {guests.map((guest, index) => (
                <motion.tr
                  key={guest.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="hover:bg-sage/5 transition-colors"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-charcoal">{guest.name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-charcoal/70">
                      <Phone className="w-4 h-4" />
                      <span>{guest.phone}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-charcoal/70 max-w-[200px]">
                    {guest.notes ? (
                      <span className="truncate block">{guest.notes}</span>
                    ) : (
                      <span className="text-charcoal/40">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {guest.invitation_sent ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-sage/10 text-sage text-xs font-semibold">{t('common.sent')}</span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-charcoal/5 text-charcoal text-xs">{t('common.not_sent')}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {guest.rsvp_received ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-sage/10 text-sage text-xs font-semibold">{t('common.yes')}</span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-charcoal/5 text-charcoal text-xs">{t('common.no')}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-charcoal/70">
                    {new Date(guest.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleDownloadQR(guest)}
                        disabled={downloadingQR === guest.id}
                        title={t('invited_guests.download_qr')}
                      >
                        <QrCode className="w-4 h-4" />
                      </Button>
                      <Button
                        variant={copiedId === guest.id ? 'primary' : 'secondary'}
                        size="sm"
                        onClick={() => handleCopyURL(guest)}
                        title={t('invited_guests.copy_url')}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => onEdit(guest)}
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => onDelete(guest)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {guests.map((guest, index) => (
          <motion.div
            key={guest.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="glass-card rounded-2xl p-5 shadow-lg"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-charcoal text-lg mb-1">
                  {guest.name}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="icon"
                  onClick={() => handleDownloadQR(guest)}
                  disabled={downloadingQR === guest.id}
                  title={t('invited_guests.download_qr')}
                >
                  <QrCode className="w-4 h-4" />
                </Button>
                <Button
                  variant={copiedId === guest.id ? 'primary' : 'secondary'}
                  size="icon"
                  onClick={() => handleCopyURL(guest)}
                  title={t('invited_guests.copy_url')}
                >
                  <Copy className="w-4 h-4" />
                </Button>
                <Button
                  variant="secondary"
                  size="icon"
                  onClick={() => onEdit(guest)}
                >
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button
                  variant="danger"
                  size="icon"
                  onClick={() => onDelete(guest)}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-charcoal/70">
                <Phone className="w-4 h-4 shrink-0" />
                <span>{guest.phone}</span>
              </div>
              <div className="flex items-center gap-2 text-sm mt-2">
                <strong className="text-charcoal/70">{t('invited_guests.status')}:</strong>
                {guest.invitation_sent ? (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-sage/10 text-sage text-xs font-semibold">{t('common.sent')}</span>
                ) : (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-charcoal/5 text-charcoal text-xs">{t('common.not_sent')}</span>
                )}
              </div>
              <div className="flex items-center gap-2 text-sm mt-2">
                <strong className="text-charcoal/70">{t('invited_guests.rsvp')}:</strong>
                {guest.rsvp_received ? (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-sage/10 text-sage text-xs font-semibold">{t('common.yes')}</span>
                ) : (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-charcoal/5 text-charcoal text-xs">{t('common.no')}</span>
                )}
              </div>
              {guest.notes && (
                <div className="flex items-start gap-2 text-charcoal/70">
                  <StickyNote className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{guest.notes}</span>
                </div>
              )}
              <div className="pt-2 border-t border-charcoal/10 text-charcoal/50">
                {t('invited_guests.added')}: {new Date(guest.created_at).toLocaleDateString()}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </>
  )
}
