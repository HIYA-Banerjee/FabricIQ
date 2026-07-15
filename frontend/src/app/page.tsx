"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, Legend, LineChart, Line, CartesianGrid
} from "recharts";
import { 
  AlertTriangle, CheckCircle, Flame, Activity, 
  Settings, Users, ShoppingBag, ShieldAlert, RefreshCw
} from "lucide-react";

interface Machine {
  id: string;
  name: string;
  type: string;
  status: string;
  failure_prob: number;
}

interface KPIs {
  total_orders: number;
  orders_in_progress: number;
  orders_completed: number;
  high_risk_orders: number;
  on_time_rate: number;
  avg_machine_utilization: number;
  avg_worker_productivity: number;
}

export default function Dashboard() {
  const [tenant, setTenant] = useState("factory_alpha");
  const [kpis, setKpis] = useState<KPIs>({
    total_orders: 0,
    orders_in_progress: 0,
    orders_completed: 0,
    high_risk_orders: 0,
    on_time_rate: 0,
    avg_machine_utilization: 0,
    avg_worker_productivity: 0,
  });
  const [machines, setMachines] = useState<Machine[]>([]);
  const [materials, setMaterials] = useState<any[]>([]);
  const [ordersProgressData, setOrdersProgressData] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<string[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  const fetchDashboardData = async (currentTenant: string) => {
    try {
      const resp = await fetch("http://localhost:8000/api/v1/analytics", {
        headers: { "X-Tenant-ID": currentTenant }
      });
      if (resp.ok) {
        const data = await resp.json();
        setKpis(data.kpis);
        setMachines(data.machines.list || []);
        
        // Format materials pie data
        const matData = Object.entries(data.materials || {}).map(([name, val]) => ({
          name,
          value: val
        }));
        setMaterials(matData);

        // Fetch active orders to plot chart
        fetchOrdersProgress(currentTenant);
      }
    } catch (e) {
      console.error("Failed to load dashboard statistics:", e);
    }
  };

  const fetchOrdersProgress = async (currentTenant: string) => {
    try {
      // Mock progress data for charts or run predictions to get list
      const resp = await fetch("http://localhost:8000/api/v1/predictions/batch", {
        method: "POST",
        headers: { "X-Tenant-ID": currentTenant }
      });
      if (resp.ok) {
        const data = await resp.json();
        const formatted = (data.predictions || []).slice(0, 7).map((p: any) => ({
          name: p.order_id.replace(`ORD-${currentTenant}-`, ""),
          progress: Math.round(p.top_features.progress * 100),
          remaining: Math.round((1 - p.top_features.progress) * 100),
          risk: p.probability
        }));
        setOrdersProgressData(formatted);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSyncPredictions = async () => {
    setIsSyncing(true);
    await fetchDashboardData(tenant);
    setIsSyncing(false);
  };

  useEffect(() => {
    const handleTenantChange = () => {
      const activeTenant = localStorage.getItem("tenant_id") || "factory_alpha";
      setTenant(activeTenant);
      fetchDashboardData(activeTenant);
    };

    const handleWsNotification = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail && detail.message) {
        setNotifications((prev) => [detail.message, ...prev.slice(0, 4)]);
      }
    };

    // Load initial tenant
    const initTenant = localStorage.getItem("tenant_id") || "factory_alpha";
    setTenant(initTenant);
    fetchDashboardData(initTenant);

    window.addEventListener("tenantChanged", handleTenantChange);
    window.addEventListener("wsNotification", handleWsNotification);
    
    return () => {
      window.removeEventListener("tenantChanged", handleTenantChange);
      window.removeEventListener("wsNotification", handleWsNotification);
    };
  }, [tenant]);

  // Recharts colors
  const COLORS = ["#8B5CF6", "#3B82F6", "#10B981", "#F59E0B", "#EF4444"];

  const getStatusColorClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "running": return "bg-emerald-500 shadow-[0_0_12px_#10b981]";
      case "idle": return "bg-blue-500 shadow-[0_0_12px_#3b82f6]";
      case "maintenance": return "bg-amber-500 shadow-[0_0_12px_#f59e0b]";
      case "error": return "bg-red-500 shadow-[0_0_12px_#ef4444]";
      default: return "bg-gray-500";
    }
  };

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex justify-between items-center bg-white/5 border border-white/5 rounded-2xl p-6 glass-panel">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-wide">
            Factory Floor Analytics
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Real-time telemetry, delay risk probability projections, and digital twin monitoring.
          </p>
        </div>
        <button
          onClick={handleSyncPredictions}
          disabled={isSyncing}
          className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-semibold shadow-md active:scale-95 transition-all duration-150"
        >
          <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
          {isSyncing ? "Evaluating Risks..." : "Recalculate AI Predictions"}
        </button>
      </div>

      {/* Live Warnings Banner */}
      {notifications.length > 0 && (
        <div className="bg-red-950/20 border border-red-500/20 rounded-2xl p-4 flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-red-400 animate-bounce shrink-0" />
          <div className="flex-1">
            <span className="text-[10px] uppercase font-extrabold tracking-widest text-red-400 block">
              SYSTEM CRITICAL EVENT
            </span>
            <span className="text-xs text-gray-300 font-mono">{notifications[0]}</span>
          </div>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="glass-panel p-5 relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start">
              <span className="text-xs uppercase font-bold text-gray-400 tracking-wider">Total Active Orders</span>
              <ShoppingBag className="w-5 h-5 text-violet-400" />
            </div>
            <div className="text-3xl font-extrabold text-white mt-3">{kpis.total_orders}</div>
          </div>
          <div className="text-[10px] text-gray-500 mt-2">Currently loaded in queue</div>
        </div>

        {/* KPI 2 */}
        <div className={`glass-panel p-5 relative overflow-hidden flex flex-col justify-between border ${
          kpis.high_risk_orders > 0 ? "border-red-500/30 glow-border-purple" : ""
        }`}>
          <div>
            <div className="flex justify-between items-start">
              <span className="text-xs uppercase font-bold text-gray-400 tracking-wider">High Risk Orders</span>
              <AlertTriangle className={`w-5 h-5 ${kpis.high_risk_orders > 0 ? "text-red-400 animate-pulse" : "text-gray-400"}`} />
            </div>
            <div className={`text-3xl font-extrabold mt-3 ${kpis.high_risk_orders > 0 ? "text-red-400 glow-text-purple" : "text-white"}`}>
              {kpis.high_risk_orders}
            </div>
          </div>
          <div className="text-[10px] text-gray-500 mt-2">Predicted delay likelihood &gt; 70%</div>
        </div>

        {/* KPI 3 */}
        <div className="glass-panel p-5 relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start">
              <span className="text-xs uppercase font-bold text-gray-400 tracking-wider">Loom Utilization</span>
              <Activity className="w-5 h-5 text-violet-400" />
            </div>
            <div className="text-3xl font-extrabold text-white mt-3">{kpis.avg_machine_utilization}%</div>
          </div>
          <div className="text-[10px] text-gray-500 mt-2">Average active run workload</div>
        </div>

        {/* KPI 4 */}
        <div className="glass-panel p-5 relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start">
              <span className="text-xs uppercase font-bold text-gray-400 tracking-wider">Shift Productivity</span>
              <Users className="w-5 h-5 text-violet-400" />
            </div>
            <div className="text-3xl font-extrabold text-white mt-3">{kpis.avg_worker_productivity}%</div>
          </div>
          <div className="text-[10px] text-gray-500 mt-2">Labor efficiency average</div>
        </div>
      </div>

      {/* Main Row: Twin & In Progress orders */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Digital Twin Map */}
        <div className="lg:col-span-2 glass-panel p-6 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center border-b border-white/5 pb-4">
              <h3 className="font-bold text-base text-white tracking-wide">
                LoomSense Digital Twin Workspace
              </h3>
              <span className="text-[10px] bg-violet-950/60 border border-violet-500/20 text-violet-400 px-2 py-0.5 rounded font-mono uppercase tracking-widest">
                Active Telemetry
              </span>
            </div>
            
            {/* Machine Layout Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
              {machines.map((m) => (
                <div key={m.id} className="p-4 bg-slate-900/60 border border-white/5 rounded-xl flex items-center justify-between">
                  <div className="space-y-1">
                    <span className="text-xs font-bold text-white block">{m.name}</span>
                    <span className="text-[10px] text-gray-500 block uppercase tracking-wider">{m.type} Loom</span>
                    {/* Predictive Failure prob */}
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span className="text-[9px] text-gray-400">Failure Risk:</span>
                      <span className={`text-[9px] font-bold ${m.failure_prob > 0.6 ? "text-red-400 animate-pulse" : "text-gray-300"}`}>
                        {Math.round(m.failure_prob * 100)}%
                      </span>
                    </div>
                  </div>
                  <span className={`w-3.5 h-3.5 rounded-full ${getStatusColorClass(m.status)}`} title={`Status: ${m.status}`} />
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-white/5 flex gap-4 text-[10px] text-gray-400 justify-end">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" /> Running
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-[0_0_8px_#3b82f6]" /> Idle
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-[0_0_8px_#f59e0b]" /> Maintenance
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_8px_#ef4444]" /> Error
            </div>
          </div>
        </div>

        {/* Material Distribution Card */}
        <div className="glass-panel p-6 flex flex-col justify-between">
          <h3 className="font-bold text-base text-white tracking-wide border-b border-white/5 pb-4">
            Material Load Demands
          </h3>
          <div className="h-[250px] w-full flex items-center justify-center mt-4">
            {materials.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={materials}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {materials.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#0f0c1b", borderColor: "rgba(139, 92, 246, 0.2)", borderRadius: "8px" }}
                    itemStyle={{ color: "#f3f4f6", fontSize: "12px" }}
                  />
                  <Legend 
                    wrapperStyle={{ fontSize: "11px", color: "#9ca3af" }}
                    verticalAlign="bottom"
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <span className="text-xs text-gray-500">No active stock demands.</span>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: In-Progress Orders Delay Probability */}
      <div className="glass-panel p-6">
        <h3 className="font-bold text-base text-white tracking-wide border-b border-white/5 pb-4 mb-6">
          Order Delay Risk Analytics (XGBoost Predictions)
        </h3>
        <div className="h-[280px] w-full">
          {ordersProgressData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ordersProgressData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={11} />
                <YAxis stroke="#9ca3af" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "#0f0c1b", borderColor: "rgba(139, 92, 246, 0.2)", borderRadius: "8px" }}
                  itemStyle={{ fontSize: "12px" }}
                />
                <Bar dataKey="progress" stackId="a" fill="#8B5CF6" name="Progress (%)" radius={[0, 0, 0, 0]} />
                <Bar dataKey="remaining" stackId="a" fill="rgba(255,255,255,0.05)" name="Remaining (%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center">
              <span className="text-xs text-gray-500">Evaluating active order queue. Run 'Recalculate AI Predictions' above.</span>
            </div>
          )}
        </div>
        
        {/* Navigation list link */}
        <div className="mt-4 pt-4 border-t border-white/5">
          <label className="text-xs text-gray-400 block mb-2">Inspect individual order explainability factors:</label>
          <div className="flex flex-wrap gap-2">
            {ordersProgressData.map((op) => (
              <Link
                key={op.name}
                href={`/orders/ORD-${tenant}-${op.name}`}
                className="px-3 py-1.5 bg-slate-900 border border-white/5 hover:border-violet-500/30 rounded-lg text-xs font-mono text-gray-300 hover:text-violet-400 hover:bg-violet-950/10 transition-colors"
              >
                ORD-{op.name} (Risk: {Math.round(op.risk * 100)}%)
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
