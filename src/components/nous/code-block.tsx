import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";

function extractText(node: React.ReactNode): string {
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  if (!node) return "";
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (
    typeof node === "object" &&
    node !== null &&
    "props" in node &&
    (node as { props?: { children?: React.ReactNode } }).props?.children
  ) {
    return extractText((node as { props: { children: React.ReactNode } }).props.children);
  }
  return "";
}

export function CodeBlock({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  const text = extractText(children).replace(/\n$/, "");

  const match = /language-([a-z0-9_-]+)/i.exec(className || "");
  const language = match ? match[1] : undefined;

  const handleCopy = async () => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2_000);
    } catch {
      // Ignore clipboard write failures in restricted contexts
    }
  };

  return (
    <div className="group relative my-3 overflow-hidden rounded-lg border border-border/80 bg-card/60 font-mono text-xs shadow-sm">
      <div className="flex items-center justify-between border-b border-border/50 bg-muted/40 px-3 py-1.5 text-[11px] text-muted-foreground">
        <span className="font-semibold uppercase tracking-wider text-foreground/80">
          {language || "code"}
        </span>
        <Button
          variant="ghost"
          size="sm"
          type="button"
          onClick={() => void handleCopy()}
          className="h-6 gap-1 px-2 text-[11px] hover:bg-background/80"
          aria-label="Αντιγραφή κώδικα"
        >
          {copied ? (
            <>
              <Check className="size-3 text-ok" />
              <span className="text-ok">Αντιγράφηκε</span>
            </>
          ) : (
            <>
              <Copy className="size-3" />
              <span>Αντιγραφή</span>
            </>
          )}
        </Button>
      </div>
      <pre className="overflow-x-auto p-3 text-[12px] leading-relaxed">
        <code>{children}</code>
      </pre>
    </div>
  );
}
