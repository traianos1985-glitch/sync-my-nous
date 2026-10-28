import { useEffect, useRef, useState } from 'react';
import { UploadCloud, Search, RefreshCw, FileText, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { nousFetch } from '@/lib/nous-api';
import type { useDashboard } from './use-dashboard';

type Hit = { id: string; documentName: string; text: string; score: number };
export function KnowledgeIngestionPanel({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
  const [dragging, setDragging] = useState(false);
  const [query, setQuery] = useState('');
  const [type, setType] = useState('');
  const [relevance, setRelevance] = useState(0.2);
  const [hits, setHits] = useState<Hit[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const busy = useRef(false);
  const searchController = useRef<AbortController | null>(null);
  const loader = useRef(dashboard.loadKnowledgeDocuments);
  loader.current = dashboard.loadKnowledgeDocuments;

  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      await loader.current();
      if (!disposed) timer = setTimeout(() => void poll(), 5000);
    };
    timer = setTimeout(() => void poll(), 5000);
    return () => { disposed = true; clearTimeout(timer); searchController.current?.abort(); };
  }, []);

  const upload = async (file?: File) => {
    if (!file || busy.current) return;
    setPendingFile(file);
    setError('');
    busy.current = true;
    setUploading(true);
    try { await dashboard.uploadKnowledgeDocument(file); setPendingFile(null); }
    catch (e) { setError(e instanceof Error ? e.message : 'Το ανέβασμα απέτυχε.'); }
    finally { busy.current = false; setUploading(false); }
  };
  const search = async () => {
    if (!query.trim()) { setHits(null); return; }
    searchController.current?.abort();
    const controller = new AbortController();
    searchController.current = controller;
    setSearching(true); setError('');
    try {
      const params = new URLSearchParams({ q: query.trim(), type, min_score: String(relevance) });
      const data = await nousFetch<{ hits: Hit[] }>(`/api/knowledge/search?${params}`, { signal: controller.signal });
      if (controller.signal.aborted) return;
      if (!Array.isArray(data.hits)) throw new Error('Μη έγκυρη απάντηση αναζήτησης.');
      setHits(data.hits);
    } catch (e) { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Η αναζήτηση απέτυχε.'); }
    finally { if (searchController.current === controller) setSearching(false); }
  };
  return <div className="mt-5 space-y-4">
    <label onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); void upload(e.dataTransfer.files[0]); }} className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border border-dashed p-8 text-center ${dragging ? 'border-primary bg-accent' : 'border-border bg-background'}`}>
      {uploading ? <Loader2 className="size-7 animate-spin text-primary" /> : <UploadCloud className="size-7 text-primary" />}
      <span className="text-sm font-semibold">{uploading ? 'Ανέβασμα και ευρετηρίαση…' : 'Έγγραφα Knowledge'}</span>
      <span className="text-xs text-muted-foreground">PDF · DOCX · TXT · MD · εικόνες · έως 15 MB</span>
      <input disabled={uploading} type="file" aria-label="Ανέβασμα εγγράφου" className="sr-only" accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp" onChange={e => { void upload(e.target.files?.[0]); e.target.value = ''; }} />
    </label>
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
    {pendingFile && !uploading && <Button variant="outline" onClick={() => void upload(pendingFile)}><RefreshCw className="size-4" /> Επανάληψη: {pendingFile.name}</Button>}
    {dashboard.knowledgeUpload === 'indexed' && <p role="status" className="text-sm text-ok">Το έγγραφο ευρετηριάστηκε.</p>}
    {dashboard.knowledgeUpload === 'stored' && <p role="status" className="text-sm text-warn">Αποθηκεύτηκε χωρίς αναγνώσιμο κείμενο.</p>}
    <form onSubmit={e => { e.preventDefault(); void search(); }} className="flex flex-wrap items-end gap-2">
      <input aria-label="Αναζήτηση γνώσης" placeholder="Αναζήτηση στο περιεχόμενο…" maxLength={1000} value={query} onChange={e => setQuery(e.target.value)} className="min-w-0 flex-1 rounded-md border border-border bg-background p-2 text-sm" />
      <select aria-label="Τύπος εγγράφου" value={type} onChange={e => setType(e.target.value)} className="max-w-full rounded-md border border-border bg-background p-2 text-sm"><option value="">Όλοι οι τύποι</option value="application/pdf">PDF</option><option value="text/">Κείμενα</option><option value="image/">Εικόνες</option><option value="application/vnd.openxmlformats-officedocument.wordprocessingml.document">DOCX</option></select>
      <label className="text-xs text-muted-foreground">Συνάφεια {Math.round(relevance * 100)}%<input aria-label="Ελάχιστη συνάφεια" type="range" min="0" max="1" step="0.05" value={relevance} onChange={e => setRelevance(Number(e.target.value))} className="block w-28 accent-primary" /></label>
      <Button type="submit" disabled={searching || uploading} size="icon" title="Αναζήτηση" aria-label="Εκτέλεση αναζήτησης γνώσης">{searching ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}</Button>
    </form>
    <div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">{dashboard.knowledgeDocuments.length} έγγραφα · {dashboard.knowledgeDocuments.filter(d => d.status === 'indexed').length} ευρετηριασμένα</p><Button variant="ghost" size="icon" title="Ανανέωση εγγράφων" aria-label="Ανανέωση εγγράφων" onClick={() => void dashboard.loadKnowledgeDocuments()}><RefreshCw className="size-4" /></Button></div>
    {dashboard.knowledgeLoadStatus === 'error' && <p role="alert" className="text-sm text-destructive">Δεν ήταν δυνατή η ανανέωση εγγράφων.</p>}
    {hits !== null ? <div className="space-y-3">{hits.length === 0 && <p className="text-sm text-muted-foreground">Δεν βρέθηκαν αποτελέσματα με αυτά τα φίλτρα.</p>}{hits.map(hit => <article key={hit.id} className="rounded-md border border-border p-3"><p className="break-words text-sm font-semibold">{hit.documentName} <span className="text-xs text-primary">{Math.round(hit.score * 100)}%</span></p><p className="mt-2 whitespace-pre-wrap break-words text-xs text-muted-foreground">{hit.text}</p></article>)}</div> : <div className="space-y-2">{dashboard.knowledgeDocuments.map(doc => <div key={doc.id} className="flex min-w-0 items-center gap-3 rounded-md border border-border p-3"><FileText className="size-4 shrink-0 text-primary" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{doc.originalName}</p><p className="text-xs text-muted-foreground">{Math.ceil(doc.sizeBytes / 1024)} KB</p></div><span className="shrink-0 text-xs text-primary">{doc.status}</span></div>)}{dashboard.knowledgeDocuments.length === 0 && <p className="text-sm text-muted-foreground">Δεν υπάρχουν έγγραφα.</p>}</div>}
  </div>;
}