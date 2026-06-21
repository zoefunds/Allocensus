import { cn } from "@/lib/utils";

const variants = {
  default: "bg-secondary text-muted-foreground border-border",
  success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  danger: "bg-red-500/10 text-red-400 border-red-500/20",
  info: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  pending: "bg-blue-500/10 text-blue-400 border-blue-500/20",
};

export function Badge({ variant = "default", children, className }: {
  variant?: keyof typeof variants;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border", variants[variant], className)}>
      {children}
    </span>
  );
}
