/**
 * Utility functions for file saving with save dialog support
 */

export interface SaveFileOptions {
  filename: string;
  blob: Blob;
  fileType?: {
    description: string;
    mimeType: string;
    extension: string;
  };
}

/**
 * Save a file using the File System Access API if available, 
 * otherwise fall back to traditional download
 */
export async function saveFileWithDialog(options: SaveFileOptions): Promise<boolean> {
  const { filename, blob, fileType } = options;
  
  // Default to PDF if no file type specified
  const defaultFileType = {
    description: 'PDF files',
    mimeType: 'application/pdf',
    extension: '.pdf'
  };
  
  const type = fileType || defaultFileType;
  
  // Try to use the File System Access API for modern browsers
  if ('showSaveFilePicker' in window) {
    try {
      const fileHandle = await window.showSaveFilePicker!({
        suggestedName: filename,
        types: [{
          description: type.description,
          accept: { [type.mimeType]: [type.extension] }
        }]
      });
      
      const writable = await fileHandle.createWritable();
      await writable.write(blob);
      await writable.close();
      
      return true;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        // User cancelled the save dialog
        return false;
      }
      throw error;
    }
  } else {
    // Fallback for browsers without File System Access API
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    return true;
  }
}

/**
 * Check if the File System Access API is supported
 */
export function isFileSystemAccessSupported(): boolean {
  return 'showSaveFilePicker' in window;
}
