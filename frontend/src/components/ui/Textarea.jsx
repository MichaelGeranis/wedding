import { cn } from "../../lib/utils"

export function Textarea({ className, ref, ...props }) {
  return (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-[100px] w-full rounded-xl border-2 border-charcoal/20 bg-white px-4 py-3 text-base transition-all",
        "placeholder:text-charcoal/40",
        "focus:border-sage focus:outline-hidden focus:ring-2 focus:ring-sage/20",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "resize-y",
        className
      )}
      {...props}
    />
  )
}
