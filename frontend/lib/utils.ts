import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(seconds?: number): string {
  if (!seconds) return "0s";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export function formatTimestamp(seconds?: number): string {
  if (seconds === undefined || seconds === null) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function statusColor(status: string): string {
  switch (status) {
    case "done": return "text-green-500";
    case "failed": return "text-red-500";
    case "pending": return "text-gray-400";
    default: return "text-yellow-500";
  }
}

export function statusBadgeClass(status: string): string {
  switch (status) {
    case "done": return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
    case "failed": return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
    case "pending": return "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400";
    default: return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
  }
}

export function truncate(str: string, len: number): string {
  if (!str) return "";
  return str.length > len ? str.slice(0, len) + "..." : str;
}
