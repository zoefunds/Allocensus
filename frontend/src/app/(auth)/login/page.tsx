"use client";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Zap, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { authAPI } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Required"),
});
type Form = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: Form) => {
    try {
      const res = await authAPI.login(data);
      const d = res.data;
      setAuth({ id: d.user_id, email: data.email, full_name: "", role: d.role, is_active: true, is_email_verified: true, wallet_address: d.wallet_address, created_at: "" }, d.access_token, d.refresh_token, d.wallet_address);
      router.push("/dashboard");
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Login failed";
      toast.error(msg);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-2.5 mb-10">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Zap className="w-4 h-4 text-emerald-400" />
            </div>
            <span className="text-sm font-bold tracking-tight">ALLOCENSUS</span>
          </div>
          <h1 className="text-2xl font-bold mb-2">Welcome back</h1>
          <p className="text-muted-foreground text-sm mb-8">Sign in to your institutional account</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input label="Email" type="email" placeholder="you@firm.com" error={errors.email?.message} {...register("email")} />
            <Input label="Password" type="password" placeholder="••••••••" error={errors.password?.message} {...register("password")} />
            <div className="flex justify-end">
              <Link href="/forgot-password" className="text-xs text-muted-foreground hover:text-emerald-400 transition-colors">Forgot password?</Link>
            </div>
            <Button type="submit" size="lg" loading={isSubmitting} className="w-full">
              Sign in <ArrowRight className="w-4 h-4" />
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-6">
            No account?{" "}
            <Link href="/register" className="text-emerald-400 hover:text-emerald-300 font-medium">Create one</Link>
          </p>
        </div>
      </div>

      {/* Right — visual */}
      <div className="hidden lg:flex flex-1 relative overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,hsl(222_47%_7%)_0%,hsl(222_47%_3%)_100%)]" />
        <div className="absolute top-1/3 left-1/4 w-96 h-96 rounded-full bg-emerald-500/8 blur-[80px]" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 rounded-full bg-indigo-500/8 blur-[60px]" />
        <div className="relative z-10 flex flex-col justify-center p-16">
          <blockquote className="text-2xl font-light text-foreground/80 leading-relaxed mb-8">
            &ldquo;The first platform where AI investment reasoning is transparent, auditable, and on-chain.&rdquo;
          </blockquote>
          <div className="glass rounded-2xl p-6 border border-emerald-500/20 max-w-sm">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-emerald-400 font-mono">LIVE EVALUATION</span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-muted-foreground">Portfolio</span><span className="font-mono text-foreground">$24.8M AUM</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Validators</span><span className="font-mono text-foreground">5 / 5 agreed</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Outcome</span><span className="text-emerald-400 font-medium">APPROVED</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">On-chain</span><span className="font-mono text-muted-foreground text-xs">0x3f9a...d2e8</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
