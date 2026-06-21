"""ALLOCENSUS — Frontend Pages: Landing, Auth, Dashboard"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

# ── Landing page ────────────────────────────────────────────────────────────
write("frontend/src/app/page.tsx", '''\
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Shield, Zap, BarChart3, Globe, CheckCircle, ChevronDown } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">

      {/* ── NAV ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-border">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Zap className="w-4 h-4 text-emerald-400" />
            </div>
            <span className="text-sm font-bold tracking-tight">ALLOCENSUS</span>
            <span className="hidden sm:block px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs border border-emerald-500/20 font-mono">StudioNet</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
            <Link href="#features" className="hover:text-foreground transition-colors">Features</Link>
            <Link href="#how-it-works" className="hover:text-foreground transition-colors">How it works</Link>
            <Link href="#contract" className="hover:text-foreground transition-colors">The Contract</Link>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-4 py-2">Sign in</Link>
            <Link href="/register" className="inline-flex items-center gap-2 text-sm font-medium bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-xl transition-colors shadow-lg shadow-emerald-900/30">
              Get started <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="relative pt-32 pb-24 px-6">
        {/* Background grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:72px_72px] pointer-events-none" />

        {/* Glow orbs */}
        <div className="absolute top-1/3 left-1/4 w-[600px] h-[600px] rounded-full bg-emerald-500/5 blur-[120px] pointer-events-none" />
        <div className="absolute top-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-indigo-500/5 blur-[100px] pointer-events-none" />

        <div className="relative max-w-6xl mx-auto text-center">
          {/* Tag */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass border border-border mb-8 text-sm text-muted-foreground">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Powered by Genlayer Intelligent Contracts
          </div>

          {/* Headline */}
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
            Portfolio decisions<br />
            <span className="text-gradient-green">validated by AI,</span><br />
            <span className="text-gradient-indigo">sealed on-chain.</span>
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
            Allocensus evaluates every rebalancing decision through Genlayer validator consensus — producing transparent, auditable rationale that withstands institutional scrutiny.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
            <Link href="/register" className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-base transition-all shadow-2xl shadow-emerald-900/40 glow-green">
              Start evaluating <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="#how-it-works" className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl glass border border-border text-foreground font-medium text-base hover:border-emerald-500/30 transition-all">
              See how it works <ChevronDown className="w-4 h-4" />
            </Link>
          </div>

          {/* Hero image — institutional dashboard mockup */}
          <div className="relative mx-auto max-w-5xl">
            <div className="absolute -inset-4 bg-gradient-to-b from-transparent via-emerald-500/5 to-background pointer-events-none z-10" />
            <div className="glass rounded-3xl border border-border overflow-hidden shadow-2xl">
              <Image
                src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1400&q=80&auto=format&fit=crop"
                alt="Allocensus portfolio dashboard"
                width={1400}
                height={780}
                className="w-full opacity-60"
                priority
              />
              {/* Overlay stat cards */}
              <div className="absolute top-6 left-6 glass rounded-2xl p-4 border border-emerald-500/20 text-left">
                <p className="text-xs text-muted-foreground mb-1">Portfolio Value</p>
                <p className="text-2xl font-bold text-foreground">$24.8M</p>
                <p className="text-xs text-emerald-400 mt-0.5">+4.2% this month</p>
              </div>
              <div className="absolute top-6 right-6 glass rounded-2xl p-4 border border-indigo-500/20 text-left">
                <p className="text-xs text-muted-foreground mb-1">AI Consensus</p>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <p className="text-sm font-semibold text-emerald-400">APPROVED</p>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">5/5 validators</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── LOGOS / AUDIENCE ── */}
      <section className="py-12 px-6 border-y border-border">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-widest mb-8">Built for institutional investment teams</p>
          <div className="flex flex-wrap items-center justify-center gap-8 text-sm text-muted-foreground/60 font-medium">
            {["Wealth Managers", "Family Offices", "DAOs", "Asset Managers", "Treasury Teams", "Institutional Investors"].map(a => (
              <span key={a} className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-emerald-500" />{a}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Everything institutional rebalancing requires</h2>
            <p className="text-muted-foreground text-lg">Not a black box. Not a heuristic. A full AI reasoning chain, auditable forever.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: Shield,
                title: "Constraint enforcement",
                desc: "8 hard portfolio rules enforced before any proposal reaches the AI — concentration limits, liquidity floors, leverage bans.",
                color: "emerald",
              },
              {
                icon: Zap,
                title: "Genlayer validator consensus",
                desc: "Multiple independent AI validators evaluate each proposal. Semantic consensus — not a single oracle — determines approval.",
                color: "indigo",
              },
              {
                icon: BarChart3,
                title: "6-dimension rationale",
                desc: "Constraint compliance · Risk alignment · Diversification quality · Liquidity · Objective alignment · Market context.",
                color: "emerald",
              },
              {
                icon: Globe,
                title: "Live market context",
                desc: "Validators fetch real-time market data during evaluation. Rationale reflects actual market conditions, not stale assumptions.",
                color: "indigo",
              },
              {
                icon: CheckCircle,
                title: "On-chain audit trail",
                desc: "Every evaluation is immutably recorded on StudioNet. Provide auditors a transaction hash — the rationale lives forever.",
                color: "emerald",
              },
              {
                icon: ArrowRight,
                title: "Full asset class coverage",
                desc: "Crypto · Tokenised RWA · DeFi Protocols · Equities · Fixed Income · Commodities. One platform for the modern portfolio.",
                color: "indigo",
              },
            ].map(({ icon: Icon, title, desc, color }) => (
              <div key={title} className={`glass rounded-2xl p-6 border border-border hover:border-${color}-500/30 transition-all group`}>
                <div className={`w-10 h-10 rounded-xl bg-${color}-500/10 border border-${color}-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon className={`w-5 h-5 text-${color}-400`} />
                </div>
                <h3 className="text-base font-semibold mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how-it-works" className="py-24 px-6 border-t border-border">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">How Allocensus works</h2>
            <p className="text-muted-foreground">From portfolio input to on-chain rationale in four steps.</p>
          </div>
          <div className="space-y-6">
            {[
              { n: "01", title: "Define your portfolio", desc: "Input current holdings across any asset class. Set target weights. Link your investor profile with risk tolerance, horizon, and objectives.", img: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&q=80" },
              { n: "02", title: "Propose a rebalance", desc: "Adjust target allocations in the rebalancing workspace. The constraint engine validates your proposal against 8 hard rules before submission.", img: "https://images.unsplash.com/photo-1642790106117-e829e14a795f?w=600&q=80" },
              { n: "03", title: "Genlayer evaluates", desc: "Your proposal is submitted to the Intelligent Contract on StudioNet. Validators independently run LLM-powered analysis and reach consensus.", img: "https://images.unsplash.com/photo-1639762681057-408e52192e55?w=600&q=80" },
              { n: "04", title: "Receive your rationale", desc: "A structured, on-chain rationale arrives — approved or rejected — with risk analysis, constraint review, and actionable recommendation.", img: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&q=80" },
            ].map(({ n, title, desc, img }, i) => (
              <div key={n} className={`flex gap-8 items-center glass rounded-3xl p-8 border border-border ${i % 2 === 1 ? "flex-row-reverse" : ""}`}>
                <div className="flex-1">
                  <div className="text-5xl font-black text-gradient-green mb-4 font-mono">{n}</div>
                  <h3 className="text-xl font-bold mb-3">{title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{desc}</p>
                </div>
                <div className="flex-1 rounded-2xl overflow-hidden">
                  <Image src={img} alt={title} width={600} height={360} className="w-full object-cover opacity-70 rounded-2xl" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CONTRACT CALLOUT ── */}
      <section id="contract" className="py-24 px-6 border-t border-border">
        <div className="max-w-4xl mx-auto text-center">
          <div className="glass rounded-3xl p-12 border border-emerald-500/20 glow-green">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs mb-6 font-mono">
              Portfolio Rebalancing Rationale Contract
            </div>
            <h2 className="text-4xl font-bold mb-4">The Intelligent Contract</h2>
            <p className="text-muted-foreground text-lg mb-8 max-w-2xl mx-auto">
              A single, production-ready Genlayer contract deployed on StudioNet. Each evaluation call triggers independent LLM reasoning across multiple validators — semantically compared, consensus-confirmed, permanently recorded.
            </p>
            <div className="grid grid-cols-3 gap-6 mb-8">
              {[["GEN", "Fee token", "emerald"], ["5+", "Validators", "indigo"], ["∞", "On-chain lifetime", "emerald"]].map(([val, label, c]) => (
                <div key={label} className="glass rounded-2xl p-4 border border-border">
                  <div className={`text-3xl font-bold text-${c}-400 mb-1`}>{val}</div>
                  <div className="text-sm text-muted-foreground">{label}</div>
                </div>
              ))}
            </div>
            <Link href="/register" className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold transition-all glow-green">
              Start your first evaluation <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-border py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <span className="text-sm font-bold">ALLOCENSUS</span>
          </div>
          <p className="text-xs text-muted-foreground">AI-Validated Portfolio Rebalancing Intelligence · Powered by Genlayer StudioNet</p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <Link href="/login" className="hover:text-foreground transition-colors">Sign in</Link>
            <Link href="/register" className="hover:text-foreground transition-colors">Get started</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
''')

# ── Auth pages ──────────────────────────────────────────────────────────────
write("frontend/src/app/(auth)/login/page.tsx", '''\
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
''')

write("frontend/src/app/(auth)/register/page.tsx", '''\
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
''')

print("✅ Landing + auth pages complete.")
