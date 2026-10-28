import { useState } from 'react';
import { History, Plus, Pencil, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { searchSessions } from './chat-sessions-model';
import type { useDashboard } from './use-dashboard';

export function ChatHistoryDrawer({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
  const [query, setQuery] = useState('');
  const [editing, setEditing] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  return <>
    <Button variant="ghost" size="icon" aria-label="Ιστορικό συνομιλιών" title="Ιστορικό συνομιλιών" onClick={() => dashboard.setHistoryOpen(true)}><History className="size-4" /></Button>
    <Sheet open={dashboard.historyOpen} onOpenChange={dashboard.setHistoryOpen}>
      <SheetContent side="right" className="flex w-full max-w-sm flex-col">
        <SheetTitle>Συνομιλίες</SheetTitle>
        <SheetDescription>Ιστορικό σε αυτόν τον browser</SheetDescription>
        <Button onClick={dashboard.newSession}><Plus className="size-4" /> Νέα συνομιλία</Button>
        <input aria-label="Αναζήτηση συνομιλιών" placeholder="Αναζήτηση συνομιλιών…" value={query} onChange={e => setQuery(e.target.value)} className="rounded-md border border-border bg-background p-2 text-sm" />
        {dashboard.storageError && <p role="alert" className="text-sm text-destructive">{dashboard.storageError}</p>}
        <div className="min-h-0 flex-1 space-y-2 overflow-y-auto">
          {searchSessions(dashboard.sessions, query).map(session => <div key={session.id} className={`flex min-w-0 items-center gap-1 rounded-md border p-2 ${session.id === dashboard.sessionId ? 'border-primary bg-accent' : 'border-border'}`}>
            {editing === session.id ? <form className="flex min-w-0 flex-1 gap-1" onSubmit={e => { e.preventDefault(); dashboard.renameSession(session.id, title); setEditing(null); }}>
              <input autoFocus aria-label="Όνομα συνομιλίας" value={title} maxLength={120} onChange={e => setTitle(e.target.value)} className="min-w-0 flex-1 rounded border border-border bg-background px-2 text-sm" />
              <Button type="submit" variant="ghost" size="icon" aria-label="Αποθήκευση ονόματος"><Check className="size-4" /></Button>
            </form> : <>
              <Button variant="ghost" onClick={() => dashboard.selectSession(session.id)} className="h-auto min-w-0 flex-1 flex-col items-start text-left"><span className="w-full truncate">{session.title}</span><span className="text-xs text-muted-foreground">{session.messages.filter(m => m.id !== 'welcome').length} μηνύματα</span></Button>
              <Button variant="ghost" size="icon" title="Μετονομασία" aria-label={`Μετονομασία ${session.title}`} onClick={() => { setEditing(session.id); setTitle(session.title); }}><Pencil className="size-4" /></Button>
            </>}
          </div>)}
          {searchSessions(dashboard.sessions, query).length === 0 && <p className="text-sm text-muted-foreground">Δεν βρέθηκαν συνομιλίες.</p>}
        </div>
      </SheetContent>
    </Sheet>
  </>;
}