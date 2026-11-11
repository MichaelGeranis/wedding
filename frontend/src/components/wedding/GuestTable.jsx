import { motion } from 'framer-motion'
import { Trash2, Mail, Phone, UtensilsCrossed, MessageSquare } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { useTranslation } from 'react-i18next'

export function GuestTable({ guests, onDelete }) {
  const { t } = useTranslation()

  if (!guests || guests.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center">
        <p className="text-charcoal/60 text-lg">{t('admin.no_guests')}</p>
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
                  {t('admin.guest_name')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('admin.contact')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('admin.status')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('admin.plus_one')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('admin.children', 'Children')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('admin.dietary')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('admin.message')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('admin.confirmation')}
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-charcoal uppercase tracking-wider">
                  {t('admin.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-charcoal/10">
              {guests.map((guest, index) => (
                <motion.tr
                  key={guest.confirmation_number}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="hover:bg-sage/5 transition-colors"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-charcoal">{guest.guest_name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1 text-sm">
                      <div className="flex items-center gap-2 text-charcoal/70">
                        <Mail className="w-4 h-4" />
                        <span className="truncate max-w-[200px]">{guest.email}</span>
                      </div>
                      {guest.phone && (
                        <div className="flex items-center gap-2 text-charcoal/70">
                          <Phone className="w-4 h-4" />
                          <span>{guest.phone}</span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant={guest.attending ? 'success' : 'error'}>
                      {guest.attending ? t('admin.attending') : t('admin.not_attending')}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 text-sm text-charcoal/70">
                    {guest.plus_one ? t('common.yes') : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-charcoal/70">
                    {guest.children_count > 0 ? guest.children_count : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-charcoal/70">
                    {guest.dietary_restrictions ? (
                      <span className="max-w-[200px] truncate block" title={guest.dietary_restrictions}>
                        {guest.dietary_restrictions}
                      </span>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-charcoal/70">
                    {guest.message ? (
                      <span className="max-w-[200px] truncate block" title={guest.message}>
                        {guest.message}
                      </span>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <code className="text-xs bg-charcoal/10 px-2 py-1 rounded font-mono">
                      {guest.confirmation_number}
                    </code>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => onDelete(guest)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
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
            key={guest.confirmation_number}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="glass-card rounded-2xl p-5 shadow-lg"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-charcoal text-lg mb-1">
                  {guest.guest_name}
                </h3>
                <Badge variant={guest.attending ? 'success' : 'error'}>
                  {guest.attending ? t('admin.attending') : t('admin.not_attending')}
                </Badge>
              </div>
              <Button
                variant="danger"
                size="icon"
                onClick={() => onDelete(guest)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-charcoal/70">
                <Mail className="w-4 h-4 flex-shrink-0" />
                <span className="truncate">{guest.email}</span>
              </div>
              {guest.phone && (
                <div className="flex items-center gap-2 text-charcoal/70">
                  <Phone className="w-4 h-4 flex-shrink-0" />
                  <span>{guest.phone}</span>
                </div>
              )}
              {guest.plus_one && (
                <div className="text-charcoal/70">
                  <span className="font-medium">{t('admin.plus_one')}:</span> {t('common.yes')}
                </div>
              )}
              {guest.children_count > 0 && (
                <div className="text-charcoal/70">
                  <span className="font-medium">{t('admin.children', 'Children')}:</span> {guest.children_count}
                </div>
              )}
              {guest.dietary_restrictions && (
                <div className="flex items-start gap-2 text-charcoal/70">
                  <UtensilsCrossed className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{guest.dietary_restrictions}</span>
                </div>
              )}
              {guest.message && (
                <div className="flex items-start gap-2 text-charcoal/70">
                  <MessageSquare className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span className="italic">{guest.message}</span>
                </div>
              )}
              <div className="pt-2 border-t border-charcoal/10">
                <code className="text-xs bg-charcoal/10 px-2 py-1 rounded font-mono">
                  {guest.confirmation_number}
                </code>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </>
  )
}
