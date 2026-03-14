"use client";
import { useState, useRef, useEffect } from "react";

const METRIC_DESCRIPTIONS: Record<string, string> = {
  "Player": "Athlete identifier from device or CSV upload",
  "Min": "Total minutes of recorded activity",
  "Minutes Played": "Total minutes of recorded activity",
  "Dist (m)": "Total distance covered in metres, calculated from GPS positions",
  "Total Distance": "Total distance covered in metres, calculated from GPS positions",
  "m/min": "Distance per minute — higher values mean more ground covered per minute on the field",
  "Dist/Min": "Distance per minute — higher values mean more ground covered per minute on the field",
  "Distance / Min": "Distance per minute — higher values mean more ground covered per minute on the field",
  "Top Speed": "Peak speed recorded during the session in km/h",
  "HSR (m)": "High-Speed Running — metres covered above 20 km/h. Measures explosive, high-intensity effort",
  "HSR Distance": "High-Speed Running — metres covered above 20 km/h. Measures explosive, high-intensity effort",
  "Sprints": "Number of sprint efforts (bursts above 20 km/h sustained for at least 1 second)",
  "Sprint Count": "Number of sprint efforts (bursts above 20 km/h sustained for at least 1 second)",
  "Accels": "Sharp accelerations (>2 m/s²) — quick bursts to change pace",
  "Accel Count": "Sharp accelerations (>2 m/s²) — quick bursts to change pace",
  "Accelerations": "Sharp accelerations (>2 m/s²) — quick bursts to change pace",
  "Decels": "Sharp decelerations (<-2 m/s²) — sudden stops or direction changes",
  "Decel Count": "Sharp decelerations (<-2 m/s²) — sudden stops or direction changes",
  "Decelerations": "Sharp decelerations (<-2 m/s²) — sudden stops or direction changes",
  "Load": "Total mechanical load from accelerometer data — combines all movement intensity into one number",
  "Total Load": "Total mechanical load from accelerometer data — combines all movement intensity into one number",
  "Load / Min": "Mechanical load per minute — normalises intensity for different playing times",
  "Impact Count": "Number of detected high-force impacts (collisions, falls, hard tackles)",
  "Movement Count": "Total number of distinct movements detected by the accelerometer",
  "Peak 1min": "Highest 1-minute rolling average intensity — shows peak burst capacity",
  "Peak 3min": "Highest 3-minute rolling average intensity",
  "Peak 5min": "Highest 5-minute rolling average intensity — sustained effort capacity",
};

export function MetricTooltip({ label, children }: { label: string; children: React.ReactNode }) {
  const [show, setShow] = useState(false);
  const [pos, setPos] = useState<"above" | "below">("above");
  const ref = useRef<HTMLDivElement>(null);
  const desc = METRIC_DESCRIPTIONS[label];

  useEffect(() => {
    if (show && ref.current) {
      const rect = ref.current.getBoundingClientRect();
      setPos(rect.top < 80 ? "below" : "above");
    }
  }, [show]);

  if (!desc) return <>{children}</>;

  return (
    <div
      ref={ref}
      className="relative inline-flex items-center gap-1 cursor-help"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      <svg className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
      {show && (
        <div className={`absolute z-50 w-56 px-3 py-2 text-xs text-gray-200 bg-gray-800 border border-gray-700 rounded-lg shadow-xl ${
          pos === "above" ? "bottom-full mb-2" : "top-full mt-2"
        } left-1/2 -translate-x-1/2`}>
          {desc}
          <div className={`absolute left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-800 border-gray-700 rotate-45 ${
            pos === "above" ? "bottom-0 translate-y-1/2 border-r border-b" : "top-0 -translate-y-1/2 border-l border-t"
          }`} />
        </div>
      )}
    </div>
  );
}
