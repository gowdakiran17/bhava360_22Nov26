import { catalogue } from '@bhava360/i18n';

export default async function Home({ searchParams }: {
  searchParams: Promise<{ lang?: string }>
}) {
  const { lang } = await searchParams;
  const locale = lang === 'kn' || lang === 'hi' ? lang : 'en';
  const copy = catalogue(locale);
  return <main lang={locale} style={{ maxWidth: '40rem', margin: '12vh auto', padding: '1.5rem' }}>
    <h1>{process.env.APP_DISPLAY_NAME || copy.appName}</h1>
    <p>{copy.footer}</p>
    <nav>{(['en', 'kn', 'hi'] as const).map((code, index) =>
      <a key={code} href={'?lang=' + code} lang={code} hrefLang={code}
        aria-current={code === locale ? 'page' : undefined} style={{ marginInlineEnd: '1rem' }}>
        {catalogue(code)[(['english', 'kannada', 'hindi'] as const)[index]]}
      </a>)}</nav>
  </main>;
}
