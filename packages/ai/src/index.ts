export interface PhrasingPort {
  phrase(text: string, locale: string): Promise<{ text: string; attribution: '✦ AI' }>;
}
