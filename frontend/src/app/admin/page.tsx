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
