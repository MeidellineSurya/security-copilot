"use client";

const DEFAULT_PROMPTS = [
  "What are my biggest risks?",
  "What should I fix first?",
  "What are the quick wins?",
  "Explain my AWS risks",
  "What's the business impact of the top risks?",
];

interface Props {
  prompts?: string[];
  onSelect: (prompt: string) => void;
}

export function SuggestedPrompts({ prompts = DEFAULT_PROMPTS, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {prompts.map((p) => (
        <button
          key={p}
          onClick={() => onSelect(p)}
          className="text-xs px-3 py-1.5 rounded-full border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
        >
          {p}
        </button>
      ))}
    </div>
  );
}