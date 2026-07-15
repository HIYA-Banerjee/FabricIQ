"use client";

import React, { useState, useEffect } from "react";
import { 
  Settings, Play, AlertTriangle, CheckCircle, 
  HelpCircle, ShieldAlert, Cpu, Sparkles, TrendingUp 
} from "lucide-react";

interface ScheduledJob {
  order_id: string;
  task_name: string;
  machine_id: string;
  start_hour: number;
  end_hour: number;
  duration_hours: number;
}

interface SimulationResult {
  scenario_description: string;
  original_delayed_orders: number;
  simulated_delayed_orders: number;
  original_makespan_hours: number;
  simulated_makespan_hours: number;
  revenue_at_risk: number;
  mitigation_actions: string[];
  impacted_order_ids: string[];
}

export default function SchedulerWorkspace() {
  const [tenant, setTenant] = useState("factory_alpha");
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [machines, setMachines] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  
  // Scenario forms state
  const [selectedMachine, setSelectedMachine] = useState("");
  const [selectedSupplier, setSelectedSupplier] = useState("");
  const [supplierDelayDays, setSupplierDelayDays] = useState(0);
  const [rushQty, setRushQty] = useState(0);
  const [rushMaterial, setRushMaterial] = useState("Cotton");

  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  const fetchBaselineSchedule = async (currentTenant: string) => {
    setIsLoading(true);
    try {
      // Fetch schedule timeline
      const resp = await fetch("http://localhost:8000/api/v1/optimization/schedule", {
        headers: { "X-Tenant-ID": currentTenant }
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.success) {
          setJobs(data.scheduled_jobs || []);
        }
      }

      // Fetch directories to populate form dropdowns
      const dirResp = await fetch("http://localhost:8000/api/v1/analytics", {
        headers: { "X-Tenant-ID": currentTenant }
      });
      if (dirResp.ok) {
        const dirData = await dirResp.json();
        setMachines(dirData.machines.list || []);
        setSuppliers(dirData.suppliers || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const handleTenantChange = () => {
      const activeTenant = localStorage.getItem("tenant_id") || "factory_alpha";
      setTenant(activeTenant);
      setSimResult(null); // Clear previous scenarios
      fetchBaselineSchedule(activeTenant);
    };

    const initTenant = localStorage.getItem("tenant_id") || "factory_alpha";
    setTenant(initTenant);
    fetchBaselineSchedule(initTenant);

    window.addEventListener("tenantChanged", handleTenantChange);
    return () => {
      window.removeEventListener("tenantChanged", handleTenantChange);
    };
  }, [tenant]);

  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSimulating(true);
    
    try {
      const resp = await fetch("http://localhost:8000/api/v1/simulator/simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenant
        },
        body: JSON.stringify({
          machine_id_outage: selectedMachine || null,
          supplier_id_delay: selectedSupplier || null,
          supplier_delay_days: Number(supplierDelayDays),
          rush_order_qty: Number(rushQty),
          rush_order_material: rushMaterial
        })
      });

      if (resp.ok) {
        const result = await resp.json();
        setSimResult(result);
        
        // Broadcast critical alerts to WebSockets if simulation causes new delays
        if (result.simulated_delayed_orders > result.original_delayed_orders) {
          const ws = new WebSocket("ws://localhost:8000/ws");
          ws.onopen = () => {
            ws.send(JSON.stringify({
              type: "critical_warning",
              message: `Scenario Simulation Warning: Outage or delays threaten ${result.simulated_delayed_orders} orders. Revenue risk: $${result.revenue_at_risk}`
            }));
            setTimeout(() => ws.close(), 500);
          };
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleClearScenario = () => {
    setSelectedMachine("");
    setSelectedSupplier("");
    setSupplierDelayDays(0);
    setRushQty(0);
    setSimResult(null);
    fetchBaselineSchedule(tenant);
  };

  // Group scheduled jobs by machine ID to draw Gantt
  const getJobsForMachine = (macId: string) => {
    return jobs.filter((j) => j.machine_id === macId);
  };

  const taskColors: Record<string, string> = {
    "Spinning": "bg-violet-600 border-violet-500 text-white",
    "Weaving": "bg-blue-600 border-blue-500 text-white",
    "Dyeing": "bg-emerald-600 border-emerald-500 text-white",
    "QC": "bg-amber-600 border-amber-500 text-white"
  };

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="bg-white/5 border border-white/5 rounded-2xl p-6 glass-panel">
        <h2 className="text-2xl font-bold text-white tracking-wide">
          Production Scheduler & Scenario Workspace
        </h2>
        <p className="text-gray-400 text-sm mt-1">
          Formulate flexible job shop constraints via Google OR-Tools and execute what-if risk simulations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Hand side: Simulator Form panel */}
        <div className="glass-panel p-6 border border-white/5 flex flex-col justify-between">
          <form onSubmit={handleRunSimulation} className="space-y-6">
            <div className="border-b border-white/5 pb-3">
              <h3 className="font-bold text-sm text-white">Simulation Parameters</h3>
            </div>

            {/* Input 1: Machine Breakdown */}
            <div>
              <label className="text-xs text-gray-300 font-medium block mb-2">
                Simulate Machine Outage
              </label>
              <select
                value={selectedMachine}
                onChange={(e) => setSelectedMachine(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-xs text-gray-200 focus:outline-none focus:border-violet-500"
              >
                <option value="">No Outages (Healthy Floor)</option>
                {machines.map((m) => (
                  <option key={m.id} value={m.id}>
                    Outage: {m.name} ({m.type})
                  </option>
                ))}
              </select>
            </div>

            {/* Input 2: Supplier Shipment delays */}
            <div className="space-y-3">
              <label className="text-xs text-gray-300 font-medium block">
                Simulate Supplier Delay
              </label>
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={selectedSupplier}
                  onChange={(e) => setSelectedSupplier(e.target.value)}
                  className="bg-slate-900 border border-white/10 rounded-xl p-2.5 text-xs text-gray-200 focus:outline-none focus:border-violet-500"
                >
                  <option value="">No Supplier Delays</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.material})
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  placeholder="Delay days"
                  value={supplierDelayDays || ""}
                  onChange={(e) => setSupplierDelayDays(Math.max(0, Number(e.target.value)))}
                  className="bg-slate-900 border border-white/10 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                />
              </div>
            </div>

            {/* Input 3: Rush Order Injections */}
            <div className="space-y-3">
              <label className="text-xs text-gray-300 font-medium block">
                Inject Rush Order (Demand Spike)
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  placeholder="Qty (e.g. 1500)"
                  value={rushQty || ""}
                  onChange={(e) => setRushQty(Math.max(0, Number(e.target.value)))}
                  className="bg-slate-900 border border-white/10 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                />
                <select
                  value={rushMaterial}
                  onChange={(e) => setRushMaterial(e.target.value)}
                  className="bg-slate-900 border border-white/10 rounded-xl p-2.5 text-xs text-gray-200 focus:outline-none focus:border-violet-500"
                >
                  <option value="Cotton">Cotton</option>
                  <option value="Polyester">Polyester</option>
                  <option value="Silk">Silk</option>
                  <option value="Wool">Wool</option>
                  <option value="Linen">Linen</option>
                </select>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 pt-4">
              <button
                type="submit"
                disabled={isSimulating}
                className="flex-1 bg-violet-600 hover:bg-violet-700 text-white rounded-xl py-2.5 text-xs font-semibold hover:scale-[1.02] active:scale-95 transition-all"
              >
                {isSimulating ? "Running CP-SAT Solver..." : "Solve Scenario Impact"}
              </button>
              {(selectedMachine || selectedSupplier || rushQty > 0 || simResult) && (
                <button
                  type="button"
                  onClick={handleClearScenario}
                  className="px-4 bg-slate-800 border border-white/10 rounded-xl text-gray-400 hover:text-white text-xs font-semibold hover:bg-slate-700"
                >
                  Reset
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Right Hand side: Simulation Results Display */}
        <div className="lg:col-span-2 space-y-6">
          {simResult ? (
            <>
              {/* Scenario metrics comparison cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Delayed count comparison */}
                <div className={`glass-panel p-5 border ${
                  simResult.simulated_delayed_orders > simResult.original_delayed_orders
                    ? "border-red-500/20"
                    : "border-emerald-500/20"
                }`}>
                  <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider block">
                    Delayed Orders Delta
                  </span>
                  <div className="flex items-baseline gap-2 mt-2">
                    <span className="text-2xl font-extrabold text-white">
                      {simResult.simulated_delayed_orders}
                    </span>
                    <span className="text-xs text-gray-500">
                      (Baseline: {simResult.original_delayed_orders})
                    </span>
                  </div>
                </div>

                {/* Makespan delta */}
                <div className="glass-panel p-5">
                  <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider block">
                    Makespan Duration
                  </span>
                  <div className="flex items-baseline gap-2 mt-2">
                    <span className="text-2xl font-extrabold text-white">
                      {simResult.simulated_makespan_hours} hrs
                    </span>
                    <span className="text-xs text-gray-500">
                      (Baseline: {simResult.original_makespan_hours}h)
                    </span>
                  </div>
                </div>

                {/* Revenue-at-risk flash card */}
                <div className={`glass-panel p-5 border ${
                  simResult.revenue_at_risk > 0
                    ? "border-red-500/30 glow-border-purple"
                    : "border-emerald-500/20"
                }`}>
                  <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider block">
                    Revenue-At-Risk
                  </span>
                  <span className={`text-2xl font-extrabold block mt-2 ${
                    simResult.revenue_at_risk > 0 ? "text-red-400 glow-text-purple" : "text-emerald-400"
                  }`}>
                    ${simResult.revenue_at_risk.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Actionable recommendations */}
              <div className="glass-panel p-6 border border-violet-500/20">
                <div className="flex items-center gap-2 border-b border-white/5 pb-3">
                  <Sparkles className="w-5 h-5 text-violet-400 glow-text-purple animate-bounce" />
                  <h4 className="font-bold text-sm text-white">Prescriptive Action Plan</h4>
                </div>
                <div className="mt-4 space-y-2.5">
                  {simResult.mitigation_actions.map((act, idx) => (
                    <div key={idx} className="p-3 bg-violet-950/20 border border-violet-500/10 rounded-xl text-xs text-gray-300">
                      {act}
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="glass-panel p-12 text-center text-gray-400 text-sm h-full flex flex-col justify-center items-center gap-2">
              <Settings className="w-10 h-10 text-violet-400/50 animate-spin" />
              <span>Configure and run a What-If scenario in the simulator sidebar to display optimization analytics.</span>
            </div>
          )}
        </div>
      </div>

      {/* Gantt Timeline View */}
      <div className="glass-panel p-6">
        <h3 className="font-bold text-base text-white border-b border-white/5 pb-4 mb-6">
          Machine Assignment Gantt Chart (OR-Tools Schedule Layout)
        </h3>
        
        {isLoading ? (
          <div className="h-40 flex items-center justify-center text-xs text-gray-400 font-mono">
            Optimizing constraints...
          </div>
        ) : (
          <div className="space-y-4 overflow-x-auto">
            {machines.map((mac) => {
              const macJobs = getJobsForMachine(mac.id);
              return (
                <div key={mac.id} className="flex items-center min-w-[700px] border-b border-white/5 pb-3">
                  {/* Machine label */}
                  <div className="w-40 shrink-0 pr-4">
                    <span className="text-xs font-bold text-white block">{mac.name}</span>
                    <span className="text-[10px] text-gray-500 block uppercase tracking-wider">{mac.type}</span>
                  </div>
                  
                  {/* Timeline block track */}
                  <div className="flex-1 bg-slate-900/60 border border-white/5 h-10 rounded-xl relative flex items-center p-1">
                    {macJobs.map((job, idx) => {
                      // Basic width calculation based on 200 hours scheduling horizon
                      const leftPercent = Math.min(95, (job.start_hour / 200) * 100);
                      const widthPercent = Math.max(8, (job.duration_hours / 200) * 100);
                      return (
                        <div
                          key={idx}
                          style={{
                            left: `${leftPercent}%`,
                            width: `${widthPercent}%`,
                            position: "absolute"
                          }}
                          className={`h-8 border rounded-lg px-2 flex flex-col justify-center text-[9px] font-mono select-none overflow-hidden transition-all duration-300 hover:scale-105 active:scale-95 ${
                            taskColors[job.task_name] || "bg-violet-600 text-white"
                          }`}
                          title={`Order: ${job.order_id} | Step: ${job.task_name} | Hours: ${job.start_hour} - ${job.end_hour}`}
                        >
                          <span className="font-bold truncate">{job.order_id.substring(job.order_id.lastIndexOf("-")+1)}</span>
                          <span className="opacity-80 truncate">{job.duration_hours}h</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
        <div className="mt-4 pt-4 border-t border-white/5 flex gap-4 text-[9px] font-mono text-gray-400 justify-end">
          <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-violet-600" /> Spinning</div>
          <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-blue-600" /> Weaving</div>
          <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-600" /> Dyeing</div>
          <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-amber-600" /> Quality QC</div>
        </div>
      </div>
    </div>
  );
}
