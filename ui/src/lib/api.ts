import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export interface UploadResponse {
  success: boolean;
  message: string;
  filename?: string;
}

export interface HistoryItem {
  id: string;
  query: string;
  answer: string;
  timestamp: string;
  language: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  limit: number;
}

export interface StatsResponse {
  total_queries: number;
  total_documents: number;
  avg_response_time: number;
}

export interface SavedFile {
  name: string;
  size: number;
  modified: string;
  url: string;
}

// Upload PDF file
export async function uploadPDF(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(`${BASE_URL}/api/ingest/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
}

// Create EventSource for streaming responses
export function createSearchStream(query: string, settings: any = {}) {
  const params = new URLSearchParams({
    query,
    translate_to_arabic: settings.translateToArabic || 'false',
    top_k: settings.topK || '5',
    top_k_r: settings.topKR || '3',
    temperature: settings.temperature || '0.7',
  });

  return new EventSource(`${BASE_URL}/api/qa/ask?${params}`, {
    withCredentials: false,
  });
}

// Create EventSource for processing progress
export function createProgressStream() {
  return new EventSource(`${BASE_URL}/api/ingest/progress`, {
    withCredentials: false,
  });
}

// Get history
export async function getHistory(page = 1, limit = 15): Promise<HistoryResponse> {
  const response = await axios.get(`${BASE_URL}/api/history/`, {
    params: { page, limit }
  });
  return response.data;
}

// Get stats
export async function getStats(): Promise<StatsResponse> {
  const response = await axios.get(`${BASE_URL}/api/qa/stats`);
  return response.data;
}

// Get saved files
export async function getSavedFiles(): Promise<SavedFile[]> {
  try {
    await axios.get(`${BASE_URL}/saved/`);
    // The response might be HTML directory listing, so we'll need to parse it
    // For now, return empty array and implement later
    return [];
  } catch (error) {
    console.error('Failed to get saved files:', error);
    return [];
  }
}

// Download saved file
export async function downloadSavedFile(filename: string): Promise<Blob> {
  const response = await axios.get(`${BASE_URL}/saved/${filename}`, {
    responseType: 'blob',
  });
  return response.data;
}

// Reset corpus
export async function resetCorpus(): Promise<{ success: boolean; message: string }> {
  const response = await axios.post(`${BASE_URL}/api/ingest/reset`);
  return response.data;
}

// Trigger processing
export async function triggerProcessing(): Promise<{ success: boolean; message: string }> {
  const response = await axios.post(`${BASE_URL}/api/ingest/process`);
  return response.data;
}
