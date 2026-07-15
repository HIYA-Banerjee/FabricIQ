"use client";

import React, { useState } from "react";
import { Upload, FileText, CheckCircle, ShieldCheck, Sparkles, RefreshCw } from "lucide-react";

interface OCRData {
  order_id: string;
  supplier_name: string;
  material_type: string;
  quantity: number;
  invoice_date: string;
  expected_delivery_date: string;
}

export default function OCRScanner() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRData | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestLog, setIngestLog] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setOcrResult(null);
      setIngestLog("");
    }
  };

  const handleScan = async () => {
    if (!selectedFile) return;
    setIsScanning(true);
    setIngestLog("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const resp = await fetch("http://localhost:8000/api/v1/ocr/scan", {
        method: "POST",
        body: formData
      });
      if (resp.ok) {
        const result = await resp.json();
        setOcrResult(result.data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsScanning(false);
    }
  };

  const handleCommitIngest = async () => {
    if (!ocrResult) return;
    setIsIngesting(true);
    
    // Simulate mapping extracted fields to CSV string for IngestionService
    const tenantId = localStorage.getItem("tenant_id") || "factory_alpha";
    const csvHeader = "id,customer,material_type,quantity,start_date,due_date\n";
    const csvRow = `${ocrResult.order_id},${ocrResult.supplier_name},${ocrResult.material_type},${ocrResult.quantity},${ocrResult.invoice_date},${ocrResult.expected_delivery_date}\n`;
    
    try {
      const blob = new Blob([csvHeader + csvRow], { type: "text/csv" });
      const formData = new FormData();
      formData.append("file", blob, "ocr_extracted.csv");

      const resp = await fetch("http://localhost:8000/api/v1/ingestion/upload", {
        method: "POST",
        headers: { "X-Tenant-ID": tenantId },
        body: formData
      });

      if (resp.ok) {
        const logData = await resp.json();
        if (logData.success) {
          setIngestLog(`Successfully ingested Order ${ocrResult.order_id} into ${tenantId} database.`);
          setOcrResult(null);
          setSelectedFile(null);
        } else {
          setIngestLog(`Ingestion warnings: ${logData.errors.join(", ")}`);
        }
      }
    } catch (e) {
      console.error(e);
      setIngestLog("Network failure connecting to ingestion service.");
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white/5 border border-white/5 rounded-2xl p-6 glass-panel">
        <h2 className="text-2xl font-bold text-white tracking-wide">
          OCR Invoice Ingestion Engine
        </h2>
        <p className="text-gray-400 text-sm mt-1">
          Scan paper challans, supplier invoices, and purchase orders to automatically extract and register active demands.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload card */}
        <div className="glass-panel p-6 border border-white/5 flex flex-col justify-between h-[360px]">
          <div>
            <div className="border-b border-white/5 pb-3 mb-6">
              <h3 className="font-bold text-sm text-white">Upload Documents</h3>
            </div>
            
            {/* Dropzone */}
            <div className="border border-dashed border-violet-500/20 rounded-xl p-8 hover:bg-violet-950/5 hover:border-violet-500/40 transition-colors flex flex-col items-center justify-center gap-3 relative cursor-pointer group">
              <input
                type="file"
                onChange={handleFileChange}
                accept="image/*,.pdf,.txt"
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Upload className="w-10 h-10 text-violet-400 group-hover:scale-110 transition-transform" />
              <div className="text-center">
                <span className="text-xs font-bold text-gray-200 block">
                  {selectedFile ? selectedFile.name : "Select Invoice image / Challan PDF"}
                </span>
                <span className="text-[10px] text-gray-500 block mt-1">
                  Supports PNG, JPG, PDF, TXT (Max 5MB)
                </span>
              </div>
            </div>
          </div>

          {selectedFile && !ocrResult && (
            <button
              onClick={handleScan}
              disabled={isScanning}
              className="w-full bg-violet-600 hover:bg-violet-700 text-white rounded-xl py-2.5 text-xs font-semibold flex items-center justify-center gap-2"
            >
              {isScanning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Running OCR Model...
                </>
              ) : (
                "Scan & Extract Invoice Fields"
              )}
            </button>
          )}
        </div>

        {/* OCR Result card */}
        <div className="glass-panel p-6 border border-white/5 min-h-[360px] flex flex-col justify-between">
          <div>
            <div className="border-b border-white/5 pb-3 mb-6">
              <h3 className="font-bold text-sm text-white">Extracted Metadata</h3>
            </div>

            {ocrResult ? (
              <div className="space-y-4 font-mono text-xs text-gray-300">
                <div className="flex justify-between border-b border-white/5 py-2">
                  <span className="text-gray-500">Order ID:</span>
                  <span className="text-white font-bold">{ocrResult.order_id}</span>
                </div>
                <div className="flex justify-between border-b border-white/5 py-2">
                  <span className="text-gray-500">Supplier:</span>
                  <span className="text-white font-bold">{ocrResult.supplier_name}</span>
                </div>
                <div className="flex justify-between border-b border-white/5 py-2">
                  <span className="text-gray-500">Material Type:</span>
                  <span className="text-white font-bold">{ocrResult.material_type}</span>
                </div>
                <div className="flex justify-between border-b border-white/5 py-2">
                  <span className="text-gray-500">Quantity:</span>
                  <span className="text-white font-bold">{ocrResult.quantity} units</span>
                </div>
                <div className="flex justify-between border-b border-white/5 py-2">
                  <span className="text-gray-500">Challan Date:</span>
                  <span className="text-white font-bold">{ocrResult.invoice_date}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-gray-500">Target Delivery Date:</span>
                  <span className="text-white font-bold">{ocrResult.expected_delivery_date}</span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center text-gray-500 text-xs h-[180px]">
                <FileText className="w-8 h-8 text-gray-700 mb-2" />
                No scan data currently parsed. Upload a document to scan.
              </div>
            )}
          </div>

          {ocrResult && (
            <button
              onClick={handleCommitIngest}
              disabled={isIngesting}
              className="w-full bg-violet-600 hover:bg-violet-700 text-white rounded-xl py-2.5 text-xs font-semibold flex items-center justify-center gap-2 shadow-md shadow-violet-950/20"
            >
              {isIngesting ? "Running Ingestion Validation..." : "Commit Extracted Order to Ingestion Queue"}
            </button>
          )}

          {ingestLog && (
            <div className="mt-4 p-3 bg-emerald-950/30 border border-emerald-500/20 rounded-xl text-[11px] text-emerald-400 font-mono flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{ingestLog}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
