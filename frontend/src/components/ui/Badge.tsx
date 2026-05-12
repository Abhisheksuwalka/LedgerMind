import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/cn"

const badgeVariants = cva(
  "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider",
  {
    variants: {
      intent: {
        critical: "bg-danger-subtle text-danger-bright border border-danger-muted",
        warning: "bg-warning-subtle text-warning-bright border border-warning-muted",
        info: "bg-primary-950 text-primary-300 border border-primary-800",
      },
    },
    defaultVariants: {
      intent: "info",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, intent, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ intent }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
