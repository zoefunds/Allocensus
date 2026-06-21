"use client";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Zap, ArrowRight, Wallet, Shield } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { authAPI } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

const schema = z.object({
  full_name: z.string().min(2, "Name too short"),
  email: z.string().email("Invalid email"),
  password: z.string().min(8).regex(/[A-Z]/, "Uppercase required").regex(/[0-9]/, "Number required"),
  confirm: z.string(),
}).refine(d => d.password === d.confirm, { message: "Passwords don't match", path: ["confirm"] });

type Form = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({ resolver: zodResolver(schema) });

  const onSubmit = async ({ full_name, email, password }: Form) => {
    try {
      const res = await authAPI.register({ full_name, email, password });
      const d = res.data;
      setAuth({ id: d.user_id, email, full_name, role: d.role, is_active: true, is_email_verified: false, wallet_address: d.wallet_address, created_at: "" }, d.access_token, d.refresh_token, d.wallet_address);
      toast.success("Account created! A blockchain wallet has been provisioned for you.");
      router.push("/dashboard");
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Registration failed";
      toast.error(msg);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-2.5 mb-10">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Zap className="w-4 h-4 text-emerald-400" />
            </div>
            <span className="text-sm font-bold tracking-tight">ALLOCENSUS</span>
          </div>
          <h1 className="text-2xl font-bold mb-2">Create your account</h1>
          <p className="text-muted-foreground text-sm mb-2">Institutional access to AI-validated rebalancing</p>

          <div className="flex items-start gap-2 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10 mb-6">
            <Wallet className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-muted-foreground">A StudioNet blockchain wallet is automatically created and linked to your account on registration.</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input label="Full name" placeholder="Alex Johnson" error={errors.full_name?.message} {...register("full_name")} />
            <Input label="Work email" type="email" placeholder="you@firm.com" error={errors.email?.message} {...register("email")} />
            <Input label="Password" type="password" placeholder="Min. 8 chars, 1 uppercase, 1 number" error={errors.password?.message} {...register("password")} />
            <Input label="Confirm password" type="password" placeholder="••••••••" error={errors.confirm?.message} {...register("confirm")} />
            <Button type="submit" size="lg" loading={isSubmitting} className="w-full">
              Create account <ArrowRight className="w-4 h-4" />
            </Button>
          </form>

          <div className="flex items-center gap-2 mt-4 text-xs text-muted-foreground">
            <Shield className="w-3 h-3" />
            <span>Private key encrypted with AES-256-GCM. Only you can export it.</span>
          </div>

          <p className="text-center text-sm text-muted-foreground mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-emerald-400 hover:text-emerald-300 font-medium">Sign in</Link>
          </p>
        </div>
      </div>

      <div className="hidden lg:flex flex-1 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-indigo-950/20" />
        <div className="absolute top-1/4 right-1/3 w-72 h-72 rounded-full bg-indigo-500/8 blur-[80px]" />
        <div className="relative z-10 flex flex-col justify-center p-16">
          <h2 className="text-3xl font-bold mb-6 leading-tight">Every rebalancing decision, <span className="text-gradient-indigo">accountable forever.</span></h2>
          <div className="space-y-4">
            {[
              { icon: Shield, text: "8 constraint rules enforced before AI evaluation" },
              { icon: Zap, text: "Genlayer validator consensus — not a single AI" },
              { icon: Wallet, text: "On-chain audit trail linked to your wallet" },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3 text-sm text-muted-foreground">
                <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
                  <Icon className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                {text}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
