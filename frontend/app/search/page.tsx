"use client";
import { useState, useEffect, useCallback } from "react";
import { Search, ArrowLeft, ExternalLink } from "lucide-react";
import Link from "next/link";
import { search } from "@/lib/api";
import { SearchResult } from "@/types";
import ThemeToggle from "@/components/ThemeToggle";
import { formatTimestamp } from "@/lib/utils";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); setSearched(false); return; }
    setLoading(true);
    setSearched(true);
    try {
      const data = await search(q);
      setResults(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => doSearch(query), 400);
    return () => clearTimeout(timer);
  }, [query, doSearch]);

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b px-4 py-2 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-1 text-sm hover:text-primary">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <ThemeToggle />
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <div className="space-y-2">
          <h1 className="font-bold text-2xl">Search</h1>
          <p className="text-muted-foreground text-sm">Search across all screen recordings by content</p>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across everything you've recorded…"
            autoFocus
            className="w-full border rounded-lg pl-9 pr-4 py-3 bg-background text-sm"
          />
        </div>

        {loading && (
          <div className="text-center text-muted-foreground text-sm animate-pulse">Searching…</div>
        )}

        {!loading && searched && results.length === 0 && (
          <div className="text-center text-muted-foreground py-12">
            <p>No results found for &ldquo;{query}&rdquo;</p>
            <p className="text-xs mt-1">Make sure Ollama is running and sessions have been indexed.</p>
          </div>
        )}

        {!loading && !searched && (
          <div className="text-center text-muted-foreground py-12">
            <Search className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p>Search across everything you&apos;ve recorded</p>
          </div>
        )}

        <div className="space-y-3">
          {results.map((r) => (
            <div key={r.step_id} className="border rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">{r.session_name}</span>
                  {r.page_title && <> → {r.page_title}</>}
                  {r.timestamp !== undefined && <> · {formatTimestamp(r.timestamp)}</>}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">{Math.round((r.score || 0) * 100)}% match</span>
                  <Link href={`/step/${r.step_id}`} className="text-xs text-primary hover:underline flex items-center gap-0.5">
                    View <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              </div>
              <p className="text-sm font-mono bg-muted rounded px-2 py-1 text-muted-foreground leading-relaxed">
                {r.excerpt}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
