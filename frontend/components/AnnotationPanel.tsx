"use client";
import { useState, useEffect } from "react";
import { MessageSquare, Trash2 } from "lucide-react";
import { Annotation } from "@/types";
import { getAnnotations, addAnnotation, deleteAnnotation } from "@/lib/api";
import { format } from "date-fns";

interface Props {
  stepId: string;
}

export default function AnnotationPanel({ stepId }: Props) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [author, setAuthor] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);

  const load = async () => {
    const data = await getAnnotations(stepId);
    setAnnotations(data);
  };

  useEffect(() => { load(); }, [stepId]);

  const handleAdd = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      await addAnnotation(stepId, { author_name: author, content });
      setContent("");
      await load();
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteAnnotation(id);
    await load();
  };

  return (
    <div className="space-y-3">
      <h3 className="font-medium flex items-center gap-2 text-sm">
        <MessageSquare className="w-4 h-4" /> Team Notes ({annotations.length})
      </h3>

      <div className="space-y-2 max-h-48 overflow-y-auto">
        {annotations.length === 0 && (
          <p className="text-muted-foreground text-xs">No notes yet. Add one below.</p>
        )}
        {annotations.map((ann) => (
          <div key={ann.id} className="bg-muted rounded p-2 text-sm group">
            <div className="flex justify-between items-start">
              <span className="font-medium text-xs text-muted-foreground">
                {ann.author_name || "Anonymous"} · {format(new Date(ann.created_at), "MMM d, HH:mm")}
              </span>
              <button
                onClick={() => handleDelete(ann.id)}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-destructive"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
            <p className="mt-1">{ann.content}</p>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <input
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          placeholder="Your name (optional)"
          className="w-full text-xs border rounded px-2 py-1 bg-background"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Add a note…"
          rows={2}
          className="w-full text-sm border rounded px-2 py-1 bg-background resize-none"
          onKeyDown={(e) => e.key === "Enter" && e.ctrlKey && handleAdd()}
        />
        <button
          onClick={handleAdd}
          disabled={loading || !content.trim()}
          className="text-xs px-3 py-1 bg-primary text-primary-foreground rounded disabled:opacity-50"
        >
          Add Note
        </button>
      </div>
    </div>
  );
}
