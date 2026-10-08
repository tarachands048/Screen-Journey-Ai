"use client";
import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Film } from "lucide-react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getSessions, getSession, getFolders } from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";
import SessionList from "@/components/SessionList";
import NavigationTree from "@/components/NavigationTree";
import HeatmapTimeline from "@/components/HeatmapTimeline";
import ChatPanel from "@/components/ChatPanel";
import StatsBar from "@/components/StatsBar";
import { SessionDetail, TreeNode } from "@/types";
import { useRouter as useNavRouter } from "next/navigation";

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(searchParams.get("session"));
  const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);

  const { data: sessions = [], refetch: refetchSessions } = useQuery({ queryKey: ["sessions"], queryFn: getSessions, refetchInterval: 5000 });
  const { data: folders = [] } = useQuery({ queryKey: ["folders"], queryFn: getFolders });

  useEffect(() => {
    if (!activeSessionId) return;
    getSession(activeSessionId).then(setActiveSession).catch(() => {});
  }, [activeSessionId]);

  const handleSelect = (id: string) => {
    setActiveSessionId(id);
    router.push(`/dashboard?session=${id}`, { scroll: false });
    getSession(id).then(setActiveSession);
  };

  const treeData = activeSession?.tree;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Nav */}
      <nav className="border-b px-4 py-2 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2 font-semibold text-sm">
          <Film className="w-4 h-4 text-primary" />
          Screen Journey
        </div>
        <div className="flex items-center gap-3">
          <Link href="/" className="text-xs hover:text-primary">Upload</Link>
          <Link href="/search" className="text-xs hover:text-primary">Search</Link>
          <Link href="/compare" className="text-xs hover:text-primary">Compare</Link>
          <ThemeToggle />
        </div>
      </nav>

      {/* Three-panel layout */}
      <div className="flex-1 flex overflow-hidden" style={{ height: "calc(100vh - 48px)" }}>
        {/* LEFT: Session list */}
        <div className="w-64 border-r flex-shrink-0 overflow-hidden">
          <SessionList
            sessions={sessions}
            folders={folders}
            activeSessionId={activeSessionId || undefined}
            onSelect={handleSelect}
          />
        </div>

        {/* CENTER: Tree + Timeline */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 min-w-0">
          {activeSession ? (
            <>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h1 className="font-bold text-lg">{activeSession.name}</h1>
                  {activeSession.description && (
                    <p className="text-muted-foreground text-sm">{activeSession.description}</p>
                  )}
                  {activeSession.session_summary && (
                    <p className="text-sm mt-1 text-muted-foreground line-clamp-2">{activeSession.session_summary}</p>
                  )}
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <Link href={`/session/${activeSession.id}`} className="text-xs px-3 py-1.5 border rounded hover:bg-accent">
                    View Steps
                  </Link>
                  <Link href={`/export/${activeSession.id}`} className="text-xs px-3 py-1.5 border rounded hover:bg-accent">
                    Export
                  </Link>
                </div>
              </div>

              <StatsBar
                totalPages={activeSession.total_pages}
                totalSteps={activeSession.total_steps}
                totalDuration={activeSession.total_duration_seconds}
                totalBacktracks={activeSession.total_backtracks}
              />

              {treeData?.tree && (
                <div className="border rounded-lg p-4">
                  <h2 className="font-semibold text-sm mb-3">Navigation Tree</h2>
                  <NavigationTree
                    tree={treeData.tree}
                    onNodeClick={(node) => {
                      // Find a step for this page and navigate to it
                    }}
                  />
                </div>
              )}

              {treeData?.timeline && (
                <div className="border rounded-lg p-4">
                  <h2 className="font-semibold text-sm mb-3">Timeline</h2>
                  <HeatmapTimeline
                    timeline={treeData.timeline}
                    totalDuration={activeSession.total_duration_seconds}
                    onStepClick={(stepId) => router.push(`/step/${stepId}`)}
                  />
                </div>
              )}

              {activeSession.status !== "done" && (
                <div className="border rounded-lg p-6 text-center text-muted-foreground">
                  <p className="font-medium">Processing in progress…</p>
                  <p className="text-sm">Status: {activeSession.status}</p>
                  <Link href={`/processing/${activeSession.id}`} className="text-primary text-sm hover:underline mt-1 inline-block">
                    View progress →
                  </Link>
                </div>
              )}
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              <div className="text-center space-y-2">
                <Film className="w-12 h-12 mx-auto opacity-30" />
                <p>Select a session from the left panel</p>
                <Link href="/" className="text-primary text-sm hover:underline">
                  Upload a new recording →
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Chat */}
        <div className="w-80 border-l flex-shrink-0 overflow-hidden">
          {activeSession?.id ? (
            <ChatPanel sessionId={activeSession.id} sessionName={activeSession.name} />
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground text-sm p-4 text-center">
              Select a session to start chatting
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense>
      <DashboardContent />
    </Suspense>
  );
}
