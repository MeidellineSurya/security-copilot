const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function querycopilot(
  query: string,
  assessmentId: string,
  conversationHistory: { role: string; content: string }[]
) {
  const res = await fetch(`${API_BASE}/copilot/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      assessment_id: assessmentId,
      conversation_history: conversationHistory,
    }),
  });

  if (!res.ok) throw new Error("Copilot query failed");
  return res.json();
}

export async function fetchAssessments() {
  const res = await fetch(`${API_BASE}/assessments/`);
  if (!res.ok) throw new Error("Failed to fetch assessments");
  return res.json();
}

export async function seedData() {
  const res = await fetch(`${API_BASE}/assessments/seed`, { method: "POST" });
  if (!res.ok) throw new Error("Seed failed");
  return res.json();
}