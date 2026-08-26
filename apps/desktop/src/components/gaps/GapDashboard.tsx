import { useEffect, useState } from "react";
import { getGaps, resolveGap } from "../../services/jarvisApi";
import { useAppStore, AppState } from "../../stores/useAppStore";

export function GapDashboard() {
  const [gaps, setGaps] = useState<any[]>([]);
  const setUnresolvedGapCount = useAppStore((state: AppState) => state.setUnresolvedGapCount);

  const loadGaps = async () => {
    try {
      const data = await getGaps();
      setGaps(data);
      setUnresolvedGapCount(data.filter((g: any) => !g.resolved).length);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadGaps();
    // In a real app we'd also listen for the websocket event here to auto-refresh
  }, []);

  const handleResolve = async (gapId: string) => {
    try {
      await resolveGap(gapId);
      loadGaps();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="w-full h-full bg-[#030812] text-white p-8 pr-[calc(var(--dock-width)+2rem)] overflow-y-auto font-mono">
      <h2 className="text-xl mb-4 font-bold text-[var(--color-cyan)]">Capability Gap Log</h2>
      <div className="flex flex-col gap-4">
        {gaps.map(gap => (
          <div key={gap.gap_id} className={`p-4   border ${gap.resolved ? "border-gray-800 opacity-50" : "border-[var(--color-cyan)]"} rounded bg-[#061020]`}>
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs text-gray-400">{new Date(gap.timestamp).toLocaleString()}</span>
              {!gap.resolved && (
                <button
                  onClick={() => handleResolve(gap.gap_id)}
                  className="px-3 py-1 bg-cyan-900/50 hover:bg-cyan-800 border border-[var(--color-cyan)] rounded text-xs text-[var(--color-cyan)]"
                >
                  Mark resolved
                </button>
              )}
              {gap.resolved && (
                <span className="text-xs text-green-500 uppercase">Resolved</span>
              )}
            </div>
            <div className="text-sm mb-1"><span className="text-gray-500">Request:</span> {gap.user_request}</div>
            <div className="text-sm text-gray-400"><span className="text-gray-500">Response/Reason:</span> {gap.gap_reason}</div>
          </div>
        ))}
        {gaps.length === 0 && (
          <div className="text-gray-500 text-sm">No capability gaps logged yet.</div>
        )}
      </div>
    </div>
  );
}
