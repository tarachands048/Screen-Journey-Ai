import { create } from "zustand";
import { persist } from "zustand/middleware";
import { SessionListItem, SessionDetail } from "@/types";

interface AppState {
  selectedSessionId: string | null;
  sessions: SessionListItem[];
  activeSession: SessionDetail | null;
  setSelectedSessionId: (id: string | null) => void;
  setSessions: (sessions: SessionListItem[]) => void;
  setActiveSession: (session: SessionDetail | null) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      selectedSessionId: null,
      sessions: [],
      activeSession: null,
      setSelectedSessionId: (id) => set({ selectedSessionId: id }),
      setSessions: (sessions) => set({ sessions }),
      setActiveSession: (session) => set({ activeSession: session }),
    }),
    { name: "screen-journey-store", partialize: (state) => ({ selectedSessionId: state.selectedSessionId }) }
  )
);
