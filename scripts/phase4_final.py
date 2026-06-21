"""ALLOCENSUS — Phase 4: Admin page + startup scripts"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("frontend/src/app/admin/page.tsx", '''\
"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import toast from "react-hot-toast";
import { DashboardNav } from "@/components/layout/DashboardNav";
import { Shield, Users, Briefcase, RefreshCw } from "lucide-react";

export default function AdminPage() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const qc = useQueryClient();

  useEffect(() => {
    if (!isAuthenticated || user?.role !== "admin") router.push("/dashboard");
  }, [isAuthenticated, user, router]);

  const { data: statsRes } = useQuery({ queryKey: ["admin-stats"], queryFn: () => adminAPI.stats() });
  const { data: usersRes } = useQuery({ queryKey: ["admin-users"], queryFn: () => adminAPI.users() });

  const stats = statsRes?.data;
  const users = usersRes?.data ?? [];

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => adminAPI.updateRole(userId, role),
    onSuccess: () => { toast.success("Role updated"); qc.invalidateQueries({ queryKey: ["admin-users"] }); },
  });

  return (
    <div className="min-h-screen bg-background">
      <DashboardNav />
      <main className="ml-64 p-8 space-y-6">
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-indigo-400" />
          <h1 className="text-2xl font-bold">Admin Console</h1>
        </div>

        {stats && (
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Total users", value: stats.total_users, icon: Users, color: "indigo" },
              { label: "Portfolios", value: stats.total_portfolios, icon: Briefcase, color: "emerald" },
              { label: "Evaluations", value: stats.total_proposals, icon: RefreshCw, color: "emerald" },
            ].map(({ label, value, icon: Icon, color }) => (
              <Card key={label}>
                <div className={`w-9 h-9 rounded-xl bg-${color}-500/10 border border-${color}-500/20 flex items-center justify-center mb-3`}>
                  <Icon className={`w-4 h-4 text-${color}-400`} />
                </div>
                <p className="text-2xl font-bold">{value}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </Card>
            ))}
          </div>
        )}

        <Card>
          <CardTitle className="mb-6">Users</CardTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-3 text-muted-foreground font-medium">Name</th>
                  <th className="pb-3 text-muted-foreground font-medium">Email</th>
                  <th className="pb-3 text-muted-foreground font-medium">Role</th>
                  <th className="pb-3 text-muted-foreground font-medium">Status</th>
                  <th className="pb-3 text-muted-foreground font-medium">Joined</th>
                  <th className="pb-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map((u: { id: string; full_name: string; email: string; role: string; is_active: boolean; created_at: string }) => (
                  <tr key={u.id} className="hover:bg-secondary/20">
                    <td className="py-3 font-medium">{u.full_name}</td>
                    <td className="py-3 text-muted-foreground">{u.email}</td>
                    <td className="py-3">
                      <select
                        value={u.role}
                        onChange={e => roleMutation.mutate({ userId: u.id, role: e.target.value })}
                        className="bg-secondary border border-border rounded-lg px-2 py-1 text-xs outline-none"
                      >
                        <option value="analyst">Analyst</option>
                        <option value="portfolio_manager">Portfolio Manager</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="py-3">
                      <span className={`text-xs ${u.is_active ? "text-emerald-400" : "text-red-400"}`}>
                        {u.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="py-3 text-right">
                      {u.role !== "admin" && (
                        <Button variant="ghost" size="sm" onClick={() => adminAPI.updateRole(u.id, "analyst")}>Reset</Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </main>
    </div>
  );
}
''')

# ── Startup / dev scripts ────────────────────────────────────────────────────
write("scripts/start_dev.sh", '''\
#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║           ALLOCENSUS — Dev Environment           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Start Docker Desktop first."
  exit 1
fi

# Copy .env if not present
if [ ! -f backend/.env ]; then
  echo "📋 Copying backend .env.example → .env"
  cp backend/.env.example backend/.env
  echo "⚠️  Edit backend/.env with your secrets before proceeding."
fi

if [ ! -f frontend/.env.local ]; then
  echo "📋 Copying frontend .env.example → .env.local"
  cp frontend/.env.example frontend/.env.local
fi

echo ""
echo "🐳 Starting PostgreSQL + Redis + API..."
cd backend && docker-compose up -d db redis

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 5

echo ""
echo "🗄️  Running migrations..."
docker-compose run --rm api alembic upgrade head || echo "⚠️  Migration skipped (API container may need image build first)"

echo ""
echo "🚀 Starting API server..."
docker-compose up -d api worker

echo ""
echo "📦 Installing frontend dependencies..."
cd ../frontend
if [ ! -d node_modules ]; then
  npm install
fi

echo ""
echo "✅ Backend running at http://localhost:8000"
echo "   API docs:    http://localhost:8000/api/docs"
echo ""
echo "▶  Starting frontend..."
npm run dev
''')

write("scripts/stop_dev.sh", '''\
#!/bin/bash
echo "🛑 Stopping Allocensus dev environment..."
cd backend && docker-compose down
echo "✅ Done."
''')

write("scripts/reset_db.sh", '''\
#!/bin/bash
echo "⚠️  This will destroy all data. Ctrl+C to cancel."
sleep 3
cd backend
docker-compose down -v
docker-compose up -d db redis
sleep 5
docker-compose run --rm api alembic upgrade head
echo "✅ Database reset and migrated."
''')

# Make scripts executable marker
write("scripts/setup_backend_local.sh", '''\
#!/bin/bash
# For running backend locally without Docker (e.g. for development/testing)
set -e

cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
echo "✅ Backend venv created. Edit backend/.env then run:"
echo "   source backend/.venv/bin/activate"
echo "   uvicorn app.main:app --reload"
''')

write("scripts/run_tests.sh", '''\
#!/bin/bash
set -e
cd backend
source .venv/bin/activate 2>/dev/null || true
pytest tests/ -v --cov=app --cov-report=term-missing
''')

write("scripts/deploy_contract.md", """\
# Deploying the Allocensus Intelligent Contract

## File
`contracts/portfolio_rebalancing_rationale.py`

## Steps

1. **Open Genlayer Studio**
   - Visit https://studio.genlayer.com
   - Connect your wallet (funded with GEN on StudioNet)

2. **Load the contract**
   - Click "New Contract"
   - Upload `contracts/portfolio_rebalancing_rationale.py`

3. **Deploy**
   - Click Deploy
   - Confirm GEN fee transaction
   - Wait for StudioNet confirmation
   - Copy the deployed contract address

4. **Configure backend**
   ```bash
   # backend/.env
   GENLAYER_CONTRACT_ADDRESS=0x<your_address_here>
   GENLAYER_DEPLOYER_PRIVATE_KEY=0x<your_pk>
   ```

5. **Verify deployment**
   ```bash
   cd backend
   python -c "
   from app.services.genlayer_service import genlayer_service
   import asyncio
   async def test():
       r = await genlayer_service._rpc('eth_blockNumber', [])
       print('Block:', r)
   asyncio.run(test())
   "
   ```

6. **Provide contract address**
   Once deployed, provide the contract address and it will be integrated.
""")

# ── Vercel config ────────────────────────────────────────────────────────────
write("frontend/vercel.json", '''\
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm ci",
  "env": {
    "NEXT_PUBLIC_API_URL": "@allocensus-api-url",
    "NEXT_PUBLIC_APP_NAME": "Allocensus"
  }
}
''')

print("✅ Phase 4 final files complete.")
