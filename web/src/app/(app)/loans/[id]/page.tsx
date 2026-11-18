import Placeholder from "@/components/Placeholder";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <Placeholder title={`Loan ${id}`} task="T-25, T-26" notes="Status, conditions, notes, activity, contacts, documents." />;
}
