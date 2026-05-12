import * as React from "react"
import { cn } from "@/lib/cn"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, leftIcon, rightIcon, ...props }, ref) => {
    return (
      <div className="relative w-full">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center justify-center text-tertiary">
            {leftIcon}
          </div>
        )}
        <input
          type={type}
          className={cn(
            "flex h-10 w-full rounded-md border border-border-default bg-bg-sunken px-3 py-2 text-sm text-primary transition-all duration-150 file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-tertiary focus-visible:outline-none focus-visible:border-primary-500 focus-visible:ring-[3px] focus-visible:ring-primary-500/15 disabled:cursor-not-allowed disabled:opacity-50",
            leftIcon && "pl-10",
            rightIcon && "pr-10",
            className
          )}
          ref={ref}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center text-tertiary">
            {rightIcon}
          </div>
        )}
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input }
