"use client";
import { useState } from "react";
import { Clock, Plus, FolderOpen, Tag, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { SessionListItem, Folder } from "@/types";
import { statusBadgeClass, truncate } from "@/lib/utils";
import { format } from "date-fns";
import Link from "next/link";

interface Props {
  sessions: SessionListItem[];
  folders: Folder[];
  activeSessionId?: string;
  onSelect: (id: string) => void;
}

export default function SessionList({ sessions, folders, activeSessionId, onSelect }: Props) {
  const [search, setSearch] = useState("");
  const [filterTag, setFilterTag] = useState("");
  const [filterFolder, setFilterFolder] = useState("");

  const filtered = sessions.filter((s) => {
    if (search && !s.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterFolder && s.folder?.id !== filterFolder) return false;
    if (filterTag && !s.tags.some((t) => t.id === filterTag)) return false;
    return true;
  });

  // Group by folder
  const folderMap: Record<string, SessionListItem[]> = { "": [] };
  folders.forEach((f) => { folderMap[f.id] = []; });
  filtered.forEach((s) => {
    const fid = s.folder?.id || "";
    folderMap[fid] = [...(folderMap[fid] || []), s];
  });

  const allTags = Array.from(new Map(sessions.flatMap((s) => s.tags).map((t) => [t.id, t])).values());

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-sm">Sessions</h2>
          <Link href="/" className="text-xs text-primary hover:underline flex items-center gap-0.5">
            <Plus className="w-3 h-3" /> New
          </Link>
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search sessions…"
          className="w-full text-xs border rounded px-2 py-1 bg-background"
        />
        <div className="flex gap-1">
          <select
            value={filterFolder}
            onChange={(e) => setFilterFolder(e.target.value)}
            className="text-xs border rounded px-1 py-0.5 bg-background flex-1"
          >
            <option value="">All Folders</option>
            {folders.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
          {allTags.length > 0 && (
            <select
              value={filterTag}
              onChange={(e) => setFilterTag(e.target.value)}
              className="text-xs border rounded px-1 py-0.5 bg-background flex-1"
            >
              <option value="">All Tags</option>
              {allTags.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {folders.map((folder) => {
          const fSessions = folderMap[folder.id] || [];
          if (fSessions.length === 0) return null;
          return (
            <div key={folder.id}>
              <div className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground sticky top-0 bg-background border-b">
                <FolderOpen className="w-3 h-3" style={{ color: folder.color }} />
                {folder.name}
              </div>
              {fSessions.map((s) => <SessionItem key={s.id} session={s} active={s.id === activeSessionId} onSelect={onSelect} />)}
            </div>
          );
        })}

        {(folderMap[""] || []).length > 0 && (
          <div>
            {folders.length > 0 && (
              <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground sticky top-0 bg-background border-b">
                No Folder
              </div>
            )}
            {(folderMap[""] || []).map((s) => <SessionItem key={s.id} session={s} active={s.id === activeSessionId} onSelect={onSelect} />)}
          </div>
        )}

        {filtered.length === 0 && (
          <div className="p-4 text-center text-muted-foreground text-sm">No sessions found</div>
        )}
      </div>
    </div>
  );
}

function SessionItem({ session, active, onSelect }: { session: SessionListItem; active: boolean; onSelect: (id: string) => void }) {
  const StatusIcon = session.status === "done" ? CheckCircle : session.status === "failed" ? XCircle : Loader2;
  const iconClass = session.status === "done" ? "text-green-500" : session.status === "failed" ? "text-red-500" : "text-yellow-500 animate-spin";

  return (
    <button
      onClick={() => onSelect(session.id)}
      className={`w-full text-left px-3 py-2.5 border-b hover:bg-accent/50 transition-colors ${active ? "bg-accent" : ""}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <StatusIcon className={`w-3 h-3 flex-shrink-0 ${iconClass}`} />
            <span className="text-sm font-medium truncate">{session.name}</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
            <Clock className="w-3 h-3" />
            {format(new Date(session.created_at), "MMM d, yyyy")}
          </div>
          {session.tags.length > 0 && (
            <div className="flex gap-1 mt-1 flex-wrap">
              {session.tags.slice(0, 3).map((t) => (
                <span key={t.id} className="px-1.5 py-0 rounded-full text-xs text-white" style={{ backgroundColor: t.color }}>
                  {t.name}
                </span>
              ))}
            </div>
          )}
        </div>
        <span className={`text-xs px-1.5 py-0.5 rounded-full flex-shrink-0 ${statusBadgeClass(session.status)}`}>
          {session.status === "done" ? `${session.total_pages}p` : session.status}
        </span>
      </div>
    </button>
  );
}
