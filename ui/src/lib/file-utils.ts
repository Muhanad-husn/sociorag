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
  
  console.log('Save file attempt:', { 
    filename, 
    hasFileSystemAccess: 'showSaveFilePicker' in window,
    isSecureContext: window.isSecureContext,
    userAgent: navigator.userAgent
  });
  
  // Try to use the File System Access API for modern browsers
  if ('showSaveFilePicker' in window && window.isSecureContext) {
    try {
      console.log('Attempting to use File System Access API for:', filename);
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
      
      console.log('File saved successfully using File System Access API');
      return true;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        // User cancelled the save dialog
        console.log('User cancelled the save dialog');
        return false;
      }
      // For other errors, fall back to traditional download
      console.warn('File System Access API failed, falling back to download:', error);
    }
  } else {
    console.log('File System Access API not available. Details:', {
      hasShowSaveFilePicker: 'showSaveFilePicker' in window,
      isSecureContext: window.isSecureContext,
      protocol: window.location.protocol
    });
  }

  // Alternative: Try to simulate save dialog behavior
  try {
    console.log('Attempting alternative save method with user confirmation');
    const userConfirmed = confirm(`Save file "${filename}" to Downloads folder?`);
    if (!userConfirmed) {
      console.log('User cancelled file save');
      return false;
    }
  } catch (e) {
    console.log('Confirmation dialog not available, proceeding with download');
  }

  // Fallback for browsers without File System Access API or when API fails
  console.log('Using traditional download method for:', filename);
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  
  // Cleanup
  setTimeout(() => {
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }, 100);
  
  return true;
}

/**
 * Check if the File System Access API is supported
 */
export function isFileSystemAccessSupported(): boolean {
  return 'showSaveFilePicker' in window && window.isSecureContext;
}
