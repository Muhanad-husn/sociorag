export interface I18nText {
  en: string;
  ar: string;
}

export const translations = {
  appTitle: {
    en: 'SocioGraph',
    ar: 'سوسيوجراف'
  },  navigation: {
    home: { en: 'Home', ar: 'الرئيسية' },
    history: { en: 'History', ar: 'التاريخ' },
    saved: { en: 'Saved', ar: 'المحفوظات' },
    settings: { en: 'Settings', ar: 'الإعدادات' },
    menu: { en: 'Menu', ar: 'القائمة' },
    toggleTheme: { en: 'Toggle theme', ar: 'تبديل المظهر' },
    lightMode: { en: 'Light mode', ar: 'المظهر الفاتح' }
  },  search: {
    placeholder: { en: 'Ask a question...', ar: 'اطرح سؤالاً...' },
    askButton: { en: 'Ask', ar: 'اسأل' },
    translate: { en: 'Translate to Arabic', ar: 'ترجم إلى العربية' },
    enterHint: { en: 'Press Enter to search', ar: 'اضغط Enter للبحث' }
  },
  home: {
    subtitle: { en: 'Ask questions about your documents', ar: 'اطرح أسئلة حول وثائقك' },
    searchTab: { en: 'Search', ar: 'البحث' },
    uploadTab: { en: 'Upload', ar: 'رفع' },
    quickStart: { en: 'Quick Start', ar: 'البداية السريعة' },
    quickStart1: { en: 'Upload PDF documents using the Upload tab', ar: 'ارفع وثائق PDF باستخدام تبويب الرفع' },
    quickStart2: { en: 'Wait for processing to complete', ar: 'انتظر حتى تكتمل المعالجة' },
    quickStart3: { en: 'Ask questions about your documents', ar: 'اطرح أسئلة حول وثائقك' },
    quickStart4: { en: 'Toggle Arabic translation if needed', ar: 'فعّل الترجمة العربية إذا لزم الأمر' },
    uploadInstructions: { en: 'Upload Instructions', ar: 'تعليمات الرفع' },
    uploadInstr1: { en: 'Only PDF files are supported', ar: 'ملفات PDF فقط مدعومة' },
    uploadInstr2: { en: 'Maximum file size: 50MB', ar: 'الحد الأقصى لحجم الملف: 50 ميجابايت' },
    uploadInstr3: { en: 'Files are processed automatically after upload', ar: 'الملفات تُعالج تلقائياً بعد الرفع' },
    uploadInstr4: { en: 'You can upload multiple files at once', ar: 'يمكنك رفع ملفات متعددة في مرة واحدة' },
    uploadInstr5: { en: 'Processing time depends on document size and complexity', ar: 'وقت المعالجة يعتمد على حجم الوثيقة وتعقيدها' }
  },
  upload: {
    title: { en: 'Upload PDF', ar: 'رفع ملف PDF' },
    dragDrop: { en: 'Drag & drop a PDF file here, or click to select', ar: 'اسحب وأفلت ملف PDF هنا، أو انقر للاختيار' },
    uploading: { en: 'Uploading...', ar: 'جاري الرفع...' },
    success: { en: 'File uploaded successfully!', ar: 'تم رفع الملف بنجاح!' },
    error: { en: 'Upload failed', ar: 'فشل الرفع' }
  },
  processing: {
    title: { en: 'Processing', ar: 'المعالجة' },
    status: { en: 'Status', ar: 'الحالة' },
    progress: { en: 'Progress', ar: 'التقدم' }
  },  history: {
    title: { en: 'Query History', ar: 'تاريخ الاستعلامات' },
    empty: { en: 'No queries yet', ar: 'لا توجد استعلامات بعد' },
    emptyDesc: { en: 'Your search history will appear here once you start asking questions.', ar: 'سيظهر تاريخ البحث الخاص بك هنا بمجرد أن تبدأ في طرح الأسئلة.' },
    copyQuery: { en: 'Copy Query', ar: 'نسخ الاستعلام' },
    delete: { en: 'Delete', ar: 'حذف' },
    refresh: { en: 'Refresh', ar: 'تحديث' },
    rerunResults: { en: 'Rerun Results', ar: 'نتائج إعادة التشغيل' },
    originalQuery: { en: 'Original Query', ar: 'الاستعلام الأصلي' },
    previousAnswer: { en: 'Previous Answer', ar: 'الإجابة السابقة' },    deleteComingSoon: { en: 'Delete functionality coming soon', ar: 'وظيفة الحذف قادمة قريباً' },
    loadFailed: { en: 'Failed to load history', ar: 'فشل في تحميل التاريخ' },
    queryCopied: { en: 'Query copied to clipboard', ar: 'تم نسخ الاستعلام إلى الحافظة' },
    copyFailed: { en: 'Failed to copy query', ar: 'فشل في نسخ الاستعلام' },
    deleteConfirm: { en: 'Are you sure you want to delete this query?', ar: 'هل أنت متأكد من حذف هذا الاستعلام؟' },
    deleteSuccess: { en: 'Query deleted successfully', ar: 'تم حذف الاستعلام بنجاح' },
    deleteFailed: { en: 'Failed to delete query', ar: 'فشل في حذف الاستعلام' }
  },saved: {
    title: { en: 'Saved Documents', ar: 'الوثائق المحفوظة' },
    empty: { en: 'No saved documents', ar: 'لا توجد وثائق محفوظة' },
    emptyDesc: { en: 'Upload some PDF documents to see them here.', ar: 'ارفع بعض وثائق PDF لرؤيتها هنا.' },    download: { en: 'Save As', ar: 'حفظ باسم' },
    downloading: { en: 'Saving', ar: 'جاري الحفظ' },
    size: { en: 'Size', ar: 'الحجم' },
    modified: { en: 'Modified', ar: 'آخر تعديل' },
    refresh: { en: 'Refresh', ar: 'تحديث' },
    aboutTitle: { en: 'About Saved Documents', ar: 'حول الوثائق المحفوظة' },
    about1: { en: 'Documents are automatically saved after successful upload and processing', ar: 'الوثائق تُحفظ تلقائياً بعد الرفع والمعالجة بنجاح' },
    about2: { en: 'You can download any document at any time', ar: 'يمكنك تحميل أي وثيقة في أي وقت' },
    about3: { en: 'Original formatting and content are preserved', ar: 'التنسيق والمحتوى الأصلي محفوظان' },
    about4: { en: 'Files are stored securely on the server', ar: 'الملفات مخزنة بأمان على الخادم' },
    loadFailed: { en: 'Failed to load saved files', ar: 'فشل في تحميل الملفات المحفوظة' },    downloadSuccess: { en: 'File saved successfully', ar: 'تم حفظ الملف بنجاح' },
    downloadFailed: { en: 'Failed to save file', ar: 'فشل في حفظ الملف' }
  },settings: {
    title: { en: 'Settings', ar: 'الإعدادات' },
    appearance: { en: 'Appearance', ar: 'المظهر' },
    darkMode: { en: 'Dark Mode', ar: 'الوضع المظلم' },
    darkModeDesc: { en: 'Switch between light and dark themes', ar: 'التبديل بين المظاهر الفاتحة والمظلمة' },
    language: { en: 'Language / اللغة', ar: 'Language / اللغة' },
    search: { en: 'Search Settings', ar: 'إعدادات البحث' },
    topK: { en: 'Top K Results', ar: 'أفضل K نتائج' },
    topKR: { en: 'Top K Rerank', ar: 'أفضل K إعادة ترتيب' },
    temperature: { en: 'Temperature', ar: 'درجة الحرارة' },
    reset: { en: 'Reset Corpus', ar: 'إعادة تعيين المجموعة' },
    resetConfirm: { en: 'Are you sure? This will delete all documents.', ar: 'هل أنت متأكد؟ سيؤدي هذا إلى حذف جميع الوثائق.' },
    resetDefaults: { en: 'Reset to Defaults', ar: 'إعادة تعيين للافتراضيات' },
    // Toast messages
    settingsSaved: { en: 'Settings saved successfully', ar: 'تم حفظ الإعدادات بنجاح' },
    settingsSavedServer: { en: 'Settings saved successfully on the server', ar: 'تم حفظ الإعدادات بنجاح على الخادم' },
    settingsFailedServer: { en: 'Failed to save LLM settings on the server', ar: 'فشل في حفظ إعدادات LLM على الخادم' },
    settingsReset: { en: 'Settings reset to defaults', ar: 'تم إعادة تعيين الإعدادات للافتراضية' },
    corpusResetSuccess: { en: 'Corpus reset successfully', ar: 'تم إعادة تعيين المجموعة بنجاح' },
    corpusResetFailed: { en: 'Failed to reset corpus', ar: 'فشل في إعادة تعيين المجموعة' },
    apiKeyRequired: { en: 'Please enter a valid API key', ar: 'يرجى إدخال مفتاح API صالح' },
    apiKeyUpdated: { en: 'API key updated successfully', ar: 'تم تحديث مفتاح API بنجاح' },
    apiKeyFailed: { en: 'Failed to update API key', ar: 'فشل في تحديث مفتاح API' },
    modelSelectionConfirmed: { en: 'Model selection confirmed successfully! Note: Server restart may be required for changes to take effect.', ar: 'تم تأكيد اختيار النموذج بنجاح! ملاحظة: قد تكون هناك حاجة لإعادة تشغيل الخادم لتطبيق التغييرات.' },
    modelSelectionFailed: { en: 'Failed to save model selection to server', ar: 'فشل في حفظ اختيار النموذج على الخادم' },
    modelSelectionLocal: { en: 'Model selection confirmed!', ar: 'تم تأكيد اختيار النموذج!' },
    modelSelectionError: { en: 'Failed to confirm model selection', ar: 'فشل في تأكيد اختيار النموذج' },    modelsReset: { en: 'Model selections reset to system defaults', ar: 'تم إعادة تعيين اختيارات النماذج للافتراضيات' },    loadInfoFailed: { en: 'Failed to load system information', ar: 'فشل في تحميل معلومات النظام' },
    loadSettingsFailed: { en: 'Failed to load LLM settings', ar: 'فشل في تحميل إعدادات LLM' },    validationError: { en: 'Please fix the following issues:', ar: 'يرجى إصلاح المشاكل التالية:' }
  },common: {
    loading: { en: 'Loading...', ar: 'جاري التحميل...' },
    error: { en: 'Error', ar: 'خطأ' },
    success: { en: 'Success', ar: 'نجح' },
    cancel: { en: 'Cancel', ar: 'إلغاء' },
    confirm: { en: 'Confirm', ar: 'تأكيد' },
    close: { en: 'Close', ar: 'إغلاق' },    save: { en: 'Save', ar: 'حفظ' }
  }
};

export type TranslationKey = keyof typeof translations;

export function t(
  key: string, 
  lang: 'en' | 'ar' = 'en'
): string {
  const keys = key.split('.');
  let value: any = translations;
  
  for (const k of keys) {
    value = value?.[k];
    if (!value) break;
  }
  
  if (value && typeof value === 'object' && 'en' in value && 'ar' in value) {
    return value[lang];
  }
  
  return key; // Return key if translation not found
}

export function isRTL(lang: string): boolean {
  return lang === 'ar';
}

export function getDirection(lang: string): 'ltr' | 'rtl' {
  return isRTL(lang) ? 'rtl' : 'ltr';
}

export function detectLanguage(text: string): 'en' | 'ar' | 'mixed' {
  const arabicRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDCF\uFDF0-\uFDFF\uFE70-\uFEFF]/;
  const englishRegex = /[a-zA-Z]/;
  
  const hasArabic = arabicRegex.test(text);
  const hasEnglish = englishRegex.test(text);
  
  if (hasArabic && hasEnglish) return 'mixed';
  if (hasArabic) return 'ar';
  return 'en';
}
