import { cn } from "../../lib/utils"

export function Select({ className, ref, ...props }) {
  return (
    <select
      ref={ref}
      className={cn(
        "flex h-12 w-full rounded-xl border-2 border-charcoal/20 bg-white px-4 py-3 text-base transition-all",
        "focus:border-sage focus:outline-hidden focus:ring-2 focus:ring-sage/20",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "cursor-pointer",
        className
      )}
      {...props}
    />
  )
}
