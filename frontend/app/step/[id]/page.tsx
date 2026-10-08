"use client";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getStep, getSteps } from "@/lib/api";
import { ArrowLeft, ArrowRight, Copy, Check } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import ThemeToggle from "@/components/ThemeToggle";
import AnnotationPanel from "@/components/AnnotationPanel";
import BookmarkButton from "@/components/BookmarkButton";
import { formatTimestamp } from "@/lib/utils";

export default function StepDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [copied, setCopied] = useState(false);

  const { data: step } = useQuery({ queryKey: ["step", id], queryFn: () => getStep(id) });
  const { data: steps = [] } = useQuery({
    queryKey: ["steps", step?.session_id],
    queryFn: () => getSteps(step!.session_id),
    enabled: !!step?.session_id,
  });

  const currentIdx = steps.findIndex((s: any) => s.id === id);
  const prevStep = currentIdx > 0 ? steps[currentIdx - 1] : null;
  const nextStep = currentIdx < steps.length - 1 ? steps[currentIdx + 1] : null;

  const copyText = async () => {
    if (step?.extracted_text) {
      await navigator.clipboard.writeText(step.extracted_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  if (!step) return <div className="min-h-screen flex items-center justify-center text-muted-foreground">Loading…</div>;

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b px-4 py-2 flex items-center justify-between">
        <Link href={`/session/${step.session_id}`} className="flex items-center gap-1 text-sm hover:text-primary">
          <ArrowLeft className="w-4 h-4" /> Back to Session
        </Link>
        <div className="flex items-center gap-2">
          <BookmarkButton stepId={step.id} sessionId={step.session_id} />
          <ThemeToggle />
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Screenshot */}
          <div className="space-y-4">
            {step.screenshot_url ? (
              <img src={step.screenshot_url} alt="Screenshot" className="w-full rounded-lg border" />
            ) : (
              <div className="w-full h-64 bg-muted rounded-lg flex items-center justify-center text-muted-foreground">No screenshot</div>
            )}

            {/* Navigation */}
            <div className="flex justify-between">
              {prevStep ? (
                <Link href={`/step/${(prevStep as any).id}`} className="flex items-center gap-1 text-sm hover:text-primary">
                  <ArrowLeft className="w-4 h-4" /> Previous
                </Link>
              ) : <span />}
              <span className="text-xs text-muted-foreground">
                Step {currentIdx + 1} of {steps.length}
              </span>
              {nextStep ? (
                <Link href={`/step/${(nextStep as any).id}`} className="flex items-center gap-1 text-sm hover:text-primary">
                  Next <ArrowRight className="w-4 h-4" />
                </Link>
              ) : <span />}
            </div>
          </div>

          {/* Right: Details */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="px-2 py-0.5 bg-muted rounded">{step.step_type || "action"}</span>
              <span>@ {formatTimestamp(step.timestamp_start)}</span>
              {step.is_backtrack && <span className="text-yellow-500 font-medium">↩ backtrack</span>}
              {step.ocr_confidence !== undefined && (
                <span className="ml-auto">OCR: {Math.round((step.ocr_confidence || 0) * 100)}%</span>
              )}
            </div>

            {step.text_summary && (
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-3">
                <p className="text-sm font-medium text-primary">AI Summary</p>
                <p className="text-sm mt-1">{step.text_summary}</p>
              </div>
            )}

            {step.extracted_text && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">Extracted Text</h3>
                  <button onClick={copyText} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
                    {copied ? <><Check className="w-3 h-3 text-green-500" /> Copied</> : <><Copy className="w-3 h-3" /> Copy</>}
                  </button>
                </div>
                <pre className="text-xs bg-muted rounded p-3 overflow-y-auto max-h-48 whitespace-pre-wrap font-mono">
                  {step.extracted_text}
                </pre>
              </div>
            )}

            <div className="border-t pt-4">
              <AnnotationPanel stepId={step.id} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
