import { create } from "zustand";

const HISTORY_SIZE = 40;
// Exponential smoothing factor applied on each incoming raw level, so the
// visual reacts as a smooth pulse instead of snapping to each raw WS value.
const SMOOTHING = 0.35;

interface MicLevelState {
  level: number;
  history: number[];
  pushLevel: (raw: number) => void;
}

export const useMicLevelStore = create<MicLevelState>((set, get) => ({
  level: 0,
  history: [],
  pushLevel: (raw) => {
    const clamped = Math.max(0, Math.min(1, raw));
    const smoothed = get().level + (clamped - get().level) * SMOOTHING;
    const history = [...get().history, clamped].slice(-HISTORY_SIZE);
    set({ level: smoothed, history });
  },
}));
