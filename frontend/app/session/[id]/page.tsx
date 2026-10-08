"use client";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Film } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getSession, getSteps } from "@/lib/api";
import { Step } from "@/types";
import { formatTimestamp, statusBadgeClass, truncate } from "@/lib/utils";
import ThemeToggle from "@/components/ThemeToggle";

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const { data: session } = useQuery({ queryKey: ["session", id], queryFn: () => getSession(id) });
  const { data: steps = [] } = useQuery({ queryKey: ["steps", id], queryFn: () => getSteps(id) });

  const [filterType, setFilterType] = useState("all");

  const filtered = (steps as Step[]).filter((s) => filterType === "all" || s.step_type === filterType);
  const stepTypes = Array.from(new Set((steps as Step[]).map((s) => s.step_type).filter(Boolean)));

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link href={`/dashboard?session=${id}`} className="flex items-center gap-1 text-sm hover:text-primary">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <Link href={`/export/${id}`} className="text-xs px-3 py-1.5 border rounded hover:bg-accent">Export</Link>
          <ThemeToggle />
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        <div>
          <h1 className="font-bold text-xl">{session?.name}</h1>
          {session?.session_summary && <p className="text-muted-foreground text-sm mt-1">{session.session_summary}</p>}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-sm border rounded px-2 py-1 bg-background"
          >
            <option value="all">All Steps ({steps.length})</option>
            {stepTypes.map((t) => <option key={t} value={t!}>{t}</option>)}
          </select>
        </div>

        <div className="grid gap-3">
          {filtered.map((step: Step) => (
            <Link key={step.id} href={`/step/${step.id}`}>
              <div className="border rounded-lg p-4 hover:bg-accent/50 transition-colors flex gap-4">
                {step.screenshot_url && (
                  <img
                    src={step.screenshot_url}
                    alt="Screenshot"
                    className="w-24 h-16 object-cover rounded border flex-shrink-0"
                  />
                )}
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="px-1.5 py-0.5 bg-muted rounded">{step.step_type || "action"}</span>
                    <span>@ {formatTimestamp(step.timestamp_start)}</span>
                    {step.is_backtrack && <span className="text-yellow-500 font-medium">↩ backtrack</span>}
                  </div>
                  <p className="text-sm font-medium">{step.text_summary || "No summary"}</p>
                  {step.extracted_text && (
                    <p className="text-xs text-muted-foreground font-mono">{truncate(step.extracted_text, 120)}</p>
                  )}
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground self-center flex-shrink-0" />
              </div>
            </Link>
          ))}
          {filtered.length === 0 && (
            <div className="text-center text-muted-foreground py-12">
              {session?.status !== "done" ? `Processing: ${session?.status}` : "No steps found"}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
