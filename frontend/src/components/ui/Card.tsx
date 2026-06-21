import { cn } from "@/lib/utils";

interface CardProps { className?: string; children: React.ReactNode; glow?: "green" | "indigo" }

export function Card({ className, children, glow }: CardProps) {
  return (
    <div className={cn(
      "glass rounded-2xl p-6 transition-all duration-300",
      glow === "green" && "glow-green hover:border-emerald-500/30",
      glow === "indigo" && "glow-indigo hover:border-indigo-500/30",
      className
    )}>
      {children}
    </div>
  );
}

export function CardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("mb-4", className)}>{children}</div>;
}

export function CardTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return <h3 className={cn("text-lg font-semibold text-foreground", className)}>{children}</h3>;
}
