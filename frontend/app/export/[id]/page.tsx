"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getSession, exportSession, generateSOP } from "@/lib/api";
import { ArrowLeft, Download, FileText, Loader2 } from "lucide-react";
import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";
import ReactMarkdown from "react-markdown";

export default function ExportPage() {
  const { id } = useParams<{ id: string }>();
  const { data: session } = useQuery({ queryKey: ["session", id], queryFn: () => getSession(id) });

  const [format, setFormat] = useState("markdown");
  const [includeScreenshots, setIncludeScreenshots] = useState(false);
  const [includeText, setIncludeText] = useState(true);
  const [includeSummaries, setIncludeSummaries] = useState(true);
  const [includeTree, setIncludeTree] = useState(true);
  const [includeAnnotations, setIncludeAnnotations] = useState(true);
  const [includeSop, setIncludeSop] = useState(false);
  const [sopContent, setSopContent] = useState<string | null>(null);
  const [sopLoading, setSopLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleGenerateSOP = async () => {
    setSopLoading(true);
    try {
      const data = await generateSOP(id);
      setSopContent(data.sop_markdown);
    } finally {
      setSopLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportSession(id, {
        format,
        include_screenshots: includeScreenshots,
        include_text: includeText,
        include_summaries: includeSummaries,
        include_tree: includeTree,
        include_annotations: includeAnnotations,
        include_sop: includeSop,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${session?.name || "export"}_${format}.${format === "json" ? "json" : "md"}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b px-4 py-2 flex items-center justify-between">
        <Link href={`/session/${id}`} className="flex items-center gap-1 text-sm hover:text-primary">
          <ArrowLeft className="w-4 h-4" /> Back
        </Link>
        <ThemeToggle />
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <div>
          <h1 className="font-bold text-2xl">Export Session</h1>
          <p className="text-muted-foreground text-sm mt-1">{session?.name}</p>
        </div>

        <div className="border rounded-lg p-4 space-y-4">
          <div>
            <label className="text-sm font-medium">Format</label>
            <div className="flex gap-3 mt-2">
              {["markdown", "json", "documentation"].map((f) => (
                <label key={f} className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" value={f} checked={format === f} onChange={() => setFormat(f)} />
                  <span className="text-sm capitalize">{f}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              ["includeScreenshots", "Include screenshots", includeScreenshots, setIncludeScreenshots],
              ["includeText", "Include extracted text", includeText, setIncludeText],
              ["includeSummaries", "Include AI summaries", includeSummaries, setIncludeSummaries],
              ["includeTree", "Include navigation tree", includeTree, setIncludeTree],
              ["includeAnnotations", "Include annotations", includeAnnotations, setIncludeAnnotations],
              ["includeSop", "Include SOP", includeSop, setIncludeSop],
            ].map(([key, label, val, setter]) => (
              <label key={key as string} className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={val as boolean} onChange={(e) => (setter as any)(e.target.checked)} />
                <span className="text-sm">{label as string}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleGenerateSOP}
            disabled={sopLoading}
            className="flex items-center gap-2 px-4 py-2 border rounded-md text-sm hover:bg-accent disabled:opacity-50"
          >
            {sopLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            Generate SOP Preview
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium disabled:opacity-50 ml-auto"
          >
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Export Now
          </button>
        </div>

        {sopContent && (
          <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
            <h3 className="font-medium text-sm mb-3">SOP Preview</h3>
            <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none">{sopContent}</ReactMarkdown>
          </div>
        )}
      </main>
    </div>
  );
}
