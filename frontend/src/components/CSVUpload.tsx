"use client";
import { useState, useRef } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UploadResult {
  assessment_id: string;
  company: string;
  valid_rows: number;
  skipped_rows: number;
  errors: string[];
}

interface Props {
  onUploadSuccess: (assessmentId: string, company: string) => void;
}

export function CSVUpload({ onUploadSuccess }: Props) {
  const [company, setCompany] = useState("");
  const [industry, setIndustry] = useState("");
  const [scope, setScope] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped?.name.endsWith(".csv")) {
      setFile(dropped);
      setError(null);
    } else {
      setError("Only .csv files are accepted");
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0];
    if (selected?.name.endsWith(".csv")) {
      setFile(selected);
      setError(null);
    } else {
      setError("Only .csv files are accepted");
    }
  }

  async function handleDownloadTemplate() {
    const res = await fetch(`${API_BASE}/upload/template`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "risks_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleUpload() {
    if (!file || !company || !industry || !scope) {
      setError("Please fill in all fields and select a CSV file");
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("company", company);
      formData.append("industry", industry);
      formData.append("scope", scope);

      const res = await fetch(`${API_BASE}/upload/upload`, {
        method: "POST",
        body: formData,
        // NOTE: do NOT set Content-Type header manually
        // The browser sets it automatically with the correct boundary for multipart/form-data
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data.detail?.message || data.detail || "Upload failed");
        return;
      }

      const data: UploadResult = await res.json();
      setResult(data);
      onUploadSuccess(data.assessment_id, data.company);
    } catch {
      setError("Could not reach the backend — is FastAPI running?");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 w-full max-w-lg shadow-sm">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="font-semibold text-gray-900">Upload Risk Assessment</h2>
          <p className="text-xs text-gray-500 mt-0.5">Import your risks via CSV to start querying</p>
        </div>
        <button
          onClick={handleDownloadTemplate}
          className="text-xs px-3 py-1.5 border border-blue-200 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors flex items-center gap-1.5"
        >
          ↓ Download template
        </button>
      </div>

      {/* Company details */}
      <div className="space-y-3 mb-4">
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Company name</label>
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="e.g. AcmePay"
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Industry</label>
          <input
            type="text"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="e.g. Fintech, Healthcare, SaaS"
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Assessment scope</label>
          <input
            type="text"
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            placeholder="e.g. AWS infrastructure, web app, internal APIs"
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* File drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors mb-4 ${
          dragging
            ? "border-blue-400 bg-blue-50"
            : file
            ? "border-green-300 bg-green-50"
            : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleFileChange}
        />
        {file ? (
          <div>
            <p className="text-sm font-medium text-green-700">✓ {file.name}</p>
            <p className="text-xs text-green-600 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div>
            <p className="text-sm text-gray-500">Drag & drop your CSV here</p>
            <p className="text-xs text-gray-400 mt-1">or click to browse</p>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-xs text-red-700">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm font-medium text-green-800">
            ✅ {result.valid_rows} risks imported for {result.company}
          </p>
          {result.skipped_rows > 0 && (
            <p className="text-xs text-yellow-700 mt-1">
              ⚠️ {result.skipped_rows} rows skipped
            </p>
          )}
          {result.errors.length > 0 && (
            <ul className="mt-2 space-y-0.5">
              {result.errors.map((e, i) => (
                <li key={i} className="text-xs text-red-600">• {e}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={uploading || !file || !company || !industry || !scope}
        className="w-full py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {uploading ? "Uploading..." : "Upload & create assessment"}
      </button>
    </div>
  );
}