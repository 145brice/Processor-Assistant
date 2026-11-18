// Signed-in layout: sidebar + pipeline header. Sign-in guard is middleware.ts (T-12).
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import GeminiSetupWizard from "@/components/GeminiSetupWizard";

export default function AppLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1">{children}</main>
      </div>
      <GeminiSetupWizard />
    </div>
  );
}
