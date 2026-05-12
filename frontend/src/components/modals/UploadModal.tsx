import * as Dialog from '@radix-ui/react-dialog';
import { useQueryClient } from '@tanstack/react-query';
import { AlertCircle, CheckCircle, FileText, Loader2, Upload, X } from 'lucide-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useUploadModal } from '../../hooks/useUploadModal';
import { apiUpload, pollRunStatus, resetData } from '../../lib/api';
import { cn } from '../../lib/cn';

type UploadState = 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error' | 'duplicate';

interface UploadResult {
  run_id: string;
  status: 'accepted' | 'duplicate';
  message: string;
}

const ANALYSIS_STEPS = [
  { id: 0, label: 'Parsing data' },
  { id: 1, label: 'Running financial analysis' },
  { id: 2, label: 'Generating insights' },
];

export function UploadModal() {
  const { isUploadModalOpen, closeModal } = useUploadModal();
  const queryClient = useQueryClient();
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [clearExistingData, setClearExistingData] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<(() => void) | null>(null);

  const reset = useCallback(() => {
    setIsDragging(false);
    setUploadState('idle');
    setFile(null);
    setProgress(0);
    setAnalysisStep(0);
    setErrorMessage('');
    setClearExistingData(false);
    abortRef.current = null;
  }, []);

  useEffect(() => {
    if (!isUploadModalOpen) {
      const t = setTimeout(reset, 300);
      return () => clearTimeout(t);
    }
  }, [isUploadModalOpen, reset]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'text/csv' || droppedFile.name.endsWith('.csv') || droppedFile.name.endsWith('.json')) {
        startUpload(droppedFile);
      } else {
        setErrorMessage('Please upload a CSV or JSON file.');
        setUploadState('error');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      startUpload(e.target.files[0]);
    }
  };

  const startUpload = async (selectedFile: File) => {
    setFile(selectedFile);
    setUploadState('uploading');
    setProgress(0);
    setErrorMessage('');

    try {
      if (clearExistingData) {
        await resetData();
      }

      // ── Real upload to POST /api/v1/run ────────────────────────────────────
      const result = await apiUpload<UploadResult>(selectedFile, (pct) => {
        setProgress(pct);
      });

      if (result.status === 'duplicate') {
        setUploadState('duplicate');
        setTimeout(() => closeModal(), 3000);
        return;
      }

      // ── Poll for pipeline completion ───────────────────────────────────────
      const runId = result.run_id;
      setUploadState('analyzing');
      setAnalysisStep(0);

      let stepTimer = setInterval(() => {
        setAnalysisStep((s) => (s < ANALYSIS_STEPS.length - 1 ? s + 1 : s));
      }, 2000);

      const finalResult = await pollRunStatus(runId, (_status) => {
        // status updates handled by step animation
      });

      clearInterval(stepTimer);

      if (finalResult.status === 'completed') {
        setAnalysisStep(ANALYSIS_STEPS.length - 1);
        setUploadState('complete');
        // Invalidate snapshot and alerts so they refresh with new data
        queryClient.invalidateQueries({ queryKey: ['snapshot'] });
        queryClient.invalidateQueries({ queryKey: ['alerts'] });
        setTimeout(() => closeModal(), 2000);
      } else {
        const msg = finalResult.errorMessage
          ? `Pipeline failed: ${finalResult.errorMessage}`
          : 'The analysis pipeline encountered an error. Please try again.';
        setErrorMessage(msg);
        setUploadState('error');
      }
    } catch (err) {
      setErrorMessage((err as Error).message || 'Upload failed. Is the backend running?');
      setUploadState('error');
    }
  };

  const truncateFilename = (name: string, maxLength = 30) => {
    if (name.length <= maxLength) return name;
    return name.slice(0, maxLength - 3) + '...';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <Dialog.Root open={isUploadModalOpen} onOpenChange={(open) => !open && closeModal()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-[4px] z-50 transition-opacity duration-300 data-[state=closed]:opacity-0 data-[state=open]:opacity-100" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-[520px] -translate-x-1/2 -translate-y-1/2
          bg-bg-elevated border border-border-default rounded-xl shadow-xl p-6
          data-[state=open]:animate-in data-[state=closed]:animate-out
          data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
          data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95
          duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]"
        >
          <div className="flex justify-between items-center mb-6">
            <Dialog.Title className="text-xl font-semibold text-primary">Upload Financial Data</Dialog.Title>
            <Dialog.Close className="text-tertiary hover:text-primary transition-colors">
              <X size={20} />
            </Dialog.Close>
          </div>

          {/* ── Idle: drop zone ─────────────────────────────────────────── */}
          {uploadState === 'idle' && (
            <div className="space-y-4">
              <div
                className={cn(
                  "h-[180px] border-2 border-dashed rounded-lg flex flex-col items-center justify-center transition-all duration-150 cursor-pointer",
                  isDragging
                    ? "border-primary-500 bg-[rgba(59,130,246,0.06)]"
                    : "border-border-default bg-bg-sunken hover:bg-bg-hover hover:border-border-strong"
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click();
                }}
                aria-label="Upload CSV or JSON file"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".csv,.json"
                  className="hidden"
                />
                <Upload
                  size={32}
                  className={cn(
                    "mb-3 transition-transform duration-150",
                    isDragging ? "text-primary-500 scale-110" : "text-tertiary"
                  )}
                />
                <p className="text-base text-primary font-medium">Drag & drop your CSV or JSON here</p>
                <p className="text-sm text-tertiary mt-1">or click to browse</p>
              </div>

              {/* CSV format hint */}
              <details className="text-xs text-tertiary cursor-pointer group">
                <summary className="flex items-center gap-1 hover:text-secondary transition-colors">
                  <FileText size={12} />
                  Expected CSV format
                </summary>
                <div className="mt-2 p-3 bg-bg-sunken rounded-md font-mono text-xs space-y-1">
                  <p className="text-secondary font-semibold">Required columns:</p>
                  <p><span className="text-primary">date</span>, <span className="text-primary">description</span>, <span className="text-primary">amount</span></p>
                  <p className="text-tertiary mt-1">Optional: category, currency</p>
                  <p className="text-tertiary mt-1 font-sans">Stripe CSV exports are auto-detected and normalized.</p>
                </div>
              </details>

              {/* Clear existing data option */}
              <div className="flex items-center gap-2 mt-4">
                <input 
                  type="checkbox" 
                  id="clearData" 
                  className="rounded border-border-default bg-bg-sunken text-primary-500 focus:ring-primary-500 focus:ring-offset-bg-elevated cursor-pointer"
                  checked={clearExistingData}
                  onChange={(e) => setClearExistingData(e.target.checked)}
                />
                <label htmlFor="clearData" className="text-sm text-secondary cursor-pointer hover:text-primary transition-colors">
                  Clear existing data before uploading
                </label>
              </div>
            </div>
          )}

          {/* ── Error state ─────────────────────────────────────────────── */}
          {uploadState === 'error' && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 bg-red-900/20 border border-red-700/40 rounded-lg">
                <AlertCircle size={20} className="text-red-400 shrink-0" />
                <p className="text-sm text-red-300">{errorMessage}</p>
              </div>
              <button
                onClick={reset}
                className="w-full py-2 rounded-lg border border-border-default text-secondary hover:text-primary hover:border-border-strong transition-colors text-sm"
              >
                Try again
              </button>
            </div>
          )}

          {/* ── Duplicate ───────────────────────────────────────────────── */}
          {uploadState === 'duplicate' && (
            <div className="flex items-center gap-3 p-4 bg-amber-900/20 border border-amber-700/40 rounded-lg">
              <AlertCircle size={20} className="text-amber-400 shrink-0" />
              <p className="text-sm text-amber-300">
                This file has already been processed. Using your existing analysis.
              </p>
            </div>
          )}

          {/* ── In-progress / complete ──────────────────────────────────── */}
          {(uploadState === 'uploading' || uploadState === 'analyzing' || uploadState === 'complete') && file && (
            <div className="space-y-6">
              <div className="flex items-center justify-between bg-bg-sunken border border-border-default rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <CheckCircle size={24} className="text-success-default shrink-0" />
                  <div className="overflow-hidden">
                    <p className="text-sm font-medium text-primary truncate" title={file.name}>
                      {truncateFilename(file.name)}
                    </p>
                    <p className="text-xs text-tertiary">{formatFileSize(file.size)}</p>
                  </div>
                </div>
              </div>

              {uploadState === 'uploading' && (
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-medium text-secondary">
                    <span>Uploading...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full h-1 bg-bg-hover rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary-500 to-primary-300 rounded-full transition-all duration-150 ease-in-out"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}

              {(uploadState === 'analyzing' || uploadState === 'complete') && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    {uploadState === 'analyzing' ? (
                      <Loader2 size={24} className="text-primary-500 animate-spin" />
                    ) : (
                      <CheckCircle size={24} className="text-success-default" />
                    )}
                    <p className="text-base italic text-secondary">
                      {uploadState === 'analyzing' ? 'CashPilot is analyzing your data...' : 'Analysis complete!'}
                    </p>
                  </div>

                  <div className="space-y-3 pl-2 border-l-[1px] border-border-subtle ml-[11px]">
                    {ANALYSIS_STEPS.map((step) => {
                      const isComplete = analysisStep > step.id || uploadState === 'complete';
                      const isActive = analysisStep === step.id && uploadState !== 'complete';

                      return (
                        <div key={step.id} className="flex items-center gap-3 -ml-[7px]">
                          <div className={cn(
                            "w-3 h-3 rounded-full border-2 bg-bg-raised transition-colors duration-200",
                            isComplete ? "border-success-default bg-success-default" :
                            isActive ? "border-primary-500" : "border-border-strong"
                          )} />
                          <span className={cn(
                            "text-sm transition-colors duration-200",
                            isComplete ? "text-primary" :
                            isActive ? "text-primary font-medium" : "text-tertiary"
                          )}>
                            {step.label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
