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
  },
  search: {
    placeholder: { en: 'Ask a question...', ar: 'اطرح سؤالاً...' },
    askButton: { en: 'Ask', ar: 'اسأل' },
    translate: { en: 'Translate to Arabic', ar: 'ترجم إلى العربية' }
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
  },
  history: {
    title: { en: 'Query History', ar: 'تاريخ الاستعلامات' },
    empty: { en: 'No queries yet', ar: 'لا توجد استعلامات بعد' },
    rerun: { en: 'Rerun', ar: 'إعادة تشغيل' },
    delete: { en: 'Delete', ar: 'حذف' }
  },
  saved: {
    title: { en: 'Saved Documents', ar: 'الوثائق المحفوظة' },
    empty: { en: 'No saved documents', ar: 'لا توجد وثائق محفوظة' },
    download: { en: 'Download', ar: 'تحميل' },
    size: { en: 'Size', ar: 'الحجم' },
    modified: { en: 'Modified', ar: 'آخر تعديل' }
  },
  settings: {
    title: { en: 'Settings', ar: 'الإعدادات' },
    appearance: { en: 'Appearance', ar: 'المظهر' },
    darkMode: { en: 'Dark Mode', ar: 'الوضع المظلم' },
    search: { en: 'Search Settings', ar: 'إعدادات البحث' },
    topK: { en: 'Top K Results', ar: 'أفضل K نتائج' },
    topKR: { en: 'Top K Rerank', ar: 'أفضل K إعادة ترتيب' },
    temperature: { en: 'Temperature', ar: 'درجة الحرارة' },
    reset: { en: 'Reset Corpus', ar: 'إعادة تعيين المجموعة' },
    resetConfirm: { en: 'Are you sure? This will delete all documents.', ar: 'هل أنت متأكد؟ سيؤدي هذا إلى حذف جميع الوثائق.' }
  },
  common: {
    loading: { en: 'Loading...', ar: 'جاري التحميل...' },
    error: { en: 'Error', ar: 'خطأ' },
    success: { en: 'Success', ar: 'نجح' },
    cancel: { en: 'Cancel', ar: 'إلغاء' },
    confirm: { en: 'Confirm', ar: 'تأكيد' },
    close: { en: 'Close', ar: 'إغلاق' },
    save: { en: 'Save', ar: 'حفظ' }
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
