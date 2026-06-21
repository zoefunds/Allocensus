"use client";
import { useQuery } from "@tanstack/react-query";
import { auditAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { FileText, ExternalLink } from "lucide-react";
import type { AuditEvent } from "@/types";

export default function AuditPage() {
  const { data: res } = useQuery({ queryKey: ["audit"], queryFn: () => auditAPI.events({ limit: 100 }) });
  const events: AuditEvent[] = res?.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Audit Trail</h1>
        <p className="text-muted-foreground text-sm mt-1">Immutable record of all account and portfolio actions</p>
      </div>
      <Card>
        <CardTitle className="mb-6">Event log ({events.length})</CardTitle>
        {events.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <FileText className="w-10 h-10 mx-auto mb-3 opacity-30" />
            No events yet.
          </div>
        ) : (
          <div className="space-y-2">
            {events.map((e) => (
              <div key={e.id} className="flex items-start gap-4 p-3 rounded-xl hover:bg-secondary/30 transition-colors">
                <div className="w-2 h-2 rounded-full bg-emerald-500 mt-2 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-medium text-foreground">{e.event_type}</span>
                    {e.resource_id && <span className="text-xs text-muted-foreground font-mono">{e.resource_id.slice(0, 16)}...</span>}
                  </div>
                  {e.on_chain_ref && (
                    <div className="flex items-center gap-1 mt-0.5">
                      <ExternalLink className="w-3 h-3 text-emerald-400" />
                      <span className="text-xs font-mono text-emerald-400">{e.on_chain_ref}</span>
                    </div>
                  )}
                </div>
                <span className="text-xs text-muted-foreground flex-shrink-0">{new Date(e.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
