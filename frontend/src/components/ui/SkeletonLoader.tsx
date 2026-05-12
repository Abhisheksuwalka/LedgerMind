import * as React from "react"
import { cn } from "@/lib/cn"

export interface SkeletonLoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "kpi-grid" | "chart" | "list" | "table" | "default";
}

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("skeleton", className)}
      {...props}
    />
  )
}

function SkeletonLoader({ className, variant = "default", ...props }: SkeletonLoaderProps) {
  if (variant === "kpi-grid") {
    return (
      <div className={cn("grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4", className)} {...props}>
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-bg-raised border border-border-subtle rounded-lg p-6 flex flex-col gap-4 shadow-md">
            <div className="flex justify-between items-center">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-4 rounded-full" />
            </div>
            <Skeleton className="h-8 w-20" />
            <div className="flex justify-between items-end mt-2">
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (variant === "chart") {
    return (
      <div className={cn("bg-bg-raised border border-border-subtle rounded-lg p-6 shadow-md flex flex-col gap-6", className)} {...props}>
        <div className="flex justify-between items-center">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-8 w-32" />
        </div>
        <Skeleton className="h-[320px] w-full" />
      </div>
    )
  }

  if (variant === "list") {
    return (
      <div className={cn("bg-bg-raised border border-border-subtle rounded-lg shadow-md flex flex-col", className)} {...props}>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="p-4 border-b border-border-subtle flex items-center justify-between last:border-0">
            <div className="flex items-center gap-3 w-full">
              <Skeleton className="h-5 w-5 rounded-full" />
              <div className="flex flex-col gap-2 flex-1">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-3 w-1/4" />
              </div>
            </div>
            <Skeleton className="h-6 w-16" />
          </div>
        ))}
      </div>
    )
  }

  if (variant === "table") {
    return (
      <div className={cn("bg-bg-raised border border-border-subtle rounded-lg shadow-md overflow-hidden", className)} {...props}>
        <div className="bg-bg-sunken p-3 border-b border-border-subtle flex gap-4">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/4" />
        </div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="p-4 border-b border-border-subtle flex gap-4 last:border-0">
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-4 w-1/4" />
          </div>
        ))}
      </div>
    )
  }

  return <Skeleton className={className} {...props} />
}

export { SkeletonLoader, Skeleton }
