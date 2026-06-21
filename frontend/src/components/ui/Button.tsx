import { cn } from "@/lib/utils";
import { type ButtonHTMLAttributes, forwardRef } from "react";

const variants = {
  primary: "bg-emerald-500 hover:bg-emerald-400 text-white shadow-lg shadow-emerald-900/30",
  secondary: "bg-secondary hover:bg-secondary/80 text-foreground border border-border",
  ghost: "hover:bg-secondary/50 text-muted-foreground hover:text-foreground",
  danger: "bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20",
  outline: "border border-border hover:bg-secondary/50 text-foreground",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs rounded-lg",
  md: "px-4 py-2 text-sm rounded-xl",
  lg: "px-6 py-3 text-base rounded-xl",
  xl: "px-8 py-4 text-lg rounded-2xl",
};

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, Props>(
  ({ className, variant = "primary", size = "md", loading, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed select-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.2" />
          <path d="M22 12a10 10 0 01-10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        </svg>
      )}
      {children}
    </button>
  )
);
Button.displayName = "Button";
