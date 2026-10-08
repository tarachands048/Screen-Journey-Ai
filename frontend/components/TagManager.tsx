"use client";
import { useState } from "react";
import { Plus, X } from "lucide-react";
import { Tag } from "@/types";
import { createTag, assignTag, removeTag } from "@/lib/api";

interface Props {
  sessionId: string;
  currentTags: Tag[];
  allTags: Tag[];
  onUpdate: () => void;
}

const PRESET_COLORS = ["#6366f1", "#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#ec4899"];

export default function TagManager({ sessionId, currentTags, allTags, onUpdate }: Props) {
  const [newName, setNewName] = useState("");
  const [newColor, setNewColor] = useState(PRESET_COLORS[0]);
  const [showCreate, setShowCreate] = useState(false);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    const tag = await createTag({ name: newName.trim(), color: newColor });
    await assignTag(sessionId, tag.id);
    setNewName("");
    setShowCreate(false);
    onUpdate();
  };

  const handleAssign = async (tag: Tag) => {
    await assignTag(sessionId, tag.id);
    onUpdate();
  };

  const handleRemove = async (tagId: string) => {
    await removeTag(sessionId, tagId);
    onUpdate();
  };

  const unassigned = allTags.filter((t) => !currentTags.find((ct) => ct.id === t.id));

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1">
        {currentTags.map((tag) => (
          <span
            key={tag.id}
            className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs text-white"
            style={{ backgroundColor: tag.color }}
          >
            {tag.name}
            <button onClick={() => handleRemove(tag.id)} className="hover:opacity-70">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs border hover:bg-accent"
        >
          <Plus className="w-3 h-3" /> Add
        </button>
      </div>

      {showCreate && (
        <div className="flex gap-2 items-center">
          {unassigned.length > 0 && (
            <select
              onChange={(e) => { if (e.target.value) handleAssign(allTags.find((t) => t.id === e.target.value)!); }}
              className="text-xs border rounded px-1 py-0.5 bg-background"
              defaultValue=""
            >
              <option value="">Existing tag…</option>
              {unassigned.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          )}
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="New tag name"
            className="text-xs border rounded px-2 py-0.5 bg-background flex-1"
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          />
          <div className="flex gap-1">
            {PRESET_COLORS.map((c) => (
              <button
                key={c}
                onClick={() => setNewColor(c)}
                className="w-4 h-4 rounded-full border-2"
                style={{ backgroundColor: c, borderColor: newColor === c ? "white" : "transparent" }}
              />
            ))}
          </div>
          <button onClick={handleCreate} className="text-xs px-2 py-0.5 bg-primary text-primary-foreground rounded">
            Create
          </button>
        </div>
      )}
    </div>
  );
}
