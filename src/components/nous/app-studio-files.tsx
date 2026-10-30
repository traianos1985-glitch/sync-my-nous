import { FileCode2, Folder } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fileTree, type FileNode, type StudioFile } from "./app-studio-model";

export function StudioFiles({ files, selected, onSelect }: { files: StudioFile[]; selected: string; onSelect: (path: string) => void }) {
  const render = (nodes: FileNode[]) => nodes.map((node) => node.file ? (
    <Button key={node.path} variant="ghost" className={`h-8 w-full min-w-0 justify-start gap-2 px-2 text-xs ${selected === node.path ? "bg-accent text-primary" : "text-muted-foreground"}`} onClick={() => onSelect(node.path)} title={node.path}>
      <FileCode2 className="size-3 shrink-0" /><span className="truncate">{node.name}</span>
    </Button>
  ) : <details key={node.path} open><summary className="flex cursor-pointer items-center gap-2 py-2 text-xs"><Folder className="size-3 text-primary" />{node.name}</summary><div className="ml-3 border-l border-border pl-2">{render(node.children)}</div></details>);
  return <div aria-label="Αρχεία εφαρμογής" className="min-w-0">{render(fileTree(files))}</div>;
}