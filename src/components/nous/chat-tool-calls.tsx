import {
  Tool,
  ToolContent,
  ToolHeader,
  ToolInput,
  ToolOutput,
} from "@/components/ai-elements/tool";
import type { ChatToolCall } from "./chat-tool-model";

export function ChatToolCalls({ calls }: { calls: ChatToolCall[] }) {
  return (
    <div className="mt-3 min-w-0 space-y-2" aria-label="Εκτελέσεις εργαλείων">
      {calls.map((call) => (
        <Tool key={call.id} defaultOpen={false} className="mb-0 min-w-0">
          <ToolHeader
            type="dynamic-tool"
            toolName={call.name}
            title={call.name}
            state={
              call.status === "running"
                ? "input-available"
                : call.status === "completed"
                  ? "output-available"
                  : call.status === "blocked"
                    ? "output-denied"
                    : "output-error"
            }
          />
          <ToolContent className="max-h-96 min-w-0 overflow-auto">
            {call.summary && (
              <div>
                <h4 className="mb-1 text-xs font-medium text-muted-foreground">Σκοπός ενέργειας</h4>
                <p className="break-words text-xs">{call.summary}</p>
              </div>
            )}
            <ToolInput input={call.input} />
            <ToolOutput
              output={call.output}
              errorText={
                call.error ??
                (call.status === "interrupted" ? "Η εκτέλεση δεν επιβεβαιώθηκε." : undefined)
              }
            />
          </ToolContent>
        </Tool>
      ))}
    </div>
  );
}
