"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

const MatchReplay = dynamic(() => import("@/components/MatchReplay"), { ssr: false });

export default function ReplaySection({ matchId }: { matchId: string }) {
  const [show, setShow] = useState(false);

  return (
    <div className="mt-6">
      <button
        onClick={() => setShow(!show)}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          show
            ? "bg-emerald-600 text-white"
            : "bg-gray-800 text-gray-300 hover:bg-gray-700"
        }`}
      >
        {show ? "Hide Replay" : "🎬 Match Replay"}
      </button>
      {show && (
        <div className="mt-4">
          <MatchReplay matchId={matchId} />
        </div>
      )}
    </div>
  );
}
