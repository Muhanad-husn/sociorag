import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Export the base URL for use by other modules
export function getApiUrl(): string {
  return BASE_URL;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  filename?: string;
}

export interface HistoryItem {
  id: number;
  query: string;
  timestamp: string;
  token_count: number;
  context_count: number;
  metadata: any;
}

export interface HistoryResponse {
  records: HistoryItem[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface StatsResponse {
  total_queries: number;
  total_documents: number;
  avg_response_time: number;
}

export interface SavedFile {
  filename: string;
  size: number;
  created_at: string;
  modified_at: string;
  file_type: string;
  download_url: string;
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

// Interface for ask question request
export interface AskRequest {
  query: string;
  translate_to_arabic?: boolean;
  top_k?: number;
  top_k_r?: number;
  temperature?: number;
  answer_model?: string;
  max_tokens?: number;
  context_window?: number;
  generate_pdf?: boolean;
}

// Interface for ask question response
export interface AskResponse {
  answer: string;
  answer_html: string;  // Pre-rendered HTML for frontend consumption
  query: string;
  language: string;
  pdf_url: string;
  context_count: number;
  token_count: number;
  duration: number;
  entities?: any[];
  context?: any[];
}

// Interface for progress response
export interface ProgressResponse {
  progress: number;
  status: string;
  complete: boolean;
}

// Ask question with regular HTTP request (replaces createSearchStream)
export async function askQuestion(query: string, settings: any = {}): Promise<AskResponse> {
  const requestData: AskRequest = {
    query,
    translate_to_arabic: settings.translateToArabic || false,
    top_k: settings.topK || 5,
    top_k_r: settings.topKR || 3,
    temperature: settings.temperature || 0.7,
    answer_model: settings.answerModel || '',
    max_tokens: settings.maxTokensAnswer || 4000,
    context_window: settings.contextWindow || 128000,
    generate_pdf: settings.generatePdf !== undefined ? settings.generatePdf : true
  };

  const response = await axios.post(`${BASE_URL}/api/qa/ask`, requestData);
  return response.data;
}

// Get processing progress with polling (replaces createProgressStream)
export async function getProcessingProgress(): Promise<ProgressResponse> {
  const response = await axios.get(`${BASE_URL}/api/ingest/progress`);
  return response.data;
}

// Get history
export async function getHistory(page = 1, per_page = 15): Promise<HistoryResponse> {
  const response = await axios.get(`${BASE_URL}/api/history/`, {
    params: { page, per_page }
  });
  return response.data;
}

// Get stats
export async function getStats(): Promise<StatsResponse> {
  const response = await axios.get(`${BASE_URL}/api/qa/stats`);
  return response.data;
}

// Get saved files
export async function getSavedFiles(sortBy?: string, sortOrder?: string): Promise<SavedFile[]> {
  try {
    const params = new URLSearchParams();
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);
    
    const response = await axios.get(`${BASE_URL}/api/saved/files?${params.toString()}`);
    return response.data.files;
  } catch (error) {
    console.error('Failed to get saved files:', error);
    return [];
  }
}

// Download saved file - fetch from working endpoint and return blob for local saving
export async function downloadSavedFile(filename: string): Promise<Blob> {
  const response = await axios.get(`${BASE_URL}/static/saved/${filename}`, {
    responseType: 'blob',
    // Ensure we get the raw binary data without any transformations
    headers: {
      'Accept': 'application/pdf,application/octet-stream,*/*'
    }
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

// Admin API Types
export interface SystemConfig {
  config_values: Record<string, any>;
  config_source: string;
  last_modified: string | null;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  uptime: number;
  components: Record<string, any>;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: Record<string, any>;
  disk_usage: Record<string, any>;
  database_stats: Record<string, any>;
  vector_store_stats: Record<string, any>;
  timestamp: string;
}

// Admin API Functions
export async function getSystemConfig(): Promise<SystemConfig> {
  const response = await axios.get(`${BASE_URL}/api/admin/config`);
  return response.data;
}

export async function getSystemHealth(): Promise<HealthStatus> {
  const response = await axios.get(`${BASE_URL}/api/admin/health`);
  return response.data;
}

export async function getSystemMetrics(): Promise<SystemMetrics> {
  const response = await axios.get(`${BASE_URL}/api/admin/metrics`);
  return response.data;
}

export interface ApiKeyUpdate {
  openrouter_api_key?: string;
  huggingface_token?: string;
}

export async function updateApiKeys(apiKeys: ApiKeyUpdate): Promise<{ success: boolean; message: string }> {
  const response = await axios.put(`${BASE_URL}/api/admin/api-keys`, apiKeys);
  return response.data;
}

export interface LLMSettingsUpdate {
  entity_llm_model?: string;
  entity_llm_temperature?: number;
  entity_llm_max_tokens?: number;
  entity_llm_stream?: boolean;
  
  answer_llm_model?: string;
  answer_llm_temperature?: number;
  answer_llm_max_tokens?: number;
  answer_llm_context_window?: number;
  answer_llm_stream?: boolean;
  
  translate_llm_model?: string;
  translate_llm_temperature?: number;
  translate_llm_max_tokens?: number;
  translate_llm_stream?: boolean;
  
  // Search parameters
  top_k?: number;
  top_k_rerank?: number;
}

export async function updateLLMSettings(settings: LLMSettingsUpdate): Promise<{ success: boolean; message: string }> {
  const response = await axios.put(`${BASE_URL}/api/admin/llm-settings`, settings);
  return response.data;
}

export async function getLLMSettings(): Promise<{ success: boolean; data: any }> {
  const response = await axios.get(`${BASE_URL}/api/admin/llm-settings`);
  return response.data;
}

// Complete PDF download workflow - fetch from working endpoint and save to user location
export async function downloadAndSavePDF(filename: string, userFilename?: string): Promise<boolean> {
  try {
    // Step 1: Fetch the PDF blob from the working backend endpoint
    const blob = await downloadSavedFile(filename);
    
    // Step 2: Use file-utils to save with user dialog
    const { saveFileWithDialog } = await import('./file-utils');
    
    const success = await saveFileWithDialog({
      filename: userFilename || filename,
      blob,
      fileType: {
        description: 'PDF files',
        mimeType: 'application/pdf',
        extension: '.pdf'
      }
    });
    
    return success;
  } catch (error) {
    console.error('Failed to download and save PDF:', error);
    throw error;
  }
}

// Delete history record
export async function deleteHistoryRecord(recordId: number): Promise<{ success: boolean; message: string }> {
  const response = await axios.delete(`${BASE_URL}/api/history/record/${recordId}`);
  return {
    success: response.data.status === 'success',
    message: response.data.message
  };
}
