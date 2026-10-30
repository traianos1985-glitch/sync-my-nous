export type ExecutionReceipt = {
  id: string;
  operation: "chat";
  status: "completed" | "failed";
  startedAt: string;
  completedAt: string;
  verified: false;
  evidence: {
    provider: "gemini-api";
    model: string;
    researchUsed: boolean;
    persisted: boolean;
  };
};

export function createChatReceipt(input: {
  id: string;
  startedAt: string;
  model: string;
  researchUsed: boolean;
  persisted: boolean;
  status?: "completed" | "failed";
}): ExecutionReceipt {
  return {
    id: input.id,
    operation: "chat",
    status: input.status ?? "completed",
    startedAt: input.startedAt,
    completedAt: new Date().toISOString(),
    verified: false,
    evidence: {
      provider: "gemini-api",
      model: input.model,
      researchUsed: input.researchUsed,
      persisted: input.persisted,
    },
  };
}
