"use client";
import { TimelineEvent } from "@/types";
import { formatTimestamp } from "@/lib/utils";

interface Props {
  timeline: TimelineEvent[];
  totalDuration?: number;
  onStepClick?: (stepId: string) => void;
}

const EVENT_COLORS: Record<string, string> = {
  forward: "#6366f1",
  back: "#f59e0b",
  page_load: "#6366f1",
  back_navigation: "#f59e0b",
  modal_open: "#a855f7",
  tab_switch: "#3b82f6",
  scroll: "#94a3b8",
};

export default function HeatmapTimeline({ timeline, totalDuration, onStepClick }: Props) {
  if (!timeline || timeline.length === 0) {
    return <div className="text-muted-foreground text-sm px-2">No timeline data</div>;
  }

  const max = totalDuration || (timeline[timeline.length - 1]?.timestamp + 5) || 1;

  return (
    <div className="space-y-1">
      <div className="flex gap-0.5 h-8 rounded overflow-hidden bg-muted">
        {timeline.map((event, i) => {
          const next = timeline[i + 1];
          const start = event.timestamp / max;
          const end = next ? next.timestamp / max : 1;
          const width = Math.max(end - start, 0.01);
          const color = EVENT_COLORS[event.event] || "#94a3b8";
          return (
            <div
              key={event.step_id || i}
              className="h-full cursor-pointer hover:opacity-80 transition-opacity"
              style={{ width: `${width * 100}%`, backgroundColor: color }}
              title={`${event.event} @ ${formatTimestamp(event.timestamp)}`}
              onClick={() => onStepClick?.(event.step_id)}
            />
          );
        })}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground px-0.5">
        <span>0:00</span>
        <span>{formatTimestamp(totalDuration)}</span>
      </div>
      <div className="flex gap-3 text-xs text-muted-foreground flex-wrap">
        {Object.entries(EVENT_COLORS).filter(([k]) => ["forward", "back", "modal_open", "tab_switch"].includes(k)).map(([k, c]) => (
          <span key={k} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: c }} />
            {k.replace("_", " ")}
          </span>
        ))}
      </div>
    </div>
  );
}
