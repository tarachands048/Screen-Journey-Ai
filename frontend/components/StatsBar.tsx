import { LayoutGrid, Clock, ArrowLeft, FileText } from "lucide-react";
import { formatDuration } from "@/lib/utils";

interface Props {
  totalPages: number;
  totalSteps: number;
  totalDuration?: number;
  totalBacktracks: number;
}

export default function StatsBar({ totalPages, totalSteps, totalDuration, totalBacktracks }: Props) {
  const stats = [
    { icon: LayoutGrid, label: "Pages", value: totalPages },
    { icon: FileText, label: "Steps", value: totalSteps },
    { icon: Clock, label: "Duration", value: formatDuration(totalDuration) },
    { icon: ArrowLeft, label: "Backtracks", value: totalBacktracks },
  ];
  return (
    <div className="flex gap-4 px-4 py-2 bg-card border rounded-lg text-sm">
      {stats.map(({ icon: Icon, label, value }) => (
        <div key={label} className="flex items-center gap-1.5 text-muted-foreground">
          <Icon className="w-3.5 h-3.5" />
          <span className="font-medium text-foreground">{value}</span>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}
