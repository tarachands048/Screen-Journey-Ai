"use client";
import { useState } from "react";
import { Bookmark, BookmarkCheck } from "lucide-react";
import { addBookmark, deleteBookmark } from "@/lib/api";

interface Props {
  stepId: string;
  sessionId: string;
  existingBookmarkId?: string;
  label?: string;
  onToggle?: (bookmarkId: string | null) => void;
}

export default function BookmarkButton({ stepId, sessionId, existingBookmarkId, label, onToggle }: Props) {
  const [bookmarkId, setBookmarkId] = useState<string | null>(existingBookmarkId || null);
  const [loading, setLoading] = useState(false);

  const toggle = async () => {
    setLoading(true);
    try {
      if (bookmarkId) {
        await deleteBookmark(bookmarkId);
        setBookmarkId(null);
        onToggle?.(null);
      } else {
        const bm = await addBookmark({ step_id: stepId, session_id: sessionId, label: label || "" });
        setBookmarkId(bm.id);
        onToggle?.(bm.id);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={toggle}
      disabled={loading}
      className="p-1.5 rounded hover:bg-accent transition-colors"
      title={bookmarkId ? "Remove bookmark" : "Add bookmark"}
    >
      {bookmarkId ? (
        <BookmarkCheck className="w-4 h-4 text-yellow-500" />
      ) : (
        <Bookmark className="w-4 h-4 text-muted-foreground" />
      )}
    </button>
  );
}
