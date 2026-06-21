import { cn } from "@/lib/utils";
import { type InputHTMLAttributes, forwardRef } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, Props>(
  ({ className, label, error, hint, ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-sm font-medium text-muted-foreground">{label}</label>}
      <input
        ref={ref}
        className={cn(
          "w-full bg-secondary border border-border rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/50 outline-none transition-all",
          "focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30",
          error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
      {hint && !error && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
);
Input.displayName = "Input";
