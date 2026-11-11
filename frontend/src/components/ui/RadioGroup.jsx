import { cn } from "../../lib/utils"

export function RadioGroup({ className, ...props }) {
  return (
    <div
      className={cn("grid gap-3", className)}
      role="radiogroup"
      {...props}
    />
  )
}

export function RadioGroupItem({ className, children, id, value, checked, onChange, ...props }) {
  return (
    <div className="flex items-center space-x-3">
      <input
        type="radio"
        id={id}
        value={value}
        checked={checked}
        onChange={onChange}
        className={cn(
          "h-5 w-5 rounded-full border-2 border-charcoal/30 text-sage transition-all",
          "focus:ring-2 focus:ring-sage focus:ring-offset-2",
          "checked:border-sage checked:bg-sage",
          className
        )}
        {...props}
      />
      <label
        htmlFor={id}
        className="text-base font-medium text-charcoal cursor-pointer select-none"
      >
        {children}
      </label>
    </div>
  )
}
