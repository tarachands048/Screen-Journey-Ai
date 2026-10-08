"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { CheckCircle, Circle, Loader2, Film, XCircle } from "lucide-react";
import { getSessionStatus, getSession } from "@/lib/api";
import Link from "next/link";

const STEPS = [
  { key: "extracting_frames", label: "Extracting frames" },
  { key: "detecting_pages", label: "Detecting page changes" },
  { key: "extracting_text", label: "Running OCR" },
  { key: "deduplicating", label: "Deduplicating content" },
  { key: "building_tree", label: "Building navigation tree" },
  { key: "generating_summaries", label: "Generating AI summaries" },
  { key: "indexing", label: "Building search index" },
];

const STATUS_ORDER = STEPS.map((s) => s.key);

export default function ProcessingPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [status, setStatus] = useState<any>(null);
  const [sessionName, setSessionName] = useState("");

  useEffect(() => {
    getSession(id).then((s) => setSessionName(s.name));
  }, [id]);

  useEffect(() => {
    const poll = async () => {
      try {
        const s = await getSessionStatus(id);
        setStatus(s);
        if (s.status === "done") {
          setTimeout(() => router.push(`/dashboard?session=${id}`), 1500);
        }
      } catch {}
    };
    poll();
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, [id, router]);

  const currentIdx = STATUS_ORDER.indexOf(status?.status || "");
  const progress = status?.progress_percent || 0;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="max-w-md w-full mx-4 space-y-6">
        <div className="text-center space-y-1">
          <Film className="w-8 h-8 text-primary mx-auto" />
          <h1 className="font-bold text-xl">{sessionName || "Processing…"}</h1>
          <p className="text-muted-foreground text-sm">
            {status?.status === "done" ? "Done! Redirecting…" : status?.status === "failed" ? "Processing failed." : "Please wait while your recording is processed."}
          </p>
        </div>

        {/* Progress bar */}
        <div className="bg-muted rounded-full h-2">
          <div
            className="bg-primary rounded-full h-2 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-center text-sm text-muted-foreground">{progress}%</p>

        {/* Steps list */}
        <div className="space-y-2">
          {STEPS.map((step, i) => {
            const done = i < currentIdx || status?.status === "done";
            const active = i === currentIdx && status?.status !== "done";
            const failed = status?.status === "failed" && i === currentIdx;
            return (
              <div key={step.key} className="flex items-center gap-3">
                {failed ? (
                  <XCircle className="w-5 h-5 text-destructive" />
                ) : done ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : active ? (
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                ) : (
                  <Circle className="w-5 h-5 text-muted-foreground" />
                )}
                <span className={`text-sm ${active ? "font-medium text-foreground" : done ? "text-foreground" : "text-muted-foreground"}`}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>

        <div className="flex gap-2">
          <Link href={`/dashboard?session=${id}`} className="flex-1 text-center text-sm py-2 border rounded-md hover:bg-accent transition-colors">
            View in Dashboard
          </Link>
          <Link href="/" className="flex-1 text-center text-sm py-2 border rounded-md hover:bg-accent transition-colors">
            Upload Another
          </Link>
        </div>
      </div>
    </div>
  );
}
