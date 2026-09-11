/**
 * REST API Client for V7 Measurement Jobs & Reference Standards Fleet.
 */

import {
  MeasurementJob,
  ReferenceStandard,
  ImportPreviewResponse,
} from '../types/job';

const API_BASE = '/api';

export async function fetchJobs(status?: string, search?: string): Promise<MeasurementJob[]> {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  if (search) params.append('search', search);

  const res = await fetch(`${API_BASE}/jobs?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch jobs: ${res.statusText}`);
  const data = await res.json();
  return data.jobs || [];
}

export async function fetchJob(jobId: string): Promise<MeasurementJob> {
  const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`);
  if (!res.ok) throw new Error(`Failed to fetch job ${jobId}: ${res.statusText}`);
  const data = await res.json();
  return data.job;
}

export async function createJob(payload: Partial<MeasurementJob>): Promise<MeasurementJob> {
  const res = await fetch(`${API_BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to create job: ${res.statusText}`);
  const data = await res.json();
  return data.job;
}

export async function updateJob(jobId: string, updates: Partial<MeasurementJob>): Promise<MeasurementJob> {
  const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error(`Failed to update job ${jobId}: ${res.statusText}`);
  const data = await res.json();
  return data.job;
}

export async function previewImport(
  content: string,
  filename?: string,
  targetUnit: string = 'mm'
): Promise<ImportPreviewResponse> {
  const res = await fetch(`${API_BASE}/jobs/import/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, filename, target_unit: targetUnit }),
  });
  if (!res.ok) throw new Error(`Failed to preview import: ${res.statusText}`);
  return await res.json();
}

export async function applyImport(
  jobId: string,
  payload: {
    raw_measurements: number[];
    mapped_columns: Record<string, any>;
    environment?: Record<string, any>;
    nominal_value?: number;
  }
): Promise<MeasurementJob> {
  const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}/apply-import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to apply import to job ${jobId}: ${res.statusText}`);
  const data = await res.json();
  return data.job;
}

export async function runPipeline(jobId: string): Promise<MeasurementJob> {
  const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}/pipeline`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Pipeline execution failed: ${res.statusText}`);
  }
  const data = await res.json();
  return data.job;
}

export async function approveJob(
  jobId: string,
  payload: {
    signer_name: string;
    signer_role: string;
    meaning: string;
  }
): Promise<MeasurementJob> {
  const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to approve job ${jobId}: ${res.statusText}`);
  const data = await res.json();
  return data.job;
}

export async function duplicateJob(jobId: string, operator: string = 'Metrology Specialist'): Promise<MeasurementJob> {
  const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}/duplicate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operator }),
  });
  if (!res.ok) throw new Error(`Failed to duplicate job ${jobId}: ${res.statusText}`);
  const data = await res.json();
  return data.job;
}

export async function fetchReferenceStandards(category?: string): Promise<ReferenceStandard[]> {
  const params = new URLSearchParams();
  if (category) params.append('category', category);

  const res = await fetch(`${API_BASE}/reference-standards?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch reference standards: ${res.statusText}`);
  const data = await res.json();
  return data.standards || [];
}

export function getCertificatePdfUrl(jobId: string): string {
  return `${API_BASE}/jobs/${encodeURIComponent(jobId)}/certificate`;
}

export function getEvidencePackageUrl(jobId: string): string {
  return `${API_BASE}/jobs/${encodeURIComponent(jobId)}/evidence-package`;
}

export async function fetchAssets(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/v1/assets`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.assets || [];
  } catch {
    return [];
  }
}

export async function scanAsset(identifier: string): Promise<any> {
  const res = await fetch(`${API_BASE}/v1/assets/scan/${encodeURIComponent(identifier)}`);
  if (!res.ok) return { found: false };
  return await res.json();
}

export async function runAutomatedCalibration(jobId: string, ambient?: Record<string, any>): Promise<any> {
  const res = await fetch(`${API_BASE}/v1/calibration/run-automated/${encodeURIComponent(jobId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ambient || {}),
  });
  if (!res.ok) throw new Error(`Automated calibration failed: ${res.statusText}`);
  return await res.json();
}
