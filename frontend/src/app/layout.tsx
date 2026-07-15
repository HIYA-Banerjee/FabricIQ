"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  CalendarClock, 
  ScanQrCode, 
  History, 
  Cpu, 
  MessageSquare,
  Network
} from "lucide-react";
import "./globals.css";
import AIAssistant from "@/components/AIAssistant";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [tenant, setTenant] = useState("factory_alpha");
  const [wsStatus, setWsStatus] = useState("disconnected");

  useEffect(() => {
    // Sync tenant with local storage for HTTP requests
    localStorage.setItem("tenant_id", tenant);
    // Dispatch event to notify child components
    window.dispatchEvent(new Event("tenantChanged"));
  }, [tenant]);

  useEffect(() => {
    // Setup WebSocket connection to backend
    const ws = new WebSocket("ws://localhost:8000/ws");
    
    ws.onopen = () => {
      setWsStatus("connected");
      console.log("Dashboard connected to LoomSense WebSocket bus.");
    };
    
    ws.onclose = () => {
      setWsStatus("disconnected");
      console.log("Dashboard disconnected from WebSocket.");
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        console.log("WebSocket event received:", payload);
        // Custom event to broadcast websocket signals to pages
        const wsEvent = new CustomEvent("wsNotification", { detail: payload });
        window.dispatchEvent(wsEvent);
      } catch (e) {
        console.error(e);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const navItems = [
    { name: "Executive Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Simulation & Scheduler", href: "/scheduler", icon: CalendarClock },
    { name: "Invoice OCR Ingestion", href: "/ocr", icon: ScanQrCode },
  ];

  return (
    <html lang="en">
      <head>
        <title>LoomSense AI - Production Intelligence Platform</title>
        <meta name="description" content="AI-driven decision support layer for textile manufacturing." />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="flex h-screen overflow-hidden">
        {/* Navigation Sidebar */}
        <aside className="w-72 glass-panel m-4 mr-0 flex flex-col justify-between border-r border-violet-950/20">
          <div>
            {/* Logo */}
            <div className="p-6 flex items-center gap-3 border-b border-white/5">
              <Cpu className="w-8 h-8 text-violet-400 glow-text-purple" />
              <div>
                <h1 className="font-bold text-lg tracking-wider bg-gradient-to-r from-violet-200 to-indigo-200 bg-clip-text text-transparent">
                  LoomSense AI
                </h1>
                <p className="text-[10px] text-violet-400 font-semibold tracking-widest uppercase">
                  Industry 4.0 layer
                </p>
              </div>
            </div>

            {/* Tenant Switcher */}
            <div className="p-4 border-b border-white/5 bg-violet-950/10">
              <label className="text-[10px] uppercase font-bold text-violet-300 tracking-wider block mb-2">
                Active Tenant Factory
              </label>
              <select
                value={tenant}
                onChange={(e) => setTenant(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-sm text-gray-200 focus:outline-none focus:border-violet-500"
              >
                <option value="factory_alpha">Factory Alpha (Loom Group)</option>
                <option value="factory_beta">Factory Beta (Dyeing Facility)</option>
              </select>
            </div>

            {/* Menu Links */}
            <nav className="p-4 space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-all duration-200 ${
                      isActive
                        ? "bg-violet-600/35 border border-violet-500/50 text-white font-medium shadow-md shadow-violet-950/30"
                        : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? "text-violet-400" : "text-gray-400"}`} />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Footer statuses */}
          <div className="p-4 border-t border-white/5 space-y-3 bg-violet-950/5">
            {/* Live Indicator */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-gray-400">
                <Network className="w-4 h-4 text-violet-400" />
                <span>Live Event Stream</span>
              </div>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-medium border ${
                wsStatus === "connected"
                  ? "bg-emerald-950/40 border-emerald-500/50 text-emerald-400"
                  : "bg-red-950/40 border-red-500/50 text-red-400"
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${wsStatus === "connected" ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`} />
                {wsStatus === "connected" ? "Connected" : "Offline"}
              </span>
            </div>
            
            <div className="text-[10px] text-gray-500 text-center">
              LoomSense AI platform v1.0.0
            </div>
          </div>
        </aside>

        {/* Content Pane */}
        <main className="flex-1 flex flex-col h-full overflow-hidden p-4">
          <div className="flex-1 overflow-y-auto pr-1">
            {children}
          </div>
        </main>

        {/* Floating conversational Assistant */}
        <AIAssistant />
      </body>
    </html>
  );
}
