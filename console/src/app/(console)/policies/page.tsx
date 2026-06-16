"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, 
  Save, 
  History, 
  Check, 
  AlertTriangle, 
  FileText, 
  ArrowLeft,
  ChevronRight,
  GitCompare,
  Plus
} from "lucide-react";

interface PolicyVersion {
  id: string;
  name: string;
  version: number;
  is_active: boolean;
  created_at: string;
}

interface DiffLine {
  type: "add" | "delete" | "same";
  text: string;
}

const DEFAULT_YAML = `name: Global Security Policy
description: Default AI safety guidelines and topic classification rules.
regex_rules:
  - name: SSN Detection
    pattern: '\\b\\d{3}-\\d{2}-\\d{4}\\b'
  - name: Email Detection
    pattern: '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
model_whitelist:
  - gpt-4o
  - claude-3-5-sonnet
  - gemini-2.5-flash-lite`;

export default function PoliciesPage() {
  const [activeTab, setActiveTab] = useState<"editor" | "history">("editor");
  const [yaml, setYaml] = useState(DEFAULT_YAML);
  const [policyName, setPolicyName] = useState("Global Security Policy");
  const [policyDesc, setPolicyDesc] = useState("Default AI safety guidelines.");
  const [history, setHistory] = useState<PolicyVersion[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [loadingActive, setLoadingActive] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // Status/Alert states
  const [validationError, setValidationError] = useState<string | null>(null);
  const [validationSuccess, setValidationSuccess] = useState(false);
  const [saving, setSaving] = useState(false);

  // Diff states
  const [diffTargetVersion, setDiffTargetVersion] = useState<PolicyVersion | null>(null);
  const [diffLines, setDiffLines] = useState<DiffLine[]>([]);
  const [diffActive, setDiffActive] = useState(false);

  const fetchActivePolicy = async () => {
    try {
      const res = await fetch("/api/policies/active");
      if (res.status === 401) {
        window.location.href = "/login";
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setYaml(data.policy_yaml);
        setPolicyName(data.name);
        setPolicyDesc(data.description || "");
      } else {
        // Fallback to default if 404
        setYaml(DEFAULT_YAML);
      }
    } catch (err: any) {
      console.warn("Failed to load active policy:", err.message);
    } finally {
      setLoadingActive(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch("/api/policies");
      if (res.status === 401) {
        window.location.href = "/login";
        return;
      }
      if (!res.ok) throw new Error("Failed to fetch policy history");
      const data = await res.json();
      setHistory(data || []);
      setHistoryError(null);
    } catch (err: any) {
      console.warn("Policies fetchHistory failed:", err.message);
      setHistoryError(err.message || "Failed to load policy history");
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchActivePolicy();
    fetchHistory();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setValidationError(null);
    setValidationSuccess(false);

    try {
      const res = await fetch("/api/policies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: policyName,
          description: policyDesc,
          policy_yaml: yaml
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Policy validation failed");
      }

      setValidationSuccess(true);
      fetchHistory();
    } catch (err: any) {
      setValidationError(err.message || "Failed to validate and save policy");
    } finally {
      setSaving(false);
    }
  };

  // Compute simple LCS line diff between active editor YAML and compared YAML
  const handleCompareDiff = (comparePolicy: PolicyVersion) => {
    setDiffTargetVersion(comparePolicy);
    setLoadingActive(true);
    
    // Fetch target policy yaml or query it if we had a detail route
    // Wait, let's fetch it from the server, but since we only have list policies in Next.js,
    // how do we get the detail yaml of the compare policy?
    // Let's create a quick API proxy or retrieve it. Wait! Let's check if we can query the database directly in a Next.js route, 
    // or we can write a GET endpoint for specific policy.
    // Yes! Let's add the query directly inside a Next.js API route!
    // Let's see: we can fetch `/api/policies?id=UUID` and it returns the specific policy detail!
    // Let's implement the diff retrieval:
    fetch(`/api/policies?id=${comparePolicy.id}`)
      .then((res) => res.json())
      .then((data) => {
        const compareYaml = data.policy_yaml || "";
        const diff = calculateDiff(compareYaml, yaml);
        setDiffLines(diff);
        setDiffActive(true);
      })
      .catch((err) => {
        console.error("Failed to load policy details for diff:", err);
      })
      .finally(() => {
        setLoadingActive(false);
      });
  };

  const calculateDiff = (oldText: string, newText: string): DiffLine[] => {
    const oldLines = oldText.split("\n");
    const newLines = newText.split("\n");
    const diff: DiffLine[] = [];

    let i = 0, j = 0;
    while (i < oldLines.length || j < newLines.length) {
      if (i < oldLines.length && j < newLines.length && oldLines[i] === newLines[j]) {
        diff.push({ type: "same", text: oldLines[i] });
        i++;
        j++;
      } else if (j < newLines.length && (i >= oldLines.length || !oldLines.slice(i).includes(newLines[j]))) {
        diff.push({ type: "add", text: newLines[j] });
        j++;
      } else {
        diff.push({ type: "delete", text: oldLines[i] });
        i++;
      }
    }
    return diff;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
          Governance Policies
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Edit YAML guardrails, validate OPA rules, and trace revisions for prompt redaction and model whitelisting.
        </p>
      </div>

      {/* Tabs Selector */}
      <div className="flex border-b border-slate-800/80 gap-6">
        <button
          onClick={() => { setActiveTab("editor"); setDiffActive(false); }}
          className={`pb-3.5 text-sm font-semibold transition relative ${
            activeTab === "editor" && !diffActive ? "text-indigo-400" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {activeTab === "editor" && !diffActive && <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 rounded-full" />}
          Policy Editor
        </button>
        <button
          onClick={() => { setActiveTab("history"); setDiffActive(false); }}
          className={`pb-3.5 text-sm font-semibold transition relative flex items-center gap-1.5 ${
            activeTab === "history" ? "text-indigo-400" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {activeTab === "history" && <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 rounded-full" />}
          Version Revisions
        </button>
        {diffActive && (
          <button
            className="pb-3.5 text-sm font-semibold text-indigo-400 relative flex items-center gap-1.5"
          >
            <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 rounded-full" />
            Diff: Active vs v{diffTargetVersion?.version}
          </button>
        )}
      </div>

      {/* Main Body */}
      {diffActive ? (
        /* Diff Viewer UI */
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-[#0d0d14] border border-slate-800 p-4 rounded-xl">
            <div className="text-xs">
              <p className="text-slate-500">COMPARING WORKSPACE</p>
              <h3 className="font-bold text-slate-200">Active Buffer vs Version {diffTargetVersion?.version}</h3>
            </div>
            <button
              onClick={() => setDiffActive(false)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Back to History
            </button>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#09090d] p-6 shadow-2xl overflow-x-auto font-mono text-[11px] leading-relaxed">
            {diffLines.map((line, idx) => (
              <div 
                key={idx}
                className={`flex px-2 py-0.5 ${
                  line.type === "add" 
                    ? "bg-emerald-500/10 text-emerald-300" 
                    : line.type === "delete" 
                      ? "bg-red-500/10 text-red-300 line-through" 
                      : "text-slate-400"
                }`}
              >
                <span className="w-8 select-none text-slate-600 inline-block text-right pr-4">
                  {line.type === "add" ? "+" : line.type === "delete" ? "-" : " "}
                </span>
                <pre className="whitespace-pre-wrap">{line.text || " "}</pre>
              </div>
            ))}
          </div>
        </div>
      ) : activeTab === "editor" ? (
        /* Editor Interface */
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* YAML Editor Panel (Span 3) */}
          <div className="lg:col-span-3 space-y-4">
            
            {/* Header Toolbar */}
            <div className="flex items-center justify-between bg-[#09090d] border border-slate-800 p-3.5 rounded-xl">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-slate-300">policy.yaml</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleSave}
                  disabled={saving || loadingActive}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg transition active:scale-[0.98] disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  {saving ? "Validating..." : "Validate & Deploy"}
                </button>
              </div>
            </div>

            {/* Validation Alerts */}
            {validationError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-xs flex items-start gap-3">
                <AlertTriangle className="w-4.5 h-4.5 text-red-400 flex-shrink-0" />
                <div>
                  <h4 className="font-bold">Validation Error</h4>
                  <p className="mt-1 font-mono">{validationError}</p>
                </div>
              </div>
            )}
            
            {validationSuccess && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-200 text-xs flex items-start gap-3">
                <Check className="w-4.5 h-4.5 text-emerald-400 flex-shrink-0" />
                <div>
                  <h4 className="font-bold">Policy Deployed Successfully</h4>
                  <p className="mt-1">Syntax is valid, rules are compiled, and gateways are invalidated via Redis hot reload.</p>
                </div>
              </div>
            )}

            {/* Core Textarea TextEditor */}
            <div className="relative rounded-2xl border border-slate-800 bg-[#07070a] shadow-2xl overflow-hidden min-h-[450px] flex flex-col">
              <textarea
                value={yaml}
                onChange={(e) => setYaml(e.target.value)}
                disabled={loadingActive}
                className="w-full flex-1 p-6 bg-transparent text-slate-300 font-mono text-xs focus:outline-none resize-none leading-relaxed min-h-[450px]"
                placeholder="# Input YAML policies here..."
              />
            </div>

          </div>

          {/* Form Properties Sidebar (Span 1) */}
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-[#09090d] p-5 shadow-xl space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Policy Properties</h3>
              
              <div>
                <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Policy Name</label>
                <input
                  type="text"
                  value={policyName}
                  onChange={(e) => setPolicyName(e.target.value)}
                  placeholder="e.g. Acme Policy Rules"
                  className="w-full px-3 py-1.5 rounded bg-[#07070a] border border-slate-800 text-slate-300 text-xs focus:outline-none focus:border-indigo-500/80 transition"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Description</label>
                <textarea
                  value={policyDesc}
                  onChange={(e) => setPolicyDesc(e.target.value)}
                  placeholder="Brief summary of policy bounds..."
                  className="w-full px-3 py-1.5 rounded bg-[#07070a] border border-slate-800 text-slate-300 text-xs focus:outline-none focus:border-indigo-500/80 transition h-20 resize-none"
                />
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-[#09090d] p-5 shadow-xl">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-amber-500" /> YAML Guardrails
              </h3>
              <p className="text-[11px] text-slate-500 leading-normal">
                Policies specify regular expressions for PII matching and lists of whitelisted model names. The engine hot-reloads OPA rule logic on each save.
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* Revisions History UI */
        <div className="rounded-2xl bg-[#09090d] border border-slate-800/80 shadow-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800/80 bg-[#0c0c12]/60">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-400" />
              Revision Trail
            </h3>
          </div>

          <div className="divide-y divide-slate-800/60">
            {loadingHistory ? (
              <div className="p-8 text-center flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500" />
              </div>
            ) : historyError ? (
              <div className="p-12 text-center text-red-450 flex flex-col items-center justify-center min-h-[200px]">
                <AlertTriangle className="w-8 h-8 mb-3 text-red-400" />
                <h4 className="text-sm font-semibold">Failed to Retrieve History</h4>
                <p className="text-xs text-slate-550 mt-1">{historyError}</p>
              </div>
            ) : history.length === 0 ? (
              <div className="p-12 text-center text-slate-500 text-xs">
                No policy revisions found. Save a policy in the editor to record the first version.
              </div>
            ) : (
              history.map((rev) => (
                <div key={rev.id} className="px-6 py-4 flex items-center justify-between hover:bg-slate-800/10 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-slate-800/40 border border-slate-700/60 flex items-center justify-center font-bold text-indigo-400 text-xs">
                      v{rev.version}
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-200 text-sm">{rev.name}</h4>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        Created {new Date(rev.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {rev.is_active ? (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                        Active Policy
                      </span>
                    ) : (
                      <button
                        onClick={() => handleCompareDiff(rev)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-850 hover:bg-slate-800 text-slate-300 border border-slate-850 hover:border-slate-700 text-xs font-semibold transition"
                      >
                        <GitCompare className="w-3.5 h-3.5 text-indigo-400" />
                        Diff vs Current
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
