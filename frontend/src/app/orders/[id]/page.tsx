"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { BarChart, Bar, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { 
  ArrowLeft, ShieldAlert, Sparkles, CheckCircle2, 
  Hourglass, AlertTriangle, Hammer, Truck, Activity 
} from "lucide-react";

interface Prediction {
  order_id: string;
  probability: number;
  risk: string;
  top_features: any;
  shap_values: Record<string, number>;
  recommendations: string[];
  created_at: string;
  model_version: string;
}

export default function OrderDetails() {
  const params = useParams();
  const orderId = params.id as string;
  const [tenant, setTenant] = useState("factory_alpha");
  const [data, setData] = useState<Prediction | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const activeTenant = localStorage.getItem("tenant_id") || "factory_alpha";
    setTenant(activeTenant);

    const fetchOrderPrediction = async () => {
      try {
        const resp = await fetch(`http://localhost:8000/api/v1/predictions/order/${orderId}`, {
          headers: { "X-Tenant-ID": activeTenant }
        });
        if (resp.ok) {
          const resJson = await resp.json();
          setData(resJson);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrderPrediction();
  }, [orderId]);

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center text-sm font-mono text-gray-400">
        Loading SHAP explanation models...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Link href="/" className="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Return to Dashboard
        </Link>
        <div className="glass-panel p-8 text-center text-gray-400 text-sm">
          No prediction record found for Order '{orderId}'. Please run predictions from the dashboard first.
        </div>
      </div>
    );
  }

  // Format SHAP data for Recharts
  // SHAP input: Record<string, number> -> [{ name: string, impact: number }]
  const shapChartData = Object.entries(data.shap_values).map(([name, val]) => ({
    name,
    impact: Math.round(val * 100),
    fill: val > 0 ? "#EF4444" : "#10B981" // Red increases risk, Green decreases it
  }));

  const getRiskIcon = (risk: string) => {
    switch (risk.toLowerCase()) {
      case "high": return <AlertTriangle className="w-8 h-8 text-red-400 animate-pulse" />;
      case "medium": return <Hourglass className="w-8 h-8 text-amber-400" />;
      default: return <CheckCircle2 className="w-8 h-8 text-emerald-400" />;
    }
  };

  const getRiskBadgeClass = (risk: string) => {
    switch (risk.toLowerCase()) {
      case "high": return "bg-red-950/40 border-red-500/50 text-red-400";
      case "medium": return "bg-amber-950/40 border-amber-500/50 text-amber-400";
      default: return "bg-emerald-950/40 border-emerald-500/50 text-emerald-400";
    }
  };

  return (
    <div className="space-y-6">
      {/* Return button */}
      <div>
        <Link href="/" className="inline-flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-all">
          <ArrowLeft className="w-4 h-4" /> Back to Factory Map
        </Link>
      </div>

      {/* Main Order Header */}
      <div className="glass-panel p-6 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Order: {data.order_id}</h2>
          <div className="flex gap-4 mt-2 text-xs text-gray-400 font-mono">
            <span>Model: {data.model_version}</span>
            <span>Refreshed: {new Date(data.created_at).toLocaleTimeString()}</span>
          </div>
        </div>
        
        {/* Risk Probability badge */}
        <div className={`px-4 py-3 rounded-2xl border flex items-center gap-3 ${getRiskBadgeClass(data.risk)}`}>
          {getRiskIcon(data.risk)}
          <div>
            <span className="text-[10px] uppercase font-extrabold tracking-widest block opacity-70">
              Delay Risk Status
            </span>
            <span className="text-lg font-extrabold font-mono">
              {Math.round(data.probability * 100)}% ({data.risk} Risk)
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Column 1: Explainability factors (SHAP Waterfall/Bar) */}
        <div className="lg:col-span-2 glass-panel p-6">
          <div className="border-b border-white/5 pb-4 mb-6">
            <h3 className="font-bold text-base text-white tracking-wide">
              Explainable AI (SHAP Factors)
            </h3>
            <p className="text-xs text-gray-400 mt-1">
              Positive values indicate drivers that increase delivery delay risk. Negative values decrease risk.
            </p>
          </div>
          
          <div className="h-[300px] w-full">
            {shapChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={shapChartData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                >
                  <XAxis type="number" stroke="#9ca3af" fontSize={11} />
                  <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={10} width={130} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f0c1b", borderColor: "rgba(255,255,255,0.08)", borderRadius: "8px" }}
                    itemStyle={{ fontSize: "11px" }}
                  />
                  <ReferenceLine x={0} stroke="rgba(255,255,255,0.2)" />
                  <Bar dataKey="impact" name="Impact score (%)" radius={[0, 4, 4, 0]}>
                    {shapChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-gray-500">
                No explainability logs registered.
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Prescriptive Actions & Timeline */}
        <div className="space-y-6">
          {/* Actions */}
          <div className="glass-panel p-6 border border-violet-500/20 shadow-md shadow-violet-950/20">
            <div className="flex items-center gap-2 border-b border-white/5 pb-3">
              <Sparkles className="w-5 h-5 text-violet-400 glow-text-purple" />
              <h3 className="font-bold text-sm text-white">AI Copilot Recommendations</h3>
            </div>
            <div className="mt-4 space-y-3">
              {data.recommendations.map((rec, idx) => (
                <div key={idx} className="p-3 bg-violet-950/20 border border-violet-500/10 rounded-xl flex items-start gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-400 mt-1.5 shrink-0" />
                  <p className="text-xs text-gray-300 leading-normal">{rec}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline details */}
          <div className="glass-panel p-6">
            <h3 className="font-bold text-sm text-white border-b border-white/5 pb-3">
              Production Stage Progress
            </h3>
            
            {/* Simple stages */}
            <div className="mt-4 space-y-4">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Quantity Demanded:</span>
                <span className="font-bold text-white">{data.top_features.quantity} units</span>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>Progress Completed:</span>
                <span className="font-bold text-white">{Math.round(data.top_features.progress * 100)}%</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-900 border border-white/5 h-3.5 rounded-full overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-violet-600 to-indigo-600 h-full rounded-full"
                  style={{ width: `${data.top_features.progress * 100}%` }}
                />
              </div>

              {/* Dynamic steps indicator */}
              <div className="relative border-l border-white/10 ml-2 pl-6 space-y-4 mt-6">
                <div className="relative">
                  <span className="absolute -left-8 top-0.5 w-4 h-4 rounded-full bg-violet-600 flex items-center justify-center">
                    <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                  </span>
                  <div className="text-xs">
                    <span className="font-bold text-gray-200 block">Spinning & Weaving</span>
                    <span className="text-[10px] text-violet-400 font-semibold block">Completed Stage</span>
                  </div>
                </div>
                <div className="relative">
                  <span className="absolute -left-8 top-0.5 w-4 h-4 rounded-full bg-violet-600 flex items-center justify-center animate-pulse">
                    <Activity className="w-3.5 h-3.5 text-white" />
                  </span>
                  <div className="text-xs">
                    <span className="font-bold text-gray-200 block">Dyeing & Quality QC</span>
                    <span className="text-[10px] text-amber-400 font-semibold block">Active Processing Stage</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
