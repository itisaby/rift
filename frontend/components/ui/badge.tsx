import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
        variants: {
            variant: {
                default:
                    "border-transparent bg-cyan-500 text-black shadow-lg shadow-cyan-500/50",
                secondary:
                    "border-transparent bg-purple-500 text-white shadow-lg shadow-purple-500/50",
                destructive:
                    "border-transparent bg-red-500 text-white shadow-lg shadow-red-500/50",
                outline: "border-cyan-500 text-cyan-400",
                success:
                    "border-transparent bg-green-500 text-white shadow-lg shadow-green-500/50",
                warning:
                    "border-transparent bg-yellow-500 text-black shadow-lg shadow-yellow-500/50",
            },
        },
        defaultVariants: {
            variant: "default",
        },
    }
)

export interface BadgeProps
    extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> { }

function Badge({ className, variant, ...props }: BadgeProps) {
    return (
        <div className={cn(badgeVariants({ variant }), className)} {...props} />
    )
}

export { Badge, badgeVariants }
