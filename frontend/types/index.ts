export interface Tag {
  id: string;
  name: string;
  color: string;
}

export interface Folder {
  id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface SessionListItem {
  id: string;
  name: string;
  description?: string;
  status: "pending" | "processing" | "extracting_frames" | "detecting_pages" | "extracting_text" | "deduplicating" | "building_tree" | "generating_summaries" | "indexing" | "done" | "failed";
  total_pages: number;
  total_steps: number;
  total_backtracks: number;
  created_at: string;
  processed_at?: string;
  tags: Tag[];
  folder?: Folder;
}

export interface TreeNode {
  id: string;
  title: string;
  depth: number;
  time_spent: number;
  timestamp_start: number;
  visit_count: number;
  page_summary?: string;
  is_backtrack_destination: boolean;
  children: TreeNode[];
}

export interface TimelineEvent {
  sequence: number;
  step_id: string;
  page_id: string;
  event: string;
  timestamp: number;
  is_backtrack: boolean;
}

export interface SessionDetail extends SessionListItem {
  total_duration_seconds?: number;
  session_summary?: string;
  tree?: {
    tree: TreeNode;
    timeline: TimelineEvent[];
  };
}

export interface Step {
  id: string;
  session_id: string;
  page_id?: string;
  step_type?: string;
  screenshot_path?: string;
  screenshot_url?: string;
  extracted_text?: string;
  text_summary?: string;
  timestamp_start?: number;
  timestamp_end?: number;
  ocr_confidence?: number;
  sequence_order?: number;
  is_backtrack: boolean;
}

export interface Annotation {
  id: string;
  author_name?: string;
  content: string;
  created_at: string;
}

export interface Bookmark {
  id: string;
  step_id: string;
  label?: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatSource {
  step_id: string;
  excerpt: string;
  timestamp?: number;
  page_title?: string;
  score?: number;
}

export interface SearchResult {
  step_id: string;
  session_id: string;
  session_name: string;
  page_title?: string;
  excerpt: string;
  score: number;
  timestamp?: number;
}

export interface ProcessingStatus {
  status: string;
  progress_percent: number;
  current_step: string;
  estimated_seconds_remaining?: number;
}

export interface CompareResult {
  session_a: { id: string; name: string; total_pages: number; total_steps: number; total_duration_seconds?: number; total_backtracks: number; tree?: any; pages: Array<{ id: string; title?: string; depth: number }> };
  session_b: { id: string; name: string; total_pages: number; total_steps: number; total_duration_seconds?: number; total_backtracks: number; tree?: any; pages: Array<{ id: string; title?: string; depth: number }> };
  diff: {
    common_pages: string[];
    unique_to_a: string[];
    unique_to_b: string[];
    path_divergence_point?: string;
  };
}
