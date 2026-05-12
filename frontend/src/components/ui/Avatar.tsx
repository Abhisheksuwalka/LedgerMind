import * as React from "react"
import { cn } from "@/lib/cn"

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string
  fallback: string
  name?: string
}

const colors = [
  "bg-primary-800",
  "bg-success-muted",
  "bg-warning-muted",
  "bg-danger-muted",
  "bg-primary-900",
  "bg-border-strong"
];

function getHashColor(name: string) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, fallback, name = "User", ...props }, ref) => {
    const bgColor = src ? "bg-transparent" : getHashColor(name);

    return (
      <div
        ref={ref}
        className={cn(
          "relative flex h-8 w-8 shrink-0 overflow-hidden rounded-full items-center justify-center text-white text-xs font-medium",
          bgColor,
          className
        )}
        {...props}
      >
        {src ? (
          <img
            src={src}
            alt={name}
            className="aspect-square h-full w-full object-cover"
          />
        ) : (
          <span>{fallback}</span>
        )}
      </div>
    )
  }
)
Avatar.displayName = "Avatar"

export { Avatar }
