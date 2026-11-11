import { motion } from 'framer-motion'
import { Users, UserCheck, UserX, Clock, Baby } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function GuestStatsCards({ stats }) {
  const { t } = useTranslation()
  if (!stats) return null

  const statCards = [
    {
      label: t('admin.total_rsvps'),
      value: stats.total || 0,
      icon: Users,
      color: 'text-charcoal',
      bgColor: 'bg-charcoal/10',
    },
    {
      label: t('admin.attending'),
      value: stats.attending || 0,
      icon: UserCheck,
      color: 'text-sage',
      bgColor: 'bg-sage/20',
    },
    {
      label: t('admin.not_attending'),
      value: stats.not_attending || 0,
      icon: UserX,
      color: 'text-rose-dark',
      bgColor: 'bg-rose-dusty/20',
    },
    {
      label: t('admin.children_attending', 'Children'),
      value: stats.children || 0,
      icon: Baby,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      label: t('admin.pending'),
      value: typeof stats.pending === 'number' ? stats.pending : Math.max(0, (stats.total || 0) - (stats.attending || 0) - (stats.not_attending || 0)),
      icon: Clock,
      color: 'text-yellow-700',
      bgColor: 'bg-yellow-100',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
      {statCards.map((card, index) => {
        const Icon = card.icon
        return (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            className="glass-card rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`${card.bgColor} ${card.color} p-3 rounded-xl`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
            <div className={`text-3xl md:text-4xl font-serif font-bold ${card.color} mb-1`}>
              {card.value}
            </div>
            <div className="text-sm text-charcoal/60 uppercase tracking-wider">
              {card.label}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
