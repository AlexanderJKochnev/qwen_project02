// -------
// import { getAuthToken } from '../lib/apiClient'; // Импортируйте это
// -------
import { createContext, h, VNode } from 'preact';
import { useContext, useState } from 'preact/hooks';
import { useEffect } from 'preact/hooks';
import { API_BASE_URL } from '../config/api';


// Define the supported languages as a dynamic type
export type Language = string;

// Define the context type
interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  availableLanguages: Language[];
}

// Create the context with default values
const LanguageContext = createContext<LanguageContextType>({
  language: 'en',
  setLanguage: () => {},
  t: (key: string) => key,
  availableLanguages: ['en', 'ru', 'fr'],
});

// Translation dictionary
const translations = {
  en: {
    welcome: 'Welcome',
    language: 'Language',
    home: 'Home',
    about: 'About',
    contact: 'Contact',
    login: 'Login',
    logout: 'Logout',
    username: 'Username',
    password: 'Password',
    submit: 'Submit',
    cancel: 'Cancel',
    save: 'Save',
    edit: 'Edit',
    delete: 'Delete',
    search: 'Search',
    filter: 'Filter',
    create: 'Create',
    update: 'Update',
    view: 'View',
    details: 'Details',
    items: 'Items',
    item: 'Item',
    name: 'Name',
    description: 'Description',
    actions: 'Actions',
    confirm: 'Confirm',
    confirmDelete: 'Are you sure you want to delete this item?',
    yes: 'Yes',
    no: 'No',
    success: 'Success',
    error: 'Error',
    loading: 'Loading...',
    noData: 'No data available',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
    first: 'First',
    last: 'Last',
    of: 'of',
    results: 'results',
    total: 'Total',
    page: 'Page',
    records: 'records',
    settings: 'Settings',
    profile: 'Profile',
    dashboard: 'Dashboard',
    admin: 'Admin',
    user: 'User',
    role: 'Role',
    status: 'Status',
    active: 'Active',
    inactive: 'Inactive',
    enabled: 'Enabled',
    disabled: 'Disabled',
    date: 'Date',
    time: 'Time',
    created: 'Created',
    updated: 'Updated',
    deleted: 'Deleted',
    refresh: 'Refresh',
    download: 'Download',
    upload: 'Upload',
    import: 'Import',
    export: 'Export',
    print: 'Print',
    share: 'Share',
    copy: 'Copy',
    paste: 'Paste',
    cut: 'Cut',
    select: 'Select',
    all: 'All',
    none: 'None',
    clear: 'Clear',
    reset: 'Reset',
    apply: 'Apply',
    close: 'Close',
    open: 'Open',
    minimize: 'Minimize',
    maximize: 'Maximize',
    restore: 'Restore',
    help: 'Help',
    aboutApp: 'About Application',
    version: 'Version',
    copyright: 'Copyright',
    privacy: 'Privacy Policy',
    terms: 'Terms of Service',
    cookies: 'Cookies',
    accessibility: 'Accessibility',
    feedback: 'Feedback',
    support: 'Support',
    documentation: 'Documentation',
    tutorial: 'Tutorial',
    examples: 'Examples',
    faq: 'FAQ',
    news: 'News',
    updates: 'Updates',
    notifications: 'Notifications',
    messages: 'Messages',
    inbox: 'Inbox',
    sent: 'Sent',
    drafts: 'Drafts',
    spam: 'Spam',
    trash: 'Trash',
    calendar: 'Calendar',
    events: 'Events',
    tasks: 'Tasks',
    reminders: 'Reminders',
    notes: 'Notes',
    files: 'Files',
    folders: 'Folders',
    tags: 'Tags',
    categories: 'Categories',
    filters: 'Filters',
    sorting: 'Sorting',
    group: 'Group',
    order: 'Order',
    ascending: 'Ascending',
    descending: 'Descending',
    equal: 'Equal',
    notEqual: 'Not Equal',
    greater: 'Greater',
    less: 'Less',
    greaterOrEqual: 'Greater or Equal',
    lessOrEqual: 'Less or Equal',
    contains: 'Contains',
    startsWith: 'Starts With',
    endsWith: 'Ends With',
    empty: 'Empty',
    notEmpty: 'Not Empty',
    null: 'Null',
    notNull: 'Not Null',
    today: 'Today',
    yesterday: 'Yesterday',
    tomorrow: 'Tomorrow',
    thisWeek: 'This Week',
    lastWeek: 'Last Week',
    nextWeek: 'Next Week',
    thisMonth: 'This Month',
    lastMonth: 'Last Month',
    nextMonth: 'Next Month',
    thisYear: 'This Year',
    lastYear: 'Last Year',
    nextYear: 'Next Year',
  },
  ru: {
    welcome: 'Добро пожаловать',
    language: 'Язык',
    home: 'Главная',
    about: 'О нас',
    contact: 'Контакты',
    login: 'Войти',
    logout: 'Выйти',
    username: 'Имя пользователя',
    password: 'Пароль',
    submit: 'Отправить',
    cancel: 'Отмена',
    save: 'Сохранить',
    edit: 'Редактировать',
    delete: 'Удалить',
    search: 'Поиск',
    filter: 'Фильтр',
    create: 'Создать',
    update: 'Обновить',
    view: 'Просмотр',
    details: 'Детали',
    items: 'Элементы',
    item: 'Элемент',
    name: 'Имя',
    description: 'Описание',
    actions: 'Действия',
    confirm: 'Подтвердить',
    confirmDelete: 'Вы уверены, что хотите удалить этот элемент?',
    yes: 'Да',
    no: 'Нет',
    success: 'Успешно',
    error: 'Ошибка',
    loading: 'Загрузка...',
    noData: 'Нет доступных данных',
    back: 'Назад',
    next: 'Далее',
    previous: 'Предыдущий',
    first: 'Первый',
    last: 'Последний',
    of: 'из',
    results: 'результаты',
    total: 'Всего',
    page: 'Страница',
    records: 'записи',
    settings: 'Настройки',
    profile: 'Профиль',
    dashboard: 'Панель управления',
    admin: 'Админ',
    user: 'Пользователь',
    role: 'Роль',
    status: 'Статус',
    active: 'Активный',
    inactive: 'Неактивный',
    enabled: 'Включено',
    disabled: 'Отключено',
    date: 'Дата',
    time: 'Время',
    created: 'Создано',
    updated: 'Обновлено',
    deleted: 'Удалено',
    refresh: 'Обновить',
    download: 'Скачать',
    upload: 'Загрузить',
    import: 'Импорт',
    export: 'Экспорт',
    print: 'Печать',
    share: 'Поделиться',
    copy: 'Копировать',
    paste: 'Вставить',
    cut: 'Вырезать',
    select: 'Выбрать',
    all: 'Все',
    none: 'Ничего',
    clear: 'Очистить',
    reset: 'Сбросить',
    apply: 'Применить',
    close: 'Закрыть',
    open: 'Открыть',
    minimize: 'Свернуть',
    maximize: 'Развернуть',
    restore: 'Восстановить',
    help: 'Помощь',
    aboutApp: 'О приложении',
    version: 'Версия',
    copyright: 'Авторские права',
    privacy: 'Политика конфиденциальности',
    terms: 'Условия использования',
    cookies: 'Файлы cookie',
    accessibility: 'Доступность',
    feedback: 'Обратная связь',
    support: 'Поддержка',
    documentation: 'Документация',
    tutorial: 'Руководство',
    examples: 'Примеры',
    faq: 'Часто задаваемые вопросы',
    news: 'Новости',
    updates: 'Обновления',
    notifications: 'Уведомления',
    messages: 'Сообщения',
    inbox: 'Входящие',
    sent: 'Отправленные',
    drafts: 'Черновики',
    spam: 'Спам',
    trash: 'Корзина',
    calendar: 'Календарь',
    events: 'События',
    tasks: 'Задачи',
    reminders: 'Напоминания',
    notes: 'Заметки',
    files: 'Файлы',
    folders: 'Папки',
    tags: 'Теги',
    categories: 'Категории',
    filters: 'Фильтры',
    sorting: 'Сортировка',
    group: 'Группа',
    order: 'Порядок',
    ascending: 'По возрастанию',
    descending: 'По убыванию',
    equal: 'Равно',
    notEqual: 'Не равно',
    greater: 'Больше',
    less: 'Меньше',
    greaterOrEqual: 'Больше или равно',
    lessOrEqual: 'Меньше или равно',
    contains: 'Содержит',
    startsWith: 'Начинается с',
    endsWith: 'Заканчивается на',
    empty: 'Пусто',
    notEmpty: 'Не пусто',
    null: 'Пустое значение',
    notNull: 'Не пустое значение',
    today: 'Сегодня',
    yesterday: 'Вчера',
    tomorrow: 'Завтра',
    thisWeek: 'На этой неделе',
    lastWeek: 'На прошлой неделе',
    nextWeek: 'На следующей неделе',
    thisMonth: 'В этом месяце',
    lastMonth: 'В прошлом месяце',
    nextMonth: 'В следующем месяце',
    thisYear: 'В этом году',
    lastYear: 'В прошлом году',
    nextYear: 'В следующем году',
  }
};

