import { notFound } from "next/navigation";
import Placeholder from "@/components/Placeholder";
import { TOOL_TASKS } from "@/lib/nav";

export default async function Page({ params }: { params: Promise<{ tool: string }> }) {
  const { tool } = await params;
  const task = TOOL_TASKS[tool];
  if (!task) notFound();
  return <Placeholder title={tool.replace(/_/g, " ")} task={task} notes="Expose the tool as POST /api/tools/<key>, then build this page." />;
}
