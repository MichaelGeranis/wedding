import { cn } from "../../lib/utils"

export function Label({ className, ...props }) {
  return (
    <label
      className={cn(
        "text-sm font-medium text-charcoal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
        className
      )}
      {...props}
    />
  )
}
