const API_BASE = "http://127.0.0.1:8000";


export async function fetchDirections() {
  const response = await fetch(`${API_BASE}/api/directions`);
  if (!response.ok) throw new Error("方向接口暂时不可用");
  return response.json();
}


export async function fetchQuestions() {
  const response = await fetch(`${API_BASE}/api/questions`);
  if (!response.ok) throw new Error("题目接口暂时不可用");
  return response.json();
}


export async function submitAssessment(answers) {
  const response = await fetch(`${API_BASE}/api/assessment/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers })
  });
  if (!response.ok) throw new Error("测评接口暂时不可用");
  return response.json();
}
