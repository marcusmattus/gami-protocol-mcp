import { useEffect, useRef, useState } from "react";

type AgentEvent = {
  event: string;
  origin: string;
  payload: Record<string, unknown>;
};

type Options = {
  url?: string;
};

export function useAgentStream({ url }: Options = {}) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const streamUrl = url || import.meta.env.VITE_SSE_URL || "http://localhost:9000/api/stream";

  useEffect(() => {
    if (eventSourceRef.current) return;

    const source = new EventSource(streamUrl);
    eventSourceRef.current = source;

    source.onmessage = (message) => {
      try {
        const parsed = JSON.parse(message.data) as AgentEvent;
        setEvents((prev) => [parsed, ...prev].slice(0, 200));
      } catch (error) {
        console.error("Malformed SSE payload", error);
      }
    };

    source.onerror = (err) => {
      console.error("SSE error", err);
      source.close();
      eventSourceRef.current = null;
      setTimeout(() => {
        eventSourceRef.current = new EventSource(streamUrl);
      }, 5000);
    };

    return () => {
      source.close();
      eventSourceRef.current = null;
    };
  }, [streamUrl]);

  return events;
}