// Provider component
export const LanguageProvider = ({ children }: { children: VNode }) => {
  // Initialize with language from localStorage or default
  const initialLanguage = localStorage.getItem('language') as Language || 'en';
  const [language, setLanguage] = useState<Language>(initialLanguage);
  const [availableLanguages, setAvailableLanguages] = useState<Language[]>(['en', 'ru']); // Initialize with defaults

  useEffect(() => {
    // Fetch available languages from the backend
    const fetchAvailableLanguages = async () => {

      const token = localStorage.getItem('auth_token');
      // Если токена нет, не шлем запрос, чтобы не получить 401
      if (!token || token === 'undefined' || token === 'null') {
        console.warn('Attempted to fetch languages without token');
        return;
      }

      try {
        console.log('Token in Storage:', localStorage.getItem('auth_token'))
        const response = await fetch(`${API_BASE_URL}/get/languages`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`,
            'Content-Type': 'application/json'
          }
        }); // Using the proper API endpoint
        if (response.ok) {
          const data = await response.json();
          const langs = data.languages || ['en', 'ru', 'fr'];
          setAvailableLanguages(langs);
          
          // Check for saved language preference in localStorage
          const savedLang = localStorage.getItem('language') as Language;
          if (savedLang && langs.includes(savedLang)) {
            setLanguage(savedLang);
          } else {
            // Fallback to default language from backend or browser language
            const defaultLang = data.default || 'en';
            const browserLang = navigator.language.split('-')[0]; // Get base language code
            const preferredLang = langs.includes(browserLang) ? browserLang : defaultLang;
            setLanguage(preferredLang);
          }
        } else {
          // Fallback to default languages if API call fails
          const defaultLang = 'en';
          const browserLang = navigator.language.split('-')[0];
          const langs = ['en', 'ru', 'fr']; // Default fallback
          setAvailableLanguages(langs);
          const preferredLang = langs.includes(browserLang) ? browserLang : defaultLang;
          setLanguage(preferredLang);
        }
      } catch (error) {
        console.error('Error fetching available languages:', error);
        // Fallback to default languages if API call fails
        const defaultLang = 'en';
        const browserLang = navigator.language.split('-')[0];
        // Use the same defaults as in the project config
        const langs = ['en', 'ru', 'fr']; // This should match the backend settings
        setAvailableLanguages(langs);
        const preferredLang = langs.includes(browserLang) ? browserLang : defaultLang;
        setLanguage(preferredLang);
      }
    };

    fetchAvailableLanguages();
  }, []);

  // Save language preference to localStorage whenever it changes
  useEffect(() => {
    if (language) {
      localStorage.setItem('language', language);
    }
  }, [language]);

  // Translation function
  const t = (key: string): string => {
    // Use the current language for translation if available in the dictionary
    const currentLangTranslations = (translations as Record<string, Record<string, string>>)[language];
    const translation = currentLangTranslations?.[key];
    return translation || key; // Return the key itself if no translation found
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, availableLanguages }}>
      {children}
    </LanguageContext.Provider>
  );
};

// Custom hook to use the language context
export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};