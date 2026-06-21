"use client";
import { useAuthStore } from "@/stores/auth";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useState } from "react";
import { userAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Input } from "@/components/ui/Input";
import { Eye, EyeOff, Copy } from "lucide-react";

export default function SettingsPage() {
  const { user, walletAddress } = useAuthStore();
  const [exportPassword, setExportPassword] = useState("");
  const [exportedKey, setExportedKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    try {
      setExporting(true);
      const res = await userAPI.exportKey(exportPassword);
      setExportedKey(res.data.private_key);
      toast.success("Private key exported. Store it securely.");
    } catch {
      toast.error("Incorrect password");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <CardTitle className="mb-4">Account</CardTitle>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-muted-foreground">Name</span>
            <span>{user?.full_name}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-muted-foreground">Email</span>
            <span>{user?.email}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-muted-foreground">Role</span>
            <span className="capitalize">{user?.role?.replace("_", " ")}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-muted-foreground">Email verified</span>
            <span className={user?.is_email_verified ? "text-emerald-400" : "text-amber-400"}>
              {user?.is_email_verified ? "Verified" : "Pending"}
            </span>
          </div>
        </div>
      </Card>

      <Card>
        <CardTitle className="mb-4">Blockchain Wallet</CardTitle>
        <div className="space-y-4">
          <div className="p-4 bg-secondary/50 rounded-xl">
            <p className="text-xs text-muted-foreground mb-1">Wallet address (StudioNet)</p>
            <div className="flex items-center gap-2">
              <p className="font-mono text-sm text-emerald-400">{walletAddress ?? "Not found"}</p>
              {walletAddress && (
                <button onClick={() => { navigator.clipboard.writeText(walletAddress); toast.success("Copied!"); }}>
                  <Copy className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                </button>
              )}
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium">Export private key</p>
            <p className="text-xs text-muted-foreground">Enter your account password to decrypt and export your private key. Store it in a hardware wallet or cold storage immediately.</p>
            <Input
              type="password"
              placeholder="Your account password"
              value={exportPassword}
              onChange={e => setExportPassword(e.target.value)}
            />
            <Button variant="outline" onClick={handleExport} loading={exporting} disabled={!exportPassword}>
              Export private key
            </Button>

            {exportedKey && (
              <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-red-400 font-medium">PRIVATE KEY — Store securely and never share</p>
                  <button onClick={() => setShowKey(!showKey)}>
                    {showKey ? <EyeOff className="w-4 h-4 text-muted-foreground" /> : <Eye className="w-4 h-4 text-muted-foreground" />}
                  </button>
                </div>
                {showKey ? (
                  <p className="font-mono text-xs break-all text-red-300">{exportedKey}</p>
                ) : (
                  <p className="font-mono text-xs text-muted-foreground">••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••</p>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
