import { useEffect, useState } from 'react'
import {
  DEFAULT_LANGUAGE,
  isLanguage,
  LANGUAGE_STORAGE_KEY,
  translations,
  type Language,
} from './translations'

function getInitialLanguage(): Language {
  if (typeof window === 'undefined') return DEFAULT_LANGUAGE

  try {
    const savedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY)
    return isLanguage(savedLanguage) ? savedLanguage : DEFAULT_LANGUAGE
  } catch {
    return DEFAULT_LANGUAGE
  }
}

export function useLanguage() {
  const [language, setLanguage] = useState<Language>(getInitialLanguage)
  const translation = translations[language]

  useEffect(() => {
    document.documentElement.lang = language
    document.title = translation.meta.title
    document.querySelector('meta[name="description"]')?.setAttribute('content', translation.meta.description)

    try {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language)
    } catch {
      // The UI can still switch languages when storage is unavailable.
    }
  }, [language, translation])

  function toggleLanguage() {
    setLanguage((current) => (current === 'zh-CN' ? 'en' : 'zh-CN'))
  }

  return {
    language,
    setLanguage,
    toggleLanguage,
    translation,
  }
}
