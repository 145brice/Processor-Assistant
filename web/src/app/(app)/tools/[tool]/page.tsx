import { notFound } from "next/navigation";
import { TOOLS } from "@/lib/tools";
import ToolRunner from "./_components/ToolRunner";

export default async function Page({ params }: { params: Promise<{ tool: string }> }) {
  const { tool } = await params;
  if (!TOOLS[tool]) notFound();
  return <ToolRunner toolKey={tool} />;
}
