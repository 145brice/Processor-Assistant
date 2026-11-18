import Link from "next/link";

export default function Page() {
  return <main className="mx-auto max-w-3xl px-6 py-10">
    <h1 className="text-3xl font-bold">Privacy Policy</h1>
    <p className="mt-2 text-sm text-[var(--muted)]">Last updated: November 10, 2026</p>
    <article className="prose prose-slate dark:prose-invert mt-8 max-w-none">
      <h3>Documents and saved data</h3>
      <p>We never store your documents. We only save the loan details extracted from them so you don&apos;t have to re-scan.</p>
      <p>Uploaded documents are processed in memory only and are never stored by Processor Assistant. We save extracted loan data (parsed fields) and scan history in Supabase, tied to your account, so you can return to previous results without re-scanning. Extracted fields may include borrower and loan information from the documents you process.</p>
      <h3>Account information</h3>
      <p>We store your name, email, and role to provide and manage your account. Your Gemini API key is saved encrypted for your signed-in account when you configure it.</p>
      <h3>How we use information</h3>
      <p>We use your information to parse documents, display extracted loan details, maintain your scan history, manage your account, and provide subscription and payment services.</p>
      <h3>Third parties that handle data</h3>
      <ul>
        <li><strong>Google Gemini API</strong> processes document content for parsing and AI assistance. Google does not use your data to train its models when you use a paid-tier Gemini API key. Enable billing for the Google AI project associated with your key before processing documents. Google&apos;s processing is subject to its <a href="https://ai.google.dev/gemini-api/terms">Gemini API terms</a>.</li>
        <li><strong>Supabase</strong> provides the database and authentication, including account information, extracted loan details, and scan history linked to your account.</li>
        <li><strong>Railway</strong> hosts Processor Assistant and runs its in-memory document processing.</li>
        <li><strong>Stripe</strong> handles subscription payments and related billing information.</li>
      </ul>
      <h3>Retention and deletion</h3>
      <p>Saved loan data and scan history are kept until you delete them or close your account. Account information is kept while your account is active. You can request deletion of saved loan data, scan history, or your account by emailing info@edgelandings.com.</p>
      <h3>Your privacy rights</h3>
      <p>We do not sell your personal data. You can email info@edgelandings.com to request access to your information, corrections, deletion, or information about how it is used. These requests include applicable GDPR and CCPA rights.</p>
      <h3>Privacy questions</h3>
      <p>Email info@edgelandings.com.</p>
    </article>
    <footer className="mt-10 border-[var(--border)] border-t pt-4 text-center text-sm text-[var(--muted)]"><Link href="/privacy" className="text-blue-600 dark:text-blue-300">Privacy Policy</Link> <span className="mx-2">|</span> <Link href="/terms" className="text-blue-600 dark:text-blue-300">Terms of Service</Link></footer>
  </main>;
}
