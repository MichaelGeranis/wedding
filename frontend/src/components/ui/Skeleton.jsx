import { cn } from "../../lib/utils"

export function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl bg-charcoal/10",
        className
      )}
      {...props}
    />
  )
}
