"use client";
import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Upload, Film, CheckCircle } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getSessions, getFolders, uploadVideo } from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";
import { SessionListItem } from "@/types";
import { format } from "date-fns";
import { statusBadgeClass } from "@/lib/utils";

export default function HomePage() {
  const router = useRouter();
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [folderId, setFolderId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const { data: sessions = [] } = useQuery({ queryKey: ["sessions"], queryFn: getSessions });
  const { data: folders = [] } = useQuery({ queryKey: ["folders"], queryFn: getFolders });

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) { setFile(f); setName(f.name.replace(/\.[^/.]+$/, "")); }
  }, []);

  const handleSubmit = async () => {
    if (!file || !name.trim()) { setError("Please select a video and enter a name."); return; }
    setUploading(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("video", file);
      fd.append("name", name);
      fd.append("description", description);
      if (folderId) fd.append("folder_id", folderId);
      const res = await uploadVideo(fd);
      router.push(`/processing/${res.session_id}`);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Upload failed. Is the backend running?");
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="border-b px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold">
          <Film className="w-5 h-5 text-primary" />
          Screen Journey
        </div>
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-sm hover:text-primary transition-colors">Dashboard</Link>
          <Link href="/search" className="text-sm hover:text-primary transition-colors">Search</Link>
          <ThemeToggle />
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-4 py-12 space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Turn screen recordings into searchable memory</h1>
          <p className="text-muted-foreground">Upload a recording and get a structured, searchable, AI-powered knowledge base.</p>
        </div>

        {/* Upload zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${dragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
          onClick={() => document.getElementById("file-input")?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".mp4,.mov,.avi,.mkv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) { setFile(f); setName(f.name.replace(/\.[^/.]+$/, "")); }
            }}
          />
          {file ? (
            <div className="space-y-1">
              <CheckCircle className="w-8 h-8 text-green-500 mx-auto" />
              <p className="font-medium">{file.name}</p>
              <p className="text-sm text-muted-foreground">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="font-medium">Drop a video here, or click to browse</p>
              <p className="text-sm text-muted-foreground">MP4, MOV · Max 500 MB</p>
            </div>
          )}
        </div>

        {/* Form */}
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium">Session Name *</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Product demo walkthrough"
              className="mt-1 w-full border rounded-md px-3 py-2 bg-background text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="What does this recording show?"
              className="mt-1 w-full border rounded-md px-3 py-2 bg-background text-sm resize-none"
            />
          </div>
          {folders.length > 0 && (
            <div>
              <label className="text-sm font-medium">Folder (optional)</label>
              <select
                value={folderId}
                onChange={(e) => setFolderId(e.target.value)}
                className="mt-1 w-full border rounded-md px-3 py-2 bg-background text-sm"
              >
                <option value="">No folder</option>
                {folders.map((f: any) => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
            </div>
          )}
          {error && <p className="text-destructive text-sm">{error}</p>}
          <button
            onClick={handleSubmit}
            disabled={uploading || !file || !name.trim()}
            className="w-full py-2.5 rounded-md bg-primary text-primary-foreground font-medium disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {uploading ? <><span className="animate-spin">⟳</span> Uploading…</> : "Start Processing"}
          </button>
        </div>

        {/* Recent sessions */}
        {sessions.length > 0 && (
          <div>
            <h2 className="font-semibold mb-3 text-sm text-muted-foreground uppercase tracking-wide">Recent Sessions</h2>
            <div className="space-y-2">
              {(sessions as SessionListItem[]).slice(0, 5).map((s) => (
                <Link
                  key={s.id}
                  href={`/dashboard?session=${s.id}`}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div>
                    <p className="font-medium text-sm">{s.name}</p>
                    <p className="text-xs text-muted-foreground">{format(new Date(s.created_at), "MMM d, yyyy")} · {s.total_pages} pages</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadgeClass(s.status)}`}>{s.status}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
