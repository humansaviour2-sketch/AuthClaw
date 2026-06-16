import React from "react";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Console Settings</h1>
        <p className="text-slate-400 text-sm mt-1">
          Manage tenant members, roles, API keys, and platform preferences.
        </p>
      </div>

      <div className="relative overflow-hidden rounded-2xl bg-[#09090d] border border-slate-800 p-8 flex flex-col items-center justify-center text-center min-h-[300px] shadow-lg">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 rounded-full bg-indigo-500/5 blur-[80px] pointer-events-none" />
        
        <div className="w-12 h-12 rounded-xl bg-slate-800/40 border border-slate-700/60 flex items-center justify-center mb-4 text-indigo-400">
          <Settings className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-semibold text-slate-200">Tenant Settings</h3>
        <p className="text-slate-500 text-sm max-w-sm mt-2">
          API Key creation and revocation, user role mapping, and MFA toggle settings will be fully integrated during Phase 12.
        </p>
      </div>
    </div>
  );
}
