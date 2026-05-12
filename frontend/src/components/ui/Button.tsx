import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/cn"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 disabled:opacity-40 disabled:cursor-not-allowed",
  {
    variants: {
      intent: {
        primary: "bg-primary-600 text-white hover:bg-primary-500",
        ghost: "bg-transparent text-secondary hover:bg-bg-hover hover:text-primary",
        danger: "bg-danger-subtle text-danger-bright hover:bg-danger-muted",
        outline: "border border-border-default bg-transparent text-primary hover:border-border-strong",
      },
      size: {
        sm: "h-8 rounded-md px-3 text-xs",
        md: "h-10 rounded-md px-4 py-2",
        lg: "h-11 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      intent: "primary",
      size: "md",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, intent, size, asChild = false, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ intent, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
