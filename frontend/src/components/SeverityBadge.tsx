import { Severity } from "@/types";

const styles: Record<Severity, string> = {
  Critical: "bg-red-100 text-red-800 border border-red-200",
  High: "bg-orange-100 text-orange-800 border border-orange-200",
  Medium: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  Low: "bg-green-100 text-green-800 border border-green-200",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${styles[severity]}`}>
      {severity}
    </span>
  );
}