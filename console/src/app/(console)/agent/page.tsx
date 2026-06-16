"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Bot, 
  Send, 
  ShieldCheck, 
  Cpu, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  X,
  Play, 
  User, 
  Sparkles,
  Layers,
  KeyRound,
  Lock,
  Loader2,
  Terminal,
  Activity
} from "lucide-react";

interface Workflow {
  id: string;
  workflow_id: string;
  framework: string;
  current_state: string;
  execution_status: string;
  risk_score: number | null;
  started_at: string;
  completed_at: string | null;
  approval_id: string | null;
}

interface Approval {
  id: string;
  action_id: string;
  action_type: string;
  action_description: string;
  status: string;
  expires_at: string;
  created_at: string;
}

interface Message {
  sender: "user" | "agent";
  text: string;
  timestamp: Date;
  results?: any;
}

export default function AgentPage() {
  const [activePane, setActivePane] = useState<"chat" | "scans">("chat");
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggeringScan, setTriggeringScan] = useState(false);

  // Chat States
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "agent",
      text: "Hello! I am your AuthClaw Compliance Agent. I orchestrate GDPR, HIPAA, and SOC 2 audits, check active gate rules, and propose infrastructure remediations. How can I assist you today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [selectedResult, setSelectedResult] = useState<any>(null);

  // HITL Approval States
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [mfaError, setMfaError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [showMfaInput, setShowMfaInput] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchWorkflowsAndApprovals = async () => {
    try {
      const res = await fetch("/api/workflows");
      if (res.status === 401) {
        window.location.href = "/login";
        return;
      }
      if (!res.ok) throw new Error("Failed to load workflows");
      const data = await res.json();
      setWorkflows(data.workflows || []);
      setApprovals(data.approvals || []);
    } catch (err: any) {
      console.warn("Agent fetchWorkflowsAndApprovals failed:", err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflowsAndApprovals();
    const interval = setInterval(fetchWorkflowsAndApprovals, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const triggerScan = async (framework: string) => {
    setTriggeringScan(true);
    try {
      const res = await fetch("/api/workflows", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ framework }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || "Failed to start workflow");
      }

      const newScan = await res.json();
      await fetchWorkflowsAndApprovals();
      return newScan;
    } catch (err: any) {
      throw err;
    } finally {
      setTriggeringScan(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatLoading) return;

    const userText = input;
    setInput("");
    setMessages((prev) => [...prev, { sender: "user", text: userText, timestamp: new Date() }]);
    setChatLoading(true);

    // Foundation for plain-English query analysis
    setTimeout(async () => {
      const query = userText.toLowerCase();
      let responseText = "";
      let resultsData = null;

      try {
        if (query.includes("gdpr") && (query.includes("run") || query.includes("scan") || query.includes("start"))) {
          responseText = "Launching GDPR compliance scan workflow. Spinning up an ephemeral worker container in the control plane...";
          const scan = await triggerScan("GDPR");
          responseText += `\n\n[System] Workflow launched! ID: ${scan.workflow_id}. State: ${scan.current_state}.`;
          resultsData = scan;
        } else if (query.includes("soc") && (query.includes("run") || query.includes("scan") || query.includes("start"))) {
          responseText = "Initiating SOC 2 compliance check. Analyzing active IAM roles and public bucket metadata...";
          const scan = await triggerScan("SOC2");
          responseText += `\n\n[System] Workflow launched! ID: ${scan.workflow_id}. State: ${scan.current_state}.`;
          resultsData = scan;
        } else if (query.includes("hipaa") && (query.includes("run") || query.includes("scan") || query.includes("start"))) {
          responseText = "Launching HIPAA technical safeguards scan. Checking vector database configuration and data redaction policies...";
          const scan = await triggerScan("HIPAA");
          responseText += `\n\n[System] Workflow launched! ID: ${scan.workflow_id}. State: ${scan.current_state}.`;
          resultsData = scan;
        } else if (query.includes("gate") || query.includes("route")) {
          const res = await fetch("/api/gateways");
          const gateways = await res.json();
          responseText = `I found ${gateways.length} active gateway routes configured for this tenant.`;
          resultsData = gateways;
        } else if (query.includes("approval") || query.includes("hitl")) {
          responseText = `There are currently ${approvals.filter(a => a.status === "PENDING").length} pending approvals requiring authorization.`;
          resultsData = approvals;
        } else if (query.includes("help") || query.includes("command")) {
          responseText = "You can interact with me using plain-English. Here are some commands I understand:\n" +
            "• 'Run GDPR compliance scan'\n" +
            "• 'Start SOC2 audit check'\n" +
            "• 'List configured gateway routes'\n" +
            "• 'Show pending approvals'";
        } else {
          responseText = "I've analyzed your query. I am ready to trigger compliance scans or inspect active configurations. Try typing 'Run GDPR compliance scan' to test the LangGraph workflow engine.";
        }
      } catch (err: any) {
        responseText = `Failed to execute request: ${err.message}`;
      }

      setMessages((prev) => [
        ...prev, 
        { sender: "agent", text: responseText, timestamp: new Date(), results: resultsData }
      ]);
      if (resultsData) {
        setSelectedResult(resultsData);
      }
      setChatLoading(false);
    }, 1000);
  };

  const handleApproveClick = (appr: Approval) => {
    setSelectedApproval(appr);
    setMfaError(null);
    setTotpCode("");
    setShowMfaInput(true);
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApproval) return;
    setApproving(true);
    setMfaError(null);

    try {
      // Find the associated workflow_id
      // In python app/api/v1/endpoints/workflows.py: approve takes workflow_id, not approval_id!
      // So we must lookup the workflow_id for this approval.
      const wf = workflows.find((w) => w.approval_id === selectedApproval.id);
      if (!wf) {
        throw new Error("No active workflow is linked to this approval record");
      }

      const res = await fetch(`/api/workflows/${wf.workflow_id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ totp_code: totpCode }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "MFA validation failed");
      }

      setShowMfaInput(false);
      setSelectedApproval(null);
      await fetchWorkflowsAndApprovals();
    } catch (err: any) {
      setMfaError(err.message || "Could not authorize action");
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async (appr: Approval) => {
    if (!confirm("Are you sure you want to decline this proposed remediation?")) return;
    try {
      const wf = workflows.find((w) => w.approval_id === appr.id);
      if (!wf) throw new Error("No linked workflow found");

      const res = await fetch(`/api/workflows/${wf.workflow_id}/reject`, {
        method: "POST",
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to reject approval");
      }

      await fetchWorkflowsAndApprovals();
    } catch (err: any) {
      alert(err.message || "Error rejecting approval");
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
          Compliance Agent & Orchestrator
          <Sparkles className="w-5 h-5 text-indigo-400 inline-block ml-2.5 animate-pulse" />
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Review automated cloud remediation tasks, initiate framework audits, and interact with the AI compliance controller.
        </p>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (2/3 width) - Chat Interface or Scan Telemetry */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-[#09090d] shadow-2xl flex flex-col min-h-[550px] overflow-hidden">
          
          {/* Header tabs */}
          <div className="px-6 py-4 border-b border-slate-800/80 bg-[#0c0c12]/60 flex items-center justify-between">
            <div className="flex gap-4">
              <button
                onClick={() => setActivePane("chat")}
                className={`text-xs font-bold uppercase tracking-wider transition ${
                  activePane === "chat" ? "text-indigo-400" : "text-slate-500 hover:text-slate-350"
                }`}
              >
                Agent Chat Room
              </button>
              <button
                onClick={() => setActivePane("scans")}
                className={`text-xs font-bold uppercase tracking-wider transition ${
                  activePane === "scans" ? "text-indigo-400" : "text-slate-500 hover:text-slate-350"
                }`}
              >
                Active Scans Ledger
              </button>
            </div>
            
            {chatLoading && (
              <span className="text-[10px] text-slate-500 flex items-center gap-1.5 font-semibold">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                Agent is thinking...
              </span>
            )}
          </div>

          {/* Chat Pane */}
          {activePane === "chat" ? (
            <div className="flex-1 flex flex-col justify-between overflow-hidden">
              {/* Message History */}
              <div className="flex-1 p-6 overflow-y-auto space-y-4 max-h-[380px] min-h-[380px]">
                {messages.map((msg, idx) => (
                  <div 
                    key={idx}
                    className={`flex gap-3 max-w-[85%] ${
                      msg.sender === "user" ? "ml-auto flex-row-reverse" : ""
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center border ${
                      msg.sender === "user" 
                        ? "bg-indigo-650/10 border-indigo-500/20 text-indigo-400" 
                        : "bg-slate-800/40 border-slate-700/60 text-slate-300"
                    }`}>
                      {msg.sender === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>

                    <div className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                      msg.sender === "user"
                        ? "bg-indigo-600/10 border border-indigo-500/20 text-indigo-200 rounded-tr-none"
                        : "bg-slate-850/40 border border-slate-800 text-slate-300 rounded-tl-none"
                    }`}>
                      <pre className="whitespace-pre-wrap font-sans">{msg.text}</pre>
                      {msg.results && (
                        <button
                          onClick={() => setSelectedResult(msg.results)}
                          className="mt-2 text-[10px] font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 underline transition"
                        >
                          View Results JSON
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input */}
              <form onSubmit={handleSend} className="p-4 border-t border-slate-800/80 bg-[#07070a]/40 flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask the Compliance Agent (e.g. 'Run GDPR compliance scan')..."
                  className="flex-1 px-4 py-2.5 rounded-lg bg-[#07070a] border border-slate-800 text-slate-200 text-xs placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition"
                  disabled={chatLoading}
                />
                <button
                  type="submit"
                  disabled={chatLoading || !input.trim()}
                  className="px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg transition disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>
          ) : (
            /* Scans Telemetry Pane */
            <div className="flex-1 p-6 overflow-y-auto max-h-[440px] min-h-[440px]">
              {loading ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500" />
                </div>
              ) : workflows.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-xs flex flex-col items-center">
                  <Activity className="w-8 h-8 text-slate-600 mb-2" />
                  No compliance runs initiated yet.
                </div>
              ) : (
                <div className="space-y-4">
                  {workflows.map((wf) => {
                    const isCompleted = wf.execution_status === "COMPLETED";
                    const isPaused = wf.execution_status === "PAUSED";
                    return (
                      <div key={wf.id} className="p-4 rounded-xl border border-slate-800 bg-[#0c0c12]/40 space-y-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                              {wf.framework} framework
                            </span>
                            <h4 className="font-bold text-slate-200 text-sm mt-1.5 font-mono">{wf.workflow_id}</h4>
                          </div>

                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                            isCompleted 
                              ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" 
                              : isPaused 
                                ? "bg-amber-500/10 border border-amber-500/20 text-amber-400 animate-pulse"
                                : "bg-sky-500/10 border border-sky-500/20 text-sky-400 animate-pulse"
                          }`}>
                            {wf.execution_status}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs pt-2 border-t border-slate-850/60">
                          <div>
                            <p className="text-slate-550 text-[10px]">CURRENT STATE</p>
                            <span className="font-mono text-slate-300 font-semibold">{wf.current_state}</span>
                          </div>
                          <div>
                            <p className="text-slate-550 text-[10px]">RISK SCORE</p>
                            <span className={`font-semibold ${
                              wf.risk_score && wf.risk_score > 0.5 ? "text-red-400" : "text-emerald-400"
                            }`}>
                              {wf.risk_score !== null ? `${(wf.risk_score * 100).toFixed(0)}%` : "N/A"}
                            </span>
                          </div>
                          <div>
                            <p className="text-slate-550 text-[10px]">STARTED AT</p>
                            <span className="text-slate-400 font-mono text-[10px]">
                              {new Date(wf.started_at).toLocaleTimeString()}
                            </span>
                          </div>
                          <div>
                            <p className="text-slate-550 text-[10px]">COMPLETED</p>
                            <span className="text-slate-400 font-mono text-[10px]">
                              {wf.completed_at ? new Date(wf.completed_at).toLocaleTimeString() : "-"}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column (1/3 width) - Pending Approvals (HITL) */}
        <div className="space-y-6">
          
          {/* HITL panel */}
          <div className="rounded-2xl border border-slate-800 bg-[#09090d] shadow-xl p-5 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <ShieldCheck className="w-4.5 h-4.5 text-emerald-400" />
                Human-in-the-Loop Actions
              </h3>
              <p className="text-slate-500 text-[11px] mt-1 leading-normal">
                Remediation adjustments generated by compliance scans that require manual administrator sign-off.
              </p>
            </div>

            <div className="space-y-4">
              {loading ? (
                <div className="flex justify-center py-6">
                  <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-indigo-500" />
                </div>
              ) : approvals.filter(a => a.status === "PENDING").length === 0 ? (
                <div className="py-6 text-center text-slate-500 text-xs flex flex-col items-center">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mb-2" />
                  No actions awaiting approval.
                </div>
              ) : (
                approvals.filter(a => a.status === "PENDING").map((appr) => (
                  <div key={appr.id} className="p-3.5 rounded-xl border border-slate-800 bg-[#0c0c12]/60 space-y-3 hover:border-slate-700/80 transition duration-150">
                    <div>
                      <span className="text-[9px] uppercase font-black px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        {appr.action_type.replace("_", " ")}
                      </span>
                      <h4 className="font-bold text-slate-200 text-xs mt-2">{appr.action_description}</h4>
                      <p className="text-[10px] text-slate-500 mt-1">
                        Expires: {new Date(appr.expires_at).toLocaleTimeString()}
                      </p>
                    </div>

                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={() => handleApproveClick(appr)}
                        className="flex-1 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-[10px] shadow transition active:scale-[0.98]"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(appr)}
                        className="flex-1 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-350 border border-slate-700 text-[10px] font-semibold transition active:scale-[0.98]"
                      >
                        Decline
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Results Details Panel */}
          <div className="rounded-2xl border border-slate-800 bg-[#09090d] shadow-xl p-5 space-y-3">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs font-bold uppercase tracking-wider">
              <Terminal className="w-4 h-4 text-indigo-400" />
              Inspector Details Panel
            </div>
            
            <div className="rounded-lg border border-slate-850 bg-[#07070a] p-3 text-[10px] font-mono text-slate-400 overflow-x-auto min-h-[140px] max-h-[220px]">
              {selectedResult ? (
                <pre>{JSON.stringify(selectedResult, null, 2)}</pre>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-600 text-center italic">
                  Select a workflow result or gateway route in the chat to inspect its telemetry object.
                </div>
              )}
            </div>
          </div>

        </div>

      </div>

      {/* MFA TOTP Challenge Modal */}
      {showMfaInput && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowMfaInput(false)} />
          
          <div className="relative w-full max-w-[400px] rounded-2xl bg-[#0e0e15] border border-slate-800 shadow-2xl p-6 overflow-hidden">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 rounded-full bg-indigo-500/5 blur-[80px] pointer-events-none" />
            
            <div className="flex justify-between items-center mb-6 border-b border-slate-800/80 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                <Lock className="w-4 h-4 text-indigo-400" />
                MFA Identity Authorization
              </h3>
              <button onClick={() => setShowMfaInput(false)} className="text-slate-400 hover:text-white transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            {mfaError && (
              <div className="p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-200 text-xs">
                {mfaError}
              </div>
            )}

            <form onSubmit={handleMfaSubmit} className="space-y-4">
              <p className="text-xs text-slate-400 leading-relaxed">
                Confirm your administrator status. Enter the 6-digit TOTP code from your authenticator app (or backup recovery code).
              </p>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                  TOTP Code / Backup Code
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-650">
                    <KeyRound className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    required
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value)}
                    placeholder="Enter code"
                    className="w-full pl-10 pr-4 py-2 rounded-lg bg-[#07070a] border border-slate-800 text-slate-200 text-xs font-mono placeholder-slate-700 focus:outline-none focus:border-indigo-500/80 transition text-center tracking-widest"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-slate-850 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowMfaInput(false)}
                  className="px-4 py-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-800 text-slate-350 font-semibold text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={approving || !totpCode}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg transition disabled:opacity-50 flex items-center gap-1.5"
                >
                  {approving ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    "Authorize Action"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
