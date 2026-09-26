import { z } from "zod";

export const toolDefinitions = {
  research: {
    description: "Read-only web research with citations",
    risk: "read" as const,
    input: z.object({ query: z.string().trim().min(2).max(500) }),
  },
  createMission: {
    description: "Create a queued mission for later execution",
    risk: "write" as const,
    input: z.object({
      title: z.string().trim().min(1).max(160),
      objective: z.string().trim().min(1).max(4000),
    }),
  },
} as const;

export type ToolName = keyof typeof toolDefinitions;
export type ToolRisk = "read" | "write";

export function getToolDefinition(name: string) {
  return Object.hasOwn(toolDefinitions, name) ? toolDefinitions[name as ToolName] : null;
}

export function requiresApproval(name: string) {
  return getToolDefinition(name)?.risk === "write";
}
