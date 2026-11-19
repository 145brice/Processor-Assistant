import { notFound } from "next/navigation";
import Placeholder from "@/components/Placeholder";
import { TOOL_TASKS } from "@/lib/nav";
import { TOOLS } from "@/lib/tools";
import ToolRunner from "./_components/ToolRunner";

export default async function Page({ params }: { params: Promise<{ tool: string }> }) {
  const { tool } = await params;
  if (TOOLS[tool]) return <ToolRunner toolKey={tool} />;
  const task = TOOL_TASKS[tool];
  if (!task) notFound();
  // Not built yet: the same "Coming soon" card as other unfinished pages.
  return <Placeholder title={tool.replace(/_/g, " ")} task={task} />;
}
