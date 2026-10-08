"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSessions, compareSessions } from "@/lib/api";
import { CompareResult, SessionListItem } from "@/types";
import { ArrowLeft, GitCompare, CheckCircle, XCircle } from "lucide-react";
import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";
import { formatDuration } from "@/lib/utils";

export default function ComparePage() {
  const [sessionA, setSessionA] = useState("");
  const [sessionB, setSessionB] = useState("");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { data: sessions = [] } = useQuery({ queryKey: ["sessions"], queryFn: getSessions });
  const doneSessions = (sessions as SessionListItem[]).filter((s) => s.status === "done");

  const handleCompare = async () => {
    if (!sessionA || !sessionB) { setError("Select two sessions"); return; }
    if (sessionA === sessionB) { setError("Select different sessions"); return; }
    setLoading(true);
    setError("");
    try {
      const data = await compareSessions(sessionA, sessionB);
      setResult(data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b px-4 py-2 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-1 text-sm hover:text-primary">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <ThemeToggle />
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <div>
          <h1 className="font-bold text-2xl">Compare Sessions</h1>
          <p className="text-muted-foreground text-sm mt-1">Compare navigation paths and content between two recordings</p>
        </div>

        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="text-sm font-medium">Session A</label>
            <select value={sessionA} onChange={(e) => setSessionA(e.target.value)} className="mt-1 w-full border rounded-md px-3 py-2 bg-background text-sm">
              <option value="">Select session…</option>
              {doneSessions.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div className="flex-1">
            <label className="text-sm font-medium">Session B</label>
            <select value={sessionB} onChange={(e) => setSessionB(e.target.value)} className="mt-1 w-full border rounded-md px-3 py-2 bg-background text-sm">
              <option value="">Select session…</option>
              {doneSessions.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <button
            onClick={handleCompare}
            disabled={loading}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium disabled:opacity-50 flex items-center gap-2"
          >
            <GitCompare className="w-4 h-4" />
            {loading ? "Comparing…" : "Compare"}
          </button>
        </div>

        {error && <p className="text-destructive text-sm">{error}</p>}

        {result && (
          <div className="space-y-6">
            {/* Stats comparison */}
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-1" />
              <div className="text-center font-medium text-sm border rounded-t p-2 bg-blue-50 dark:bg-blue-950">{result.session_a.name}</div>
              <div className="text-center font-medium text-sm border rounded-t p-2 bg-purple-50 dark:bg-purple-950">{result.session_b.name}</div>
              {[
                ["Pages", result.session_a.total_pages, result.session_b.total_pages],
                ["Steps", result.session_a.total_steps, result.session_b.total_steps],
                ["Duration", formatDuration(result.session_a.total_duration_seconds), formatDuration(result.session_b.total_duration_seconds)],
                ["Backtracks", result.session_a.total_backtracks, result.session_b.total_backtracks],
              ].map(([label, a, b]) => (
                <>
                  <div key={`label-${label}`} className="text-sm text-muted-foreground border-b px-2 py-2 flex items-center">{label}</div>
                  <div key={`a-${label}`} className="text-sm text-center border-b px-2 py-2 bg-blue-50/50 dark:bg-blue-950/50 font-medium">{a}</div>
                  <div key={`b-${label}`} className="text-sm text-center border-b px-2 py-2 bg-purple-50/50 dark:bg-purple-950/50 font-medium">{b}</div>
                </>
              ))}
            </div>

            {/* Diff analysis */}
            <div className="grid grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <h3 className="font-medium text-sm flex items-center gap-1.5 text-green-600 mb-3">
                  <CheckCircle className="w-4 h-4" /> Common Pages ({result.diff.common_pages.length})
                </h3>
                <ul className="space-y-1">
                  {result.diff.common_pages.map((p) => <li key={p} className="text-xs text-muted-foreground bg-green-50 dark:bg-green-950/40 rounded px-2 py-1">{p}</li>)}
                  {result.diff.common_pages.length === 0 && <li className="text-xs text-muted-foreground">None</li>}
                </ul>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-medium text-sm flex items-center gap-1.5 text-blue-600 mb-3">
                  Only in A ({result.diff.unique_to_a.length})
                </h3>
                <ul className="space-y-1">
                  {result.diff.unique_to_a.map((p) => <li key={p} className="text-xs text-muted-foreground bg-blue-50 dark:bg-blue-950/40 rounded px-2 py-1">{p}</li>)}
                  {result.diff.unique_to_a.length === 0 && <li className="text-xs text-muted-foreground">None</li>}
                </ul>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-medium text-sm flex items-center gap-1.5 text-purple-600 mb-3">
                  Only in B ({result.diff.unique_to_b.length})
                </h3>
                <ul className="space-y-1">
                  {result.diff.unique_to_b.map((p) => <li key={p} className="text-xs text-muted-foreground bg-purple-50 dark:bg-purple-950/40 rounded px-2 py-1">{p}</li>)}
                  {result.diff.unique_to_b.length === 0 && <li className="text-xs text-muted-foreground">None</li>}
                </ul>
              </div>
            </div>

            {result.diff.path_divergence_point && (
              <div className="border rounded-lg p-4 bg-yellow-50 dark:bg-yellow-950/40">
                <p className="text-sm font-medium">Path divergence point: <span className="font-normal">{result.diff.path_divergence_point}</span></p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
