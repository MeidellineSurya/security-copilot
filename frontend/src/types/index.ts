export type Severity = "Critical" | "High" | "Medium" | "Low";

export interface Risk {
  id: string;
  assessment_id: string;
  title: string;
  description: string;
  severity: Severity;
  score: number;
  category: string;
  remediation: string;
}

export interface Assessment {
  id: string;
  company: string;
  industry: string;
  scope: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface CopilotResponse {
  answer: string;
  risks_referenced: string[];
  suggested_followups: string[];
}