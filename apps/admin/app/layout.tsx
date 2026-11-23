import type { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  return <html lang="en"><body style={{ margin: 0, background: '#faf8f3', color: '#262c32', fontFamily: 'system-ui, sans-serif' }}>{children}</body></html>;
}
