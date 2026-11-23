import en from './en.json';
import kn from './kn.json';
import hi from './hi.json';

export const catalogues = { en, kn, hi };
export type Locale = keyof typeof catalogues;
export const nativeReview = { kn: 'pending', hi: 'pending' } as const;

export function catalogue(language: string): typeof en {
  return language === 'kn' || language === 'hi' ? catalogues[language] : en;
}
