export const metadata = { robots: { index: false, follow: false } };

export default function StaffShell() {
  return <main style={{ maxWidth: '40rem', margin: '12vh auto', padding: '1.5rem' }}>
    <h1>Staff workspace</h1><p>This staff app runs on a separate origin.</p>
  </main>;
}
