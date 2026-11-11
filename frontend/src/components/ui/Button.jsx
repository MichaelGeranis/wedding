import { cva } from "class-variance-authority"
import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-base font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-rose-dusty text-white shadow-lg shadow-rose-dusty/30 hover:bg-rose-dark hover:shadow-xl hover:-translate-y-0.5",
        outline: "border-2 border-rose-dusty text-rose-dusty hover:bg-rose-dusty hover:text-white hover:shadow-md",
        ghost: "text-charcoal hover:bg-sage/10 hover:text-sage-dark",
        sage: "bg-sage text-white shadow-lg shadow-sage/30 hover:bg-sage-dark hover:shadow-xl hover:-translate-y-0.5",
        danger: "bg-red-500 text-white shadow-lg shadow-red-500/30 hover:bg-red-600 hover:shadow-xl hover:-translate-y-0.5",
      },
      size: {
        default: "h-12 px-6 py-3",
        sm: "h-9 px-4 text-sm",
        lg: "h-14 px-8 py-4 text-lg",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export function Button({ className, variant, size, ...props }) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}
