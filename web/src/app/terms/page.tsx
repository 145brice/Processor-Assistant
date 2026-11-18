import Link from "next/link";

export default function Page() {
  return <main className="mx-auto max-w-3xl px-6 py-10">
    <h1 className="text-3xl font-bold">Terms of Service</h1>
    <p className="mt-2 text-sm text-[var(--muted)]">Last updated: November 10, 2026</p>
    <article className="prose prose-slate dark:prose-invert mt-8 max-w-none">
      <h3>Your responsibilities</h3>
      <ul><li>Use Processor Assistant only for files and data you are authorized to handle.</li><li>Keep your account credentials secure.</li><li>Provide accurate information when using the service.</li></ul>
      <h3>Data usage limits</h3>
      <ul><li>Use the app for legitimate mortgage-processing and related business workflows.</li><li>Do not upload unlawful content or content that violates privacy, copyright, or confidentiality rules.</li></ul>
      <h3>Acceptable use policy</h3>
      <ul><li>Do not attempt to break, probe, or reverse engineer the service.</li><li>Do not abuse APIs, bypass limits, or interfere with service availability.</li><li>Do not use the service to send spam, malware, or fraudulent content.</li></ul>
      <h3>Liability disclaimers</h3>
      <ul><li>The service is provided &quot;as is&quot; without guarantees of uninterrupted operation.</li><li>You remain responsible for final review and compliance decisions on loan files and borrower communications.</li><li>To the fullest extent allowed by law, Processor Assistant is not liable for indirect or consequential damages.</li></ul>
      <p>By using Processor Assistant, you agree to these terms.</p>
    </article>
    <footer className="mt-10 border-[var(--border)] border-t pt-4 text-center text-sm text-[var(--muted)]"><Link href="/privacy" className="text-blue-600 dark:text-blue-300">Privacy Policy</Link> <span className="mx-2">|</span> <Link href="/terms" className="text-blue-600 dark:text-blue-300">Terms of Service</Link></footer>
  </main>;
}
