export type ExecutionReceipt = {
  id: string;
  operation: "chat" | "tool" | "sandbox" | "mission";
  status: "completed" | "failed";
  startedAt: string;
  completedAt: string;
  verified: false;
  evidence: {
    provider: string;
    model: string;
    researchUsed: boolean;
    persisted: boolean;
  };
};

export function createExecutionReceipt(input: {
  id: string;
  operation: ExecutionReceipt["operation"];
  startedAt: string;
  evidence: ExecutionReceipt["evidence"];
  status?: ExecutionReceipt["status"];
}): ExecutionReceipt {
  return {
    id: input.id,
    operation: input.operation,
    status: input.status ?? "completed",
    startedAt: input.startedAt,
    completedAt: new Date().toISOString(),
    verified: false,
    evidence: input.evidence,
  };
}

export function createChatReceipt(input: {
  id: string;
  startedAt: string;
  model: string;
  researchUsed: boolean;
  persisted: boolean;
  status?: "completed" | "failed";
}): ExecutionReceipt {
  return createExecutionReceipt({
    id: input.id,
    operation: "chat",
    startedAt: input.startedAt,
    status: input.status,
    evidence: {
      provider: "gemini-api",
      model: input.model,
      researchUsed: input.researchUsed,
      persisted: input.persisted,
    },
  });
}
