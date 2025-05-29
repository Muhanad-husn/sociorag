import { useState, useRef } from 'preact/hooks';
import { Upload, File, X, CheckCircle } from 'lucide-preact';
import { uploadPDF } from '../lib/api';
import { useAppStore } from '../hooks/useLocalState';
import { toast } from 'sonner';
import { t } from '../lib/i18n';
import clsx from 'clsx';

interface FileUploaderProps {
  onUploadComplete?: (filename: string) => void;
  onUploadStart?: () => void;
  language?: 'en' | 'ar';
}

export function FileUploader({ onUploadComplete, onUploadStart, language }: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { language: appLanguage } = useAppStore();
  const currentLanguage = language || appLanguage;

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer?.files || []);
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length === 0) {
      toast.error(t('upload.pdfOnly', currentLanguage));
      return;
    }
    
    pdfFiles.forEach(handleFileUpload);
  };

  const handleFileSelect = (e: Event) => {
    const files = Array.from((e.target as HTMLInputElement).files || []);
    files.forEach(handleFileUpload);
  };

  const handleFileUpload = async (file: File) => {
    if (file.type !== 'application/pdf') {
      toast.error(t('upload.notPdf', currentLanguage).replace('{filename}', file.name));
      return;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      toast.error(t('upload.tooLarge', currentLanguage).replace('{filename}', file.name));
      return;
    }

    setIsUploading(true);
    onUploadStart?.();

    try {
      const response = await uploadPDF(file);
      
      if (response.success) {
        toast.success(response.message || t('upload.success', currentLanguage));
        setUploadedFiles(prev => [...prev, file.name]);
        onUploadComplete?.(response.filename || file.name);
      } else {
        toast.error(response.message || t('upload.error', currentLanguage));
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(t('upload.error', currentLanguage));
    } finally {
      setIsUploading(false);
    }
  };

  const removeUploadedFile = (filename: string) => {
    setUploadedFiles(prev => prev.filter(f => f !== filename));
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-4">
      {/* Upload area */}
      <div
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragging ? 'border-primary bg-primary/5' : 'border hover:border-primary/50',
          isUploading && 'opacity-50 cursor-not-allowed'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={!isUploading ? handleClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={isUploading}
        />
        
        <div className="space-y-3">
          <Upload className={clsx(
            'mx-auto h-12 w-12',
            isUploading ? 'text-muted-foreground animate-pulse' : 'text-primary'
          )} />
          
          <div>
            <p className="text-lg font-medium">
              {isUploading ? t('upload.uploading', currentLanguage) : t('upload.title', currentLanguage)}
            </p>
            <p className="text-sm text-muted-foreground">
              {t('upload.dragDrop', currentLanguage)}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              {t('upload.fileRestrictions', currentLanguage)}
            </p>
          </div>
        </div>
      </div>

      {/* Uploaded files list */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">{t('upload.recentlyUploaded', currentLanguage)}:</h4>
          <div className="space-y-1">
            {uploadedFiles.map((filename, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-accent rounded">
                <div className="flex items-center space-x-2">
                  <File className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{filename}</span>
                  <CheckCircle className="h-4 w-4 text-green-600" />
                </div>
                <button
                  onClick={() => removeUploadedFile(filename)}
                  className="btn-secondary h-6 w-6 p-0"
                  title={t('common.remove', currentLanguage)}
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
