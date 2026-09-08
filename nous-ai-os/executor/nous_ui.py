def nous_dashboard_html():
    return r'''<!doctype html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOUS AI OS</title>
<style>
:root{
  --bg:#080d1c;
  --panel:#10172a;
  --panel2:#17203a;
  --card:#131c33;
  --text:#edf3ff;
  --muted:#8fa2c8;
  --line:#283552;
  --accent:#7c5cff;
  --accent2:#22d3ee;
  --ok:#22c55e;
  --bad:#ef4444;
  --warn:#f59e0b;
}
*{box-sizing:border-box}
body{
  margin:0;
  background:radial-gradient(circle at top left,#172554,#080d1c 45%);
  color:var(--text);
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}
button,input,textarea{font-family:inherit}
.app{display:grid;grid-template-columns:235px 1fr 380px;height:100vh;overflow:hidden}
.sidebar,.right{background:rgba(10,14,26,.97);border-color:var(--line);overflow:hidden}
.sidebar{border-right:1px solid var(--line)}
.right{border-left:1px solid var(--line);padding:14px}
.logo{font-size:23px;font-weight:900;margin-bottom:4px}
.sub{color:var(--muted);font-size:13px;margin-bottom:18px}
.nav button,.quick button,.miniBtn{
  width:100%;
  border:1px solid var(--line);
  background:var(--panel2);
  color:var(--text);
  padding:12px;
  margin:5px 0;
  border-radius:15px;
  text-align:left;
}
.nav button.active{border-color:var(--accent);background:rgba(124,92,255,.22)}
.nav button:hover,.quick button:hover,.miniBtn:hover{border-color:var(--accent)}
.main{display:flex;flex-direction:column;min-width:0}
.topbar{
  display:flex;align-items:center;justify-content:space-between;gap:10px;
  padding:14px 18px;border-bottom:1px solid var(--line);background:rgba(8,13,28,.8)
}
.badge{border:1px solid var(--line);border-radius:999px;padding:6px 10px;color:var(--muted);font-size:13px}
.ok{color:var(--ok)}.bad{color:var(--bad)}.warn{color:var(--warn)}
.workspace{flex:1;overflow:auto;padding:18px}
.hero{
  border:1px solid var(--line);border-radius:24px;padding:18px;
  background:linear-gradient(135deg,rgba(124,92,255,.20),rgba(34,211,238,.09));
  margin-bottom:14px;
}
.hero h1{margin:0 0 6px 0;font-size:24px}
.hero p{margin:0;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.card{
  background:rgba(19,28,51,.92);border:1px solid var(--line);border-radius:20px;
  padding:14px;margin-bottom:12px;
}
.card h3{margin:0 0 10px 0;font-size:16px}
.kv{display:flex;justify-content:space-between;gap:8px;border-bottom:1px solid rgba(255,255,255,.06);padding:7px 0;font-size:13px}
.kv span:first-child{color:var(--muted)}
.chat{display:flex;flex-direction:column;height:100%}
.chatlog{flex:1;overflow:auto;padding:18px}
.msg{max-width:900px;margin:0 auto 12px auto;padding:14px;border:1px solid var(--line);border-radius:18px;background:rgba(19,28,51,.86);white-space:pre-wrap}
.msg.user{background:rgba(124,92,255,.16)}
.composer{padding:14px;border-top:1px solid var(--line);background:rgba(8,13,28,.88)}
.composer-inner{max-width:940px;margin:auto;display:flex;gap:10px}
textarea{
  flex:1;resize:none;min-height:54px;max-height:160px;border-radius:16px;
  border:1px solid var(--line);padding:14px;background:var(--panel);color:var(--text);outline:none
}
.send{border:none;border-radius:16px;padding:0 18px;background:var(--accent);color:white;font-weight:800}
pre{white-space:pre-wrap;word-break:break-word;max-height:300px;overflow:auto;background:#070b16;border:1px solid var(--line);border-radius:12px;padding:10px;font-size:12px}
.section{display:none}
.section.active{display:block}
.activity{font-size:13px;color:var(--muted);line-height:1.45}
.menuBtn{display:none;position:fixed;top:12px;left:12px;z-index:50;width:44px;height:44px;border-radius:14px;border:1px solid var(--line);background:var(--accent);color:white;font-size:22px;font-weight:900}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:40}
.small{font-size:12px;color:var(--muted)}
.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:5px 8px;margin:3px;color:var(--muted);font-size:12px}
@media(max-width:1050px){
  .menuBtn{display:block}
  .app{grid-template-columns:1fr;height:auto;min-height:100vh;overflow:auto}
  .sidebar{position:fixed;left:-250px;top:0;bottom:0;width:240px;z-index:60;transition:left .22s ease;border-right:1px solid var(--line)}
  .sidebar.open{left:0}
  .overlay.show{display:block}
  .right{border:0;border-top:1px solid var(--line)}
  .main{min-height:100vh}
  .topbar{padding-left:64px}
  .grid{grid-template-columns:1fr}
}
</style>

<style id="nous-sidebar-css">
/* ── Flat nav items (Replit-style) ── */
.navItem{
  display:flex;align-items:center;gap:10px;
  padding:8px 10px;border-radius:8px;cursor:pointer;
  font-size:13.5px;color:var(--muted);
  border:none;background:none;width:100%;text-align:left;
  transition:background .12s,color .12s;margin:1px 0;
}
.navItem:hover{background:rgba(124,92,255,.13);color:var(--text)}
.navItem.active{
  background:rgba(124,92,255,.22);color:var(--text);
  font-weight:600;
}
.navItem .ni{width:22px;text-align:center;font-size:15px;flex-shrink:0}
.navSection{
  font-size:10.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.9px;color:var(--muted);opacity:.55;
  padding:12px 10px 3px 10px;user-select:none;
}
.navDivider{height:1px;background:var(--line);margin:7px 4px}
.navMore{display:none}
.navMore.open{display:block}
.navMoreBtn{
  display:flex;align-items:center;gap:8px;
  padding:7px 10px;border-radius:8px;cursor:pointer;
  font-size:12px;color:var(--muted);opacity:.7;
  border:none;background:none;width:100%;text-align:left;
}
.navMoreBtn:hover{opacity:1;color:var(--text)}
/* Sidebar layout */
.sidebar{display:flex;flex-direction:column;padding:0;background:rgba(10,14,26,.97)}
.sidebarTop{padding:16px 14px 10px 14px;flex-shrink:0}
.sidebarNav{flex:1;overflow-y:auto;overflow-x:hidden;padding:0 8px 8px 8px}
.sidebarNav::-webkit-scrollbar{width:3px}
.sidebarNav::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:99px}
.sidebarBottom{padding:8px 10px 10px 10px;border-top:1px solid var(--line);flex-shrink:0}
.sysStatRow{display:flex;align-items:center;gap:7px;font-size:11.5px;color:var(--muted);padding:3px 0}
.sysStatBar{flex:1;height:4px;background:rgba(255,255,255,.1);border-radius:99px;overflow:hidden}
.sysStatFill{height:100%;border-radius:99px;background:var(--accent);transition:width .5s}
</style>


<style id="nous-hide-tech-details-css">
.nousTechDetails{
  margin-top:10px;
  opacity:.75;
  font-size:12px;
}
.nousTechDetails summary{
  cursor:pointer;
  opacity:.8;
}
.nousTechDetails pre{
  display:none;
}
.nousTechDetails[open] pre{
  display:block;
  max-height:260px;
  overflow:auto;
  white-space:pre-wrap;
  padding:10px;
  border-radius:10px;
  background:rgba(0,0,0,.25);
}
</style>


<style id="nous-clean-chat-css">
  body {
    margin: 0;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }

  #chatUploadCard,
  #conversationPanel {
    margin: 8px 0;
    padding: 10px;
    border-radius: 12px;
  }

  #chatUploadCard h3,
  #conversationPanel h3 {
    margin: 0 0 8px 0;
    font-size: 15px;
  }

  #chatUploadCard p {
    display: none;
  }

  #chatUploadCard input,
  #conversationPanel select {
    font-size: 14px;
  }

  #chatUploadFile,
  #chatUploadNote {
    max-width: 100%;
    box-sizing: border-box;
  }

  .nousTopTools {
    margin: 8px 0;
  }

  .nousToolToggle {
    width: 100%;
    padding: 10px;
    border-radius: 12px;
    border: 1px solid #444;
    background: transparent;
    color: inherit;
    font-weight: 700;
  }

  .nousToolBody {
    display: none;
    margin-top: 8px;
  }

  .nousToolBody.open {
    display: block;
  }

  .chatlog,
  #chatlog {
    min-height: 52vh;
    max-height: 68vh;
    overflow-y: auto;
    padding: 10px;
    border-radius: 14px;
    border: 1px solid rgba(120,120,120,.35);
    background: rgba(0,0,0,.08);
    scroll-behavior: smooth;
  }

  .msg,
  .message,
  .chatMsg {
    max-width: 92%;
    margin: 8px 0;
    padding: 10px 12px;
    border-radius: 14px;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.35;
  }

  .user,
  .msg.user,
  .chatMsg.user {
    margin-left: auto;
    background: rgba(80,130,255,.20);
  }

  .bot,
  .assistant,
  .msg.bot,
  .chatMsg.bot {
    margin-right: auto;
    background: rgba(120,120,120,.18);
  }

  .technicalDetails,
  .rawJson,
  pre {
    max-height: 260px;
    overflow: auto;
    font-size: 12px;
    white-space: pre-wrap;
  }

  #output {
    max-height: 240px;
    overflow: auto;
    font-size: 12px;
    opacity: .85;
  }

  textarea,
  input[type="text"],
  #messageInput,
  #prompt,
  #chatInput {
    width: 100%;
    box-sizing: border-box;
    min-height: 44px;
    font-size: 16px;
    border-radius: 12px;
    padding: 10px;
  }

  button,
  .miniBtn {
    min-height: 40px;
    border-radius: 12px;
  }
</style>

</head>
<body>
<button class="menuBtn" onclick="openMenu()">☰</button>
<div class="overlay" id="overlay" onclick="closeMenu()"></div>

<div class="app">
  <aside class="sidebar" id="sidebar">

    <!-- Logo -->
    <div class="sidebarTop">
      <div class="logo" style="font-size:19px;font-weight:900;letter-spacing:-.5px">🧠 NOUS AI OS</div>
      <div style="color:var(--muted);font-size:12px;margin-top:2px">Personal agent workspace</div>
    </div>

    <!-- Navigation -->
    <nav class="sidebarNav" id="nav">

      <button class="navItem active" data-sec="chat" onclick="showSection('chat')"><span class="ni">💬</span> Chat</button>
      <button class="navItem" data-sec="home" onclick="showSection('home')"><span class="ni">🏠</span> Dashboard</button>

      <div class="navDivider"></div>
      <div class="navSection">Εργασία</div>
      <button class="navItem" data-sec="goals" onclick="showSection('goals')"><span class="ni">🎯</span> Goals</button>
      <button class="navItem" data-sec="missions" onclick="showSection('missions')"><span class="ni">📋</span> Missions</button>
      <button class="navItem" data-sec="planner" onclick="showSection('planner')"><span class="ni">🧩</span> Planner</button>
      <button class="navItem" data-sec="brain" onclick="showSection('brain')"><span class="ni">🧠</span> Brain & Memory</button>
      <button class="navItem" data-sec="appbuilder" onclick="showSection('appbuilder')"><span class="ni">🏗</span> App Builder</button>

      <div class="navDivider"></div>
      <div class="navSection">Εργαλεία</div>
      <button class="navItem" data-sec="documents" onclick="showSection('documents')"><span class="ni">📚</span> Documents</button>
      <button class="navItem" data-sec="scheduler" onclick="showSection('scheduler')"><span class="ni">⏱</span> Scheduler</button>
      <button class="navItem" data-sec="deploy" onclick="showSection('deploy')"><span class="ni">🚀</span> Deploy</button>
      <button class="navItem" data-sec="backup" onclick="showSection('backup')"><span class="ni">☁</span> Backup</button>
      <button class="navItem" data-sec="larmor" onclick="showSection('larmor');larmorLoadHistory()"><span class="ni">🧲</span> Larmor Monitor</button>
      <button class="navItem" data-sec="field" onclick="showSection('field');fieldDiaryLoad();fieldMarkersLoad()"><span class="ni">🔍</span> Πεδίο & Χάρτης</button>
      <button class="navItem" data-sec="remote-access" onclick="showSection('remote-access')"><span class="ni">📡</span> Remote Access</button>
      <button class="navItem" data-sec="settings" onclick="showSection('settings')"><span class="ni">⚙</span> Settings</button>

      <div class="navDivider"></div>
      <button class="navMoreBtn" onclick="toggleAdvancedNav()" id="moreNavBtn">
        <span style="font-size:14px">⋯</span> Προχωρημένα <span id="moreArrow" style="margin-left:auto;font-size:11px">▸</span>
      </button>
      <div class="navMore" id="advancedNav">
        <div class="navSection">Αυτοματισμός</div>
        <button class="navItem" data-sec="autoexec" onclick="showSection('autoexec')"><span class="ni">🤖</span> Auto Exec</button>
        <button class="navItem" data-sec="loopv3" onclick="showSection('loopv3')"><span class="ni">♾</span> Agent Loop</button>
        <button class="navItem" data-sec="autoscheduler" onclick="showSection('autoscheduler')"><span class="ni">🔁</span> AutoSched</button>
        <div class="navSection">Σύστημα</div>
        <button class="navItem" data-sec="diagnosis" onclick="showSection('diagnosis');diagRefresh();safetyLoad()"><span class="ni">🩺</span> Diagnosis</button>
        <button class="navItem" data-sec="repair" onclick="showSection('repair')"><span class="ni">🛠</span> Repair</button>
        <button class="navItem" data-sec="selfheal" onclick="showSection('selfheal')"><span class="ni">🧬</span> Self Heal</button>
        <button class="navItem" data-sec="intelligence" onclick="showSection('intelligence')"><span class="ni">🧭</span> Intelligence</button>
        <button class="navItem" data-sec="learning" onclick="showSection('learning')"><span class="ni">🎓</span> Learning</button>
        <button class="navItem" data-sec="system" onclick="showSection('system')"><span class="ni">📊</span> System</button>
        <button class="navItem" data-sec="command" onclick="showSection('command')"><span class="ni">⌨</span> Command</button>
        <button class="navItem" data-sec="approvals" onclick="showSection('approvals')"><span class="ni">✅</span> Approvals</button>
        <button class="navItem" data-sec="audit" onclick="showSection('audit')"><span class="ni">🧪</span> Audit</button>
        <button class="navItem" data-sec="patchapply" onclick="showSection('patchapply')"><span class="ni">🩹</span> PatchApply</button>
        <button class="navItem" data-sec="loopv2" onclick="showSection('loopv2')"><span class="ni">♻</span> Loop v2</button>
        <button class="navItem" data-sec="companion" onclick="showSection('companion')"><span class="ni">📱</span> Companion</button>
        <button class="navItem" data-sec="pending" onclick="showSection('pending')"><span class="ni">📥</span> Pending</button>
        <button class="navItem" data-sec="graphs" onclick="showSection('graphs')"><span class="ni">🕸</span> Graphs</button>
        <button class="navItem" data-sec="analyst" onclick="showSection('analyst')"><span class="ni">🧮</span> Analyst</button>
        <button class="navItem" data-sec="upgrades" onclick="showSection('upgrades')"><span class="ni">📦</span> Upgrades</button>
        <button class="navItem" data-sec="mega" onclick="showSection('mega')"><span class="ni">🧱</span> Mega</button>
      </div>

    </nav>

    <!-- Bottom: system stats -->
    <div class="sidebarBottom" id="sysBarWidget">
      <div class="sysStatRow"><span>CPU</span><div class="sysStatBar"><div class="sysStatFill" id="cpuBar" style="width:0%"></div></div><span id="cpuPct">…</span></div>
      <div class="sysStatRow"><span>RAM</span><div class="sysStatBar"><div class="sysStatFill" id="ramBar" style="width:0%;background:var(--accent2)"></div></div><span id="ramPct">…</span></div>
    </div>

  </aside>

  <main class="main">
    <div class="topbar">
      <div><strong id="title">NOUS Home</strong> <span class="badge" id="healthBadge">loading...</span></div>
      <span class="badge">Owner Mode</span>
    </div>

    <div class="workspace">
      <section id="home" class="section active">
        <div class="hero">
          <h1>Καλώς ήρθες στον ΝΟΥΣ</h1>
          <p>ChatGPT-style agent + Replit-style workspace + Android Companion + Vercel deploy.</p>
        </div>
        <div class="grid">
          <div class="card"><h3>System Snapshot</h3><div id="homeStatus">Loading...</div></div>
          <div class="card"><h3>Capabilities</h3><div id="homeCaps">Loading...</div></div>
          <div class="card"><h3>Companion</h3><div id="homeCompanion">Loading...</div></div>
          <div class="card"><h3>Missions</h3><div id="homeMissions">Loading...</div></div>
        </div>

        <!-- ── NOUS Πρωτοβουλίες ── -->
        <div class="card" style="margin-top:4px;border:1px solid rgba(139,92,246,.35);background:linear-gradient(135deg,rgba(139,92,246,.06) 0%,var(--panel) 60%);">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
            <div style="flex:1;">
              <h3 style="margin:0 0 2px;font-size:15px;">🤖 Τι θέλει να κάνει ο ΝΟΥΣ</h3>
              <div style="font-size:11px;color:var(--muted);">Αυτόνομες προτάσεις — έγκρινε ή απόρριψε</div>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              <button onclick="nousThinkNow()" style="padding:5px 12px;border-radius:8px;border:1px solid rgba(139,92,246,.5);background:rgba(139,92,246,.15);color:#a78bfa;font-size:12px;cursor:pointer;font-weight:600;">🧠 Σκέψου</button>
              <button onclick="loadNousInitiatives()" style="padding:5px 12px;border-radius:8px;border:1px solid rgba(139,92,246,.3);background:rgba(139,92,246,.07);color:#a78bfa;font-size:12px;cursor:pointer;">↺</button>
              <button onclick="nousSetTokenPrompt()" title="Ορισμός NOUS Token για authenticated actions" style="padding:5px 10px;border-radius:8px;border:1px solid rgba(251,191,36,.4);background:rgba(251,191,36,.08);color:#fbbf24;font-size:12px;cursor:pointer;">🔑</button>
            </div>
          </div>
          <div id="nousInitiativesBox">
            <div style="color:var(--muted);font-size:13px;">Φόρτωση προτάσεων…</div>
          </div>
        </div>

        <!-- ── Daily Brief ── -->
        <div class="card" style="margin-top:4px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
            <h3 style="margin:0;flex:1;">📋 Ημερήσια Αναφορά</h3>
            <button onclick="loadDailyBrief()" style="padding:5px 14px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">↺ Ανανέωση</button>
          </div>
          <div id="dailyBriefBox" style="font-size:13px;line-height:1.7;">
            <div style="color:var(--muted);">Φόρτωση αναφοράς…</div>
          </div>
        </div>
      </section>

      <section id="chat" class="section">
        <div class="chat" style="height:calc(100vh - 96px)">
          
<div class="card" id="chatUploadCard">
  <h3>📎 Upload & Learn</h3>
  <p>Ανέβασε PDF, DOCX, TXT ή εικόνα. Ο ΝΟΥΣ θα προσπαθήσει να το μάθει και μετά θα μπορείς να τον ρωτάς.</p>
  <input type="file" id="chatUploadFile" multiple>
  <input id="chatUploadNote" placeholder="Σημείωση π.χ. εγχειρίδιο αποκρύψεων" style="width:100%;padding:10px;margin-top:8px;">
  <button class="miniBtn" onclick="uploadChatFiles()">Upload & Learn</button>
</div>


<div class="card" id="conversationPanel">
  <h3>💬 Συνομιλίες</h3>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
    <button class="miniBtn" onclick="newNousConversation()">Νέα συνομιλία</button>
    <button class="miniBtn" onclick="loadNousConversations()">Ανανέωση</button>
  </div>
  <select id="nousConversationSelect" onchange="selectNousConversation()" style="width:100%;padding:10px;">
    <option value="">Νέα συνομιλία</option>
  </select>
  <div id="activeConversationLabel" style="font-size:12px;opacity:.75;margin-top:6px;">Ενεργή: νέα συνομιλία</div>
</div>

<div class="chatlog" id="chatlog">
            <div class="msg bot">👋 Γεια! Γράψε οτιδήποτε στα ελληνικά — ρώτα, συζήτα, ζήτα αναζήτηση.<br><br>Παραδείγματα:<br>• «κατάσταση» — live εικόνα συστήματος<br>• «ψάξε για τεχνητή νοημοσύνη» — web search<br>• «βοήθεια» — τι μπορώ να κάνω<br>• <code>/plan βελτίωσε το UI</code> — δημιούργησε αποστολή</div>
          </div>
          <div id="nousTypingIndicator" style="display:none;padding:6px 14px;font-size:13px;opacity:.6;font-style:italic;">ΝΟΥΣ σκέφτεται...</div>
          <div class="composer">
            <div class="composer-inner">
              <textarea id="prompt" placeholder="Γράψε στον ΝΟΥΣ... (Enter για αποστολή, Shift+Enter για νέα γραμμή)"></textarea>
              <div style="display:flex;gap:6px;align-items:center;">
                <label for="chatFileQuick" title="Upload αρχείο" style="cursor:pointer;font-size:20px;padding:4px 8px;opacity:.7;">📎</label>
                <input type="file" id="chatFileQuick" style="display:none" onchange="quickUpload(this)">
                <button id="voiceMicBtn" title="Φωνητική εισαγωγή" onclick="nousVoiceInput()" style="background:none;border:1px solid rgba(139,92,246,.4);border-radius:50%;width:36px;height:36px;font-size:17px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s;flex-shrink:0;" onmouseenter="this.style.background='rgba(139,92,246,.2)'" onmouseleave="this.style.background='none'">🎤</button>
                <button class="send" id="sendBtn" onclick="sendPrompt()">↑</button>
              </div>
            </div>
          </div>
        </div>
      </section>


      
      <section id="brain" class="section">
        <div class="hero">
          <h1>🧠 Brain State</h1>
          <p>Κεντρική εικόνα του ΝΟΥΣ: readiness, goals, missions, approvals και υγεία συστήματος.</p>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Brain Status</h3>
            <div id="brainStatus">Loading...</div>
          </div>

          <div class="card">
            <h3>Readiness</h3>
            <div id="brainReadiness">Loading...</div>
          </div>
        </div>

        <div class="card">
          <h3>Brain Snapshot</h3>
          <pre id="brainSnapshot">Loading...</pre>
        </div>
      </section>


      <section id="goals" class="section">
        <div class="hero"><h1>🏁 Goals</h1><p>Μακροπρόθεσμοι στόχοι, progress, linked missions και next actions.</p></div>
        <div class="grid">
          <div class="card">
            <h3>Goal Actions</h3>
            <button class="miniBtn" onclick="seedGoals()">Seed Core Goals</button>
            <button class="miniBtn" onclick="loadGoals()">Refresh Goals</button>
          </div>
          <div class="card"><h3>Goal Status</h3><div id="goalStatus">Loading...</div></div>
        </div>
        <div class="card"><h3>Goal List</h3><div id="goalList">Loading...</div></div>
      </section>

      <section id="missions" class="section">
        <div class="hero"><h1>🎯 Missions</h1><p>Αποστολές, αυτόνομα σχέδια, progress και εκτέλεση ασφαλών tasks.</p></div>
        <div class="grid">
          <div class="card">
            <h3>Create Mission</h3>
            <button class="miniBtn" onclick="createMission('system_check')">System Check Mission</button>
            <button class="miniBtn" onclick="createMission('android_check')">Android Companion Mission</button>
            <button class="miniBtn" onclick="createMission('deploy_check')">Deploy Mission</button>
            <textarea id="missionPrompt" placeholder="π.χ. βελτίωσε το UI του ΝΟΥΣ"></textarea>
            <button class="miniBtn" onclick="createWorkspaceMission()">Create From Prompt</button>
          </div>
          <div class="card"><h3>Mission Status</h3><div id="missionStatus">Loading...</div></div>
        </div>
        <div class="card"><h3>Mission List</h3><pre id="missionList">Loading...</pre></div>
      </section>

      <section id="approvals" class="section">
        <div class="hero"><h1>✅ Approvals</h1><p>Εδώ θα εμφανίζονται tasks που χρειάζονται έγκριση πριν εκτελεστούν.</p></div>
        <div class="card"><h3>Pending Approvals</h3><pre id="approvalsBox">Loading...</pre></div>
      </section>

      <section id="companion" class="section">
        <div class="hero"><h1>📱 Android Companion</h1><p>Χέρια και μάτια του ΝΟΥΣ στο Android μέσω Accessibility.</p></div>
        <div class="grid">
          <div class="card">
            <h3>Controls</h3>
            <button class="miniBtn" onclick="postAction('/remote/companion/home')">HOME</button>
            <button class="miniBtn" onclick="postAction('/remote/companion/back')">BACK</button>
            <button class="miniBtn" onclick="postAction('/remote/companion/ui-tree')">Request UI Tree</button>
          </div>
          <div class="card"><h3>Status</h3><div id="companionStatus">Loading...</div></div>
        </div>
      </section>

      <section id="deploy" class="section">
        <div class="hero"><h1>🚀 Deployments</h1><p>Vercel deployment backend και ιστορικό.</p></div>
        <div class="grid">
          <div class="card">
            <h3>Deploy Actions</h3>
            <button class="miniBtn" onclick="ops('vercel_status')">Vercel Status</button>
            <button class="miniBtn" onclick="ops('deploy_vercel_test_app')">Deploy Test App</button>
          </div>
          <div class="card"><h3>Vercel</h3><div id="deployStatus">Loading...</div></div>
        </div>
      </section>

      <section id="system" class="section">
        <div class="hero"><h1>📊 System</h1><p>Reality gate, ops, health και raw status.</p></div>
        <div class="grid">
          <div class="card"><h3>Reality</h3><div id="realityStatus">Loading...</div></div>
          <div class="card"><h3>Ops</h3><div id="opsStatus">Loading...</div></div>
        </div>
      </section>

      
      
      
      <section id="intelligence" class="section">
        <div class="hero">
          <h1>🧭 Executive Intelligence</h1>
          <p>Τι πιστεύει ο ΝΟΥΣ ότι πρέπει να γίνει μετά, με βάση goals, missions, approvals, decisions και lessons.</p>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Next Best Action</h3>
            <div id="nextBestAction">Loading...</div>
          </div>

          <div class="card">
            <h3>System Summary</h3>
            <div id="intelligenceSummary">Loading...</div>
          </div>
        </div>

        <div class="card">
          <h3>Recommendations</h3>
          <div id="intelligenceRecommendations">Loading...</div>
        </div>

        <div class="card">
          <h3>Executive Report</h3>
          <button class="miniBtn" onclick="loadIntelligence()">Refresh Intelligence</button>
          <pre id="executiveReport">Loading...</pre>
        </div>

        <!-- ── Decision Memory ── -->
        <div class="card">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
            <h3 style="margin:0;flex:1;">🧠 Αποφάσεις Πράκτορα</h3>
            <button onclick="loadDecisionMemory()" style="padding:5px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">↺ Refresh</button>
          </div>
          <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
            <input id="decisionSearchQ" type="text" placeholder="Αναζήτηση απόφασης…" style="flex:1;padding:7px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;" onkeydown="if(event.key==='Enter') searchDecisionMemory()">
            <button onclick="searchDecisionMemory()" style="padding:7px 14px;border-radius:8px;border:none;background:var(--accent);color:white;font-size:13px;cursor:pointer;font-weight:600;">🔍</button>
          </div>
          <div id="decisionMemoryStats" style="font-size:12px;color:var(--muted);margin-bottom:8px;"></div>
          <div id="decisionMemoryList" style="max-height:380px;overflow-y:auto;font-size:13px;"></div>
        </div>
      </section>


      <section id="learning" class="section">
        <div class="hero">
          <h1>🎓 Learning Memory</h1>
          <p>Τι έχει μάθει ο ΝΟΥΣ από missions, decisions και εκτελέσεις.</p>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Learning Status</h3>
            <div id="learningStatus">Loading...</div>
          </div>

          <div class="card">
            <h3>Search Lessons</h3>
            <textarea id="lessonSearch" placeholder="π.χ. backup, companion, mission"></textarea>
            <button class="miniBtn" onclick="searchLessons()">Search</button>
            <button class="miniBtn" onclick="loadLearning()">Refresh</button>
          </div>
        </div>

        <div class="card">
          <h3>Recent Lessons</h3>
          <div id="lessonList">Loading...</div>
        </div>

        <div class="card">
          <h3>Lesson Search Results</h3>
          <pre id="lessonSearchResults">–</pre>
        </div>

        <!-- ── Internet Learning Pipeline ── -->
        <div class="card">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
            <h3 style="margin:0;flex:1;">🌐 Αυτόνομη Μάθηση από το Ιντερνέτ</h3>
            <button onclick="loadInternetLearning()" style="padding:5px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">↺ Refresh</button>
          </div>
          <div id="internetLearningStatus" style="font-size:13px;color:var(--muted);margin-bottom:12px;">Φόρτωση…</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
            <input id="internetLearnTopic" type="text" placeholder="Θέμα (π.χ. 'Byzantine treasure signs Messenia')…" style="flex:1;padding:7px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
            <button onclick="triggerInternetLearn()" style="padding:7px 16px;border-radius:8px;border:none;background:var(--accent);color:white;font-size:13px;cursor:pointer;font-weight:700;">▶ Μάθε</button>
            <button onclick="triggerInternetLearn(true)" style="padding:7px 14px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:13px;cursor:pointer;">⚡ Επόμενο Θέμα</button>
          </div>
          <pre id="internetLearnResult" style="font-size:12px;max-height:280px;overflow-y:auto;display:none;"></pre>
        </div>
      </section>


      <section id="backup" class="section">
        <div class="hero">
          <h1>☁️ Brain Backup / Restore</h1>
          <p>Portable brain snapshots, verification και restore preview.</p>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Backup Actions</h3>
            <button class="miniBtn" onclick="createBrainBackup()">Create Brain Backup</button>
            <button class="miniBtn" onclick="loadBackupPanel()">Refresh Backups</button>
          </div>

          <div class="card">
            <h3>Restore Status</h3>
            <div id="restoreStatus">Loading...</div>
          </div>
        </div>

        <div class="card">
          <h3>Available Backups</h3>
          <div id="backupList">Loading...</div>
        </div>

        <div class="card">
          <h3>Backup Inspection</h3>
          <pre id="backupInspect">–</pre>
        </div>
      </section>


      <section id="settings" class="section">
        <div class="hero"><h1>⚙ Settings</h1><p>Owner token και local UI ρυθμίσεις.</p></div>
        <div class="card">
          <h3>Token</h3>
          <button class="miniBtn" onclick="setToken()">Set / Change Token</button>
          <button class="miniBtn" onclick="localStorage.removeItem('NOUS_TOKEN');alert('Token cleared')">Clear Token</button>
        </div>
      </section>
    </div>
  
      <section id="scheduler" class="section">
        <div class="hero">
          <h1>⏱ Executive Scheduler</h1>
          <p>Safe executive review loop.</p>
        </div>

        <div class="card">
          <button class="miniBtn" onclick="schedulerRunOnce()">Run Once</button>
          <button class="miniBtn" onclick="schedulerStart()">Start</button>
          <button class="miniBtn" onclick="schedulerStop()">Stop</button>
          <button class="miniBtn" onclick="loadScheduler()">Refresh</button>
        </div>

        <div class="card">
          <h3>Status</h3>
          <pre id="schedulerStatus">Loading...</pre>
        </div>
      </section>


      <section id="planner" class="section">
        <div class="hero">
          <h1>🧩 Mission Planner</h1>
          <p>Ο ΝΟΥΣ προτείνει αποστολές για goals, και εσύ τις εγκρίνεις ή τις απορρίπτεις.</p>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Planner Actions</h3>
            <button class="miniBtn" onclick="proposeMission()">➕ Propose New Mission</button>
            <button class="miniBtn" onclick="loadPlanner()">🔄 Refresh</button>
          </div>

          <div class="card">
            <h3>Planner Status</h3>
            <div id="plannerStatus">Loading...</div>
          </div>
        </div>

        <div class="card">
          <h3>Mission Proposals</h3>
          <div id="plannerProposals">Loading...</div>
        </div>
      </section>


      <section id="audit" class="section">
        <div class="hero">
          <h1>🧪 Dashboard Action Audit</h1>
          <p>Έλεγχος ότι τα βασικά κουμπιά/endpoints του NOUS απαντούν σωστά.</p>
        </div>
        <div class="card">
          <button class="miniBtn" onclick="runDashboardAudit()">Run Button Audit</button>
        </div>
        <div class="card">
          <h3>Audit Results</h3>
          <pre id="auditResults">–</pre>
        </div>
      </section>


      <!-- ══════════════════════════════════════════════════════ -->
      <!-- 🩺  SELF DIAGNOSIS + REPAIR  (unified section)       -->
      <!-- ══════════════════════════════════════════════════════ -->
      <section id="diagnosis" class="section">

        <div class="hero">
          <h1>🩺 Αυτοδιάγνωση ΝΟΥΣ</h1>
          <p>Ο ΝΟΥΣ σαρώνει τον εαυτό του, εντοπίζει αδυναμίες και προτείνει διορθώσεις — μόνο με δική σου έγκριση.</p>
        </div>

        <!-- ── Action bar ── -->
        <div class="card" style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:14px 18px;">
          <button id="diagRunBtn" onclick="diagRun()"
            style="padding:9px 20px;border-radius:10px;border:none;background:var(--accent);color:white;font-weight:700;font-size:14px;cursor:pointer;">
            🔍 Εκτέλεση Διάγνωσης
          </button>
          <button onclick="diagAiAnalyze()"
            style="padding:9px 20px;border-radius:10px;border:1px solid rgba(34,211,238,.4);background:rgba(34,211,238,.08);color:#22d3ee;font-weight:600;font-size:13px;cursor:pointer;">
            🤖 AI Ανάλυση &amp; Προτάσεις
          </button>
          <button onclick="diagRefresh()"
            style="padding:9px 16px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:13px;cursor:pointer;">
            ↺ Refresh
          </button>
          <span id="diagRunning" style="font-size:12px;color:var(--muted);display:none;">⏳ Τρέχει…</span>
        </div>

        <!-- ── Summary bar ── -->
        <div id="diagSummaryBar" style="display:none;">
          <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;">
            <div id="diagBadgeOk"   style="padding:8px 18px;border-radius:10px;font-size:13px;font-weight:700;background:rgba(34,197,94,.12);color:#22c55e;border:1px solid rgba(34,197,94,.25);">✅ OK</div>
            <div id="diagBadgeCrit" style="padding:8px 18px;border-radius:10px;font-size:13px;font-weight:700;background:rgba(239,68,68,.12);color:#ef4444;border:1px solid rgba(239,68,68,.25);display:none;">🔴 <span id="diagCritN">0</span> Κρίσιμα</div>
            <div id="diagBadgeWarn" style="padding:8px 18px;border-radius:10px;font-size:13px;font-weight:700;background:rgba(234,179,8,.12);color:#eab308;border:1px solid rgba(234,179,8,.25);display:none;">🟡 <span id="diagWarnN">0</span> Προειδοποιήσεις</div>
            <div id="diagBadgeInfo" style="padding:8px 18px;border-radius:10px;font-size:13px;font-weight:700;background:rgba(99,102,241,.10);color:#818cf8;border:1px solid rgba(99,102,241,.2);display:none;">ℹ️ <span id="diagInfoN">0</span> Πληροφορίες</div>
            <div id="diagTimeLbl"  style="margin-left:auto;font-size:11px;color:var(--muted);align-self:center;"></div>
          </div>
        </div>

        <!-- ── Issues list ── -->
        <div id="diagIssuesList"></div>

        <!-- ── AI Analysis result ── -->
        <div id="diagAiBox" style="display:none;" class="card">
          <h3 style="margin:0 0 12px;font-size:14px;">🤖 AI Ανάλυση</h3>
          <div id="diagAiSummary" style="font-size:13px;line-height:1.7;margin-bottom:16px;padding:12px;background:rgba(34,211,238,.06);border-radius:10px;border:1px solid rgba(34,211,238,.15);"></div>
          <div id="diagAiProposals"></div>
        </div>

        <!-- ── Repair Proposals ── -->
        <div class="card">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
            <h3 style="margin:0;font-size:14px;">🛠 Προτάσεις Διόρθωσης</h3>
            <button onclick="diagProposeRepair()"
              style="padding:6px 14px;border-radius:8px;border:1px solid rgba(124,92,255,.4);background:rgba(124,92,255,.1);color:#a78bfa;font-size:12px;cursor:pointer;">
              + Δημιούργησε Πρόταση
            </button>
            <button onclick="diagLoadRepair()"
              style="padding:6px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">
              ↺
            </button>
          </div>
          <div id="diagRepairStatus" style="font-size:12px;color:var(--muted);margin-bottom:10px;"></div>
          <div id="diagRepairList"><div style="color:var(--muted);font-size:13px;text-align:center;padding:20px 0;">Δεν υπάρχουν ακόμα προτάσεις. Εκτέλεσε πρώτα διάγνωση.</div></div>
        </div>

        <!-- ════════════════════════════════════════════════════════ -->
        <!-- 🛡️  ΔΙΚΛΕΙΔΑ ΑΣΦΑΛΕΙΑΣ  (Safety Net / Circuit Breaker) -->
        <!-- ════════════════════════════════════════════════════════ -->
        <div class="card" style="margin-top:6px;border:1px solid rgba(34,197,94,.2);background:rgba(34,197,94,.03);">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
            <h3 style="margin:0;font-size:14px;">🛡️ Δικλείδα Ασφαλείας</h3>
            <div id="safetyCircuitBadge" style="padding:4px 12px;border-radius:8px;font-size:12px;font-weight:700;background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3);">● ΚΛΕΙΣΤΟΣ</div>
            <button onclick="safetyLoad()"
              style="padding:5px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;margin-left:auto;">
              ↺ Refresh
            </button>
            <button id="safetyResetBtn" onclick="safetyCircuitReset()" style="display:none;padding:5px 14px;border-radius:8px;border:none;background:#ef4444;color:white;font-size:12px;font-weight:700;cursor:pointer;">
              ⚡ Reset Circuit
            </button>
          </div>

          <!-- Stats row -->
          <div id="safetyStatsRow" style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;">
            <div style="flex:1;min-width:100px;padding:10px;background:var(--panel2);border-radius:10px;text-align:center;">
              <div style="font-size:20px;font-weight:800;color:#22c55e;" id="safetyStatOk">–</div>
              <div style="font-size:11px;color:var(--muted);">Επιτυχίες</div>
            </div>
            <div style="flex:1;min-width:100px;padding:10px;background:var(--panel2);border-radius:10px;text-align:center;">
              <div style="font-size:20px;font-weight:800;color:#ef4444;" id="safetyStatFail">–</div>
              <div style="font-size:11px;color:var(--muted);">Αποτυχίες</div>
            </div>
            <div style="flex:1;min-width:100px;padding:10px;background:var(--panel2);border-radius:10px;text-align:center;">
              <div style="font-size:20px;font-weight:800;color:#a78bfa;" id="safetyStatRollback">–</div>
              <div style="font-size:11px;color:var(--muted);">Rollbacks</div>
            </div>
            <div style="flex:1;min-width:140px;padding:10px;background:var(--panel2);border-radius:10px;text-align:center;">
              <div style="font-size:13px;font-weight:700;color:var(--muted);" id="safetyStatCircuitFail">–</div>
              <div style="font-size:11px;color:var(--muted);">Circuit failures</div>
            </div>
          </div>

          <!-- How it works -->
          <details style="margin-bottom:12px;">
            <summary style="font-size:12px;color:var(--muted);cursor:pointer;user-select:none;">ℹ️ Πώς λειτουργεί η δικλείδα ασφαλείας;</summary>
            <div style="font-size:12px;color:var(--text);line-height:1.7;margin-top:8px;padding:10px;background:var(--panel2);border-radius:8px;">
              <b>Πριν κάθε αυτόνομη αλλαγή:</b><br>
              1️⃣ <b>Backup</b> — αντίγραφα όλων των αρχείων-στόχων<br>
              2️⃣ <b>Εφαρμογή</b> — η αλλαγή εκτελείται κανονικά<br>
              3️⃣ <b>Validation</b> — compile check + import check<br>
              4️⃣α Αν <b>ΕΠΙΤΥΧΙΑ</b> → καταγραφή λύσης, μηδενισμός counter<br>
              4️⃣β Αν <b>ΑΠΟΤΥΧΙΑ</b> → <span style="color:#ef4444;font-weight:700;">αυτόματο restore</span> + καταγραφή λάθους<br>
              <br>
              <b>Circuit Breaker:</b> Μετά από 3 αποτυχίες, ο ΝΟΥΣ <span style="color:#ef4444;">παγώνει</span> αυτόνομες ενέργειες για 2 λεπτά ή μέχρι χειροκίνητο reset.
            </div>
          </details>

          <!-- Incident log -->
          <div style="font-weight:700;font-size:12px;margin-bottom:8px;color:var(--muted);">📋 Ιστορικό Ενεργειών</div>
          <div id="safetyIncidentList" style="max-height:360px;overflow-y:auto;">
            <div style="color:var(--muted);font-size:13px;text-align:center;padding:20px 0;">Φόρτωση…</div>
          </div>
        </div>

        <!-- ── Project Health Snapshot ── -->
        <div class="card" style="margin-top:14px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
            <h3 style="margin:0;flex:1;">🏥 Project Health Snapshot</h3>
            <button onclick="runProjectHealth()" style="padding:7px 18px;border-radius:8px;border:none;background:var(--accent);color:white;font-weight:700;font-size:13px;cursor:pointer;">▶ Εκτέλεση</button>
            <button onclick="loadProjectHealth()" style="padding:5px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">↺ Refresh</button>
          </div>
          <div id="projectHealthSummary" style="margin-bottom:10px;font-size:13px;"></div>
          <pre id="projectHealthBox" style="font-size:12px;max-height:320px;overflow-y:auto;display:none;"></pre>
        </div>

      </section>

      <!-- Repair keeps working as hidden alias -->
      <section id="repair" class="section" style="display:none!important;"></section>


      <section id="autoexec" class="section">
        <div class="hero">
          <h1>🤖 Auto Mission Executor</h1>
          <p>Εκτελεί μόνο ασφαλείς, allowlisted αποστολές χωρίς deploy, tap, restore ή destructive actions.</p>
        </div>

        <div class="grid">
          <div class="card">
            <h3>AutoExec Actions</h3>
            <button class="miniBtn" onclick="loadAutoExec()">Refresh</button>
            <button class="miniBtn" onclick="runAutoExec()">Run Safe Cycle</button>
            <button class="miniBtn" onclick="enableAutoExec()">Enable</button>
            <button class="miniBtn" onclick="disableAutoExec()">Disable</button>
          </div>
          <div class="card">
            <h3>Status</h3>
            <div id="autoExecStatus">Loading...</div>
          </div>
        </div>

        <div class="card">
          <h3>Safe Candidates</h3>
          <pre id="autoExecCandidates">Loading...</pre>
        </div>

        <div class="card">
          <h3>Blocked / Needs Approval</h3>
          <pre id="autoExecBlocked">Loading...</pre>
        </div>
      </section>


      <section id="autoscheduler" class="section">
        <div class="hero">
          <h1>🔁 Auto Mission Scheduler</h1>
          <p>Τρέχει αυτόματα safe auto mission cycles σε χρονικό διάστημα.</p>
        </div>
        <div class="card">
          <button class="miniBtn" onclick="loadAutoScheduler()">Refresh</button>
          <button class="miniBtn" onclick="runAutoSchedulerOnce()">Run Once</button>
          <button class="miniBtn" onclick="startAutoScheduler()">Start</button>
          <button class="miniBtn" onclick="stopAutoScheduler()">Stop</button>
        </div>
        <div class="card">
          <h3>Status</h3>
          <pre id="autoSchedulerStatus">Loading...</pre>
        </div>
      </section>

      <section id="analyst" class="section">
        <div class="hero">
          <h1>🧠 Code Analyst</h1>
          <p>Αναλύει failures, βρίσκει πιθανή αιτία και προτείνει candidate files χωρίς να αλλάζει κώδικα.</p>
        </div>
        <div class="card">
          <button class="miniBtn" onclick="analyzeLatestDiagnosis()">Analyze Latest Diagnosis</button>
          <button class="miniBtn" onclick="loadCodeAnalyst()">Refresh</button>
        </div>
        <div class="card">
          <h3>Reports</h3>
          <pre id="codeAnalystReports">Loading...</pre>
        </div>
      </section>


      <section id="pending" class="section">
        <div class="hero">
          <h1>📥 Pending Review Inbox</h1>
          <p>Όλα όσα περιμένουν την έγκρισή σου από Planner, Repair, Approvals και Executive Intelligence.</p>
        </div>
        <div class="card">
          <button class="miniBtn" onclick="loadPendingReview()">Refresh Pending</button>
        </div>
        <div class="card">
          <h3>Pending Summary</h3>
          <div id="pendingSummary">Loading...</div>
        </div>
        <div class="card">
          <h3>Pending Items</h3>
          <div id="pendingItems">Loading...</div>
        </div>
      </section>

      <section id="loopv2" class="section">
        <div class="hero">
          <h1>♻ Executive Loop v2</h1>
          <p>Τρέχει diagnosis, code analysis, repair proposal, mission planner, safe execution και goal progress.</p>
        </div>
        <div class="card">
          <button class="miniBtn" onclick="runExecutiveLoopV2()">Run Executive Loop v2</button>
          <button class="miniBtn" onclick="loadExecutiveLoopV2()">Refresh</button>
        </div>
        <div class="card">
          <h3>Loop v2 Status</h3>
          <pre id="loopV2Status">Loading...</pre>
        </div>
      </section>


      <section id="command" class="section">
        <div class="hero">
          <h1>🧭 Executive Command Center</h1>
          <p>Κεντρική οθόνη ελέγχου: pending, goals, missions, diagnosis, repair, auto executor και backups.</p>
        </div>

        <div class="card">
          <button class="miniBtn" onclick="loadCommandCenter()">Refresh Command Center</button>
          <button class="miniBtn" onclick="runCommandCycle()">🚀 Run Executive Cycle</button>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Command Summary</h3>
            <div id="commandSummary">Loading...</div>
          </div>
          <div class="card">
            <h3>Next Best Action</h3>
            <div id="commandNextAction">Loading...</div>
          </div>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Pending Inbox</h3>
            <div id="commandPending">Loading...</div>
          </div>
          <div class="card">
            <h3>Automation State</h3>
            <div id="commandAutomation">Loading...</div>
          </div>
        </div>

        <div class="card">
          <h3>Full Command Data</h3>
          <pre id="commandFull">Loading...</pre>
        </div>
      </section>


      <section id="selfheal" class="section">
        <div class="hero">
          <h1>🧬 Self-Healing Lab</h1>
          <p>Deep code analysis, patch proposals και safe apply μόνο με έγκριση.</p>
        </div>

        <div class="card">
          <button class="miniBtn" onclick="runSelfHealing()">Run Self-Healing Analysis</button>
          <button class="miniBtn" onclick="loadSelfHealing()">Refresh</button>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Status</h3>
            <div id="selfHealingStatus">Loading...</div>
          </div>
          <div class="card">
            <h3>Patch Proposals</h3>
            <div id="patchProposals">Loading...</div>
          </div>
        </div>

        <div class="card">
          <h3>Full Self-Healing Data</h3>
          <pre id="selfHealingFull">Loading...</pre>
        </div>
      </section>


      <section id="mega" class="section">
        <div class="hero">
          <h1>🧱 Mega Systems</h1>
          <p>Cleanup Engine, Goal Manager V2 και Executive Memory V3.</p>
        </div>
        <div class="grid">
          <div class="card">
            <h3>Cleanup Engine</h3>
            <button class="miniBtn" onclick="cleanupPreview()">Preview Cleanup</button>
            <button class="miniBtn" onclick="cleanupApply()">Apply Cleanup</button>
            <pre id="cleanupBox">–</pre>
          </div>
          <div class="card">
            <h3>Goal Manager V2</h3>
            <button class="miniBtn" onclick="generateGoalProjects()">Generate Projects</button>
            <button class="miniBtn" onclick="loadMegaSystems()">Refresh</button>
            <pre id="goalManagerBox">–</pre>
          </div>
        </div>
        <div class="card">
          <h3>Executive Memory V3</h3>
          <button class="miniBtn" onclick="learnExecutiveMemory()">Learn From Current State</button>
          <pre id="execMemoryBox">–</pre>
        </div>
      </section>

      <section id="upgrades" class="section">
        <div class="hero">
          <h1>📦 Upgrade Planner</h1>
          <p>Ο ΝΟΥΣ προτείνει μεγάλα upgrade packs και τα βάζει σε pending review.</p>
        </div>
        <div class="card">
          <button class="miniBtn" onclick="proposeUpgradePlan()">Propose Upgrade Plan</button>
          <button class="miniBtn" onclick="loadUpgradePlans()">Refresh</button>
        </div>
        <div class="card">
          <h3>Upgrade Plans</h3>
          <div id="upgradePlansBox">Loading...</div>
        </div>
      </section>


      <section id="patchapply" class="section">
        <div class="hero"><h1>🩹 Patch Apply & Rollback</h1><p>Εφαρμογή approved patch με backup, validation και rollback.</p></div>
        <div class="card">
          <button class="miniBtn" onclick="loadPatchApply()">Refresh</button>
        </div>
        <div class="grid">
          <div class="card"><h3>Patch Apply</h3><pre id="patchApplyBox">Loading...</pre></div>
          <div class="card"><h3>Rollback</h3><pre id="rollbackBox">Loading...</pre></div>
        </div>
      </section>

      <section id="graphs" class="section">
        <div class="hero"><h1>🕸 Repository & Knowledge Graph</h1><p>Χάρτης αρχείων, routes, functions, goals, missions και lessons.</p></div>
        <div class="card">
          <button class="miniBtn" onclick="buildRepoGraph()">Build Repository Graph</button>
          <button class="miniBtn" onclick="buildKnowledgeGraph()">Build Knowledge Graph</button>
          <button class="miniBtn" onclick="loadGraphs()">Refresh</button>
        </div>
        <div class="grid">
          <div class="card"><h3>Repository Graph</h3><pre id="repoGraphBox">Loading...</pre></div>
          <div class="card"><h3>Knowledge Graph</h3><pre id="knowledgeGraphBox">Loading...</pre></div>
        </div>
      </section>

      <section id="loopv3" class="section">
        <div class="hero"><h1>👑 Executive Loop V3</h1><p>Observe → Diagnose → Analyze → Plan → Execute → Learn.</p></div>
        <div class="card">
          <button class="miniBtn" onclick="runLoopV3()">Run Executive Loop V3</button>
          <button class="miniBtn" onclick="loadLoopV3()">Refresh</button>
        </div>
        <div class="card"><pre id="loopV3Box">Loading...</pre></div>
      </section>

      <section id="appbuilder" class="section">
        <div class="hero">
          <h1>🏗️ Autonomous App Builder</h1>
          <p>Περιέγραψε οποιαδήποτε εφαρμογή στα ελληνικά — ο ΝΟΥΣ γράφει τον πλήρη κώδικα. Εσύ εγκρίνεις πριν γραφτεί οτιδήποτε.</p>
        </div>
        <div class="card">
          <h3>Νέα Εφαρμογή</h3>
          <textarea id="appBuilderPrompt" rows="3" placeholder="π.χ. φτιάξε Flask API που διαβάζει CSV και επιστρέφει JSON" style="width:100%;padding:10px;background:#1a1a1a;color:#e0e0e0;border:1px solid #333;border-radius:8px;font-size:14px;"></textarea>
          <div style="margin-top:8px;display:flex;gap:8px;">
            <button class="miniBtn" onclick="startAppBuild()" id="appBuildBtn">🚀 Σχεδίασε &amp; Δημιούργησε</button>
            <button class="miniBtn" onclick="loadAppBuilderList()">🔄 Refresh</button>
          </div>
          <div id="appBuilderStatus" style="margin-top:10px;font-size:13px;opacity:.7;"></div>
        </div>
        <div class="card">
          <h3>📋 Ιστορικό Builds</h3>
          <div id="appBuilderList">Φόρτωση...</div>
        </div>
        <div class="card">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <h3 style="margin:0;flex:1;">📁 Φάκελος Εφαρμογών — <code style="font-size:13px;color:#22d3ee;">apps/</code></h3>
            <button onclick="loadAppFiles()" style="padding:5px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">↺ Ανανέωση</button>
          </div>
          <div id="appFilesBrowser" style="font-size:13px;color:var(--muted);">Φόρτωση…</div>
        </div>
        <div class="card" id="appBuilderPreview" style="display:none;">
          <h3>👁️ Preview Σχεδίου</h3>
          <div id="appBuilderPreviewContent"></div>
        </div>
      </section>

      <section id="larmor" class="section">
        <div class="hero" style="background:linear-gradient(135deg,rgba(34,211,238,.18),rgba(124,92,255,.12));margin-bottom:12px;">
          <h1 style="margin:0 0 4px 0;">🧲 Larmor Monitor</h1>
          <p style="margin:0;color:var(--muted);">Read-only σύνδεση με τον Υπολογιστή Συχνότητας Larmor — παρακολούθηση, ανάλυση και προτάσεις έρευνας.</p>
        </div>

        <!-- ── Status bar Row 1: status + link + refresh ── -->
        <div class="card" style="padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
          <span style="font-size:12px;color:var(--muted);white-space:nowrap;">Κατάσταση:</span>
          <span id="larmorStatus" style="font-size:13px;color:var(--muted);flex:1;min-width:80px;">⏳ Έλεγχος…</span>
          <a href="https://insta-giveaway-bot-1--traianos1985.replit.app" target="_blank"
             style="font-size:12px;color:var(--accent2);text-decoration:none;border:1px solid rgba(34,211,238,.3);padding:5px 12px;border-radius:8px;white-space:nowrap;">
            🔗 Άνοιγμα ↗
          </a>
          <button onclick="larmorPing()" style="padding:5px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);cursor:pointer;font-size:12px;white-space:nowrap;">↺ Refresh</button>
        </div>

        <!-- ── Knowledge inject buttons Row 2 ── -->
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;">
          <button onclick="larmorInjectKnowledge()" id="larmorInjectBtn"
            style="padding:7px 14px;border-radius:8px;border:1px solid rgba(34,211,238,.4);background:rgba(34,211,238,.08);color:var(--accent2);cursor:pointer;font-size:12px;font-weight:600;">
            🧠 Γνώση NMR
          </button>
          <button onclick="injectCacheKnowledge()" id="cacheInjectBtn"
            style="padding:7px 14px;border-radius:8px;border:1px solid rgba(251,191,36,.4);background:rgba(251,191,36,.08);color:#fbbf24;cursor:pointer;font-size:12px;font-weight:600;">
            ⚔️ SF Caching
          </button>
          <button onclick="injectGuerrillaKnowledge()" id="guerrillaInjectBtn"
            style="padding:7px 14px;border-radius:8px;border:1px solid rgba(52,211,153,.4);background:rgba(52,211,153,.08);color:#34d399;cursor:pointer;font-size:12px;font-weight:600;">
            🗺️ Σημάδια &amp; Χάρτες
          </button>
        </div>

        <!-- ── Main grid: iframe LEFT | tabs RIGHT ── -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start;">

          <!-- LEFT: Embed iframe -->
          <div class="card" style="padding:0;overflow:hidden;">
            <div style="padding:10px 14px;border-bottom:1px solid var(--line);font-size:13px;font-weight:700;color:var(--muted);">
              👁 Live View — Read Only
            </div>
            <iframe
              src="https://insta-giveaway-bot-1--traianos1985.replit.app"
              style="width:100%;height:600px;border:none;background:#fff;display:block;"
              sandbox="allow-scripts allow-same-origin allow-forms"
              title="Larmor Frequency Calculator - Read Only">
            </iframe>
          </div>

          <!-- RIGHT: Tab panel -->
          <div style="display:flex;flex-direction:column;gap:0;">

            <!-- Tab switcher -->
            <div style="display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap;">
              <button id="ltab-calc" onclick="larmorTab('calc')"
                style="padding:7px 16px;border-radius:10px;border:1px solid rgba(34,211,238,.5);background:rgba(34,211,238,.15);color:#22d3ee;font-weight:700;cursor:pointer;font-size:13px;">
                🔢 Υπολογιστές
              </button>
              <button id="ltab-chat" onclick="larmorTab('chat')"
                style="padding:7px 16px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-weight:600;cursor:pointer;font-size:13px;">
                💬 Chat &amp; Εικόνες
              </button>
            </div>

            <!-- ── TAB: CALCULATORS ── -->
            <div id="larmor-tab-calc" style="display:flex;flex-direction:column;gap:12px;">

              <!-- Quick Calculator -->
              <div class="card">
                <h3 style="margin:0 0 12px 0;font-size:14px;">⚡ Γρήγορος Υπολογισμός NMR</h3>
                <div style="display:flex;flex-direction:column;gap:8px;">
                  <select id="larmorMaterial" style="padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
                    <option value="au-pure">197Au — Χρυσός καθαρός (0.7379 MHz/T)</option>
                    <option value="ottoman-5lira">Ottoman 5 Lira 91.7% Au (1.6155 MHz/T)</option>
                    <option value="22k-alloy">22K Κράμα Λίρας (1.619 MHz/T)</option>
                    <option value="ag">109Ag — Άργυρος (1.989 MHz/T)</option>
                    <option value="cu" selected>63Cu — Χαλκός (11.311 MHz/T)</option>
                    <option value="al">27Al — Αλουμίνιο (11.101 MHz/T)</option>
                    <option value="fe">57Fe — Σίδηρος (1.382 MHz/T)</option>
                    <option value="ammo-box">55Mn — WWII box (10.571 MHz/T)</option>
                    <option value="ba-137">137Ba — Χειροβομβίδες (4.763 MHz/T)</option>
                    <option value="sn-119">119Sn — Κασσίτερος (15.945 MHz/T)</option>
                    <option value="sb-121">121Sb — Αντιμόνιο (10.239 MHz/T)</option>
                    <option value="b-11">11B — Βόριο (13.662 MHz/T)</option>
                  </select>
                  <div style="display:flex;gap:8px;align-items:center;">
                    <label style="font-size:12px;color:var(--muted);white-space:nowrap;">B (Tesla):</label>
                    <input id="larmorBField" type="number" value="0.04823" step="0.00001"
                      style="flex:1;padding:7px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
                    <button onclick="larmorCalculate()" style="padding:7px 16px;border-radius:8px;border:none;background:var(--accent);color:white;font-size:13px;cursor:pointer;white-space:nowrap;font-weight:600;">
                      ⚡ Υπολόγισε
                    </button>
                  </div>
                </div>
                <div id="larmorCalcResult" style="margin-top:10px;font-size:13px;display:none;"></div>
              </div>

              <!-- Paste & Analyze -->
              <div class="card">
                <h3 style="margin:0 0 8px 0;font-size:14px;">🔬 Ανάλυση Δεδομένων</h3>
                <p style="font-size:12px;color:var(--muted);margin:0 0 8px 0;">
                  Επικόλλησε αποτελέσματα Larmor — ο ΝΟΥΣ αναλύει με NMR γνώση.
                </p>
                <textarea id="larmorPasteData" rows="4"
                  style="width:100%;padding:10px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;resize:vertical;box-sizing:border-box;"
                  placeholder="π.χ.: 63Cu, B=0.04823T, fL=0.546 kHz, Αρμ.3=1.638 kHz, Βάθος=1.5m…"></textarea>
                <input id="larmorQuestion" type="text"
                  style="width:100%;margin-top:6px;padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;box-sizing:border-box;"
                  placeholder="Ερώτηση (προαιρ.): «Ποια αρμονική για βάθος 2m;»">
                <button onclick="larmorAnalyze()"
                  style="width:100%;margin-top:8px;padding:10px;border-radius:8px;border:none;background:linear-gradient(135deg,var(--accent),var(--accent2));color:white;font-size:14px;font-weight:700;cursor:pointer;">
                  🧠 Ανάλυσε με ΝΟΥΣ
                </button>
                <div id="larmorAnalysisResult" style="margin-top:12px;font-size:13px;line-height:1.6;display:none;"></div>
              </div>

              <!-- Classical EM Resonance Calculator -->
              <div class="card" style="border-color:rgba(34,211,238,.25);">
                <h3 style="margin:0 0 4px 0;font-size:14px;">⚡ ΗΜ Συντονισμός Faraday/Lenz</h3>
                <p style="font-size:11px;color:var(--muted);margin:0 0 10px 0;">
                  Βέλτιστη συχνότητα για eddy current — ανεξάρτητα από NMR.
                </p>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                  <div>
                    <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px;">Υλικό στόχου</label>
                    <select id="emMetal" style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;">
                      <option value="22k_alloy">Λίρα 22K (Au+Cu)</option>
                      <option value="au">Χρυσός (Au)</option>
                      <option value="ag">Άργυρος (Ag)</option>
                      <option value="cu">Χαλκός (Cu)</option>
                      <option value="bronze">Μπρούντζος αρχαίος</option>
                      <option value="fe_pure">Σίδηρος (Fe)</option>
                      <option value="steel">Χάλυβας/WWII</option>
                      <option value="brass">Ορείχαλκος</option>
                      <option value="pb">Μόλυβδος (Pb)</option>
                    </select>
                  </div>
                  <div>
                    <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px;">Ακτίνα στόχου (cm)</label>
                    <select id="emRadius" style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;">
                      <option value="1.1">1.1 cm — μεμ. νόμισμα</option>
                      <option value="2.0">2.0 cm — λίγα νομίσματα</option>
                      <option value="3.0" selected>3.0 cm — χούφτα</option>
                      <option value="5.0">5.0 cm — κεραμικό</option>
                      <option value="8.0">8.0 cm — κιβωτάκι λιρών</option>
                      <option value="12.0">12.0 cm — αγγείο</option>
                      <option value="20.0">20.0 cm — WWII κιβώτιο</option>
                    </select>
                  </div>
                  <div>
                    <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px;">Βάθος (m)</label>
                    <input id="emDepth" type="number" value="1.5" step="0.1" min="0.1"
                      style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;box-sizing:border-box;">
                  </div>
                  <div>
                    <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px;">Τύπος εδάφους</label>
                    <select id="emSoil" style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;">
                      <option value="rock">Βραχώδες (σ=0.00001)</option>
                      <option value="dry_sand">Ξηρό/Αμμώδες (σ=0.001)</option>
                      <option value="medium" selected>Μέτριο/Υγρό (σ=0.01)</option>
                      <option value="wet_clay">Υγρό/Αργιλώδες (σ=0.05)</option>
                      <option value="saturated">Κορεσμένο (σ=0.1)</option>
                    </select>
                  </div>
                  <div>
                    <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px;">Ηλικία ταφής</label>
                    <select id="emAge" style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;">
                      <option value="recent">Πρόσφατο (0-20 χρ.)</option>
                      <option value="guerrilla" selected>Αντάρτικα 1940-50</option>
                      <option value="ottoman">Οθωμανικό (&lt;1900)</option>
                      <option value="ancient">Αρχαίο (&gt;500 χρ.)</option>
                    </select>
                  </div>
                  <div style="display:flex;align-items:flex-end;">
                    <button onclick="emCalcRun()" style="width:100%;padding:8px;border-radius:6px;border:none;background:linear-gradient(135deg,rgba(34,211,238,.6),rgba(139,92,246,.6));color:white;font-size:13px;font-weight:700;cursor:pointer;">
                      ⚡ f_optimal
                    </button>
                  </div>
                </div>
                <div id="emCalcResult" style="display:none;margin-top:8px;"></div>
              </div>

            </div><!-- end larmor-tab-calc -->

            <!-- ── TAB: CHAT & IMAGES ── -->
            <div id="larmor-tab-chat" style="display:none;">

              <!-- Chat container: full flex column, bounded by viewport -->
              <div id="larmorChatBox"
                style="display:flex;flex-direction:column;border-radius:14px;border:1px solid var(--line);background:var(--panel);overflow:hidden;max-height:72vh;min-height:0;">

                <!-- ── Header ── -->
                <div style="padding:10px 14px;background:var(--panel2);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:8px;flex-shrink:0;cursor:pointer;" onclick="larmorChatToggleMin()">
                  <span style="font-size:16px;">🧲</span>
                  <span style="font-weight:700;font-size:13px;flex:1;">Chat ΝΟΥΣ — Σημεία Ενδιαφέροντος</span>
                  <!-- history label -->
                  <span id="larmorHistoryLbl" style="font-size:10px;color:var(--muted);margin-right:6px;"></span>
                  <!-- minimize toggle -->
                  <button id="larmorMinBtn" onclick="event.stopPropagation();larmorChatToggleMin()"
                    title="Ελαχιστοποίηση / Επαναφορά"
                    style="padding:3px 8px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--muted);font-size:13px;cursor:pointer;line-height:1;flex-shrink:0;">
                    ▾
                  </button>
                  <!-- clear -->
                  <button onclick="event.stopPropagation();larmorChatClear()"
                    title="Καθαρισμός ιστορικού"
                    style="padding:3px 8px;border-radius:6px;border:1px solid rgba(239,68,68,.35);background:rgba(239,68,68,.07);color:#ef4444;font-size:12px;cursor:pointer;line-height:1;flex-shrink:0;">
                    🗑
                  </button>
                </div>

                <!-- ── Collapsible body ── -->
                <div id="larmorChatBody" style="display:flex;flex-direction:column;flex:1;min-height:0;overflow:hidden;">

                  <!-- Chat log -->
                  <div id="larmorChatLog"
                    style="flex:1;overflow-y:auto;padding:14px 16px;display:flex;flex-direction:column;gap:10px;min-height:0;scroll-behavior:smooth;">
                    <div data-placeholder="1" style="text-align:center;color:var(--muted);font-size:13px;padding:30px 0 20px;">
                      <div style="font-size:36px;margin-bottom:10px;">🧲</div>
                      <div>Ρώτα τον ΝΟΥΣ για NMR, σημάδια<br>ή ανέβασε φωτογραφία σημείου.</div>
                    </div>
                  </div>

                  <!-- Image preview bar (shown when image staged) -->
                  <div id="larmorImgPreviewBar" style="display:none;padding:8px 14px;border-top:1px solid var(--line);background:var(--panel2);flex-shrink:0;">
                    <div style="display:flex;align-items:center;gap:10px;">
                      <img id="larmorImgPreviewThumb" style="height:48px;width:48px;object-fit:cover;border-radius:6px;border:1px solid var(--line);" src="" alt="">
                      <div style="flex:1;min-width:0;">
                        <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">📎 Εικόνα επισυνάφθηκε — τύπος ανάλυσης:</div>
                        <select id="larmorImgAnalysisType"
                          style="width:100%;padding:4px 8px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;">
                          <option value="signs">🔣 Σημάδια/Σύμβολα</option>
                          <option value="terrain">🏔️ Έδαφος/Τοπίο</option>
                          <option value="map">🗺️ Παλιός Χάρτης</option>
                          <option value="rock">🪨 Χαράγματα σε Βράχο</option>
                          <option value="artifact">✨ Εύρημα</option>
                          <option value="general">🔍 Γενική</option>
                        </select>
                      </div>
                      <button onclick="larmorChatCancelImg()"
                        style="padding:5px 9px;border-radius:6px;border:1px solid rgba(239,68,68,.4);background:rgba(239,68,68,.08);color:#ef4444;font-size:13px;cursor:pointer;flex-shrink:0;">✕</button>
                    </div>
                  </div>

                  <!-- Input bar -->
                  <div style="padding:10px 12px;border-top:1px solid var(--line);background:var(--panel2);flex-shrink:0;">
                    <div style="display:flex;gap:8px;align-items:flex-end;">
                      <button onclick="document.getElementById('larmorChatImgInput').click()"
                        title="Επισύναψη εικόνας"
                        style="padding:8px 11px;border-radius:10px;border:1px solid rgba(34,211,238,.4);background:rgba(34,211,238,.08);color:#22d3ee;font-size:17px;cursor:pointer;flex-shrink:0;line-height:1;align-self:flex-end;">
                        📎
                      </button>
                      <input type="file" id="larmorChatImgInput" accept="image/*" style="display:none"
                        onchange="larmorChatStageImg(this)">
                      <textarea id="larmorChatInput" rows="1"
                        style="flex:1;padding:9px 12px;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;resize:none;line-height:1.55;max-height:120px;overflow-y:auto;"
                        placeholder="Γράψε μήνυμα… (Enter = αποστολή, Shift+Enter = νέα γραμμή)"
                        oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,120)+'px';"
                        onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();larmorChatSend();}"></textarea>
                      <button onclick="larmorChatSend()"
                        style="padding:9px 15px;border-radius:10px;border:none;background:var(--accent);color:white;font-size:16px;cursor:pointer;flex-shrink:0;font-weight:700;line-height:1;align-self:flex-end;">
                        ➤
                      </button>
                    </div>
                  </div>

                </div><!-- end larmorChatBody -->
              </div><!-- end larmorChatBox -->

            </div><!-- end larmor-tab-chat -->

          </div><!-- end right panel -->
        </div><!-- end main grid -->
      </section>

      <section id="remote-access" class="section">
        <div class="hero">
          <h1>📱 Απομακρυσμένη Πρόσβαση</h1>
          <p>Ένα κλικ και ο ΝΟΥΣ γίνεται προσβάσιμος από το κινητό σου — από οπουδήποτε.</p>
        </div>

        <!-- TUNNEL CONTROL PANEL -->
        <div class="card" id="tunnelCard" style="border:2px solid #2a4a6a;margin-bottom:12px;">
          <h3>🚇 Δημόσιο URL — Ξεκίνα εδώ</h3>
          <div id="tunnelStatus" style="margin-bottom:14px;padding:12px;background:#111;border-radius:8px;font-size:13px;">
            Έλεγχος κατάστασης...
          </div>

          <!-- Αν δεν έχει token — εμφανίζεται -->
          <div id="tokenSetupBox" style="display:none;margin-bottom:14px;">
            <div style="font-size:13px;margin-bottom:8px;">
              👤 Πρώτη φορά; <a href="https://ngrok.com" target="_blank" style="color:#6cf;">Φτιάξε δωρεάν λογαριασμό</a> και αντέγραψε το Authtoken σου:
            </div>
            <div style="display:flex;gap:8px;align-items:center;">
              <input id="ngrokTokenInput" type="password" placeholder="Επικόλλησε το ngrok authtoken εδώ..."
                style="flex:1;padding:9px 12px;background:#1a1a1a;color:#e0e0e0;border:1px solid #444;border-radius:8px;font-size:13px;font-family:monospace;" />
              <button class="miniBtn" onclick="saveTunnelToken()" style="white-space:nowrap;">💾 Αποθήκευση</button>
            </div>
            <div id="tokenSaveMsg" style="font-size:12px;margin-top:6px;color:#6c8;"></div>
          </div>

          <div style="display:flex;gap:10px;flex-wrap:wrap;">
            <button id="tunnelStartBtn" class="miniBtn" onclick="startTunnel()"
              style="background:#1a4a2a;border-color:#2a7a4a;font-size:14px;padding:10px 20px;">
              🚀 Ξεκίνα Tunnel
            </button>
            <button id="tunnelStopBtn" class="miniBtn" onclick="stopTunnel()"
              style="background:#4a1a1a;border-color:#7a2a2a;font-size:14px;padding:10px 20px;display:none;">
              ⏹ Σταμάτα
            </button>
            <button class="miniBtn" onclick="checkTunnel()" style="padding:10px 14px;">🔄</button>
          </div>

          <!-- QR Code + URL εφόσον τρέχει -->
          <div id="tunnelUrlBox" style="display:none;margin-top:16px;padding:14px;background:#0a2a1a;border-radius:10px;border:1px solid #2a6a3a;">
            <div style="font-size:12px;color:#888;margin-bottom:6px;">🌍 Δημόσιο URL:</div>
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
              <a id="tunnelUrlLink" href="#" target="_blank"
                style="font-size:18px;font-weight:700;color:#4cf;word-break:break-all;text-decoration:none;"></a>
              <button onclick="copyTunnelUrl()" style="font-size:11px;padding:4px 10px;background:#1a3a2a;border:1px solid #2a5a3a;color:#aaa;border-radius:6px;cursor:pointer;">📋 Αντιγραφή</button>
            </div>
            <div style="margin-top:12px;">
              <div style="font-size:12px;color:#888;margin-bottom:6px;">📱 Σκάναρε με το κινητό:</div>
              <canvas id="tunnelQR" width="140" height="140" style="background:#fff;border-radius:6px;padding:4px;"></canvas>
            </div>
            <div style="margin-top:10px;font-size:12px;color:#6a8a6a;">
              ✅ Ο ΝΟΥΣ είναι τώρα προσβάσιμος από οπουδήποτε. Μοιράσου αυτό το URL μόνο με εμπιστευτικά άτομα.
            </div>
          </div>
        </div>

        <div class="grid">
          <div class="card">
            <h3>📊 Πόροι Υπολογιστή Τώρα</h3>
            <div id="sysInfoFull" style="font-size:13px;line-height:2;">Φόρτωση...</div>
            <button class="miniBtn" onclick="loadSysInfo()" style="margin-top:10px;">🔄 Ανανέωση</button>
          </div>
          <div class="card">
            <h3>⚙️ Ελάχιστες Απαιτήσεις</h3>
            <div style="font-size:13px;line-height:2.1;">
              <div>🖥️ <strong>CPU:</strong> Οποιοσδήποτε (dual-core 1GHz+)</div>
              <div>🧠 <strong>RAM:</strong> 512MB ελάχιστο — 2GB+ ιδανικό</div>
              <div>💾 <strong>Δίσκος:</strong> 500MB ελεύθερα</div>
              <div>🌐 <strong>Δίκτυο:</strong> Οποιαδήποτε σύνδεση internet</div>
              <div>🐍 <strong>Python:</strong> 3.10 ή νεότερο</div>
              <div style="margin-top:8px;padding:8px;background:#1a3a1a;border-radius:6px;font-size:12px;">
                💡 Ο ΝΟΥΣ χρησιμοποιεί <strong>~80-150MB RAM</strong> σε αδράνεια.
                Η CPU φορτώνεται <strong>μόνο</strong> όταν επεξεργάζεται αίτημα.
              </div>
            </div>
          </div>
        </div>

        <div class="grid">
          <div class="card">
            <h3>🚇 Μέθοδος 1: ngrok (Πιο Εύκολη)</h3>
            <p style="font-size:13px;opacity:.8;margin-bottom:12px;">Δίνει δημόσιο URL — πρόσβαση από <strong>οπουδήποτε</strong></p>
            <div style="font-size:13px;line-height:2;">
              <div>1️⃣ Φτιάξε δωρεάν λογαριασμό: <a href="https://ngrok.com" target="_blank" style="color:#6cf;">ngrok.com</a></div>
              <div>2️⃣ Κατέβασε και εγκατάστησε το ngrok</div>
              <div>3️⃣ Τρέξε:</div>
              <pre style="background:#111;padding:8px;border-radius:6px;font-size:12px;margin:4px 0;">ngrok config add-authtoken YOUR_TOKEN</pre>
              <div>4️⃣ Ξεκίνα το tunnel:</div>
              <pre style="background:#111;padding:8px;border-radius:6px;font-size:12px;margin:4px 0;"># Windows:
deploy\\remote_access\\setup_ngrok_windows.bat

# Mac/Linux:
bash deploy/remote_access/setup_ngrok_mac_linux.sh</pre>
              <div>5️⃣ Αντέγραψε το <code>https://xxx.ngrok-free.app</code> → κινητό</div>
            </div>
            <div style="margin-top:10px;padding:8px;background:#2a1a1a;border-radius:6px;font-size:12px;">
              ⚠️ Δωρεάν: URL αλλάζει σε κάθε εκκίνηση. Για σταθερό URL → Tailscale ή ngrok $10/μήνα.
            </div>
          </div>

          <div class="card">
            <h3>🔒 Μέθοδος 2: Tailscale (Πιο Ασφαλής)</h3>
            <p style="font-size:13px;opacity:.8;margin-bottom:12px;">Ιδιωτικό VPN — σταθερό URL, κανείς άλλος δεν βλέπει τον ΝΟΥΣ</p>
            <div style="font-size:13px;line-height:2;">
              <div>1️⃣ Φτιάξε δωρεάν λογαριασμό: <a href="https://tailscale.com" target="_blank" style="color:#6cf;">tailscale.com</a></div>
              <div>2️⃣ Εγκατάστησε στον υπολογιστή:</div>
              <pre style="background:#111;padding:8px;border-radius:6px;font-size:12px;margin:4px 0;"># Linux:
bash deploy/remote_access/setup_tailscale.sh
# Windows/Mac: κατέβασε από tailscale.com/download</pre>
              <div>3️⃣ Εγκατάστησε <strong>Tailscale app</strong> στο κινητό (iOS/Android)</div>
              <div>4️⃣ Συνδέσου με τον <strong>ίδιο λογαριασμό</strong></div>
              <div>5️⃣ Βρες την Tailscale IP του PC (π.χ. <code>100.x.x.x</code>)</div>
              <div>6️⃣ Άνοιξε: <code>http://100.x.x.x:5000</code></div>
            </div>
            <div style="margin-top:10px;padding:8px;background:#1a2a1a;border-radius:6px;font-size:12px;">
              ✅ Δωρεάν έως 100 συσκευές. Σταθερή IP. Λειτουργεί πάντα.
            </div>
          </div>
        </div>

        <div class="card">
          <h3>📋 Σύγκριση Επιλογών</h3>
          <table style="width:100%;font-size:13px;border-collapse:collapse;">
            <tr style="border-bottom:1px solid #333;color:#888;">
              <th style="text-align:left;padding:8px 4px;"></th>
              <th style="padding:8px;">ngrok (δωρεάν)</th>
              <th style="padding:8px;">Tailscale</th>
              <th style="padding:8px;">VPS</th>
            </tr>
            <tr style="border-bottom:1px solid #222;">
              <td style="padding:8px 4px;">💰 Κόστος</td>
              <td style="padding:8px;text-align:center;">€0</td>
              <td style="padding:8px;text-align:center;">€0</td>
              <td style="padding:8px;text-align:center;">~€4/μήνα</td>
            </tr>
            <tr style="border-bottom:1px solid #222;">
              <td style="padding:8px 4px;">🌍 Από παντού</td>
              <td style="padding:8px;text-align:center;">✅</td>
              <td style="padding:8px;text-align:center;">✅</td>
              <td style="padding:8px;text-align:center;">✅</td>
            </tr>
            <tr style="border-bottom:1px solid #222;">
              <td style="padding:8px 4px;">⏰ 24/7 online</td>
              <td style="padding:8px;text-align:center;">❌ (PC ανοιχτό)</td>
              <td style="padding:8px;text-align:center;">❌ (PC ανοιχτό)</td>
              <td style="padding:8px;text-align:center;">✅</td>
            </tr>
            <tr style="border-bottom:1px solid #222;">
              <td style="padding:8px 4px;">🔒 Ασφάλεια</td>
              <td style="padding:8px;text-align:center;">Καλή</td>
              <td style="padding:8px;text-align:center;">Εξαιρετική</td>
              <td style="padding:8px;text-align:center;">Καλή</td>
            </tr>
            <tr>
              <td style="padding:8px 4px;">⚡ Ταχύτητα setup</td>
              <td style="padding:8px;text-align:center;">5 λεπτά</td>
              <td style="padding:8px;text-align:center;">10 λεπτά</td>
              <td style="padding:8px;text-align:center;">30 λεπτά</td>
            </tr>
          </table>
        </div>
      </section>

</main>

  <aside class="right">
    <div class="card"><h3>Activity Feed</h3><div class="activity" id="activity">Ready.</div></div>
  </aside>
</div>

<script src="https://cdn.jsdelivr.net/npm/qrcode/build/qrcode.min.js"></script>
<script>
const tokenKey="NOUS_TOKEN";
let currentSection="home";

function token(){
  let t=localStorage.getItem(tokenKey);
  if(!t){ t=prompt("Βάλε NOUS token για protected actions:"); if(t)localStorage.setItem(tokenKey,t); }
  return t||"";
}
function setToken(){ const t=prompt("NOUS token:", localStorage.getItem(tokenKey)||""); if(t)localStorage.setItem(tokenKey,t); }
function nousSetTokenPrompt(){
  const cur=localStorage.getItem(tokenKey)||"";
  const t=prompt("🔑 NOUS Token (π.χ. nous_PTuD…)\nΑντέγραψε το token που έβαλες στο Termux:", cur);
  if(t===null) return;
  if(t.trim()){
    localStorage.setItem(tokenKey,t.trim());
    alert("✅ Token αποθηκεύτηκε! Τώρα μπορείς να εγκρίνεις προτάσεις.");
  } else {
    localStorage.removeItem(tokenKey);
    alert("🔓 Token αφαιρέθηκε — open access mode.");
  }
}
function openMenu(){document.getElementById("sidebar").classList.add("open");document.getElementById("overlay").classList.add("show")}
function closeMenu(){document.getElementById("sidebar").classList.remove("open");document.getElementById("overlay").classList.remove("show")}
function renderObject(obj){document.getElementById("raw").textContent=JSON.stringify(obj,null,2)}
function feed(text){document.getElementById("activity").innerHTML=new Date().toLocaleTimeString()+" — "+text+"<br>"+document.getElementById("activity").innerHTML}
function kv(k,v){return `<div class="kv"><span>${k}</span><b>${v}</b></div>`}
function addMsg(text,cls=""){const c=document.getElementById("chatlog");const d=document.createElement("div");d.className="msg "+cls;if(window.NOUS_RENDER_CLEAN_MESSAGE){window.NOUS_RENDER_CLEAN_MESSAGE(d,text)}else{d.textContent=(typeof text==="object"?JSON.stringify(text):String(text))}c.appendChild(d);c.scrollTop=c.scrollHeight}

function showSection(id){
  closeMenu(); currentSection=id;
  document.querySelectorAll(".section").forEach(x=>x.classList.remove("active"));
  const sec=document.getElementById(id);
  if(sec) sec.classList.add("active");
  document.querySelectorAll(".navItem").forEach(x=>x.classList.remove("active"));
  const btn=document.querySelector(`.navItem[data-sec="${id}"]`);
  if(btn){
    btn.classList.add("active");
    /* auto-open advanced panel if section is inside it */
    const adv=document.getElementById("advancedNav");
    if(adv && adv.contains(btn)) adv.classList.add("open");
  }
  const labels={home:"Dashboard",chat:"Chat",goals:"Goals",missions:"Missions",planner:"Planner",brain:"Brain & Memory",appbuilder:"App Builder","remote-access":"Remote Access",documents:"Documents",scheduler:"Scheduler",deploy:"Deploy",backup:"Backup",settings:"Settings",autoexec:"Auto Exec",loopv3:"Agent Loop",autoscheduler:"AutoSched",diagnosis:"Diagnosis",repair:"Repair",selfheal:"Self Heal",intelligence:"Intelligence",learning:"Learning",system:"System",command:"Command",approvals:"Approvals",audit:"Audit",patchapply:"PatchApply",loopv2:"Loop v2",companion:"Companion",pending:"Pending",graphs:"Graphs",analyst:"Analyst",upgrades:"Upgrades",mega:"Mega"};
  document.getElementById("title").textContent="NOUS — "+(labels[id]||id.charAt(0).toUpperCase()+id.slice(1));
  refreshSection(id);
}
function toggleAdvancedNav(){
  const adv=document.getElementById("advancedNav");
  const arrow=document.getElementById("moreArrow");
  adv.classList.toggle("open");
  arrow.textContent=adv.classList.contains("open")?"▾":"▸";
}

async function refreshSection(id){
  if(id==="home") return loadHome();
  if(id==="brain") return loadBrain();
  if(id==="goals") return loadGoals();
  if(id==="missions") return loadMissions();
  if(id==="companion") return loadCompanion();
  if(id==="deploy") return loadDeploy();
  if(id==="system") return loadSystem();
  if(id==="approvals") return loadApprovals();
  if(id==="larmor") return larmorPing();
}


function getToken(){
  return localStorage.getItem("NOUS_TOKEN") || "";
}

function authHeaders(extra){
  const t = getToken();
  const h = Object.assign({"Content-Type":"application/json"}, extra || {});
  if(t){
    h["X-NOUS-Token"] = t;
    h["Authorization"] = "Bearer " + t;
  }
  return h;
}

async function getJson(url){
  const r = await fetch(url, {headers: authHeaders({})});
  const data = await r.json().catch(()=>({error:"invalid_json"}));
  if(!r.ok){
    const err = {ok:false, status:r.status, error:data.error || "request_failed", url, data};
    renderObject(err);
    feed("GET failed " + r.status + " " + url);
    return err;
  }
  return data;
}

// Silent version — for background polling (no feed logging on failure)
async function getJsonSilent(url){
  try{
    const r = await fetch(url, {headers: authHeaders({})});
    if(!r.ok) return {ok:false, status:r.status};
    return await r.json().catch(()=>({ok:false}));
  }catch(e){ return {ok:false}; }
}

async function postJson(url, body){
  const r = await fetch(url, {
    method:"POST",
    headers: authHeaders({}),
    body: JSON.stringify(body || {})
  });
  const data = await r.json().catch(()=>({error:"invalid_json"}));
  // Only log to feed when the HTTP status itself indicates failure (not 2xx)
  if(!r.ok){
    const err = {ok:false, status:r.status, error:data.error || "request_failed", url, data};
    renderObject(err);
    feed("POST failed " + r.status + " " + url + (data.error ? " — " + data.error : ""));
    return err;
  }
  return data;
}


async function loadHome(){
  const st=await getJson("/remote/status"); const ms=await getJson("/remote/missions/status"); const cp=await getJson("/remote/companion/status"); const rt=await getJson("/remote/reality/status");
  document.getElementById("homeStatus").innerHTML=kv("status","online")+kv("keys",Object.keys(st).length);
  document.getElementById("homeCaps").innerHTML=kv("internet",rt.internet?.real?"✅":"❌")+kv("android intents",rt.android?.real_intents?"✅":"❌")+kv("gestures",rt.android?.real_gestures?"✅":"❌");
  document.getElementById("homeCompanion").innerHTML=kv("available",cp.available?"✅":"❌")+kv("commands",(cp.commands||[]).join(", "));
  document.getElementById("homeMissions").innerHTML=kv("total",ms.total)+kv("active",ms.active)+kv("done",ms.done)+kv("blocked",ms.blocked);
  renderObject({status:st,missions:ms,companion:cp,reality:rt});
}






function sysBar(pct, color){
  const w = Math.round(pct);
  return `<div style="background:#222;border-radius:4px;height:6px;margin:2px 0 6px;">
    <div style="width:${w}%;background:${color};height:6px;border-radius:4px;transition:width .5s;"></div>
  </div>`;
}

// ── LARMOR MONITOR ──────────────────────────────────────────────────────────
let larmorChatHistory = [];
let _larmorStagedImgB64 = null;
let _larmorStagedImgMime = "image/jpeg";

// ── Larmor tab switcher ──
function larmorTab(tab){
  ["calc","chat"].forEach(t=>{
    const el  = document.getElementById("larmor-tab-"+t);
    const btn = document.getElementById("ltab-"+t);
    if(!el||!btn) return;
    const active = t===tab;
    el.style.display = active ? (t==="calc"?"flex":"block") : "none";
    if(active){
      btn.style.borderColor="rgba(34,211,238,.5)";
      btn.style.background="rgba(34,211,238,.15)";
      btn.style.color="#22d3ee";
    } else {
      btn.style.borderColor="var(--line)";
      btn.style.background="var(--panel2)";
      btn.style.color="var(--muted)";
    }
  });
}

// ── Chat: stage image ──
function larmorChatStageImg(input){
  const file = input.files[0];
  if(!file) return;
  _larmorStagedImgMime = file.type || "image/jpeg";
  const reader = new FileReader();
  reader.onload = e => {
    _larmorStagedImgB64 = e.target.result.split(",")[1];
    const thumb = document.getElementById("larmorImgPreviewThumb");
    if(thumb) thumb.src = e.target.result;
    const bar = document.getElementById("larmorImgPreviewBar");
    if(bar) bar.style.display = "block";
  };
  reader.readAsDataURL(file);
  input.value = "";
}

function larmorChatCancelImg(){
  _larmorStagedImgB64 = null;
  const bar = document.getElementById("larmorImgPreviewBar");
  if(bar) bar.style.display = "none";
}

function larmorChatClear(){
  if(!confirm("Να διαγραφεί όλο το ιστορικό του chat;")) return;
  larmorChatHistory = [];
  fetch("/larmor/history",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({history:[]})}).catch(()=>{});
  const lbl = document.getElementById("larmorHistoryLbl");
  if(lbl) lbl.textContent = "";
  const log = document.getElementById("larmorChatLog");
  if(log) log.innerHTML = `<div data-placeholder="1" style="text-align:center;color:var(--muted);font-size:13px;padding:30px 0 20px;">
    <div style="font-size:36px;margin-bottom:10px;">🧲</div>
    <div>Ρώτα τον ΝΟΥΣ για NMR, σημάδια<br>ή ανέβασε φωτογραφία σημείου.</div>
  </div>`;
}

// ── Minimize / expand chat ──
let _larmorMinimized = false;
function larmorChatToggleMin(){
  _larmorMinimized = !_larmorMinimized;
  const body = document.getElementById("larmorChatBody");
  const btn  = document.getElementById("larmorMinBtn");
  if(body) body.style.display = _larmorMinimized ? "none" : "flex";
  if(btn)  btn.textContent   = _larmorMinimized ? "▸" : "▾";
}

// ── Persist history to server ──
async function larmorSaveHistory(){
  try{
    await fetch("/larmor/history",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({history:larmorChatHistory})});
  }catch(e){}
}

// ── Restore history from server on section open ──
async function larmorLoadHistory(){
  try{
    const r = await fetch("/larmor/history");
    const d = await r.json();
    if(!d.ok || !Array.isArray(d.history) || d.history.length===0) return;
    larmorChatHistory = d.history;
    const log = document.getElementById("larmorChatLog");
    if(!log) return;
    log.innerHTML = "";
    // Replay all messages from history
    for(const msg of larmorChatHistory){
      if(msg.role==="user"){
        const tmp = document.createElement("div");
        tmp.style.cssText="margin:4px 0;display:flex;justify-content:flex-end;";
        tmp.innerHTML=`<div style="max-width:85%;background:rgba(124,92,255,.18);padding:8px 12px;border-radius:14px 14px 4px 14px;font-size:13px;">${escHtml(msg.content)}</div>`;
        log.appendChild(tmp);
      } else {
        const tmp = document.createElement("div");
        tmp.style.cssText="margin:4px 0;display:flex;align-items:flex-start;gap:8px;";
        tmp.innerHTML=`<div style="width:28px;height:28px;border-radius:50%;background:rgba(34,211,238,.15);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">🧲</div>
        <div style="max-width:88%;background:rgba(34,211,238,.08);padding:10px 13px;border-radius:14px 14px 14px 4px;font-size:13px;line-height:1.65;white-space:pre-wrap;">${_lcMd(msg.content)}</div>`;
        log.appendChild(tmp);
      }
    }
    log.scrollTop = log.scrollHeight;
    const lbl = document.getElementById("larmorHistoryLbl");
    if(lbl){
      const pairs = Math.floor(larmorChatHistory.length/2);
      lbl.textContent = `📂 ${pairs} μήνυμα${pairs===1?"":"τα"} αποθηκευμένα`;
    }
  }catch(e){}
}

function _lcAppend(html){
  const log = document.getElementById("larmorChatLog");
  if(!log) return;
  const ph = log.querySelector("[data-placeholder]");
  if(ph) ph.remove();
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  log.appendChild(tmp.firstElementChild || tmp);
  log.scrollTop = log.scrollHeight;
}

function _lcMd(text){
  return text
    .replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>")
    .replace(/\n/g,"<br>");
}

async function larmorPing(){
  document.getElementById("larmorStatus").textContent = "⏳ Έλεγχος…";
  try{
    const d = await getJson("/larmor/ping");
    const el = document.getElementById("larmorStatus");
    if(d.online){ el.innerHTML='<span style="color:var(--ok)">🟢 Online</span>'; }
    else{ el.innerHTML='<span style="color:var(--bad)">🔴 Offline</span> — '+( d.error||""); }
  }catch(e){ document.getElementById("larmorStatus").textContent="⚠️ Σφάλμα"; }
}

async function larmorCalculate(){
  const material = document.getElementById("larmorMaterial").value;
  const b = parseFloat(document.getElementById("larmorBField").value)||0.04823;
  const el = document.getElementById("larmorCalcResult");
  el.style.display="block"; el.textContent="⏳ Υπολογισμός…";
  try{
    const d = await postJson("/larmor/calculate", {material, b_field_T: b});
    if(d.error){ el.textContent="⚠️ "+d.error; return; }
    const top3 = d.harmonics.slice(0,5).map(h=>`n=${h.n}: ${(h.hz/1000).toFixed(3)} kHz`).join(" | ");
    el.innerHTML=`<div style="background:rgba(34,211,238,.08);border-radius:8px;padding:10px;">
      <strong>${d.material}</strong><br>
      B = ${b.toFixed(5)} T &nbsp;|&nbsp; γ/2π = ${(d.gamma_hz_per_T/1e6).toFixed(4)} MHz/T<br>
      <strong style="color:var(--accent2)">fL = ${d.f_larmor_khz.toFixed(3)} kHz (${d.f_larmor_mhz.toFixed(6)} MHz)</strong><br>
      <span style="color:var(--muted);font-size:12px">${top3}</span>
    </div>`;
  }catch(e){ el.textContent="⚠️ "+e; }
}

async function larmorAnalyze(){
  const session = document.getElementById("larmorPasteData").value.trim();
  const question = document.getElementById("larmorQuestion").value.trim();
  if(!session){ alert("Επικόλλησε δεδομένα για ανάλυση."); return; }
  const el = document.getElementById("larmorAnalysisResult");
  el.style.display="block"; el.innerHTML='<span style="color:var(--muted)">⏳ Ο ΝΟΥΣ αναλύει…</span>';
  try{
    const d = await postJson("/larmor/analyze", {session_data: session, question});
    el.innerHTML='<div style="background:rgba(124,92,255,.08);border-radius:10px;padding:12px;white-space:pre-wrap;">'+
      d.analysis.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>')+'</div>';
  }catch(e){ el.textContent="⚠️ "+e; }
}

async function larmorChatSend(){
  const input  = document.getElementById("larmorChatInput");
  const msg    = input ? input.value.trim() : "";
  const hasImg = !!_larmorStagedImgB64;
  if(!msg && !hasImg) return;
  if(input) input.value = "";

  // User bubble
  if(hasImg){
    const thumbSrc = document.getElementById("larmorImgPreviewThumb")?.src || "";
    const stagedB64 = _larmorStagedImgB64;
    const stagedMime = _larmorStagedImgMime;
    const atype = document.getElementById("larmorImgAnalysisType")?.value || "signs";
    larmorChatCancelImg();
    _lcAppend(`<div style="margin:4px 0;display:flex;justify-content:flex-end;">
      <div style="max-width:85%;background:rgba(124,92,255,.18);padding:8px 12px;border-radius:14px 14px 4px 14px;">
        ${thumbSrc?`<img src="${thumbSrc}" style="max-width:190px;max-height:150px;border-radius:8px;display:block;margin-bottom:${msg?"6px":"0"};">`:""}
        ${msg?`<span style="font-size:13px;">${escHtml(msg)}</span>`:""}
        <div style="font-size:10px;color:rgba(255,255,255,.35);margin-top:4px;text-align:right;">${new Date().toLocaleTimeString("el-GR",{hour:"2-digit",minute:"2-digit"})}</div>
      </div>
    </div>`);
    const typId = "lct-"+Date.now();
    _lcAppend(`<div id="${typId}" style="margin:4px 0;display:flex;align-items:center;gap:6px;">
      <div style="width:28px;height:28px;border-radius:50%;background:rgba(34,211,238,.15);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">🧲</div>
      <div style="background:rgba(34,211,238,.08);padding:8px 12px;border-radius:14px 14px 14px 4px;font-size:12px;color:var(--muted);">⏳ Αναλύει εικόνα…</div>
    </div>`);
    try{
      const r = await fetch("/field/analyze-image",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({image_b64:stagedB64,mime:stagedMime,analysis_type:atype,context:msg||""})});
      const d = await r.json();
      document.getElementById(typId)?.remove();
      const reply = d.ok ? (d.analysis||"—") : ("⚠️ "+(d.error||"Σφάλμα"));
      const modelLbl = d.model||"";
      larmorChatHistory.push({role:"user",content:msg?"Εικόνα + πλαίσιο: "+msg:"[Εικόνα για ανάλυση]"});
      larmorChatHistory.push({role:"assistant",content:reply});
      _lcAppend(`<div style="margin:4px 0;display:flex;align-items:flex-start;gap:8px;">
        <div style="width:28px;height:28px;border-radius:50%;background:rgba(34,211,238,.15);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">🧲</div>
        <div style="max-width:88%;background:rgba(34,211,238,.08);padding:10px 13px;border-radius:14px 14px 14px 4px;font-size:13px;line-height:1.65;white-space:pre-wrap;">
          ${_lcMd(reply)}
          ${modelLbl?`<div style="font-size:10px;color:rgba(255,255,255,.3);margin-top:6px;">🤖 ${escHtml(modelLbl)}</div>`:""}
        </div>
      </div>`);
      larmorSaveHistory();
      { const p=Math.floor(larmorChatHistory.length/2); const l=document.getElementById("larmorHistoryLbl"); if(l) l.textContent=`📂 ${p} μηνύματα`; }
    }catch(e){
      document.getElementById(typId)?.remove();
      _lcAppend(`<div style="margin:4px 0;color:var(--bad);font-size:12px;padding:0 8px;">⚠️ ${escHtml(String(e))}</div>`);
    }
  } else {
    larmorChatHistory.push({role:"user",content:msg});
    _lcAppend(`<div style="margin:4px 0;display:flex;justify-content:flex-end;">
      <div style="max-width:85%;background:rgba(124,92,255,.18);padding:8px 12px;border-radius:14px 14px 4px 14px;font-size:13px;">
        ${escHtml(msg)}
        <div style="font-size:10px;color:rgba(255,255,255,.35);margin-top:4px;text-align:right;">${new Date().toLocaleTimeString("el-GR",{hour:"2-digit",minute:"2-digit"})}</div>
      </div>
    </div>`);
    const typId = "lct-"+Date.now();
    _lcAppend(`<div id="${typId}" style="margin:4px 0;display:flex;align-items:center;gap:6px;">
      <div style="width:28px;height:28px;border-radius:50%;background:rgba(34,211,238,.15);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">🧲</div>
      <div style="background:rgba(34,211,238,.08);padding:8px 12px;border-radius:14px 14px 14px 4px;font-size:12px;color:var(--muted);">⏳ ΝΟΥΣ σκέφτεται…</div>
    </div>`);
    try{
      const d = await postJson("/larmor/chat",{conversation:larmorChatHistory});
      document.getElementById(typId)?.remove();
      const reply = d.reply||"—";
      larmorChatHistory.push({role:"assistant",content:reply});
      _lcAppend(`<div style="margin:4px 0;display:flex;align-items:flex-start;gap:8px;">
        <div style="width:28px;height:28px;border-radius:50%;background:rgba(34,211,238,.15);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">🧲</div>
        <div style="max-width:88%;background:rgba(34,211,238,.08);padding:10px 13px;border-radius:14px 14px 14px 4px;font-size:13px;line-height:1.65;white-space:pre-wrap;">
          ${_lcMd(reply)}
        </div>
      </div>`);
      larmorSaveHistory();
      { const p=Math.floor(larmorChatHistory.length/2); const l=document.getElementById("larmorHistoryLbl"); if(l) l.textContent=`📂 ${p} μηνύματα`; }
    }catch(e){
      document.getElementById(typId)?.remove();
      _lcAppend(`<div style="margin:4px 0;color:var(--bad);font-size:12px;padding:0 8px;">⚠️ ${escHtml(String(e))}</div>`);
    }
  }
}

async function emCalcRun(){
  const metal  = document.getElementById("emMetal").value;
  const radius = parseFloat(document.getElementById("emRadius").value);
  const depth  = parseFloat(document.getElementById("emDepth").value);
  const soil   = document.getElementById("emSoil").value;
  const age    = document.getElementById("emAge").value;
  const box    = document.getElementById("emCalcResult");
  box.style.display="block";
  box.innerHTML = '<div style="color:var(--muted);font-size:12px;">⏳ Υπολογισμός…</div>';
  try{
    const d = await postJson("/larmor/em-calculator",{metal,radius_cm:radius,depth_m:depth,soil,age});
    if(d.error){ box.innerHTML=`<div style="color:var(--bad);">⚠️ ${d.error}</div>`; return; }
    const pen = d.fully_penetrated
      ? `<span style="color:var(--ok)">✅ Πλήρης διείσδυση εντός αντικειμένου (δ_μετ=${d.delta_metal_mm}mm ≥ a=${(radius*10).toFixed(0)}mm)</span>`
      : `<span style="color:#f80">⚠️ Μερική διείσδυση δ_μετ=${d.delta_metal_mm}mm &lt; a=${(radius*10).toFixed(0)}mm — εξωτερική στρώση μόνο</span>`;
    const tbl = d.size_table.map(r=>
      `<tr><td style="padding:2px 8px;color:var(--muted)">${r.radius_cm}cm</td><td style="padding:2px 8px;color:var(--accent2);font-weight:700">${r.f_char_hz} Hz</td></tr>`
    ).join("");
    box.innerHTML = `
    <div style="background:var(--panel);border-radius:10px;padding:12px;border:1px solid rgba(34,211,238,.2);">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;">
        <div style="background:#111;border-radius:8px;padding:8px;text-align:center;">
          <div style="font-size:10px;color:var(--muted);">f_char (αντικείμενο)</div>
          <div style="font-size:22px;font-weight:900;color:var(--accent2)">${d.f_char_hz} <span style="font-size:13px">Hz</span></div>
          <div style="font-size:10px;color:var(--muted)">Μέγιστη απόκριση eddy current</div>
        </div>
        <div style="background:#111;border-radius:8px;padding:8px;text-align:center;">
          <div style="font-size:10px;color:var(--muted);">f_soil (διείσδυση εδάφους)</div>
          <div style="font-size:22px;font-weight:900;color:var(--ok)">${d.f_soil_limit_hz} <span style="font-size:13px">Hz</span></div>
          <div style="font-size:10px;color:var(--muted)">Max για βάθος ${depth}m</div>
        </div>
      </div>
      <div style="background:linear-gradient(135deg,rgba(34,211,238,.1),rgba(139,92,246,.1));border-radius:8px;padding:12px;text-align:center;margin-bottom:10px;border:1px solid rgba(34,211,238,.3);">
        <div style="font-size:11px;color:var(--accent2);margin-bottom:2px;">⚡ f_optimal = √(f_char × f_soil)</div>
        <div style="font-size:32px;font-weight:900;color:white">${d.f_optimal_hz} <span style="font-size:16px">Hz</span></div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px;">δ_εδ @ f_opt = ${d.delta_soil_m}m | ${pen}</div>
      </div>
      <div style="font-size:11px;color:var(--muted);margin-bottom:8px;">📐 Πίνακας f_char ανά μέγεθος (${d.metal}):</div>
      <table style="width:100%;font-size:12px;border-collapse:collapse;">${tbl}</table>
    </div>`;
  }catch(e){
    box.innerHTML=`<div style="color:var(--bad);">⚠️ ${e}</div>`;
  }
}

async function larmorInjectKnowledge(){
  const btn = document.getElementById("larmorInjectBtn");
  const orig = btn.textContent;
  btn.textContent = "⏳ Φόρτωση…"; btn.disabled = true;
  try{
    const d = await postJson("/larmor/inject-knowledge", {});
    if(d.ok){
      btn.textContent = `✅ Αποθηκεύτηκαν ${d.stored}/${d.total}`;
      btn.style.borderColor = "var(--ok)"; btn.style.color = "var(--ok)";
    } else {
      btn.textContent = "⚠️ Σφάλμα";
    }
  }catch(e){
    btn.textContent = "⚠️ " + e;
  } finally {
    setTimeout(()=>{ btn.textContent=orig; btn.disabled=false;
      btn.style.borderColor=""; btn.style.color=""; }, 4000);
  }
}

async function injectGuerrillaKnowledge(){
  const btn = document.getElementById("guerrillaInjectBtn");
  const orig = btn.textContent;
  btn.textContent = "⏳ Εγχυση…"; btn.disabled = true;
  try{
    const d = await postJson("/larmor/inject-guerrilla-knowledge", {});
    if(d.ok){
      btn.textContent = `✅ ${d.stored}/${d.total} chunks`;
      btn.style.borderColor = "var(--ok)"; btn.style.color = "var(--ok)";
    } else {
      btn.textContent = "⚠️ Σφάλμα";
    }
  }catch(e){
    btn.textContent = "⚠️ " + e;
  } finally {
    setTimeout(()=>{ btn.textContent=orig; btn.disabled=false;
      btn.style.borderColor=""; btn.style.color=""; }, 5000);
  }
}

async function injectCacheKnowledge(){
  const btn = document.getElementById("cacheInjectBtn");
  const orig = btn.textContent;
  btn.textContent = "⏳ Εγχυση…"; btn.disabled = true;
  try{
    const d = await postJson("/larmor/inject-cache-knowledge", {});
    if(d.ok){
      btn.textContent = `✅ ${d.stored}/${d.total} chunks`;
      btn.style.borderColor = "var(--ok)"; btn.style.color = "var(--ok)";
    } else {
      btn.textContent = "⚠️ Σφάλμα";
    }
  }catch(e){
    btn.textContent = "⚠️ " + e;
  } finally {
    setTimeout(()=>{ btn.textContent=orig; btn.disabled=false;
      btn.style.borderColor=""; btn.style.color=""; }, 5000);
  }
}

async function loadSysInfo(){
  try{
    const d = await getJsonSilent("/system-info");
    if(d.error){
      const msg = `<div style="color:#f88;">⚠️ ${d.error}</div>`;
      const el1 = document.getElementById("sysInfoFull");
      const el2 = document.getElementById("sysBarWidget");
      if(el1) el1.innerHTML = msg;
      if(el2) el2.innerHTML = msg;
      return;
    }
    const cpuColor = d.cpu_percent > 80 ? "#f55" : d.cpu_percent > 50 ? "#fa0" : "#4c8";
    const ramColor = d.ram_percent > 85 ? "#f55" : d.ram_percent > 60 ? "#fa0" : "#4c8";
    const diskColor = d.disk_percent > 85 ? "#f55" : d.disk_percent > 70 ? "#fa0" : "#4c8";

    const fullHtml = `
      <div>🖥️ <strong>CPU:</strong> ${d.cpu_percent}%</div>
      ${sysBar(d.cpu_percent, cpuColor)}
      <div>🧠 <strong>RAM:</strong> ${d.ram_used_gb}GB / ${d.ram_total_gb}GB (${d.ram_percent}%)</div>
      ${sysBar(d.ram_percent, ramColor)}
      <div>💾 <strong>Δίσκος:</strong> ${d.disk_used_gb}GB / ${d.disk_total_gb}GB (${d.disk_percent}%)</div>
      ${sysBar(d.disk_percent, diskColor)}
      <div>⏱️ <strong>Uptime:</strong> ${d.uptime}</div>
      <div>🔷 <strong>NOUS RAM:</strong> ${d.nous_ram_mb}MB</div>
      <div>💻 <strong>Σύστημα:</strong> ${d.platform}</div>`;

    /* Full system section */
    const el1 = document.getElementById("sysInfoFull");
    if(el1) el1.innerHTML = fullHtml;

    /* Sidebar mini bars */
    const cpuFill = document.getElementById("cpuBar");
    const ramFill = document.getElementById("ramBar");
    const cpuTxt  = document.getElementById("cpuPct");
    const ramTxt  = document.getElementById("ramPct");
    if(cpuFill){ cpuFill.style.width=d.cpu_percent+"%"; cpuFill.style.background=cpuColor; }
    if(ramFill){ ramFill.style.width=d.ram_percent+"%"; ramFill.style.background=ramColor; }
    if(cpuTxt)  cpuTxt.textContent = d.cpu_percent+"%";
    if(ramTxt)  ramTxt.textContent = d.ram_used_gb+"/"+(d.ram_total_gb||"?")+"GB";
  }catch(e){
    const el1 = document.getElementById("sysInfoFull");
    if(el1) el1.innerHTML = `<div style="color:#888;">—</div>`;
  }
}

// Auto-refresh system bar κάθε 15 δευτερόλεπτα
setInterval(loadSysInfo, 15000);

// ─────────────────────────────────────────────
// TUNNEL (ngrok) CONTROL
// ─────────────────────────────────────────────
function drawQR(url){
  // Απλό QR με το qrcode.js lib (CDN)
  if(!window.QRCode) return;
  const canvas = document.getElementById("tunnelQR");
  if(!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0,0,140,140);
  try{
    QRCode.toCanvas(canvas, url, {width:140,margin:2}, function(){});
  }catch(e){}
}

function applyTunnelState(d){
  const statusEl = document.getElementById("tunnelStatus");
  const urlBox   = document.getElementById("tunnelUrlBox");
  const startBtn = document.getElementById("tunnelStartBtn");
  const stopBtn  = document.getElementById("tunnelStopBtn");
  const tokenBox = document.getElementById("tokenSetupBox");
  if(!statusEl) return;

  if(d.status === "running" && d.url){
    statusEl.innerHTML = `<span style="color:#4c8;">●</span> <strong>Ενεργό</strong> — σύνδεση από οπουδήποτε`;
    urlBox.style.display = "block";
    startBtn.style.display = "none";
    stopBtn.style.display  = "inline-block";
    tokenBox.style.display = "none";
    const link = document.getElementById("tunnelUrlLink");
    link.href = d.url; link.textContent = d.url;
    drawQR(d.url);
  } else if(d.status === "starting"){
    statusEl.innerHTML = `<span style="color:#fa0;">●</span> Εκκίνηση tunnel...`;
    urlBox.style.display = "none";
    startBtn.disabled = true;
  } else if(d.status === "error"){
    statusEl.innerHTML = `<span style="color:#f55;">●</span> Σφάλμα: ${d.error||"άγνωστο"}`;
    urlBox.style.display = "none";
    startBtn.style.display = "inline-block";
    stopBtn.style.display  = "none";
    if(!d.has_token) tokenBox.style.display = "block";
  } else {
    statusEl.innerHTML = `<span style="color:#888;">●</span> Σταματημένο`;
    urlBox.style.display = "none";
    startBtn.style.display = "inline-block";
    startBtn.disabled = false;
    stopBtn.style.display  = "none";
    if(!d.has_token) tokenBox.style.display = "block";
  }
}

async function checkTunnel(){
  const d = await getJsonSilent("/remote/tunnel/status");
  applyTunnelState(d);
}

async function startTunnel(){
  const btn = document.getElementById("tunnelStartBtn");
  if(btn){ btn.disabled=true; btn.textContent="⏳ Εκκίνηση..."; }
  const inp = document.getElementById("ngrokTokenInput");
  const body = inp && inp.value.trim() ? {authtoken: inp.value.trim()} : {};
  const d = await postJson("/remote/tunnel/start", body);
  applyTunnelState(d);
  if(btn){ btn.disabled=false; btn.textContent="🚀 Ξεκίνα Tunnel"; }
}

async function stopTunnel(){
  const d = await postJson("/remote/tunnel/stop", {});
  applyTunnelState(d);
}

async function saveTunnelToken(){
  const inp = document.getElementById("ngrokTokenInput");
  const msg = document.getElementById("tokenSaveMsg");
  if(!inp || !inp.value.trim()){ if(msg) msg.textContent="Βάλε το token πρώτα."; return; }
  const d = await postJson("/remote/tunnel/save-token", {authtoken: inp.value.trim()});
  if(msg) msg.textContent = d.ok ? "✅ Αποθηκεύτηκε! Τώρα πάτα Ξεκίνα." : "❌ "+d.error;
}

function copyTunnelUrl(){
  const link = document.getElementById("tunnelUrlLink");
  if(!link) return;
  navigator.clipboard.writeText(link.textContent).then(()=>{
    const btn = link.nextElementSibling;
    if(btn){ const old=btn.textContent; btn.textContent="✅ Αντιγράφηκε!"; setTimeout(()=>btn.textContent=old,2000); }
  });
}

// Έλεγχος tunnel κατά την εκκίνηση
setTimeout(checkTunnel, 1500);
// Refresh κάθε 30 δευτερόλεπτα
setInterval(checkTunnel, 30000);

async function approveRecommendation(index){
  const ok = confirm("Να εγκρίνω και να εκτελέσω αυτή την πρόταση;");
  if(!ok) return;

  const data = await postJson("/remote/executive-intelligence/execute-recommendation", {index});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Approved recommendation " + index);
  await loadIntelligence();
  if(typeof loadApprovals === "function") await loadApprovals();
  if(typeof loadMissions === "function") await loadMissions();
}

async function rejectRecommendation(index){
  const reason = prompt("Λόγος απόρριψης:", "Δεν το εγκρίνω τώρα") || "User rejected recommendation";
  const data = await postJson("/remote/executive-intelligence/reject-recommendation", {index, reason});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Rejected recommendation " + index);
  await loadIntelligence();
}


async function loadIntelligence(){
  const status = await getJson("/remote/executive-intelligence/status");
  const report = await getJson("/remote/executive-intelligence/report");

  renderObject(status);

  const n = status.next_best_action || {};
  const sum = status.summary || {};

  document.getElementById("nextBestAction").innerHTML =
    kv("title", n.title || "-") +
    kv("type", n.type || "-") +
    kv("priority", n.priority ?? "-") +
    kv("action", n.action || "-") +
    `<div class="small" style="margin-top:8px">${n.reason || ""}</div>`;

  document.getElementById("intelligenceSummary").innerHTML =
    kv("goals", (sum.goals_active ?? "-") + " active / " + (sum.goals_total ?? "-")) +
    kv("missions", (sum.missions_active ?? "-") + " active, " + (sum.missions_blocked ?? "-") + " blocked") +
    kv("approvals", sum.approvals_pending ?? "-") +
    kv("decisions", sum.decisions_total ?? "-") +
    kv("lessons", (sum.lessons_total ?? "-") + " total") +
    kv("cloud ready", sum.cloud_ready) +
    kv("device ready", sum.device_ready);

  const recs = status.recommendations || [];
  document.getElementById("intelligenceRecommendations").innerHTML =
    recs.map((r,i)=>`
      <div class="card">
        <h3>${r.priority}. ${r.title}</h3>
        ${kv("type", r.type)}
        ${kv("action", r.action)}
        <div class="small">${r.reason}</div>
        <button class="miniBtn" onclick="approveRecommendation(${i})">✅ Approve & Execute</button>
        <button class="miniBtn" onclick="rejectRecommendation(${i})">❌ Reject</button>
      </div>
    `).join("");

  document.getElementById("executiveReport").textContent = report.report || JSON.stringify(report, null, 2);
}


async function loadLearning(){
  const status = await getJson("/remote/lessons/status");
  const lessons = await getJson("/remote/lessons/list");

  renderObject({status, lessons});

  document.getElementById("learningStatus").innerHTML =
    kv("total", status.total ?? "-") +
    kv("success", status.success ?? "-") +
    kv("failure", status.failure ?? "-");

  if(!lessons || lessons.length===0){
    document.getElementById("lessonList").innerHTML = "No lessons yet.";
    return;
  }

  document.getElementById("lessonList").innerHTML = lessons.slice(-20).reverse().map(l=>`
    <div class="card">
      <h3>${l.lesson}</h3>
      ${kv("outcome", l.outcome)}
      ${kv("confidence", l.confidence)}
      ${kv("mission", l.mission_id || "-")}
      <div style="margin-top:8px">${(l.tags||[]).map(x=>`<span class="pill">${x}</span>`).join("")}</div>
    </div>
  `).join("");
}

async function searchLessons(){
  const q = document.getElementById("lessonSearch").value || "";
  const data = await postJson("/remote/lessons/search", {query:q});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("lessonSearchResults").textContent = JSON.stringify(data, null, 2);
  feed("Searched lessons");
}


async function loadBackupPanel(){
  const backups = await getJson("/remote/brain-backup/list");
  const restore = await getJson("/remote/brain-restore/status");

  renderObject({backups, restore});

  document.getElementById("restoreStatus").innerHTML =
    kv("restore_dir", restore.restore_dir || "-") +
    kv("safety_backups", (restore.safety_backups || []).length) +
    kv("blocked", (restore.blocked || []).join(", "));

  if(!backups.backups || backups.backups.length===0){
    document.getElementById("backupList").innerHTML="No backups yet.";
    return;
  }

  document.getElementById("backupList").innerHTML = backups.backups.map(b=>`
    <div class="card">
      <h3>${b.name}</h3>
      ${kv("size", b.size + " bytes")}
      ${kv("sha256", b.sha256.slice(0,16)+"...")}
      <div class="small">${b.path}</div>
      <button class="miniBtn" onclick="inspectBackup('${b.path}')">Inspect Backup</button>
      <button class="miniBtn" onclick="previewRestore('${b.path}')">Restore Preview</button>
    </div>
  `).join("");
}

async function createBrainBackup(){
  const data = await postJson("/remote/brain-backup/create", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Created brain backup");
  await loadBackupPanel();
}

async function inspectBackup(path){
  const data = await postJson("/remote/brain-restore/inspect", {path});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("backupInspect").textContent = JSON.stringify(data, null, 2);
  feed("Inspected backup");
}

async function previewRestore(path){
  const data = await postJson("/remote/brain-restore/apply", {path, apply:false});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("backupInspect").textContent = JSON.stringify(data, null, 2);
  feed("Restore preview completed");
}


async function loadBrain(){
  const status = await getJson("/remote/brain/status");
  const state = await getJson("/remote/brain/state");

  renderObject(status);

  document.getElementById("brainStatus").innerHTML =
    kv("goals", status.goals?.total ?? "-") +
    kv("missions", status.missions?.total ?? "-") +
    kv("blocked", status.missions?.blocked ?? "-") +
    kv("approvals", status.approvals?.count ?? "-");

  const r = status.readiness || {};

  document.getElementById("brainReadiness").innerHTML =
    kv("cloud_ready", r.cloud_ready_foundation) +
    kv("device_ready", r.device_control_foundation) +
    kv("pending_approvals", r.pending_approvals ?? 0) +
    kv("ready_modules", (r.ready || []).length) +
    kv("missing_modules", (r.missing || []).length);

  document.getElementById("brainSnapshot").textContent =
    JSON.stringify(state.readiness, null, 2);
}


async function loadGoals(){
  const data=await getJson("/remote/goals-v2/status");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}

  document.getElementById("goalStatus").innerHTML=
    kv("total",data.total ?? "-")+
    kv("active",data.active ?? "-")+
    kv("done",data.done ?? "-");

  if(!data.goals || data.goals.length===0){
    document.getElementById("goalList").innerHTML="No goals yet.";
    return;
  }

  document.getElementById("goalList").innerHTML=data.goals.map(g=>`
    <div class="card">
      <h3>${g.title}</h3>
      ${kv("priority",g.priority)}
      ${kv("status",g.status)}
      ${kv("progress",(g.progress ?? 0)+"%")}
      ${kv("missions",(g.missions||[]).length)}
      <div class="small">${g.description||""}</div>
      <div style="margin-top:8px">${(g.next_actions||[]).map(x=>`<span class="pill">${x}</span>`).join("")}</div>
      <button class="miniBtn" onclick="refreshGoal('${g.id}')">Refresh Progress</button>
      <button class="miniBtn" onclick="createMissionForGoal('${g.id}', '${g.title.replace(/'/g, "\\'")}')">Create Mission For Goal</button>
    </div>
  `).join("");
}

async function seedGoals(){
  const data=await postJson("/remote/goals-v2/seed",{});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Seeded core goals");
  await loadGoals();
}

async function refreshGoal(id){
  const data=await postJson("/remote/goals-v2/refresh",{id});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Refreshed goal "+id);
  await loadGoals();
}


async function createMissionForGoal(goalId, goalTitle){
  const title = prompt("Mission title:", "Advance goal: " + goalTitle);
  if(!title) return;

  const description = prompt("Mission description:", "Mission linked to goal: " + goalTitle) || "";

  const data = await postJson("/remote/goals-v2/create-mission", {
    goal_id: goalId,
    title,
    description,
    tasks: [
      {title:"Check code health", action:"code_health"},
      {title:"Check git status", action:"git_status"},
      {title:"Run reality check", action:"reality_status"},
      {title:"Full validation", action:"full_validation"}
    ]
  });

  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Created mission for goal");
  await loadGoals();
  await loadMissions();
}

async function loadMissions(){
  const ms=await getJson("/remote/missions/status"); const list=await getJson("/remote/missions");
  document.getElementById("missionStatus").innerHTML=kv("total",ms.total)+kv("active",ms.active)+kv("done",ms.done)+kv("blocked",ms.blocked);
  document.getElementById("missionList").textContent=JSON.stringify(list.slice(-8),null,2);
  renderObject(ms);
}
async function loadCompanion(){const d=await getJson("/remote/companion/status");document.getElementById("companionStatus").innerHTML=kv("package",d.package)+kv("available",d.available?"✅":"❌")+kv("commands",(d.commands||[]).join(", "));renderObject(d)}
async function loadDeploy(){const d=await getJson("/remote/vercel/status");document.getElementById("deployStatus").innerHTML=kv("installed",d.installed?"✅":"❌")+kv("logged in",d.logged_in?"✅":"❌")+kv("deployments",(d.deployments||[]).length);renderObject(d)}
async function loadSystem(){const r=await getJson("/remote/reality/status");const o=await getJson("/remote/ops/status");document.getElementById("realityStatus").innerHTML=kv("internet",r.internet?.real?"✅":"❌")+kv("browser read",r.browser_read?.real?"✅":"❌")+kv("gestures",r.android?.real_gestures?"✅":"❌");document.getElementById("opsStatus").innerHTML=kv("safe actions",(o.safe_actions||[]).length)+kv("blocked",(o.blocked||[]).length);renderObject({reality:r,ops:o})}
async function loadApprovals(){
  const data=await getJson("/remote/missions/approvals");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}

  if(!data.approvals || data.approvals.length===0){
    document.getElementById("approvalsBox").innerHTML="No pending approvals.";
    return;
  }

  document.getElementById("approvalsBox").innerHTML=data.approvals.map(a=>`
    <div class="card">
      <h3>${a.task_title}</h3>
      ${kv("mission",a.mission_title)}
      ${kv("action",a.action)}
      ${kv("status",a.status)}
      <button class="miniBtn" onclick="approveTask('${a.mission_id}','${a.task_id}')">✅ Approve Task</button>
      <button class="miniBtn" onclick="runMission('${a.mission_id}')">▶ Run Mission</button>
    </div>
  `).join("");
}


async function approveTask(missionId, taskId){
  const data=await postJson("/remote/missions/approve-task",{mission_id:missionId,task_id:taskId});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Approved task "+taskId);
  await loadApprovals();
  await loadMissions();
}

async function runMission(id){
  const data=await postJson("/remote/missions/run-cycle",{id:id,max_steps:3});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Ran mission "+id);
  await loadApprovals();
  await loadMissions();
}

async function postAction(path){closeMenu();const data=await postJson(path,{});renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}feed("Action "+path);addMsg("Action: "+path+"\n"+JSON.stringify(data,null,2))}
async function ops(action){closeMenu();const payload={};if(action==="checkpoint")payload.message=prompt("Commit message:","NOUS safe checkpoint")||"NOUS safe checkpoint";const data=await postJson("/remote/ops/run",{action,payload});renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}feed("Ops "+action);addMsg("Ops: "+action+"\n"+JSON.stringify(data,null,2))}
async function createMission(kind){const data=await postJson("/remote/missions/create-standard",{kind});renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}feed("Mission created "+kind);await loadMissions()}
async function createWorkspaceMission(){const prompt=document.getElementById("missionPrompt").value||"";const data=await postJson("/remote/workspace/create-mission",{prompt});renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}feed("Workspace mission created");await loadMissions()}

function nousShowTyping(show){
  const el=document.getElementById("nousTypingIndicator");
  if(el) el.style.display=show?"block":"none";
  const btn=document.getElementById("sendBtn");
  if(btn){ btn.disabled=show; btn.textContent=show?"…":"↑"; }
  if(show){const c=document.getElementById("chatlog");if(c)c.scrollTop=c.scrollHeight;}
}

document.addEventListener("DOMContentLoaded",function(){
  const ta=document.getElementById("prompt");
  if(ta){
    ta.addEventListener("keydown",function(e){
      if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendPrompt();}
    });
  }
  loadSysInfo();
});

async function quickUpload(input){
  if(!input.files||!input.files.length)return;
  const f=input.files[0];
  input.value="";
  addMsg("📎 Ανεβάζω αρχείο: "+f.name,"user");
  nousShowTyping(true);
  try{
    const fd=new FormData();
    fd.append("file",f);
    fd.append("note","uploaded_from_chat");
    const r=await fetch("/upload",{method:"POST",body:fd});
    const d=await r.json();
    addMsg(d.answer||d.message||JSON.stringify(d),"bot");
  }catch(e){addMsg("Σφάλμα upload: "+e,"bot");}
  finally{nousShowTyping(false);}
}

async function sendPrompt(){
  const p=document.getElementById("prompt"); const text=p.value.trim(); if(!text)return; p.value=""; addMsg(text,"user");

  if(text==="/status"){
    nousShowTyping(true);
    const d=await getJson("/remote/status");
    nousShowTyping(false);
    renderObject(d);
    const lines=[];
    if(d.system) lines.push("Σύστημα: "+d.system);
    if(d.goals) lines.push("Goals: "+JSON.stringify(d.goals));
    if(d.missions) lines.push("Missions: "+JSON.stringify(d.missions));
    addMsg(lines.length ? lines.join("\n") : "NOUS AI OS — Online ✅","bot");
    return;
  }

  if(text==="/home"){nousShowTyping(true);const d=await postJson("/remote/companion/home",{});nousShowTyping(false);renderObject(d);addMsg(d.ok?"Android Home ✅":"Companion unavailable","bot");return}
  if(text==="/back"){nousShowTyping(true);const d=await postJson("/remote/companion/back",{});nousShowTyping(false);renderObject(d);addMsg(d.ok?"Android Back ✅":"Companion unavailable","bot");return}

  if(text.startsWith("/mission ")){
    nousShowTyping(true);
    const d=await postJson("/remote/workspace/create-mission",{prompt:text.slice(9)});
    nousShowTyping(false);
    renderObject(d);
    addMsg(d,"bot");
    return;
  }
  if(text.startsWith("/plan ")){
    nousShowTyping(true);
    const d=await postJson("/remote/executive/plan",{prompt:text.slice(6)});
    nousShowTyping(false);
    renderObject(d);
    addMsg(d,"bot");
    return;
  }
  if(text.startsWith("/run ")){
    nousShowTyping(true);
    const d=await postJson("/remote/executive/run",{prompt:text.slice(5),max_steps:3,execute:true});
    nousShowTyping(false);
    renderObject(d);
    addMsg(d,"bot");
    return;
  }

  // Φυσική γλώσσα → brain/chat endpoint
  nousShowTyping(true);
  try {
    const r = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text, conversation_id: window.NOUS_ACTIVE_CONVERSATION_ID || ""})
    });
    const d = await r.json();
    renderObject(d);
    addMsg(d, "bot");
  } catch(e) {
    addMsg("Σφάλμα επικοινωνίας: " + e, "bot");
  } finally {
    nousShowTyping(false);
  }
}













async function loadPatchApply(){
  const a = await getJson("/remote/patch-apply/status");
  const r = await getJson("/remote/rollback/status");
  renderObject({patch_apply:a, rollback:r});
  document.getElementById("patchApplyBox").textContent = JSON.stringify(a, null, 2);
  document.getElementById("rollbackBox").textContent = JSON.stringify(r, null, 2);
}

async function loadGraphs(){
  const repo = await getJson("/remote/repository-graph/status");
  const kg = await getJson("/remote/knowledge-graph/status");
  renderObject({repository:repo, knowledge:kg});
  document.getElementById("repoGraphBox").textContent = JSON.stringify(repo, null, 2);
  document.getElementById("knowledgeGraphBox").textContent = JSON.stringify(kg, null, 2);
}

async function buildRepoGraph(){
  const data = await postJson("/remote/repository-graph/build", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadGraphs();
}

async function buildKnowledgeGraph(){
  const data = await postJson("/remote/knowledge-graph/build", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadGraphs();
}

async function loadLoopV3(){
  const data = await getJson("/remote/executive-loop-v3/status");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("loopV3Box").textContent = JSON.stringify(data, null, 2);
}

async function runLoopV3(){
  const ok = confirm("Να τρέξει Executive Loop V3; Θα κάνει μόνο safe execution και θα αφήσει approvals για εσένα.");
  if(!ok) return;
  const data = await postJson("/remote/executive-loop-v3/run", {trigger:"dashboard"});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("loopV3Box").textContent = JSON.stringify(data, null, 2);
}


async function loadMegaSystems(){
  const cleanup = await getJson("/remote/cleanup/status");
  const goals = await getJson("/remote/goal-manager-v2/status");
  const mem = await getJson("/remote/executive-memory-v3/status");

  renderObject({cleanup, goals, mem});
  document.getElementById("cleanupBox").textContent = JSON.stringify(cleanup, null, 2);
  document.getElementById("goalManagerBox").textContent = JSON.stringify(goals, null, 2);
  document.getElementById("execMemoryBox").textContent = JSON.stringify(mem, null, 2);
}

async function cleanupPreview(){
  const data = await postJson("/remote/cleanup/preview", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("cleanupBox").textContent = JSON.stringify(data, null, 2);
}

async function cleanupApply(){
  const ok = confirm("Να εφαρμοστεί cleanup; Θα απορρίψει duplicate pending proposals και θα κρατήσει λίγα backups.");
  if(!ok) return;
  const data = await postJson("/remote/cleanup/apply", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("cleanupBox").textContent = JSON.stringify(data, null, 2);
  if(typeof loadPendingReview === "function") await loadPendingReview();
}

async function generateGoalProjects(){
  const data = await postJson("/remote/goal-manager-v2/generate", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("goalManagerBox").textContent = JSON.stringify(data, null, 2);
}

async function learnExecutiveMemory(){
  const data = await postJson("/remote/executive-memory-v3/learn", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("execMemoryBox").textContent = JSON.stringify(data, null, 2);
}

async function loadUpgradePlans(){
  const data = await getJson("/remote/upgrade-planner/plans");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  if(!data || data.length===0){
    document.getElementById("upgradePlansBox").innerHTML = "No upgrade plans.";
    return;
  }
  document.getElementById("upgradePlansBox").innerHTML = data.slice().reverse().map(p=>`
    <div class="card">
      <h3>${p.title}</h3>
      ${kv("status", p.status)}
      <pre>${JSON.stringify(p.upgrades || [], null, 2)}</pre>
      ${
        p.status === "pending"
        ? `<button class="miniBtn" onclick="approveUpgradePlan('${p.id}')">✅ Approve Plan</button>
           <button class="miniBtn" onclick="rejectUpgradePlan('${p.id}')">❌ Reject</button>`
        : ""
      }
    </div>
  `).join("");
}

async function proposeUpgradePlan(){
  const data = await postJson("/remote/upgrade-planner/propose", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadUpgradePlans();
  if(typeof loadPendingReview === "function") await loadPendingReview();
}

async function approveUpgradePlan(id){
  const data = await postJson("/remote/upgrade-planner/approve", {plan_id:String(id)});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadUpgradePlans();
}

async function rejectUpgradePlan(id){
  const reason = prompt("Λόγος απόρριψης:", "Δεν το εγκρίνω τώρα") || "User rejected upgrade plan";
  const data = await postJson("/remote/upgrade-planner/reject", {plan_id:String(id), reason});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadUpgradePlans();
}


async function loadSelfHealing(){
  const status = await getJson("/remote/self-healing/status");
  const proposals = await getJson("/remote/patch-generator/proposals");

  renderObject({status, proposals});

  const pg = status.patch_generator || {};
  document.getElementById("selfHealingStatus").innerHTML =
    kv("patch total", pg.total ?? 0) +
    kv("pending", pg.pending ?? 0) +
    kv("approved", pg.approved ?? 0) +
    kv("rejected", pg.rejected ?? 0);

  if(!proposals || proposals.length === 0){
    document.getElementById("patchProposals").innerHTML = "No patch proposals.";
  } else {
    document.getElementById("patchProposals").innerHTML = proposals.slice().reverse().map(p=>`
      <div class="card">
        <h3>${p.title}</h3>
        ${kv("status", p.status)}
        ${kv("risk", p.risk)}
        ${kv("can apply", p.can_apply)}
        <div class="small">${p.reason || ""}</div>
        <pre>${JSON.stringify(p.patches || [], null, 2)}</pre>
        ${
          p.status === "pending"
          ? `<button class="miniBtn" onclick="approvePatch('${p.id}')">✅ Approve Patch</button>
             <button class="miniBtn" onclick="rejectPatch('${p.id}')">❌ Reject Patch</button>`
          : ""
        }
      </div>
    `).join("");
  }

  document.getElementById("selfHealingFull").textContent = JSON.stringify({status, proposals}, null, 2);
}

async function runSelfHealing(){
  const data = await postJson("/remote/self-healing/run-analysis", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Self-healing analysis completed");
  await loadSelfHealing();
  if(typeof loadPendingReview === "function") await loadPendingReview();
}

async function approvePatch(id){
  const ok = confirm("Να εφαρμοστεί αυτό το patch; Θα γίνει compile check μετά.");
  if(!ok) return;
  const data = await postJson("/remote/patch-generator/approve", {proposal_id:String(id)});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  if(data.ok){ feed("Patch approved/applied"); }
  else { feed("Patch approval failed: " + (data.error || "unknown")); }
  await loadSelfHealing();
}

async function rejectPatch(id){
  const reason = prompt("Λόγος απόρριψης:", "Δεν το εγκρίνω τώρα") || "User rejected patch proposal";
  const data = await postJson("/remote/patch-generator/reject", {proposal_id:String(id), reason});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Patch proposal rejected");
  await loadSelfHealing();
}


async function loadCommandCenter(){
  const data = await getJson("/remote/command-center/status");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}

  const s = data.summary || {};
  document.getElementById("commandSummary").innerHTML =
    kv("pending", s.pending_total ?? 0) +
    kv("active goals", s.goals_active ?? 0) +
    kv("active missions", s.missions_active ?? 0) +
    kv("blocked missions", s.missions_blocked ?? 0) +
    kv("repair pending", s.repair_pending ?? 0) +
    kv("diagnosis ok", s.diagnosis_ok) +
    kv("backups", s.backup_count ?? 0);

  const next = data.intelligence?.next_best_action || {};
  document.getElementById("commandNextAction").innerHTML =
    `<h3>${next.title || "No action"}</h3>` +
    kv("type", next.type || "-") +
    kv("action", next.action || "-") +
    `<div class="small">${next.reason || ""}</div>`;

  const pending = data.pending || {};
  document.getElementById("commandPending").innerHTML =
    kv("total", pending.total ?? 0) +
    kv("repair", pending.counts?.repair_proposals ?? 0) +
    kv("missions", pending.counts?.mission_proposals ?? 0) +
    kv("approvals", pending.counts?.mission_task_approvals ?? 0) +
    kv("executive", pending.counts?.executive_recommendations ?? 0) +
    `<button class="miniBtn" onclick="showSection('pending')">Open Pending Inbox</button>`;

  document.getElementById("commandAutomation").innerHTML =
    kv("auto executor", s.auto_executor_enabled) +
    kv("auto scheduler", s.auto_scheduler_enabled) +
    `<button class="miniBtn" onclick="showSection('autoexec')">Open AutoExec</button>
     <button class="miniBtn" onclick="showSection('autoscheduler')">Open AutoSched</button>`;

  document.getElementById("commandFull").textContent = JSON.stringify(data, null, 2);
}

async function runCommandCycle(){
  const ok = confirm("Να τρέξει ο πλήρης Executive Cycle; Θα κάνει safe execution και θα αφήσει εγκρίσεις στο Pending Inbox.");
  if(!ok) return;
  const data = await postJson("/remote/command-center/run-cycle", {trigger:"command_center"});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("commandFull").textContent = JSON.stringify(data, null, 2);
  feed("Executive command cycle completed");
  await loadCommandCenter();
}


async function loadPendingReview(){
  const data = await getJson("/remote/pending-review/status");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}

  document.getElementById("pendingSummary").innerHTML =
    kv("total", data.total ?? 0) +
    kv("repair", data.counts?.repair_proposals ?? 0) +
    kv("missions", data.counts?.mission_proposals ?? 0) +
    kv("approvals", data.counts?.mission_task_approvals ?? 0) +
    kv("executive", data.counts?.executive_recommendations ?? 0);

  const items = data.items || [];
  if(items.length === 0){
    document.getElementById("pendingItems").innerHTML = "No pending items.";
    return;
  }

  document.getElementById("pendingItems").innerHTML = items.map(x=>`
    <div class="card">
      <h3>${x.title || "-"}</h3>
      ${kv("type", x.type)}
      ${kv("source", x.source)}
      ${kv("risk", x.risk || "-")}
      <pre>${JSON.stringify(x.data || x, null, 2)}</pre>
      <button class="miniBtn" onclick="showSection('${x.action_tab}')">Open ${x.action_tab}</button>
    </div>
  `).join("");
}

async function loadExecutiveLoopV2(){
  const data = await getJson("/remote/executive-loop-v2/status");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("loopV2Status").textContent = JSON.stringify(data, null, 2);
}

async function runExecutiveLoopV2(){
  const ok = confirm("Να τρέξει Executive Loop v2; Θα κάνει μόνο safe execution και θα αφήσει approvals για εσένα.");
  if(!ok) return;
  const data = await postJson("/remote/executive-loop-v2/run", {trigger:"dashboard"});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("loopV2Status").textContent = JSON.stringify(data, null, 2);
  feed("Executive Loop v2 completed");
  await loadPendingReview();
}


async function loadAutoScheduler(){
  const data = await getJson("/remote/auto-mission-scheduler/status");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("autoSchedulerStatus").textContent = JSON.stringify(data, null, 2);
}

async function runAutoSchedulerOnce(){
  const data = await postJson("/remote/auto-mission-scheduler/run-once", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadAutoScheduler();
}

async function startAutoScheduler(){
  const secs = prompt("Interval seconds", "900");
  const data = await postJson("/remote/auto-mission-scheduler/start", {interval_seconds: parseInt(secs || "900")});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadAutoScheduler();
}

async function stopAutoScheduler(){
  const data = await postJson("/remote/auto-mission-scheduler/stop", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadAutoScheduler();
}

async function loadCodeAnalyst(){
  const data = await getJson("/remote/code-analyst/reports");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("codeAnalystReports").textContent = JSON.stringify(data, null, 2);
}

async function analyzeLatestDiagnosis(){
  const data = await postJson("/remote/code-analyst/analyze-latest-diagnosis", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadCodeAnalyst();
}


async function loadAutoExec(){
  const data = await getJson("/remote/auto-mission-executor/status");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}

  document.getElementById("autoExecStatus").innerHTML =
    kv("enabled", data.enabled) +
    kv("candidates", (data.candidates || []).length) +
    kv("blocked", (data.blocked || []).length);

  document.getElementById("autoExecCandidates").textContent = JSON.stringify(data.candidates || [], null, 2);
  document.getElementById("autoExecBlocked").textContent = JSON.stringify(data.blocked || [], null, 2);
}

async function runAutoExec(){
  const ok = confirm("Να τρέξει safe auto mission cycle; Θα εκτελεστούν μόνο allowlisted safe tasks.");
  if(!ok) return;
  const data = await postJson("/remote/auto-mission-executor/run", {
    max_missions: 1,
    max_steps_per_mission: 3,
    trigger: "dashboard"
  });
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  if(data.ok){ feed("Auto mission executor completed"); }
  else { feed("Auto mission executor failed: " + (data.error || "unknown")); }
  await loadAutoExec();
  if(typeof loadMissions === "function") await loadMissions();
  if(typeof loadGoals === "function") await loadGoals();
}

async function enableAutoExec(){
  const data = await postJson("/remote/auto-mission-executor/enable", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadAutoExec();
}

async function disableAutoExec(){
  const data = await postJson("/remote/auto-mission-executor/disable", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadAutoExec();
}


// ── DIAGNOSIS UI helpers ────────────────────────────────────────────────────

function _diagSevStyle(sev){
  const s = {
    critical: {bg:"rgba(239,68,68,.10)",  border:"rgba(239,68,68,.3)",  color:"#ef4444", icon:"🔴"},
    warning:  {bg:"rgba(234,179,8,.09)",  border:"rgba(234,179,8,.3)",  color:"#eab308", icon:"🟡"},
    info:     {bg:"rgba(99,102,241,.08)", border:"rgba(99,102,241,.2)", color:"#818cf8", icon:"ℹ️"},
  };
  return s[sev] || s.info;
}

function _diagRenderIssues(issues){
  const el = document.getElementById("diagIssuesList");
  if(!el) return;
  if(!issues || issues.length === 0){
    el.innerHTML = `<div class="card" style="text-align:center;color:var(--muted);padding:28px 0;">
      <div style="font-size:32px;margin-bottom:8px;">✅</div>
      <div style="font-size:14px;">Δεν εντοπίστηκαν προβλήματα — ο ΝΟΥΣ είναι σε άριστη κατάσταση!</div>
    </div>`;
    return;
  }
  el.innerHTML = issues.map(iss => {
    const st = _diagSevStyle(iss.severity || "info");
    return `<div class="card" style="margin-bottom:10px;border-left:4px solid ${st.border};padding:14px 16px;">
      <div style="display:flex;align-items:flex-start;gap:10px;">
        <span style="font-size:18px;flex-shrink:0;">${st.icon}</span>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:700;font-size:13px;color:${st.color};margin-bottom:3px;">${escHtml(iss.title||"")}</div>
          <div style="font-size:11px;color:var(--muted);margin-bottom:6px;">📂 ${escHtml(iss.category||"")} ${iss.file?`· <code>${escHtml(iss.file)}</code>`:""}</div>
          ${iss.detail?`<div style="font-size:12px;color:var(--text);opacity:.8;background:var(--panel2);padding:6px 10px;border-radius:6px;white-space:pre-wrap;max-height:100px;overflow-y:auto;">${escHtml(iss.detail)}</div>`:""}
        </div>
      </div>
    </div>`;
  }).join("");
}

function _diagRenderSummary(report){
  const sum = report.summary || {};
  const bar = document.getElementById("diagSummaryBar");
  if(bar) bar.style.display = "block";
  const crit = sum.critical || 0;
  const warn = sum.warning  || 0;
  const info = sum.info     || 0;
  const elOk   = document.getElementById("diagBadgeOk");
  const elCrit = document.getElementById("diagBadgeCrit");
  const elWarn = document.getElementById("diagBadgeWarn");
  const elInfo = document.getElementById("diagBadgeInfo");
  const elTime = document.getElementById("diagTimeLbl");
  const elCritN = document.getElementById("diagCritN");
  const elWarnN = document.getElementById("diagWarnN");
  const elInfoN = document.getElementById("diagInfoN");
  if(elOk)   elOk.style.display   = (crit===0 && warn===0) ? "block" : "none";
  if(elCrit) { elCrit.style.display = crit>0 ? "block":"none"; if(elCritN) elCritN.textContent=crit; }
  if(elWarn) { elWarn.style.display = warn>0 ? "block":"none"; if(elWarnN) elWarnN.textContent=warn; }
  if(elInfo) { elInfo.style.display = info>0 ? "block":"none"; if(elInfoN) elInfoN.textContent=info; }
  if(elTime && report.time) elTime.textContent = "🕐 " + new Date(report.time*1000).toLocaleString("el-GR");
}

function _diagRenderRepairList(proposals){
  const el = document.getElementById("diagRepairList");
  if(!el) return;
  if(!proposals || proposals.length === 0){
    el.innerHTML = `<div style="color:var(--muted);font-size:13px;text-align:center;padding:20px 0;">Δεν υπάρχουν ακόμα προτάσεις διόρθωσης.</div>`;
    return;
  }
  const sorted = [...proposals].sort((a,b)=>(b.created||0)-(a.created||0));
  el.innerHTML = sorted.map(p => {
    const statusStyle = {
      pending:  "color:#eab308;",
      approved: "color:#22c55e;",
      rejected: "color:#ef4444;",
      failed:   "color:#f97316;",
    }[p.status] || "";
    const statusIcon = {pending:"⏳",approved:"✅",rejected:"❌",failed:"⚠️"}[p.status]||"•";
    return `<div style="border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:10px;background:var(--panel2);">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
        <span style="font-weight:700;font-size:13px;flex:1;">${escHtml(p.title||"Πρόταση")}</span>
        <span style="font-size:12px;${statusStyle}">${statusIcon} ${escHtml(p.status||"")}</span>
        <span style="font-size:10px;color:var(--muted);">${p.created?new Date(p.created*1000).toLocaleString("el-GR"):""}</span>
      </div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:8px;">${escHtml(p.description||"")}</div>
      ${p.target_files&&p.target_files.length?`<div style="font-size:11px;color:var(--muted);margin-bottom:8px;">📁 ${p.target_files.map(f=>`<code>${escHtml(f)}</code>`).join(", ")}</div>`:""}
      ${p.diff?`<details style="margin-bottom:8px;"><summary style="font-size:11px;cursor:pointer;color:var(--muted);">Diff / Patch</summary><pre style="font-size:10px;overflow:auto;max-height:180px;margin-top:6px;">${escHtml(p.diff)}</pre></details>`:""}
      ${p.status==="pending"&&p.fix_id!=="no_action_needed"?
        `<div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button onclick="diagApproveRepair('${p.id}')"
            style="padding:6px 14px;border-radius:8px;border:none;background:#22c55e;color:white;font-size:12px;font-weight:700;cursor:pointer;">✅ Εγκρίνω &amp; Εφαρμόζω</button>
          <button onclick="diagRejectRepair('${p.id}')"
            style="padding:6px 14px;border-radius:8px;border:1px solid rgba(239,68,68,.4);background:rgba(239,68,68,.08);color:#ef4444;font-size:12px;cursor:pointer;">❌ Απορρίπτω</button>
        </div>`:
        p.status==="pending"?`<div style="font-size:12px;color:var(--muted);">Δεν απαιτείται ενέργεια.</div>`:""}
    </div>`;
  }).join("");
}

async function diagRefresh(){
  const d = await getJson("/remote/self-diagnosis/status");
  const rep = d.report || d;
  if(rep.issues){ _diagRenderSummary(rep); _diagRenderIssues(rep.issues||[]); }
  await diagLoadRepair();
  await safetyLoad();
}

async function diagRun(){
  const btn = document.getElementById("diagRunBtn");
  const spin = document.getElementById("diagRunning");
  if(btn){ btn.disabled=true; btn.textContent="⏳ Σαρώνω…"; }
  if(spin) spin.style.display="inline";
  const d = await postJson("/remote/self-diagnosis/run", {});
  if(btn){ btn.disabled=false; btn.textContent="🔍 Εκτέλεση Διάγνωσης"; }
  if(spin) spin.style.display="none";
  const rep = d.report || d;
  _diagRenderSummary(rep);
  _diagRenderIssues(rep.issues || []);
  feed("Αυτοδιάγνωση ολοκληρώθηκε — " + (rep.summary?.total_issues||0) + " θέματα");
  await diagLoadRepair();
}

async function diagAiAnalyze(){
  const box  = document.getElementById("diagAiBox");
  const sumEl = document.getElementById("diagAiSummary");
  const propEl = document.getElementById("diagAiProposals");
  if(box) box.style.display="block";
  if(sumEl) sumEl.innerHTML = "⏳ Ο ΝΟΥΣ αναλύει τα δεδομένα διάγνωσης…";
  if(propEl) propEl.innerHTML = "";
  const d = await postJson("/remote/self-diagnosis/ai-analyze", {});
  if(!d.ok){
    if(sumEl) sumEl.innerHTML = `<span style="color:var(--bad);">⚠️ ${escHtml(d.error||"Σφάλμα")}</span>`;
    return;
  }
  if(sumEl) sumEl.innerHTML = escHtml(d.analysis||"—").replace(/\n/g,"<br>");
  const proposals = d.proposals || [];
  if(propEl && proposals.length){
    const riskColor = {low:"#22c55e", medium:"#eab308", high:"#ef4444"};
    propEl.innerHTML = `<div style="font-weight:700;font-size:13px;margin-bottom:10px;">📋 Προτεινόμενες Ενέργειες (${proposals.length})</div>` +
    proposals.map((p,i) => {
      const rc = riskColor[p.risk] || "#818cf8";
      return `<div style="border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:8px;background:var(--panel2);">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-weight:700;font-size:13px;flex:1;">${i+1}. ${escHtml(p.issue_title||"")}</span>
          <span style="font-size:11px;padding:2px 8px;border-radius:6px;border:1px solid ${rc};color:${rc};">⚡ ${escHtml(p.risk||"")}</span>
          ${p.auto_fixable?`<span style="font-size:11px;color:#22d3ee;">🤖 Αυτόματη διόρθωση</span>`:`<span style="font-size:11px;color:var(--muted);">✋ Χειροκίνητη</span>`}
        </div>
        <div style="font-size:12px;color:var(--muted);margin-bottom:6px;">💬 ${escHtml(p.explanation_el||"")}</div>
        <div style="font-size:12px;color:var(--text);background:rgba(34,211,238,.06);padding:8px 10px;border-radius:6px;border:1px solid rgba(34,211,238,.1);">
          ✅ ${escHtml(p.action_el||"")}
        </div>
      </div>`;
    }).join("");
  } else if(propEl){
    propEl.innerHTML = `<div style="color:#22c55e;font-size:13px;">✅ Δεν απαιτείται καμία ενέργεια.</div>`;
  }
  feed("AI ανάλυση ολοκληρώθηκε");
}

async function diagLoadRepair(){
  const statusEl = document.getElementById("diagRepairStatus");
  const d = await getJson("/remote/autonomous-repair/status");
  if(statusEl && d.total !== undefined){
    statusEl.textContent = `Σύνολο: ${d.total} · Εκκρεμή: ${d.pending} · Εγκεκριμένα: ${d.approved} · Απορριφθέντα: ${d.rejected}`;
  }
  const pd = await getJson("/remote/autonomous-repair/proposals");
  const proposals = Array.isArray(pd) ? pd : (pd.proposals || []);
  _diagRenderRepairList(proposals);
}

async function diagProposeRepair(){
  const d = await postJson("/remote/autonomous-repair/propose", {});
  feed("Πρόταση διόρθωσης δημιουργήθηκε");
  await diagLoadRepair();
}

async function diagApproveRepair(id){
  if(!confirm("Να εφαρμόσω αυτή τη διόρθωση;")) return;
  const d = await postJson("/remote/autonomous-repair/approve", {proposal_id:String(id)});
  if(d.ok){ feed("✅ Διόρθωση εφαρμόστηκε"); }
  else { feed("⚠️ Αποτυχία διόρθωσης: " + (d.error||"unknown")); }
  await diagLoadRepair();
}

async function diagRejectRepair(id){
  const reason = prompt("Λόγος απόρριψης:", "Δεν το εγκρίνω τώρα") || "User rejected";
  await postJson("/remote/autonomous-repair/reject", {proposal_id:String(id), reason});
  feed("Πρόταση απορρίφθηκε");
  await diagLoadRepair();
}

// Legacy aliases (kept for backward compat)
async function loadSelfDiagnosis(){ await diagRefresh(); }
async function runSelfDiagnosis(){ await diagRun(); }
async function loadRepair(){ await diagLoadRepair(); }
async function proposeRepair(){ await diagProposeRepair(); }
async function approveRepair(id){ await diagApproveRepair(id); }
async function rejectRepair(id){ await diagRejectRepair(id); }

// ── ΔΙΚΛΕΙΔΑ ΑΣΦΑΛΕΙΑΣ (Safety Net / Circuit Breaker) ─────────────────────

async function safetyLoad(){
  const d = await getJson("/remote/safety/status");
  const sum = d.summary || {};
  const circ = sum.circuit || d.circuit || {};

  const okEl    = document.getElementById("safetyStatOk");
  const failEl  = document.getElementById("safetyStatFail");
  const rbEl    = document.getElementById("safetyStatRollback");
  const cfEl    = document.getElementById("safetyStatCircuitFail");
  const badge   = document.getElementById("safetyCircuitBadge");
  const resetBtn= document.getElementById("safetyResetBtn");

  if(okEl)   okEl.textContent   = sum.successes ?? "–";
  if(failEl) failEl.textContent = sum.failures  ?? "–";
  if(rbEl)   rbEl.textContent   = sum.rollbacks  ?? "–";
  if(cfEl)   cfEl.textContent   = (circ.failures ?? 0) + " / 3";

  const state = circ.state || "closed";
  if(badge){
    if(state === "closed"){
      badge.textContent = "● ΚΛΕΙΣΤΟΣ";
      badge.style.background = "rgba(34,197,94,.15)"; badge.style.color="#22c55e";
      badge.style.borderColor = "rgba(34,197,94,.3)";
    } else if(state === "open"){
      const rem = circ.cooldown_remaining_sec ?? "?";
      badge.textContent = `🔴 ΑΝΟΙΧΤΟΣ — αναμονή ${rem}s`;
      badge.style.background = "rgba(239,68,68,.15)"; badge.style.color="#ef4444";
      badge.style.borderColor = "rgba(239,68,68,.3)";
    } else {
      badge.textContent = "🟡 ΜΙΣΟ-ΑΝΟΙΧΤΟΣ (δοκιμή)";
      badge.style.background = "rgba(234,179,8,.15)"; badge.style.color="#eab308";
      badge.style.borderColor = "rgba(234,179,8,.3)";
    }
  }
  if(resetBtn) resetBtn.style.display = (state !== "closed") ? "inline-block" : "none";

  _safetyRenderIncidents(d.recent_incidents || []);
}

function _safetyRenderIncidents(incidents){
  const el = document.getElementById("safetyIncidentList");
  if(!el) return;
  if(!incidents || incidents.length === 0){
    el.innerHTML = `<div style="color:var(--muted);font-size:13px;text-align:center;padding:20px 0;">Δεν υπάρχουν ακόμα ενέργειες.</div>`;
    return;
  }
  el.innerHTML = incidents.map(inc => {
    const isOk      = inc.outcome === "success";
    const isBlock   = inc.outcome === "blocked";
    const isRollback= inc.outcome === "rollback_manual";
    const color = isOk ? "#22c55e" : isBlock ? "#eab308" : isRollback ? "#a78bfa" : "#ef4444";
    const icon  = isOk ? "✅" : isBlock ? "🚫" : isRollback ? "↩️" : (inc.rolled_back ? "🔄" : "❌");
    const label = isOk ? "Επιτυχία" : isBlock ? "Μπλοκαρισμένο" : isRollback ? "Χειρ. Rollback" : (inc.rolled_back ? "Αποτυχία + Restore" : "Αποτυχία");
    const ts = inc.iso ? new Date(inc.iso).toLocaleString("el-GR") : "–";
    const files = (inc.files||[]).map(f=>`<code style="font-size:10px;">${escHtml(f)}</code>`).join(", ");

    return `<div style="border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-bottom:7px;background:var(--panel2);border-left:3px solid ${color};">
      <div style="display:flex;align-items:flex-start;gap:8px;flex-wrap:wrap;">
        <span style="font-size:16px;flex-shrink:0;">${icon}</span>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:3px;">
            <span style="font-weight:700;font-size:12px;color:${color};">${label}</span>
            <span style="font-size:11px;color:var(--muted);">· ${escHtml(inc.action||"")}</span>
            <span style="font-size:10px;color:var(--muted);margin-left:auto;">${ts}</span>
          </div>
          ${files ? `<div style="font-size:11px;color:var(--muted);margin-bottom:3px;">📁 ${files}</div>` : ""}
          ${inc.error ? `<div style="font-size:11px;color:#ef4444;background:rgba(239,68,68,.06);padding:4px 8px;border-radius:5px;white-space:pre-wrap;max-height:60px;overflow-y:auto;">${escHtml(inc.error.substring(0,200))}</div>` : ""}
        </div>
        ${(inc.rolled_back===false && inc.outcome!=="success" && inc.backup_ids && inc.backup_ids.length) ?
          `<button onclick="safetyManualRollback('${inc.id}')"
            style="padding:4px 10px;border-radius:6px;border:1px solid rgba(167,139,250,.4);background:rgba(167,139,250,.1);color:#a78bfa;font-size:11px;cursor:pointer;flex-shrink:0;">
            ↩ Rollback
          </button>` : ""}
      </div>
    </div>`;
  }).join("");
}

async function safetyCircuitReset(){
  if(!confirm("Να επαναφέρω τον circuit breaker; Η εφαρμογή θα επιτρέψει ξανά αυτόνομες ενέργειες.")) return;
  const d = await postJson("/remote/safety/circuit-reset", {});
  feed(d.ok ? "✅ Circuit breaker επαναφέρθηκε" : "⚠️ " + (d.error||"Σφάλμα"));
  await safetyLoad();
}

async function safetyManualRollback(incidentId){
  if(!confirm("Να κάνω rollback στα αρχεία αυτής της αποτυχημένης ενέργειας;")) return;
  const d = await postJson("/remote/safety/rollback", {incident_id: incidentId});
  if(d.ok){
    feed("↩️ Rollback επιτυχής — αρχεία αποκαταστάθηκαν");
  } else {
    feed("⚠️ Rollback απέτυχε: " + (d.error||"unknown"));
  }
  await safetyLoad();
}


async function runDashboardAudit(){
  const data = await getJson("/remote/dashboard-action-audit");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("auditResults").textContent = JSON.stringify(data, null, 2);
  feed("Dashboard action audit completed");
}


async function loadPlanner(){
  const status = await getJson("/remote/mission-planner/status");
  const proposals = await getJson("/remote/mission-planner/proposals");

  renderObject({status, proposals});

  document.getElementById("plannerStatus").innerHTML =
    kv("total", status.total ?? "-") +
    kv("pending", status.pending ?? "-") +
    kv("approved", status.approved ?? "-") +
    kv("rejected", status.rejected ?? "-");

  if(!proposals || proposals.length===0){
    document.getElementById("plannerProposals").innerHTML = "No proposals yet.";
    return;
  }

  document.getElementById("plannerProposals").innerHTML = proposals.slice().reverse().map(p=>`
    <div class="card">
      <h3>${p.title}</h3>
      ${kv("status", p.status)}
      ${kv("goal", p.goal_title || "-")}
      ${kv("kind", p.kind || "-")}
      ${kv("risk", p.risk || "-")}
      ${kv("impact", p.expected_impact || "-")}
      <div class="small">${p.reason || ""}</div>
      <h4>Tasks</h4>
      <pre>${JSON.stringify(p.tasks || [], null, 2)}</pre>
      ${
        p.status === "pending"
        ? `<button class="miniBtn" onclick="approveProposal(String('${p.id}'))">✅ Approve Mission</button>
           <button class="miniBtn" onclick="rejectProposal(String('${p.id}'))">❌ Reject</button>`
        : ""
      }
    </div>
  `).join("");
}

async function proposeMission(){
  const data = await postJson("/remote/mission-planner/propose", {});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  feed("Mission proposal created");
  await loadPlanner();
}

async function approveProposal(id){
  const ok = confirm("Να εγκρίνω αυτή την πρόταση και να δημιουργηθεί mission;");
  if(!ok) return;
  const data = await postJson("/remote/mission-planner/approve", {proposal_id:String(id)});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  if(data.ok){ feed("Mission proposal approved"); }
  else { feed("Mission proposal approval failed: " + (data.error || "unknown")); }
  await loadPlanner();
}

async function rejectProposal(id){
  const reason = prompt("Λόγος απόρριψης:", "Δεν το εγκρίνω τώρα") || "User rejected mission proposal";
  const data = await postJson("/remote/mission-planner/reject", {proposal_id:String(id), reason});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  if(data.ok){ feed("Mission proposal rejected"); }
  else { feed("Mission proposal rejection failed: " + (data.error || "unknown")); }
  await loadPlanner();
}


async function loadScheduler(){
  const data = await getJson("/remote/executive-scheduler-loop/status");
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  document.getElementById("schedulerStatus").textContent = JSON.stringify(data,null,2);
}

async function schedulerRunOnce(){
  const data = await postJson("/remote/executive-scheduler-loop/run-once",{});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadScheduler();
}

async function schedulerStart(){
  const secs = prompt("Interval seconds","1800");
  const data = await postJson("/remote/executive-scheduler-loop/start",{interval_seconds:parseInt(secs||"1800")});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadScheduler();
}

async function schedulerStop(){
  const data = await postJson("/remote/executive-scheduler-loop/stop",{});
  renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
  await loadScheduler();
}

// ══════════════════════════════════════════════════════════════
// NOUS INITIATIVES — Approve / Reject panel
// ══════════════════════════════════════════════════════════════
const _PRIORITY_STYLE = {
  high:   { bg: "rgba(239,68,68,.12)",   border: "rgba(239,68,68,.4)",   badge: "#fca5a5", label: "🔴 ΥΨΗΛΗ" },
  medium: { bg: "rgba(251,191,36,.10)",  border: "rgba(251,191,36,.35)", badge: "#fcd34d", label: "🟡 ΜΕΣΑΙΑ" },
  low:    { bg: "rgba(34,197,94,.08)",   border: "rgba(34,197,94,.3)",   badge: "#86efac", label: "🟢 ΧΑΜΗΛΗ" },
};
const _RISK_LABEL = { none:"✅ Μηδενικό", low:"🟢 Χαμηλό", medium:"🟡 Μέτριο", high:"🔴 Υψηλό" };
const _TYPE_LABEL  = {
  upgrade:"Αναβάθμιση", mission:"Αποστολή", repair:"Επιδιόρθωση", goal_action:"Στόχος",
  drive_survival:"Επιβίωση", drive_self_improvement:"Αυτο-βελτίωση",
  drive_capability_gap:"Κενό Ικανότητας", drive_curiosity:"Πρωτοβουλία",
};
const _SOURCE_LABEL = {
  nous_drive: { label:"🧠 ΝΟΥΣ Drive", color:"#a78bfa" },
  upgrade_planner: { label:"🚀 Upgrade", color:"#60a5fa" },
  mission_planner: { label:"🎯 Mission", color:"#34d399" },
  autonomous_repair: { label:"🔧 Repair", color:"#f87171" },
};

async function loadNousInitiatives(){
  const box = document.getElementById("nousInitiativesBox");
  if(!box) return;
  box.innerHTML = '<div style="color:var(--muted);font-size:13px;">⏳ Φόρτωση προτάσεων…</div>';
  try {
    const d = await getJson("/remote/nous-initiatives");
    const items = d.initiatives || [];
    if(!items.length){
      box.innerHTML = `
        <div style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.25);border-radius:10px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
          <span style="font-size:24px;">✅</span>
          <div>
            <div style="font-weight:600;font-size:13px;color:#86efac;">Όλα εντάξει!</div>
            <div style="font-size:12px;color:var(--muted);margin-top:2px;">Ο ΝΟΥΣ δεν έχει εκκρεμείς προτάσεις αυτή τη στιγμή.</div>
          </div>
        </div>`;
      return;
    }
    box.innerHTML = items.map((item, idx) => {
      const ps = _PRIORITY_STYLE[item.priority] || _PRIORITY_STYLE.medium;
      const riskLabel = _RISK_LABEL[item.risk] || item.risk;
      const typeLabel = _TYPE_LABEL[item.type] || item.type;
      const hasReject = !!item.reject_route;
      return `
      <div id="initiative_${idx}" style="background:${ps.bg};border:1px solid ${ps.border};border-radius:12px;padding:14px 16px;margin-bottom:10px;">
        <!-- Top row -->
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;flex-wrap:wrap;">
          <span style="font-size:24px;line-height:1;">${escHtml(item.icon||'💡')}</span>
          <div style="flex:1;min-width:0;">
            <div style="font-weight:700;font-size:14px;color:#f1f5f9;margin-bottom:4px;">${escHtml(item.title)}</div>
            <div style="font-size:12px;color:var(--muted);line-height:1.5;">${escHtml(item.description)}</div>
          </div>
        </div>
        <!-- Meta badges -->
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;">
          <span style="background:rgba(0,0,0,.3);border-radius:6px;padding:2px 8px;font-size:11px;color:${ps.badge};">${ps.label}</span>
          <span style="background:rgba(0,0,0,.2);border-radius:6px;padding:2px 8px;font-size:11px;color:var(--muted);">📂 ${escHtml(typeLabel)}</span>
          <span style="background:rgba(0,0,0,.2);border-radius:6px;padding:2px 8px;font-size:11px;color:var(--muted);">⚠️ ${escHtml(riskLabel)}</span>
          ${(()=>{ const sl=_SOURCE_LABEL[item.source]; return sl ? `<span style="background:rgba(0,0,0,.25);border-radius:6px;padding:2px 8px;font-size:11px;color:${sl.color};">${sl.label}</span>` : ''; })()}
        </div>
        <!-- Action buttons -->
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button onclick="nousInitiativeAct(${idx}, 'approve')"
            style="flex:1;min-width:120px;padding:10px 16px;border-radius:10px;border:none;background:linear-gradient(135deg,#22c55e,#16a34a);color:white;font-weight:700;font-size:13px;cursor:pointer;">
            ✅ Εγκρίνω
          </button>
          ${hasReject ? `<button onclick="nousInitiativeAct(${idx}, 'reject')"
            style="flex:1;min-width:120px;padding:10px 16px;border-radius:10px;border:1px solid rgba(239,68,68,.4);background:rgba(239,68,68,.08);color:#fca5a5;font-weight:700;font-size:13px;cursor:pointer;">
            ❌ Απορρίπτω
          </button>` : ''}
        </div>
        <!-- Feedback area -->
        <div id="initiativeFeedback_${idx}" style="display:none;margin-top:10px;padding:8px 12px;border-radius:8px;font-size:12px;"></div>
      </div>`;
    }).join("");
    // Store items for act function
    window._nousInitiatives = items;
  } catch(e){
    box.innerHTML = `<div style="color:var(--bad);font-size:13px;">⚠️ ${escHtml(String(e))}</div>`;
  }
}

async function nousInitiativeAct(idx, action){
  const item = (window._nousInitiatives || [])[idx];
  if(!item) return;
  const fb   = document.getElementById("initiativeFeedback_"+idx);
  const card = document.getElementById("initiative_"+idx);
  const btns = card ? card.querySelectorAll("button") : [];
  btns.forEach(b=>b.disabled=true);

  // ── REJECT ────────────────────────────────────────────────────────────────
  if(action === "reject"){
    if(fb){ fb.style.cssText="display:block;padding:8px 12px;border-radius:8px;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#fca5a5;font-size:12px;margin-top:8px;"; fb.textContent="❌ Απορρίφθηκε."; }
    const _rh={"Content-Type":"application/json","X-NOUS-TOKEN":token()};
    try { await fetch(item.reject_route,{method:"POST",headers:_rh,body:JSON.stringify(item.reject_payload||{})}); } catch(_){}
    setTimeout(()=>{ if(card){card.style.transition="opacity .5s";card.style.opacity="0";} setTimeout(()=>loadNousInitiatives(),600); }, 1200);
    return;
  }

  // ── APPROVE ───────────────────────────────────────────────────────────────
  // Show "executing" state immediately — card stays visible
  if(fb){
    fb.style.cssText="display:block;padding:10px 12px;border-radius:8px;background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.4);color:#c4b5fd;font-size:12px;margin-top:8px;white-space:pre-wrap;line-height:1.6;";
    fb.innerHTML='<b>⏳ Εκτελείται…</b>\n<span style="color:var(--muted);font-size:11px;">Περιμένετε…</span>';
  }

  const _ah={"Content-Type":"application/json","X-NOUS-TOKEN":token()};
  let approveResp;
  try {
    const r = await fetch(item.approve_route,{method:"POST",headers:_ah,body:JSON.stringify(item.approve_payload||{})});
    approveResp = await r.json();
  } catch(e){
    if(fb){ fb.style.background="rgba(239,68,68,.1)"; fb.style.border="1px solid rgba(239,68,68,.3)"; fb.style.color="#fca5a5"; fb.textContent="⚠️ Σφάλμα: "+e; }
    btns.forEach(b=>b.disabled=false);
    return;
  }

  if(!approveResp.ok){
    if(fb){ fb.style.background="rgba(239,68,68,.1)"; fb.style.border="1px solid rgba(239,68,68,.3)"; fb.style.color="#fca5a5"; fb.textContent="⚠️ "+(approveResp.error||"Σφάλμα"); }
    btns.forEach(b=>b.disabled=false);
    return;
  }

  // ── NEEDS DEVELOPER ───────────────────────────────────────────────────────
  if(approveResp.needs_developer){
    const devMsg = approveResp.developer_message || "";
    if(fb){
      fb.style.cssText="display:block;padding:10px 14px;border-radius:8px;background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.35);color:#fde68a;font-size:12px;margin-top:8px;";
      fb.innerHTML=`<b>🛠️ Χρειάζεται υλοποίηση από τον Developer</b><br><span style="color:var(--muted);font-size:11px;margin-top:4px;display:block;">Ο ΝΟΥΣ δεν μπορεί να το κάνει μόνος του — χρειάζεται κώδικας.</span>`
        + (devMsg ? `<button onclick="nousAskDeveloper(${JSON.stringify(devMsg)})" style="margin-top:8px;padding:5px 12px;border-radius:8px;border:none;background:rgba(251,191,36,.2);color:#fde68a;cursor:pointer;font-size:12px;font-weight:700;">💬 Ζήτα από τον Developer</button>` : "");
    }
    // Don't fade — stays visible so user can click the button
    return;
  }

  // ── EXECUTING: poll for status ─────────────────────────────────────────────
  const proposalId = approveResp.proposal_id || (approveResp.proposal && approveResp.proposal.id);
  if(!proposalId){
    if(fb){ fb.textContent="✅ Εγκρίθηκε!"; }
    setTimeout(()=>loadNousInitiatives(), 2000);
    return;
  }

  // Poll every 1.5s until done/failed/needs_developer
  let polls=0;
  const pollInterval = setInterval(async ()=>{
    polls++;
    if(polls > 40){ clearInterval(pollInterval); return; } // max 60s
    try {
      const pr = await fetch("/remote/nous-drive/proposal/"+proposalId);
      const pd = await pr.json();
      const p  = pd.proposal || {};
      const log = Array.isArray(p.execution_log) ? p.execution_log : [];
      const st  = p.status || "executing";

      // Update log display
      if(fb){
        const logHtml = log.map(l=>{
          const col = l.startsWith("✅") ? "#86efac" : l.startsWith("❌") ? "#fca5a5" : l.startsWith("⚠️") ? "#fde68a" : "#c4b5fd";
          return `<span style="color:${col};">${escHtml(l)}</span>`;
        }).join("\n");

        if(st==="executing"){
          fb.style.cssText="display:block;padding:10px 12px;border-radius:8px;background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.4);color:#c4b5fd;font-size:12px;margin-top:8px;white-space:pre-wrap;line-height:1.6;";
          fb.innerHTML="<b>⏳ Εκτελείται…</b>\n"+logHtml;

        } else if(st==="done"){
          clearInterval(pollInterval);
          fb.style.cssText="display:block;padding:10px 12px;border-radius:8px;background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);color:#86efac;font-size:12px;margin-top:8px;white-space:pre-wrap;line-height:1.6;";
          fb.innerHTML="<b>✅ Ολοκληρώθηκε!</b>\n"+logHtml;
          // Fade out after user sees result
          setTimeout(()=>{ if(card){card.style.transition="opacity .6s";card.style.opacity="0";} setTimeout(()=>loadNousInitiatives(),700); },3500);

        } else if(st==="failed"){
          clearInterval(pollInterval);
          fb.style.cssText="display:block;padding:10px 12px;border-radius:8px;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#fca5a5;font-size:12px;margin-top:8px;white-space:pre-wrap;line-height:1.6;";
          fb.innerHTML="<b>❌ Αποτυχία εκτέλεσης</b>\n"+logHtml;
          btns.forEach(b=>b.disabled=false);

        } else if(st==="needs_developer"){
          clearInterval(pollInterval);
          const devMsg = p.developer_message || "";
          fb.style.cssText="display:block;padding:10px 14px;border-radius:8px;background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.35);color:#fde68a;font-size:12px;margin-top:8px;";
          fb.innerHTML=`<b>🛠️ Χρειάζεται Developer</b>\n`+logHtml
            +(devMsg?`\n<button onclick="nousAskDeveloper(${JSON.stringify(devMsg)})" style="margin-top:8px;padding:5px 12px;border-radius:8px;border:none;background:rgba(251,191,36,.2);color:#fde68a;cursor:pointer;font-size:12px;font-weight:700;">💬 Ζήτα από τον Developer</button>`:"");
        }
      }
    } catch(_){ /* network hiccup, keep polling */ }
  }, 1500);
}

function nousVoiceInput(){
  const btn = document.getElementById("voiceMicBtn");
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){ alert("Ο browser σου δεν υποστηρίζει φωνητική εισαγωγή. Δοκίμασε Chrome."); return; }
  if(btn && btn.dataset.listening === "1"){
    window._nousRecognition && window._nousRecognition.stop();
    return;
  }
  const rec = new SR();
  rec.lang = "el-GR";
  rec.continuous = false;
  rec.interimResults = false;
  window._nousRecognition = rec;
  rec.onstart = ()=>{
    if(btn){ btn.textContent="🔴"; btn.dataset.listening="1"; btn.style.border="1px solid rgba(239,68,68,.7)"; btn.style.background="rgba(239,68,68,.15)"; }
  };
  rec.onresult = e=>{
    const text = e.results[0][0].transcript;
    const prompt = document.getElementById("prompt");
    if(prompt){ prompt.value = (prompt.value ? prompt.value+" " : "") + text; prompt.focus(); }
    if(btn){ btn.textContent="🎤"; btn.dataset.listening="0"; btn.style.border="1px solid rgba(139,92,246,.4)"; btn.style.background="none"; }
  };
  rec.onerror = err=>{
    if(btn){ btn.textContent="🎤"; btn.dataset.listening="0"; btn.style.border="1px solid rgba(139,92,246,.4)"; btn.style.background="none"; }
    if(err.error !== "aborted") console.warn("Voice error:", err.error);
  };
  rec.onend = ()=>{
    if(btn){ btn.textContent="🎤"; btn.dataset.listening="0"; btn.style.border="1px solid rgba(139,92,246,.4)"; btn.style.background="none"; }
  };
  rec.start();
}

function nousAskDeveloper(message){
  // Pre-fill the chat input and switch to Chat tab
  const chatInput = document.getElementById("chatInput") || document.querySelector('textarea[id*="chat"]') || document.querySelector('input[placeholder*="Ρώτα"]');
  if(chatInput){ chatInput.value = message; chatInput.focus(); }
  // Switch to chat section if possible
  const chatNav = document.querySelector('[data-sec="chat"]') || document.querySelector('.navItem[onclick*="chat"]');
  if(chatNav){ chatNav.click(); }
  // Also try scrolling to top
  window.scrollTo(0,0);
}

async function nousThinkNow(){
  const btn = document.querySelector('button[onclick="nousThinkNow()"]');
  if(btn){ btn.textContent="⏳ Σκέφτομαι…"; btn.disabled=true; }
  const box = document.getElementById("nousInitiativesBox");
  try {
    const d = await fetch("/remote/nous-drive/think", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({force:true})
    }).then(r=>r.json());
    if(d.new_proposals > 0){
      if(box){
        const notif = document.createElement("div");
        notif.style.cssText="background:rgba(139,92,246,.15);border:1px solid rgba(139,92,246,.4);border-radius:10px;padding:10px 14px;font-size:13px;color:#a78bfa;margin-bottom:10px;";
        notif.textContent = `🧠 Ο ΝΟΥΣ σκέφτηκε και βρήκε ${d.new_proposals} νέα πράγματα!`;
        box.insertBefore(notif, box.firstChild);
        setTimeout(()=>notif.remove(), 5000);
      }
    }
    await loadNousInitiatives();
  } catch(e){ console.error(e); }
  finally {
    if(btn){ btn.textContent="🧠 Σκέψου"; btn.disabled=false; }
  }
}

// Auto-load on Home section open
document.addEventListener("DOMContentLoaded", ()=>{
  loadNousInitiatives();
  setInterval(loadNousInitiatives, 60000);
});

// ══════════════════════════════════════════════════════════════
// DAILY BRIEF
// ══════════════════════════════════════════════════════════════
async function loadDailyBrief(){
  const box = document.getElementById("dailyBriefBox");
  if(!box) return;
  box.innerHTML = '<div style="color:var(--muted);">Φόρτωση…</div>';
  try {
    const d = await getJson("/remote/daily-brief");
    if(d.error){ box.innerHTML='<div style="color:#ef4444;">'+escHtml(d.error)+'</div>'; return; }
    let html = '';
    if(d.goals && d.goals.length){
      html += '<div style="margin-bottom:8px;"><b>🎯 Goals:</b> ';
      html += d.goals.map(g=>'<span style="background:rgba(34,211,238,.1);border:1px solid rgba(34,211,238,.2);border-radius:6px;padding:2px 8px;font-size:12px;margin:2px;display:inline-block;">'+escHtml(String(g))+'</span>').join('');
      html += '</div>';
    }
    if(d.active_learning_topics && d.active_learning_topics.length){
      html += '<div style="margin-bottom:8px;"><b>🌐 Ενεργά Θέματα Μάθησης:</b> ';
      html += d.active_learning_topics.map(t=>'<span style="background:rgba(124,92,255,.1);border:1px solid rgba(124,92,255,.2);border-radius:6px;padding:2px 8px;font-size:12px;margin:2px;display:inline-block;">'+escHtml(String(t))+'</span>').join('');
      html += '</div>';
    }
    if(d.learning){
      const l = d.learning;
      html += '<div style="font-size:12px;color:var(--muted);margin-bottom:8px;">📚 Lessons: <b>'+( l.total||0)+'</b> σύνολο</div>';
    }
    if(d.recent_memory && d.recent_memory.length){
      html += '<div style="margin-bottom:4px;"><b>🧠 Πρόσφατη Μνήμη (τελευταία '+d.recent_memory.length+'):</b></div>';
      html += '<div style="display:flex;flex-direction:column;gap:4px;">';
      d.recent_memory.slice(-5).reverse().forEach(m=>{
        const ev = m.event||m.type||JSON.stringify(m).slice(0,60);
        html += '<div style="font-size:12px;padding:4px 8px;background:var(--panel2);border-radius:6px;color:var(--muted);">'+escHtml(ev)+'</div>';
      });
      html += '</div>';
    }
    if(!html) html='<div style="color:var(--muted);font-size:13px;">Δεν υπάρχουν δεδομένα ακόμα.</div>';
    box.innerHTML = html;
  } catch(e){
    box.innerHTML='<div style="color:#ef4444;">'+escHtml(String(e))+'</div>';
  }
}

// ══════════════════════════════════════════════════════════════
// DECISION MEMORY
// ══════════════════════════════════════════════════════════════
async function loadDecisionMemory(){
  try {
    const d = await getJson("/remote/decision-memory/status");
    const stats = document.getElementById("decisionMemoryStats");
    if(stats) stats.textContent = '📊 Σύνολο: ' + (d.total||0) + ' αποφάσεις';
    const list = document.getElementById("decisionMemoryList");
    if(list && d.recent){
      renderDecisions(list, d.recent.slice().reverse());
    }
  } catch(e){}
}

async function searchDecisionMemory(){
  const q = (document.getElementById("decisionSearchQ")||{}).value||"";
  try {
    const d = await postJson("/remote/decision-memory/search", {query:q, limit:30});
    const stats = document.getElementById("decisionMemoryStats");
    if(stats) stats.textContent = '🔍 Αποτελέσματα: ' + (d.length||0);
    const list = document.getElementById("decisionMemoryList");
    if(list) renderDecisions(list, (d||[]).slice().reverse());
  } catch(e){}
}

function renderDecisions(container, items){
  if(!items||!items.length){
    container.innerHTML='<div style="color:var(--muted);text-align:center;padding:16px;">Καμία απόφαση ακόμα.</div>';
    return;
  }
  const confColor = c => c>=0.8?'#22c55e':c>=0.5?'#f59e0b':'#ef4444';
  container.innerHTML = items.map(dec=>{
    const conf = (dec.confidence||0);
    const pct = Math.round(conf*100);
    const ts = dec.created ? new Date(dec.created*1000).toLocaleString('el-GR') : '';
    const tags = (dec.tags||[]).map(t=>'<span style="background:rgba(124,92,255,.1);border:1px solid rgba(124,92,255,.2);border-radius:4px;padding:1px 6px;font-size:11px;">'+escHtml(t)+'</span>').join(' ');
    return `<div style="padding:10px 12px;border:1px solid var(--line);border-radius:10px;margin-bottom:8px;background:var(--panel2);">
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;">
        <span style="font-weight:700;font-size:13px;flex:1;">${escHtml(dec.title||'—')}</span>
        <span style="font-size:12px;font-weight:700;color:${confColor(conf)};">${pct}%</span>
        <span style="font-size:11px;color:var(--muted);">${escHtml(ts)}</span>
      </div>
      ${dec.reason?'<div style="font-size:12px;color:var(--muted);margin-bottom:4px;">'+escHtml(dec.reason)+'</div>':''}
      ${tags?'<div style="margin-top:4px;">'+tags+'</div>':''}
    </div>`;
  }).join('');
}

// ══════════════════════════════════════════════════════════════
// INTERNET LEARNING PIPELINE
// ══════════════════════════════════════════════════════════════
async function loadInternetLearning(){
  const el = document.getElementById("internetLearningStatus");
  if(!el) return;
  try {
    const d = await getJson("/remote/internet-learning/status");
    const k = d.knowledge||{};
    let html = '';
    html += '<div style="display:flex;gap:16px;flex-wrap:wrap;">';
    html += '<span>📚 Γνώσεις: <b>'+(k.learned||0)+'</b></span>';
    html += '<span>📋 Ουρά: <b>'+(k.queue_open||0)+'</b> ανοιχτά</span>';
    if(d.next_topic) html += '<span>⏭️ Επόμενο: <b>'+escHtml(String(d.next_topic.topic||d.next_topic))+'</b></span>';
    html += '</div>';
    el.innerHTML = html;
  } catch(e){ el.textContent = String(e); }
}

async function triggerInternetLearn(useNext=false){
  const topicIn = document.getElementById("internetLearnTopic");
  const topic = (!useNext && topicIn && topicIn.value.trim()) ? topicIn.value.trim() : null;
  const resEl = document.getElementById("internetLearnResult");
  if(resEl){ resEl.style.display="block"; resEl.textContent="⏳ Μαθαίνω…"; }
  try {
    const payload = topic ? {topic} : {};
    const d = await postJson("/remote/internet-learning/topic", payload);
    if(resEl) resEl.textContent = JSON.stringify(d, null, 2);
    await loadInternetLearning();
    feed("Μάθηση ολοκληρώθηκε: " + (d.topic||"επόμενο θέμα"));
  } catch(e){
    if(resEl) resEl.textContent = String(e);
  }
}

// ══════════════════════════════════════════════════════════════
// PROJECT HEALTH
// ══════════════════════════════════════════════════════════════
async function loadProjectHealth(){}
async function runProjectHealth(){
  const sumEl = document.getElementById("projectHealthSummary");
  const boxEl = document.getElementById("projectHealthBox");
  if(sumEl) sumEl.innerHTML='<div style="color:var(--muted);">⏳ Εκτέλεση health check…</div>';
  if(boxEl){ boxEl.style.display="none"; boxEl.textContent=""; }
  try {
    const d = await getJson("/remote/project-health");
    if(boxEl){ boxEl.style.display="block"; boxEl.textContent=JSON.stringify(d,null,2); }
    const ok = d.compile_ok;
    const counts = d.counts||{};
    let badges = '';
    badges += '<span style="padding:3px 10px;border-radius:6px;font-size:12px;font-weight:700;background:'+(ok?'rgba(34,197,94,.15)':'rgba(239,68,68,.15)')+';color:'+(ok?'#22c55e':'#ef4444')+';border:1px solid '+(ok?'rgba(34,197,94,.3)':'rgba(239,68,68,.3)')+';">'+(ok?'✅ Compile OK':'❌ Compile Fail')+'</span> ';
    Object.entries(counts).forEach(([k,v])=>{
      badges += '<span style="padding:2px 8px;border-radius:6px;font-size:11px;background:var(--panel2);border:1px solid var(--line);color:var(--muted);">'+escHtml(k.replace('.json',''))+': '+(v===null?'–':v)+'</span> ';
    });
    if(sumEl) sumEl.innerHTML = badges;
  } catch(e){
    if(sumEl) sumEl.innerHTML='<div style="color:#ef4444;">'+escHtml(String(e))+'</div>';
  }
}

// ══════════════════════════════════════════════════════════════
// SIGNS KNOWLEDGE BASE (Guerrilla / Byzantine / Ottoman)
// ══════════════════════════════════════════════════════════════
async function signsSearch(overrideQuery){
  const qEl = document.getElementById("signsQuery");
  const q = overrideQuery !== undefined ? overrideQuery : (qEl ? qEl.value.trim() : "");
  const metaEl = document.getElementById("signsSearchMeta");
  const listEl = document.getElementById("signsResultsList");
  if(listEl) listEl.innerHTML = '<div style="color:var(--muted);text-align:center;padding:20px;">Αναζήτηση…</div>';
  try {
    const d = await postJson("/field/signs/search", {query: q});
    if(metaEl){
      metaEl.textContent = d.query
        ? '🔍 Αποτελέσματα για "'+d.query+'": '+d.total+' κατηγορίες'
        : '📖 Σύνολο κατηγοριών: '+d.total;
    }
    if(listEl){
      if(!d.results||!d.results.length){
        listEl.innerHTML='<div class="card" style="text-align:center;color:var(--muted);padding:30px;">Κανένα αποτέλεσμα για "'+escHtml(q)+'".</div>';
        return;
      }
      listEl.innerHTML = d.results.map((chunk, i)=>{
        const tags = (chunk.tags||[]).map(t=>'<span style="background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.2);border-radius:4px;padding:1px 7px;font-size:11px;color:#22d3ee;">'+escHtml(t)+'</span>').join(' ');
        const ans = (chunk.answer||"").replace(/\\n/g,'\n');
        const id = 'signs-chunk-'+i;
        return `<div class="card" style="margin-bottom:12px;">
          <div style="display:flex;align-items:flex-start;gap:10px;flex-wrap:wrap;cursor:pointer;" onclick="document.getElementById('${id}').style.display=document.getElementById('${id}').style.display==='none'?'block':'none'">
            <div style="flex:1;">
              <div style="font-weight:700;font-size:13px;margin-bottom:6px;color:var(--text);">❓ ${escHtml(chunk.question||"")}</div>
              <div style="display:flex;gap:4px;flex-wrap:wrap;">${tags}</div>
            </div>
            <span style="font-size:12px;color:var(--muted);white-space:nowrap;user-select:none;">▼ Εμφάνιση</span>
          </div>
          <div id="${id}" style="display:none;margin-top:12px;padding-top:12px;border-top:1px solid var(--line);">
            <div style="font-size:13px;line-height:1.8;color:var(--text);white-space:pre-wrap;">${escHtml(ans)}</div>
          </div>
        </div>`;
      }).join('');
    }
  } catch(e){
    if(listEl) listEl.innerHTML='<div style="color:#ef4444;text-align:center;padding:20px;">'+escHtml(String(e))+'</div>';
  }
}

function signsQuick(q){
  const el = document.getElementById("signsQuery");
  if(el) el.value = q;
  signsSearch(q);
}

async function boot(){
  try{await getJson("/health");document.getElementById("healthBadge").textContent="healthy";document.getElementById("healthBadge").className="badge ok"}catch(e){document.getElementById("healthBadge").textContent="offline";document.getElementById("healthBadge").className="badge bad"}
  await loadHome();
  await loadDailyBrief();
}
boot();
</script>

<script id="nous-auto-linkify">
(function(){
  function escapeHtml(s){
    return String(s)
      .replaceAll("&","&amp;")
      .replaceAll("<","&lt;")
      .replaceAll(">","&gt;");
  }

  function linkifyText(s){
    let html = escapeHtml(s);

    html = html.replace(
      /\b((https?:\/\/|www\.)[^\s<>"']+)/gi,
      function(url){
        let href = url.startsWith("http") ? url : "https://" + url;
        return '<a href="' + href + '" target="_blank" rel="noopener noreferrer">' + url + '</a>';
      }
    );

    html = html.replace(
      /\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b/gi,
      function(email){
        return '<a href="mailto:' + email + '">' + email + '</a>';
      }
    );

    return html;
  }

  function linkifyElement(el){
    if(!el || el.dataset.linkified === "1") return;
    if(el.children.length > 0) return;
    const text = el.textContent || "";
    if(!/(https?:\/\/|www\.|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})/i.test(text)) return;
    el.innerHTML = linkifyText(text);
    el.dataset.linkified = "1";
  }

  function scan(){
    const selectors = [
      "#chat", "#messages", "#feed", "#raw",
      ".chat", ".message", ".bubble", ".answer",
      ".assistant", ".result", ".output", "pre"
    ];
    document.querySelectorAll(selectors.join(",")).forEach(function(el){
      if(el.children.length === 0){
        linkifyElement(el);
      }else{
        el.querySelectorAll("p,div,span,pre").forEach(linkifyElement);
      }
    });
  }

  const css = document.createElement("style");
  css.id = "nous-auto-linkify-css";
  css.textContent = `
    a[href^="http"], a[href^="mailto"]{
      text-decoration: underline;
      font-weight: 700;
      word-break: break-word;
    }
  `;
  if(!document.getElementById("nous-auto-linkify-css")){
    document.head.appendChild(css);
  }

  scan();
  new MutationObserver(scan).observe(document.body, {childList:true, subtree:true});
})();
</script>


<section id="documents" class="section">
  <div class="hero">
    <h1>📚 Document Intake</h1>
    <p>Ανέβασε ή κόλλησε κείμενο ώστε ο ΝΟΥΣ να το περάσει σε γνώση/μνήμη.</p>
  </div>
  <div class="card">
    <h3>Paste document text</h3>
    <input id="docTitle" placeholder="Τίτλος εγγράφου π.χ. manual αποκρύψεων" style="width:100%;padding:10px;margin-bottom:8px;">
    <textarea id="docText" placeholder="Κόλλησε εδώ κείμενο από εγχειρίδιο, σημειώσεις, οδηγίες..." style="width:100%;min-height:180px;padding:10px;"></textarea>
    <button class="miniBtn" onclick="saveLocalDocument()">Save local document memory</button>
    <button class="miniBtn" onclick="listLocalDocuments()">List local documents</button>
  </div>
  <div class="card">
    <h3>Local file preview</h3>
    <input type="file" id="docFile" multiple onchange="previewLocalFiles(event)">
    <p>Σημείωση: Το UI preview διαβάζει κείμενα τοπικά. Για μόνιμη εισαγωγή από Termux χρησιμοποίησε: <b>python run_document_intake.py path/to/file.pdf</b></p>
    <pre id="docPreview"></pre>
  </div>
</section>

<!-- ═══════════════════════════════════════════════════════════
     ΠΕΔΙΟ & ΧΑΡΤΗΣ — Field Diary / Image Analysis / Map
     ═══════════════════════════════════════════════════════════ -->
<section id="field" class="section">
<div class="workspace" style="max-width:1100px;margin:auto;">

  <!-- Header -->
  <div class="hero" style="margin-bottom:16px;">
    <h1 style="margin:0 0 4px 0;">🔍 Εργαλείο Πεδίου</h1>
    <p style="margin:0;color:var(--muted);">Ανάλυση εικόνων σημαδιών · Ημερολόγιο ευρημάτων · Διαδραστικός χάρτης Μεσσηνίας</p>
  </div>

  <!-- Tab buttons -->
  <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
    <button id="ftab-img"    onclick="fieldTab('img')"    style="padding:8px 18px;border-radius:10px;border:1px solid rgba(34,211,238,.5);background:rgba(34,211,238,.15);color:#22d3ee;font-weight:700;cursor:pointer;font-size:13px;">📷 Ανάλυση Εικόνας</button>
    <button id="ftab-diary"  onclick="fieldTab('diary')"  style="padding:8px 18px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-weight:600;cursor:pointer;font-size:13px;">📓 Ημερολόγιο</button>
    <button id="ftab-map"    onclick="fieldTab('map')"    style="padding:8px 18px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-weight:600;cursor:pointer;font-size:13px;">🗺️ Χάρτης</button>
    <button id="ftab-signs"  onclick="fieldTab('signs')"  style="padding:8px 18px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-weight:600;cursor:pointer;font-size:13px;">📚 Γνωσιακή Βάση</button>
  </div>

  <!-- ──────── TAB: IMAGE ANALYSIS ──────── -->
  <div id="field-tab-img">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">

      <!-- Upload + Preview -->
      <div class="card">
        <h3 style="margin:0 0 12px 0;">📤 Ανέβασε Εικόνα</h3>
        <!-- Drop zone -->
        <div id="fieldDropZone"
          ondragover="event.preventDefault();this.style.borderColor='#22d3ee'"
          ondragleave="this.style.borderColor=''"
          ondrop="fieldDropImage(event)"
          style="border:2px dashed var(--line);border-radius:14px;padding:28px;text-align:center;cursor:pointer;color:var(--muted);font-size:13px;transition:border-color .2s;"
          onclick="document.getElementById('fieldImgInput').click()">
          <div style="font-size:36px;margin-bottom:8px;">🖼️</div>
          <div>Σύρε εδώ εικόνα ή <b style="color:#22d3ee;">κλικ για επιλογή</b></div>
          <div style="font-size:11px;margin-top:6px;">JPG · PNG · WEBP · HEIC</div>
        </div>
        <input type="file" id="fieldImgInput" accept="image/*" style="display:none" onchange="fieldPreviewImage(this)">

        <!-- Preview -->
        <div id="fieldImgPreview" style="margin-top:12px;display:none;">
          <img id="fieldImgTag" style="width:100%;border-radius:10px;max-height:280px;object-fit:contain;background:#0a0e1a;" src="" alt="">
          <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
            <select id="fieldAnalysisType" style="flex:1;padding:7px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
              <option value="signs">🔣 Αναγνώριση Σημαδιών/Συμβόλων</option>
              <option value="terrain">🏔️ Ανάλυση Εδάφους/Τοπογραφίας</option>
              <option value="map">🗺️ Ανάγνωση Παλιού Χάρτη</option>
              <option value="rock">🪨 Χαραγμάτα σε Βράχο/Τοίχο</option>
              <option value="artifact">✨ Αναγνώριση Ευρήματος/Αντικειμένου</option>
              <option value="general">🔍 Γενική Ανάλυση</option>
            </select>
            <button onclick="fieldAnalyzeImage()"
              style="padding:7px 16px;border-radius:8px;border:none;background:var(--accent);color:white;font-weight:700;cursor:pointer;font-size:13px;white-space:nowrap;">
              🧠 Ανάλυση AI
            </button>
          </div>
          <textarea id="fieldImgExtraCtx" rows="2" placeholder="Πρόσθεσε πλαίσιο: π.χ. 'βράχος στην πλαγιά του Ταϋγέτου, ύψος 1.2m από έδαφος'" style="width:100%;margin-top:8px;padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;resize:none;"></textarea>
        </div>
      </div>

      <!-- Analysis Result -->
      <div class="card" style="display:flex;flex-direction:column;">
        <h3 style="margin:0 0 12px 0;">🤖 Ανάλυση ΝΟΥΣ</h3>
        <div id="fieldAnalysisStatus" style="color:var(--muted);font-size:13px;">← Ανέβασε εικόνα και πάτα «Ανάλυση AI»</div>
        <div id="fieldAnalysisResult" style="flex:1;font-size:13px;line-height:1.7;color:var(--text);display:none;overflow-y:auto;max-height:420px;"></div>

        <!-- Save to diary button -->
        <div id="fieldSaveToDiary" style="display:none;margin-top:12px;padding-top:12px;border-top:1px solid var(--line);">
          <div style="font-size:12px;color:var(--muted);margin-bottom:8px;">💾 Αποθήκευσε στο Ημερολόγιο:</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <input id="fieldSaveTitle" type="text" placeholder="Τίτλος ευρήματος…" style="flex:1;padding:7px 10px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;min-width:120px;">
            <input id="fieldSaveLat" type="number" step="0.000001" placeholder="Lat" style="width:110px;padding:7px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
            <input id="fieldSaveLon" type="number" step="0.000001" placeholder="Lon" style="width:110px;padding:7px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
            <button onclick="fieldSaveAnalysis()" style="padding:7px 14px;border-radius:8px;border:none;background:var(--ok);color:white;font-weight:700;cursor:pointer;font-size:13px;">💾 Αποθήκευση</button>
          </div>
          <div id="fieldSaveMsg" style="font-size:12px;margin-top:6px;color:var(--ok);display:none;"></div>
        </div>
      </div>
    </div>

    <!-- Recent analyses -->
    <div class="card" style="margin-top:14px;">
      <h3 style="margin:0 0 10px 0;font-size:14px;">🕓 Πρόσφατες Αναλύσεις από το Ημερολόγιο</h3>
      <div id="fieldRecentAnalyses" style="font-size:13px;color:var(--muted);">Φόρτωση…</div>
    </div>
  </div>

  <!-- ──────── TAB: DIARY ──────── -->
  <div id="field-tab-diary" style="display:none;">
    <div style="display:grid;grid-template-columns:380px 1fr;gap:14px;">

      <!-- Add entry form -->
      <div class="card">
        <h3 style="margin:0 0 12px 0;">➕ Νέα Καταχώρηση</h3>
        <div style="display:flex;flex-direction:column;gap:8px;">
          <input id="diaryTitle" type="text" placeholder="Τίτλος *" style="padding:8px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
          <select id="diaryType" style="padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
            <option value="sign">🔣 Σημάδι/Σύμβολο</option>
            <option value="cache">📦 Cache/Ταφή</option>
            <option value="frp">📍 FRP — Σημείο Αναφοράς</option>
            <option value="irp">🗺️ IRP — Γενική Αναφορά</option>
            <option value="terrain">🏔️ Τοπογραφία</option>
            <option value="anomaly">⚡ Ανωμαλία Εδάφους</option>
            <option value="find">✨ Εύρημα</option>
            <option value="note">📝 Σημείωση</option>
          </select>
          <textarea id="diaryNote" rows="3" placeholder="Περιγραφή…" style="padding:8px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;resize:none;"></textarea>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <input id="diaryLat" type="number" step="0.000001" placeholder="Latitude (π.χ. 37.0)" style="padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;">
            <input id="diaryLon" type="number" step="0.000001" placeholder="Longitude (π.χ. 22.1)" style="padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;">
          </div>
          <input id="diaryTags" type="text" placeholder="Tags: ELAS, FRP, χρυσός…" style="padding:8px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;">
          <button onclick="fieldGetGPS()" style="padding:7px;border-radius:8px;border:1px solid rgba(34,211,238,.3);background:rgba(34,211,238,.07);color:#22d3ee;font-size:12px;cursor:pointer;">📡 Χρήση GPS συσκευής</button>
          <button onclick="fieldDiaryAdd()" style="padding:9px;border-radius:8px;border:none;background:var(--accent);color:white;font-weight:700;cursor:pointer;font-size:13px;">➕ Προσθήκη</button>
          <div id="diaryAddMsg" style="font-size:12px;color:var(--ok);display:none;text-align:center;"></div>
        </div>
      </div>

      <!-- Entries list -->
      <div class="card" style="overflow:hidden;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
          <h3 style="margin:0;flex:1;font-size:14px;">📋 Καταχωρήσεις</h3>
          <select id="diaryFilterType" onchange="fieldDiaryLoad()" style="padding:5px 8px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:12px;">
            <option value="">Όλες</option>
            <option value="sign">🔣 Σημάδια</option>
            <option value="cache">📦 Cache</option>
            <option value="frp">📍 FRP</option>
            <option value="find">✨ Ευρήματα</option>
            <option value="anomaly">⚡ Ανωμαλίες</option>
          </select>
          <button onclick="fieldDiaryLoad()" style="padding:5px 10px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">↺</button>
        </div>
        <div id="diaryList" style="overflow-y:auto;max-height:520px;"></div>
      </div>
    </div>
  </div>

  <!-- ──────── TAB: MAP ──────── -->
  <div id="field-tab-map" style="display:none;">
    <div class="card" style="padding:0;overflow:hidden;">
      <div style="padding:12px 16px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <span style="font-weight:700;font-size:14px;">🗺️ Χάρτης Ευρημάτων — Μεσσηνία</span>
        <span style="font-size:12px;color:var(--muted);">OpenStreetMap · Κλικ σε marker για λεπτομέρειες</span>
        <button onclick="fieldMarkersLoad()" style="margin-left:auto;padding:5px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">↺ Ανανέωση</button>
      </div>
      <!-- Leaflet map container -->
      <div id="fieldMap" style="height:560px;width:100%;background:#0a0e1a;"></div>
    </div>
    <div class="card" style="margin-top:12px;">
      <h3 style="margin:0 0 10px 0;font-size:14px;">📊 Σύνοψη Markers</h3>
      <div id="fieldMapSummary" style="font-size:13px;color:var(--muted);">Φόρτωση…</div>
    </div>
  </div>

  <!-- ──────── TAB: SIGNS KNOWLEDGE BASE ──────── -->
  <div id="field-tab-signs" style="display:none;">

    <!-- Search bar -->
    <div class="card" style="margin-bottom:12px;">
      <h3 style="margin:0 0 12px 0;">📚 Γνωσιακή Βάση — Αντάρτικα Σημάδια, Χάρτες, Βυζαντινά &amp; Οθωμανικά Σύμβολα</h3>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <input id="signsQuery" type="text" placeholder="Αναζήτηση: π.χ. ELAS, βυζαντινό, cairn, WGS84, οθωμανικό, Μεσσηνία…"
          style="flex:1;padding:9px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:13px;"
          onkeydown="if(event.key==='Enter') signsSearch()">
        <button onclick="signsSearch()" style="padding:9px 20px;border-radius:10px;border:none;background:var(--accent);color:white;font-weight:700;cursor:pointer;font-size:13px;">🔍 Αναζήτηση</button>
        <button onclick="signsSearch('')" style="padding:9px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;">📖 Όλες οι Κατηγορίες</button>
      </div>
      <div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap;">
        <span style="font-size:11px;color:var(--muted);">Γρήγορη επιλογή:</span>
        <button onclick="signsQuick('αντάρτικα')" class="miniBtn">🪖 Αντάρτικα</button>
        <button onclick="signsQuick('βυζαντιν')" class="miniBtn">⛪ Βυζαντινά</button>
        <button onclick="signsQuick('οθωμανικ')" class="miniBtn">☽ Οθωμανικά</button>
        <button onclick="signsQuick('χάρτης')" class="miniBtn">🗺️ Χάρτες</button>
        <button onclick="signsQuick('WGS84')" class="miniBtn">📡 GPS/WGS84</button>
        <button onclick="signsQuick('cairn')" class="miniBtn">🪨 Cairn</button>
        <button onclick="signsQuick('τοπωνύμ')" class="miniBtn">📍 Τοπωνύμια</button>
        <button onclick="signsQuick('Μεσσηνία')" class="miniBtn">🏛️ Μεσσηνία</button>
      </div>
      <div id="signsSearchMeta" style="font-size:12px;color:var(--muted);margin-top:8px;"></div>
    </div>

    <!-- Results -->
    <div id="signsResultsList"></div>
  </div>

</div>
</section>

<script id="nous-document-intake-ui">
function _docStore(){
  try { return JSON.parse(localStorage.getItem("NOUS_DOCUMENT_MEMORY") || "[]"); }
  catch(e){ return []; }
}
function _saveDocStore(items){
  localStorage.setItem("NOUS_DOCUMENT_MEMORY", JSON.stringify(items));
}
function saveLocalDocument(){
  const title = document.getElementById("docTitle")?.value || "Untitled document";
  const text = document.getElementById("docText")?.value || "";
  if(!text.trim()){ alert("Δεν υπάρχει κείμενο για αποθήκευση."); return; }
  const items = _docStore();
  items.push({
    id: Date.now(),
    created_at: new Date().toISOString(),
    title,
    text,
    summary: text.slice(0, 1200),
    words: text.trim().split(/\s+/).length
  });
  _saveDocStore(items);
  alert("Αποθηκεύτηκε τοπικά στο UI document memory.");
}
function listLocalDocuments(){
  const items = _docStore();
  renderObject({
    local_document_memory: items.map(x => ({
      id:x.id,
      title:x.title,
      created_at:x.created_at,
      words:x.words,
      summary:x.summary
    }))
  });
}
function previewLocalFiles(event){
  const out = document.getElementById("docPreview");
  const files = Array.from(event.target.files || []);
  out.textContent = "";
  files.forEach(file => {
    const reader = new FileReader();
    reader.onload = function(){
      out.textContent += "\n\n===== " + file.name + " =====\n" + String(reader.result).slice(0, 5000);
    };
    if(file.type.startsWith("text/") || /\.(txt|md|json|csv|py|html|css|js)$/i.test(file.name)){
      reader.readAsText(file);
    }else{
      out.textContent += "\n\n===== " + file.name + " =====\nStored preview only. Use Termux intake command for permanent library.";
    }
  });
}
</script>

















<script id="nous-clean-live-output-layer">
(function(){
  if(window.NOUS_CLEAN_LIVE_OUTPUT_LAYER) return;
  window.NOUS_CLEAN_LIVE_OUTPUT_LAYER = true;

  function parseMaybeJson(text){
    try { return JSON.parse(String(text || "").trim()); } catch(e){ return null; }
  }

  function cleanOutputFromObject(obj){
    if(!obj || typeof obj !== "object") return null;

    if(obj.mode === "document_recall" || obj.source === "document_chat_bridge"){
      return obj.human_answer || obj.answer || obj.response || obj.text || "Απάντηση από μαθημένο έγγραφο.";
    }

    if(obj.human_answer) return obj.human_answer;
    if(obj.summary && typeof obj.summary === "string") return obj.summary;
    if(obj.answer && typeof obj.answer === "string") return obj.answer;
    if(obj.response && typeof obj.response === "string") return obj.response;
    if(obj.text && typeof obj.text === "string") return obj.text;

    if(obj.executed && obj.mission){
      const title = obj.mission.title || "Αποστολή";
      const status = obj.mission.status || "άγνωστη";
      const tasks = Array.isArray(obj.mission.tasks) ? obj.mission.tasks.length : 0;
      return "Ο ΝΟΥΣ δημιούργησε αποστολή: " + title + ".\nΚατάσταση: " + status + ".\nΒήματα: " + tasks + ".";
    }

    if(obj.ok === true) return "Η ενέργεια ολοκληρώθηκε επιτυχώς.";
    if(obj.ok === false || obj.error) return "Προέκυψε σφάλμα: " + (obj.error || "άγνωστο σφάλμα") + ".";

    return null;
  }

  function cleanLiveOutputElement(el){
    if(!el || el.dataset.nousCleaned === "1") return;

    const text = el.textContent || "";
    const obj = parseMaybeJson(text);
    if(!obj) return;

    const clean = cleanOutputFromObject(obj);
    if(!clean) return;

    el.dataset.nousRawJson = text;
    el.dataset.nousCleaned = "1";
    el.textContent = clean;
  }

  function scan(){
    const candidates = [
      "#raw", "#output", "#live-output",
      ".raw", ".output", ".live-output",
      "pre"
    ];
    document.querySelectorAll(candidates.join(",")).forEach(cleanLiveOutputElement);
  }

  scan();
  new MutationObserver(scan).observe(document.body, {
    childList:true,
    subtree:true,
    characterData:true
  });
})();
</script>





<script id="nous-clean-human-answer-layer">
(function(){
  window.NOUS_CLEAN_HUMAN_ANSWER_LAYER = true;

  function normalizeText(input){
    if(input === null || input === undefined) return "";
    if(typeof input === "string") return input;
    if(typeof input === "object"){
      if(input.human_answer) return String(input.human_answer);
      if(input.answer) return String(input.answer);
      if(input.response) return String(input.response);
      if(input.text) return String(input.text);
      try { return JSON.stringify(input); } catch(e){ return String(input); }
    }
    return String(input);
  }

  function looksJson(text){
    text = String(text || "").trim();
    return text.startsWith("{") || text.startsWith("[");
  }

  function parseMaybeJson(text){
    try { return JSON.parse(String(text || "").trim()); } catch(e){ return null; }
  }

  function bestHuman(obj){
    if(!obj || typeof obj !== "object") return null;
    return obj.human_answer || obj.answer || obj.response || obj.text || obj.summary || null;
  }

  function renderCleanMessage(el, input){
    let text = normalizeText(input);

    if(!looksJson(text)){
      el.textContent = text;
      return;
    }

    const obj = parseMaybeJson(text);
    if(!obj){
      el.textContent = text;
      return;
    }

    const human = bestHuman(obj);
    if(!human){
      el.textContent = text;
      return;
    }

    el.innerHTML = "";

    const main = document.createElement("div");
    main.className = "nousHumanAnswer";
    main.textContent = String(human);
    el.appendChild(main);

    const sources = obj.sources || [];
    if(Array.isArray(sources) && sources.length){
      const srcBox = document.createElement("div");
      srcBox.className = "nousSourcesBox";
      srcBox.innerHTML = "<b>Πηγές:</b>";
      sources.slice(0,5).forEach(function(s, i){
        const line = document.createElement("div");
        line.textContent = "[" + (i+1) + "] " + (s.document || "document");
        srcBox.appendChild(line);
      });
      el.appendChild(srcBox);
    }
  }

  window.NOUS_RENDER_CLEAN_MESSAGE = renderCleanMessage;
  window.NOUS_HUMANIZE_TEXT = function(input){
    const text = normalizeText(input);
    if(!looksJson(text)) return text;
    const obj = parseMaybeJson(text);
    const human = bestHuman(obj);
    return human || text;
  };
})();
</script>


<script id="nous-chat-upload-ui">
async function uploadChatFiles(){
  const input = document.getElementById("chatUploadFile");
  const note = document.getElementById("chatUploadNote")?.value || "uploaded_from_chat";
  const files = Array.from(input?.files || []);

  if(!files.length){
    alert("Διάλεξε πρώτα αρχείο.");
    return;
  }

  for(const file of files){
    const fd = new FormData();
    fd.append("file", file);
    fd.append("note", note);

    addMsg("Ανεβάζω και μαθαίνω το αρχείο: " + file.name, "user");

    try{
      const r = await fetch("/remote/document/upload", {
        method: "POST",
        body: fd
      });

      const data = await r.json();
      addMsg(data, "bot");

      if(typeof renderObject === "function"){
        renderObject(data); if(window.nousCaptureConversation){nousCaptureConversation(data);}
      }
    }catch(e){
      addMsg("Σφάλμα upload: " + e, "bot");
    }
  }
}
</script>


<script id="nous-conversation-selector-js">
let NOUS_ACTIVE_CONVERSATION_ID = "";

function newNousConversation(){
  NOUS_ACTIVE_CONVERSATION_ID = "";
  const sel = document.getElementById("nousConversationSelect");
  if(sel) sel.value = "";
  const label = document.getElementById("activeConversationLabel");
  if(label) label.textContent = "Ενεργή: νέα συνομιλία";
  addMsg("Ξεκινάμε νέα συνομιλία.", "bot");
}

async function loadNousConversations(){
  try{
    const r = await fetch("/remote/conversations");
    const data = await r.json();
    const sel = document.getElementById("nousConversationSelect");
    if(!sel) return;

    const old = sel.value || NOUS_ACTIVE_CONVERSATION_ID || "";
    sel.innerHTML = '<option value="">Νέα συνομιλία</option>';

    (data.conversations || []).forEach(c => {
      const o = document.createElement("option");
      o.value = c.id;
      o.textContent = (c.title || "Συνομιλία") + " (" + (c.messages || 0) + ")";
      sel.appendChild(o);
    });

    if(old) sel.value = old;
  }catch(e){
    console.log("conversation list failed", e);
  }
}

async function selectNousConversation(){
  const sel = document.getElementById("nousConversationSelect");
  const id = sel ? sel.value : "";
  NOUS_ACTIVE_CONVERSATION_ID = id || "";

  const label = document.getElementById("activeConversationLabel");

  if(!id){
    if(label) label.textContent = "Ενεργή: νέα συνομιλία";
    addMsg("Άνοιξες νέα συνομιλία.", "bot");
    return;
  }

  try{
    const r = await fetch("/remote/conversations/" + encodeURIComponent(id));
    const data = await r.json();

    if(label) label.textContent = "Ενεργή: " + (data.title || id);

    const msgs = data.messages || [];
    const last = msgs.slice(-8).map(m => {
      const role = m.role === "user" ? "Εσύ" : "ΝΟΥΣ";
      return role + ": " + (m.content || "");
    }).join("\\n\\n");

    addMsg("Συνέχεια παλιάς συνομιλίας:\\n\\n" + last, "bot");
  }catch(e){
    addMsg("Δεν μπόρεσα να ανοίξω τη συνομιλία: " + e, "bot");
  }
}

window.addEventListener("load", () => {
  setTimeout(loadNousConversations, 800);
});
</script>


<script id="NOUS_CAPTURE_CONVERSATION_ID">
function nousCaptureConversation(data){
  try{
    if(data && data.conversation_id){
      NOUS_ACTIVE_CONVERSATION_ID = data.conversation_id;
      const label = document.getElementById("activeConversationLabel");
      if(label) label.textContent = "Ενεργή: " + (data.conversation?.title || data.conversation_id);
      loadNousConversations();
    }
  }catch(e){}
}
</script>


<script id="nous-clean-chat-js">
function nousTextFromResponse(data){
  try{
    if(data === null || data === undefined) return "";
    if(typeof data === "string") return data;

    if(typeof data === "object"){
      if(data.human_answer) return String(data.human_answer);
      if(data.answer) return String(data.answer);
      if(data.response) return String(data.response);
      if(data.text) return String(data.text);

      if(data.mode === "document_upload" && data.result && data.result.answer){
        return String(data.result.answer);
      }

      if(data.ok === true && data.mission){
        return "Δημιουργήθηκε αποστολή: " + (data.mission.title || "Mission") +
               "\\nΚατάσταση: " + (data.mission.status || "active") +
               "\\nΒήματα: " + ((data.mission.tasks || []).length);
      }

      return JSON.stringify(data, null, 2);
    }

    return String(data);
  }catch(e){
    return String(data);
  }
}

function nousFindChatLog(){
  return document.getElementById("chatlog")
      || document.querySelector(".chatlog")
      || document.getElementById("messages")
      || document.querySelector(".messages");
}

function nousMarkdown(text){
  // Extract code blocks first to protect them
  const codeBlocks = [];
  let s = text.replace(/```(\w*)\n?([\s\S]*?)```/g, function(_, lang, code){
    const idx = codeBlocks.length;
    const label = lang || "code";
    codeBlocks.push(`<div style="position:relative;margin:.5em 0;">
      <div style="font-size:11px;opacity:.5;padding:2px 8px;background:#0d0d0d;border-radius:6px 6px 0 0;">${label}</div>
      <pre style="margin:0;padding:10px 12px;background:#0d0d0d;border-radius:0 0 6px 6px;overflow-x:auto;font-size:13px;line-height:1.5;"><code>${code.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}</code></pre>
    </div>`);
    return `\x00CODE${idx}\x00`;
  });

  // Extract app-approval tags
  const approvals = [];
  s = s.replace(/<app-approval\s+plan_id="([^"]+)"\s+title="([^"]*)"[^>]*><\/app-approval>/g, function(_, pid, title){
    const idx = approvals.length;
    approvals.push(`<div style="margin:.8em 0;padding:12px 16px;background:#0d2b1a;border:1px solid #1a6b3a;border-radius:10px;">
      <div style="font-size:13px;margin-bottom:8px;opacity:.8;">🏗️ ${title||"Εφαρμογή"} — plan_id: <code style="font-size:11px;">${pid}</code></div>
      <div style="display:flex;gap:8px;">
        <button onclick="approveAppBuild('${pid}')" style="padding:8px 18px;background:#00c85a;color:#000;border:0;border-radius:8px;font-weight:700;cursor:pointer;font-size:14px;">✅ Εγκρίνω — Γράψε Αρχεία</button>
        <button onclick="rejectAppBuild('${pid}')" style="padding:8px 18px;background:#333;color:#e0e0e0;border:0;border-radius:8px;cursor:pointer;font-size:14px;">❌ Απόρριψη</button>
        <button onclick="viewAppBuild('${pid}')" style="padding:8px 18px;background:#222;color:#e0e0e0;border:0;border-radius:8px;cursor:pointer;font-size:14px;">👁️ Preview Κώδικα</button>
      </div>
    </div>`);
    return `\x00APPR${idx}\x00`;
  });

  // Standard markdown
  s = s
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>")
    .replace(/\*(.+?)\*/g,"<em>$1</em>")
    .replace(/`(.+?)`/g,"<code style='background:#111;padding:1px 5px;border-radius:4px;'>$1</code>")
    .replace(/^(#{1,3})\s+(.+)$/gm, function(_,h,t){
      const n=h.length; return `<h${n} style="margin:.4em 0;font-size:${1.25-n*.1}em;color:#a0e0c0">${t}</h${n}>`;
    })
    .replace(/^---+$/gm,"<hr style='border:0;border-top:1px solid #333;margin:.5em 0'>")
    .replace(/^[-•]\s+(.+)$/gm,"<li>$1</li>")
    .replace(/\n/g,"<br>");
  s = s.replace(/(<li>.*?<\/li>)(<br>(<li>.*?<\/li>))*/g, function(m){
    return "<ul style='margin:.3em 0 .3em 1.2em;padding:0'>"+m.replace(/<br>/g,"")+"</ul>";
  });

  // Restore code blocks and approvals
  codeBlocks.forEach((block, i) => { s = s.replace(`\x00CODE${i}\x00`, block); });
  approvals.forEach((block, i) => { s = s.replace(`\x00APPR${i}\x00`, block); });

  return s;
}

function nousAddMsgClean(content, who){
  const log = nousFindChatLog();
  const text = nousTextFromResponse(content);
  if(!log) return false;

  const div = document.createElement("div");
  div.className = "msg chatMsg " + (who || "bot");
  if(who === "user"){
    div.textContent = text;
  } else {
    div.innerHTML = nousMarkdown(text);
  }
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return true;
}

// Override old addMsg that printed [object Object].
window.addMsg = function(content, who){
  return nousAddMsgClean(content, who);
};

// Override renderObject so it does not dump huge JSON into chat.
window.renderObject = function(data){
  try{
    if(window.nousCaptureConversation) window.nousCaptureConversation(data);

    const out = document.getElementById("output");
    if(out){ out.textContent = JSON.stringify(data, null, 2); }
  }catch(e){}
};

function nousToggleTools(){
  const body = document.getElementById("nousToolBody");
  if(body) body.classList.toggle("open");
}

function nousWrapTools(){
  if(document.getElementById("nousToolWrapper")) return;

  const upload = document.getElementById("chatUploadCard");
  const conv = document.getElementById("conversationPanel");
  if(!upload && !conv) return;

  const wrapper = document.createElement("div");
  wrapper.id = "nousToolWrapper";
  wrapper.className = "nousTopTools";
  wrapper.innerHTML = '<button class="nousToolToggle" onclick="nousToggleTools()">⚙️ Εργαλεία / Upload / Συνομιλίες</button><div id="nousToolBody" class="nousToolBody"></div>';

  const first = upload || conv;
  first.parentNode.insertBefore(wrapper, first);

  const body = wrapper.querySelector("#nousToolBody");
  if(upload) body.appendChild(upload);
  if(conv) body.appendChild(conv);
}

async function nousSendCleanMessage(){
  const input = document.getElementById("messageInput")
             || document.getElementById("chatInput")
             || document.getElementById("prompt")
             || document.querySelector("textarea")
             || document.querySelector('input[type="text"]');

  if(!input) return false;

  const msg = (input.value || "").trim();
  if(!msg) return false;

  input.value = "";
  addMsg(msg, "user");

  try{
    const r = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        message: msg,
        conversation_id: window.NOUS_ACTIVE_CONVERSATION_ID || ""
      })
    });

    const data = await r.json();
    addMsg(data, "bot");
    renderObject(data);
  }catch(e){
    addMsg("Σφάλμα επικοινωνίας: " + e, "bot");
  }

  return true;
}

window.addEventListener("load", () => {
  setTimeout(nousWrapTools, 300);

  const sendBtn = Array.from(document.querySelectorAll("button")).find(b => 
    (b.textContent || "").trim().toLowerCase() === "send"
  );

  if(sendBtn && !sendBtn.dataset.nousCleanBound){
    sendBtn.dataset.nousCleanBound = "1";
    sendBtn.onclick = function(ev){
      ev.preventDefault();
      nousSendCleanMessage();
      return false;
    };
  }
});
</script>

<script id="nous-app-builder">
// ── App Builder ─────────────────────────────────────────────────────────────

async function startAppBuild(){
  const prompt = (document.getElementById("appBuilderPrompt")?.value||"").trim();
  if(!prompt){ alert("Περιέγραψε τι εφαρμογή θέλεις!"); return; }
  const btn = document.getElementById("appBuildBtn");
  const status = document.getElementById("appBuilderStatus");
  if(btn) btn.disabled = true;
  if(status) status.textContent = "⏳ Ο ΝΟΥΣ σχεδιάζει την εφαρμογή... (μπορεί να πάρει 20-40 δευτερόλεπτα)";
  try {
    const r = await fetch("/remote/app-builder/plan", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({description: prompt})
    });
    const d = await r.json();
    if(d.ok && d.plan){
      const plan = d.plan;
      if(status) status.textContent = "✅ Σχέδιο έτοιμο! Δες το preview και έγκρινε.";
      showAppBuildPreview(plan);
      loadAppBuilderList();
    } else {
      if(status) status.textContent = "❌ Σφάλμα: " + (d.error||"άγνωστο");
    }
  } catch(e){
    if(status) status.textContent = "❌ Σφάλμα επικοινωνίας: " + e;
  } finally {
    if(btn) btn.disabled = false;
  }
}

function showAppBuildPreview(plan){
  const preview = document.getElementById("appBuilderPreview");
  const content = document.getElementById("appBuilderPreviewContent");
  if(!preview||!content) return;
  preview.style.display = "block";
  const tech = (plan.tech_stack||[]).join(", ");
  const filesHtml = (plan.files||[]).map(f=>
    `<div style="margin:.4em 0;padding:8px;background:#111;border-radius:6px;">
      <code style="color:#a0e0c0;">${f.path}</code>
      <span style="opacity:.6;font-size:12px;margin-left:8px;">${f.description||""}</span>
      <pre style="margin:.3em 0 0;padding:8px;background:#0d0d0d;border-radius:4px;max-height:200px;overflow:auto;font-size:12px;">${(f.content||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").slice(0,1500)}</pre>
    </div>`
  ).join("");
  content.innerHTML = `
    <div style="margin-bottom:12px;">
      <strong>${plan.title||plan.app_name}</strong>
      <span style="opacity:.6;font-size:12px;margin-left:8px;">${tech}</span>
    </div>
    <div style="margin-bottom:8px;font-size:13px;opacity:.7;">${plan.description||""}</div>
    <div style="margin-bottom:12px;">${filesHtml}</div>
    ${plan.run_command?`<div style="font-size:13px;margin-bottom:4px;">▶ <code>${plan.run_command}</code></div>`:""}
    ${plan.install_notes?`<div style="font-size:12px;opacity:.6;">📦 ${plan.install_notes}</div>`:""}
    ${plan.notes?`<div style="font-size:12px;opacity:.6;margin-top:4px;">ℹ️ ${plan.notes}</div>`:""}
    <div style="margin-top:14px;display:flex;gap:8px;">
      <button onclick="approveAppBuild('${plan.plan_id}')" style="padding:10px 22px;background:#00c85a;color:#000;border:0;border-radius:8px;font-weight:700;cursor:pointer;font-size:14px;">✅ Εγκρίνω — Γράψε Αρχεία</button>
      <button onclick="rejectAppBuild('${plan.plan_id}')" style="padding:10px 18px;background:#333;color:#e0e0e0;border:0;border-radius:8px;cursor:pointer;font-size:14px;">❌ Απόρριψη</button>
    </div>
  `;
}

async function approveAppBuild(plan_id){
  const confirmed = confirm("Εγκρίνεις τη δημιουργία όλων των αρχείων στον φάκελο apps/?");
  if(!confirmed) return;
  const status = document.getElementById("appBuilderStatus");
  if(status) status.textContent = "⏳ Γράφω αρχεία...";
  try {
    const r = await fetch("/remote/app-builder/approve", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({plan_id})
    });
    const d = await r.json();
    if(d.ok){
      const loc = d.location || ("apps/" + d.app_name);
      const files = (d.files_written||[]).length;
      const errs = (d.syntax_errors||[]).length;
      const msg = errs > 0
        ? `✅ Γράφτηκαν ${files} αρχεία (⚠️ ${errs} syntax error). Φάκελος: ${loc}`
        : `✅ Γράφτηκαν ${files} αρχεία χωρίς σφάλματα!\n📁 Φάκελος: ${loc}\n▶ ${d.run_command||""}`;
      if(status) status.textContent = msg;
      alert(msg);
      loadAppBuilderList();
      // Add to chat for reference
      addMsg("✅ **App Builder:** " + d.title + " — γράφτηκε στο " + loc, "bot");
    } else {
      if(status) status.textContent = "❌ " + (d.error||"Αποτυχία");
      alert("Σφάλμα: " + (d.error||"unknown"));
    }
  } catch(e){
    if(status) status.textContent = "❌ Σφάλμα: " + e;
  }
}

async function rejectAppBuild(plan_id){
  await fetch("/remote/app-builder/reject", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({plan_id})
  });
  const status = document.getElementById("appBuilderStatus");
  if(status) status.textContent = "❌ Απορρίφθηκε";
  loadAppBuilderList();
}

async function viewAppBuild(plan_id){
  showSection("appbuilder");
  const r = await fetch("/remote/app-builder/get/" + plan_id);
  const d = await r.json();
  if(d.ok && d.build) showAppBuildPreview(d.build);
}

async function loadAppBuilderList(){
  const el = document.getElementById("appBuilderList");
  if(!el) return;
  try {
    const r = await fetch("/remote/app-builder/list");
    const d = await r.json();
    const builds = (d.builds||[]).slice().reverse();
    if(!builds.length){ el.innerHTML="<div style='opacity:.5;font-size:13px;'>Δεν υπάρχουν builds ακόμα.</div>"; return; }
    const statusIcon = s => s==="approved"?"✅":s==="rejected"?"❌":"⏳";
    el.innerHTML = builds.map(b=>{
      const appName = (b.app_name||b.title||"").toLowerCase().replace(/\s+/g,"_").replace(/[^a-z0-9_]/g,"");
      const openUrl = `/apps/${appName}/`;
      return `
      <div style="padding:10px;background:#111;border-radius:8px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div>
          <strong>${b.title||b.app_name}</strong>
          <span style="margin-left:8px;font-size:12px;opacity:.5;">${statusIcon(b.status)} ${b.status}</span>
          <div style="font-size:12px;opacity:.5;">${(b.tech_stack||[]).join(", ")} · ${(b.files||[]).length} αρχεία</div>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${b.status==="pending_approval"?`<button onclick="approveAppBuild('${b.plan_id}')" style="padding:6px 12px;background:#00c85a;color:#000;border:0;border-radius:6px;font-weight:700;cursor:pointer;font-size:12px;">Εγκρίνω</button>`:""}
          ${b.status==="approved"?`<a href="${openUrl}" target="_blank" style="padding:6px 14px;border-radius:6px;border:none;background:#22d3ee;color:#000;font-weight:700;font-size:12px;text-decoration:none;">🚀 Άνοιξε</a>`:""}
          <button onclick="viewAppBuild('${b.plan_id}')" style="padding:6px 12px;background:#222;color:#e0e0e0;border:0;border-radius:6px;cursor:pointer;font-size:12px;">Preview</button>
        </div>
      </div>`;
    }).join("");
  } catch(e){ el.textContent = "Σφάλμα: " + e; }
}

// ── App Files Browser (full) ─────────────────────────────────────────────────
let _appRunningSet = new Set();

async function loadAppFiles(){
  const el = document.getElementById("appFilesBrowser");
  if(!el) return;
  el.innerHTML = `<div style="color:var(--muted);font-size:13px;">⏳ Φόρτωση…</div>`;
  try {
    const d = await getJson("/remote/app-builder/files");
    const apps = d.apps || [];
    if(!apps.length){
      el.innerHTML = `<div style="padding:12px;background:var(--panel2);border-radius:10px;border:1px dashed var(--line);color:var(--muted);">
        Ο φάκελος <code>apps/</code> είναι άδειος — δημιούργησε και έγκρινε μια εφαρμογή πρώτα.
      </div>`;
      return;
    }
    el.innerHTML = apps.map(app => {
      const isRunning = _appRunningSet.has(app.name);
      const filesHtml = (app.files||[]).map(f=>`
        <button onclick="appViewFile('${escHtml(app.name)}','${escHtml(f.name)}')"
          style="background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.08);border-radius:6px;padding:4px 10px;font-size:11px;font-family:monospace;color:#a5f3fc;cursor:pointer;text-align:left;">
          📄 ${escHtml(f.name)} <span style="color:rgba(255,255,255,.3);margin-left:4px;">${f.size_kb}KB</span>
        </button>`).join("");
      return `
      <div id="appCard_${escHtml(app.name)}" style="background:var(--panel2);border-radius:12px;padding:14px 16px;margin-bottom:12px;border:1px solid var(--line);">
        <!-- Header row -->
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
          <span style="font-size:22px;">📂</span>
          <div style="flex:1;min-width:0;">
            <div style="font-weight:700;font-size:15px;color:#22d3ee;">${escHtml(app.name)}</div>
            <div style="font-size:11px;color:var(--muted);">${escHtml(app.path)} · ${app.file_count} αρχεία</div>
          </div>
          <!-- Action buttons -->
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <button id="runBtn_${escHtml(app.name)}"
              onclick="appRunToggle('${escHtml(app.name)}','${escHtml(app.run_command||'')}')"
              style="padding:6px 14px;border-radius:8px;border:none;background:${isRunning?'#ef4444':'#22c55e'};color:white;font-weight:700;font-size:12px;cursor:pointer;white-space:nowrap;">
              ${isRunning ? '⏹ Stop' : '▶ Run'}
            </button>
            <a href="/remote/app-builder/download/${escHtml(app.name)}"
              style="padding:6px 12px;border-radius:8px;border:1px solid rgba(251,191,36,.4);background:rgba(251,191,36,.08);color:#fbbf24;font-size:12px;font-weight:600;text-decoration:none;white-space:nowrap;">
              📥 ZIP
            </a>
          </div>
        </div>
        <!-- Run command display -->
        <div style="background:rgba(0,0,0,.4);border-radius:8px;padding:7px 12px;font-family:monospace;font-size:12px;color:#86efac;margin-bottom:10px;display:flex;align-items:center;gap:8px;">
          <span style="color:rgba(255,255,255,.3);">▶</span>
          <span>${escHtml(app.run_command||'python '+app.path+'/main.py')}</span>
        </div>
        <!-- Files list -->
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">${filesHtml}</div>
        <!-- Output terminal (hidden by default) -->
        <div id="appOutput_${escHtml(app.name)}" style="display:none;margin-top:10px;">
          <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">📟 Output:</div>
          <pre id="appLog_${escHtml(app.name)}"
            style="background:#0a0e1a;border:1px solid rgba(34,211,238,.2);border-radius:8px;padding:10px;font-size:11px;color:#86efac;white-space:pre-wrap;max-height:260px;overflow-y:auto;margin:0;"></pre>
        </div>
      </div>`;
    }).join("");
    el.innerHTML += `<div style="font-size:11px;color:var(--muted);margin-top:4px;">📁 Φάκελος: <code>apps/</code> του project</div>`;
  } catch(e){ el.innerHTML = `<div style="color:var(--bad);">⚠️ ${escHtml(String(e))}</div>`; }
}

async function appRunToggle(appName, runCmd){
  if(_appRunningSet.has(appName)){
    // STOP
    await fetch("/remote/app-builder/stop-app", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({app: appName})
    });
    _appRunningSet.delete(appName);
    const btn = document.getElementById("runBtn_"+appName);
    const out = document.getElementById("appOutput_"+appName);
    if(btn){ btn.textContent="▶ Run"; btn.style.background="#22c55e"; }
    if(out) out.style.display="none";
    return;
  }
  // RUN
  const btn = document.getElementById("runBtn_"+appName);
  const out = document.getElementById("appOutput_"+appName);
  const log = document.getElementById("appLog_"+appName);
  if(btn){ btn.textContent="⏳ Εκκίνηση…"; btn.disabled=true; }
  if(out) out.style.display="block";
  if(log) log.textContent = "⏳ Εκκίνηση εφαρμογής…\n";
  try {
    const r = await fetch("/remote/app-builder/run-app", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({app: appName, run_command: runCmd})
    });
    const d = await r.json();
    // Show repair badge if auto-repair happened
    if(d.repaired && d.repair_msg){
      const card = document.getElementById("appCard_"+appName);
      if(card){
        let badge = card.querySelector(".repair-badge");
        if(!badge){
          badge = document.createElement("div");
          badge.className = "repair-badge";
          badge.style.cssText = "background:rgba(251,191,36,.12);border:1px solid rgba(251,191,36,.4);border-radius:8px;padding:6px 12px;font-size:12px;color:#fbbf24;margin-bottom:8px;";
          card.insertBefore(badge, card.firstChild);
        }
        badge.textContent = "🔧 " + d.repair_msg;
      }
    }
    if(d.ok && d.running){
      _appRunningSet.add(appName);
      if(btn){ btn.textContent="⏹ Stop"; btn.style.background="#ef4444"; btn.disabled=false; }
      if(log) log.textContent = (d.output||"(χωρίς output ακόμα)");
      _pollAppLog(appName);
    } else {
      if(btn){ btn.textContent="▶ Run"; btn.style.background="#22c55e"; btn.disabled=false; }
      if(log) log.textContent = "❌ Αποτυχία: " + (d.error||"unknown") + "\n" + (d.output||"");
    }
  } catch(e){
    if(btn){ btn.textContent="▶ Run"; btn.style.background="#22c55e"; btn.disabled=false; }
    if(log) log.textContent = "❌ " + e;
  }
}

function _pollAppLog(appName){
  let polls = 0;
  const iv = setInterval(async ()=>{
    if(!_appRunningSet.has(appName) || polls++ > 60){ clearInterval(iv); return; }
    try {
      const d = await getJsonSilent("/remote/app-builder/app-log?app="+encodeURIComponent(appName));
      const log = document.getElementById("appLog_"+appName);
      if(log && d.log) log.textContent = d.log;
      if(log) log.scrollTop = log.scrollHeight;
      if(d.running === false){
        _appRunningSet.delete(appName);
        const btn = document.getElementById("runBtn_"+appName);
        if(btn){ btn.textContent="▶ Run"; btn.style.background="#22c55e"; btn.disabled=false; }
        if(log) log.textContent += "\n[διακόπηκε]";
        clearInterval(iv);
      }
    } catch(e){ clearInterval(iv); }
  }, 2000);
}

// ── File Viewer Modal ─────────────────────────────────────────────────────────
async function appViewFile(appName, fileName){
  // Create/reuse modal
  let modal = document.getElementById("appFileModal");
  if(!modal){
    modal = document.createElement("div");
    modal.id = "appFileModal";
    modal.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.82);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px;";
    modal.onclick = e=>{ if(e.target===modal) modal.remove(); };
    document.body.appendChild(modal);
  }
  modal.innerHTML = `<div style="background:#0d1117;border:1px solid var(--line);border-radius:14px;max-width:860px;width:100%;max-height:88vh;display:flex;flex-direction:column;">
    <div style="padding:12px 16px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;">
      <span style="font-family:monospace;font-size:13px;color:#22d3ee;font-weight:700;">📄 ${escHtml(appName)}/${escHtml(fileName)}</span>
      <button onclick="document.getElementById('appFileModal').remove()"
        style="margin-left:auto;padding:4px 12px;border-radius:6px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);cursor:pointer;font-size:13px;">✕ Κλείσιμο</button>
    </div>
    <div style="padding:12px;color:var(--muted);font-size:13px;">⏳ Φόρτωση…</div>
  </div>`;
  modal.style.display = "flex";

  try {
    const d = await getJson(`/remote/app-builder/read-file?app=${encodeURIComponent(appName)}&file=${encodeURIComponent(fileName)}`);
    const inner = modal.querySelector("div");
    const isCode = /\.(py|js|ts|html|css|json|yml|yaml|sh|txt|md|toml|ini|cfg|env)$/i.test(fileName);
    inner.innerHTML = `
      <div style="padding:12px 16px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;">
        <span style="font-family:monospace;font-size:13px;color:#22d3ee;font-weight:700;">📄 ${escHtml(appName)}/${escHtml(fileName)}</span>
        <button onclick="document.getElementById('appFileModal').remove()"
          style="margin-left:auto;padding:4px 12px;border-radius:6px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);cursor:pointer;font-size:13px;">✕ Κλείσιμο</button>
      </div>
      <pre style="margin:0;padding:16px;overflow:auto;font-size:12px;color:#e2e8f0;white-space:pre-wrap;line-height:1.6;flex:1;background:#0d1117;border-radius:0 0 14px 14px;">${escHtml(d.content||"(άδειο)")}</pre>`;
  } catch(e){
    modal.querySelector("div").innerHTML += `<div style="padding:12px;color:var(--bad);">⚠️ ${escHtml(String(e))}</div>`;
  }
}

// Load app builder list when section opens
document.addEventListener("click", function(e){
  if(e.target && e.target.textContent && e.target.textContent.includes("App Builder")){
    setTimeout(()=>{ loadAppBuilderList(); loadAppFiles(); }, 100);
  }
});

// ══════════════════════════════════════════════════════════════
// ΠΕΔΙΟ & ΧΑΡΤΗΣ — Field Diary / Image Analysis / Map
// ══════════════════════════════════════════════════════════════

// ── Tab switching ──
function fieldTab(tab){
  ["img","diary","map","signs"].forEach(t=>{
    const el = document.getElementById("field-tab-"+t);
    const btn = document.getElementById("ftab-"+t);
    if(!el||!btn) return;
    const active = t===tab;
    el.style.display = active ? "block" : "none";
    if(active){
      btn.style.borderColor="rgba(34,211,238,.5)";
      btn.style.background="rgba(34,211,238,.15)";
      btn.style.color="#22d3ee";
    } else {
      btn.style.borderColor="var(--line)";
      btn.style.background="var(--panel2)";
      btn.style.color="var(--muted)";
    }
  });
  if(tab==="map") setTimeout(fieldInitMap, 100);
  if(tab==="diary") fieldDiaryLoad();
  if(tab==="img") fieldDiaryLoadRecent();
  if(tab==="signs") signsSearch("");
}

// ── Image Analysis ──
let _fieldImgB64 = null;
let _fieldImgMime = "image/jpeg";
let _fieldLastAnalysis = "";

function fieldPreviewImage(input){
  const file = input.files[0];
  if(!file) return;
  _fieldImgMime = file.type || "image/jpeg";
  const reader = new FileReader();
  reader.onload = e => {
    _fieldImgB64 = e.target.result.split(",")[1];
    document.getElementById("fieldImgTag").src = e.target.result;
    document.getElementById("fieldImgPreview").style.display = "block";
    document.getElementById("fieldAnalysisResult").style.display = "none";
    document.getElementById("fieldSaveToDiary").style.display = "none";
    document.getElementById("fieldAnalysisStatus").textContent = "✅ Εικόνα φορτώθηκε — πάτα «Ανάλυση AI»";
  };
  reader.readAsDataURL(file);
}

function fieldDropImage(e){
  e.preventDefault();
  document.getElementById("fieldDropZone").style.borderColor="";
  const file = e.dataTransfer.files[0];
  if(!file || !file.type.startsWith("image/")) return;
  const dt = new DataTransfer();
  dt.items.add(file);
  const inp = document.getElementById("fieldImgInput");
  inp.files = dt.files;
  fieldPreviewImage(inp);
}

async function fieldAnalyzeImage(){
  if(!_fieldImgB64){
    alert("Ανέβασε πρώτα μια εικόνα.");
    return;
  }
  const analysisType = document.getElementById("fieldAnalysisType").value;
  const extraCtx = document.getElementById("fieldImgExtraCtx").value.trim();
  const status = document.getElementById("fieldAnalysisStatus");
  const result = document.getElementById("fieldAnalysisResult");
  const saveDiv = document.getElementById("fieldSaveToDiary");

  status.textContent = "⏳ Ο ΝΟΥΣ αναλύει την εικόνα…";
  result.style.display = "none";
  saveDiv.style.display = "none";

  try {
    const r = await fetch("/field/analyze-image", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        image_b64: _fieldImgB64,
        mime: _fieldImgMime,
        analysis_type: analysisType,
        context: extraCtx
      })
    });
    const d = await r.json();
    if(d.ok && d.analysis){
      _fieldLastAnalysis = d.analysis;
      result.innerHTML = "<div style='white-space:pre-wrap;'>"+escHtml(d.analysis)+"</div>"
        + "<div style='margin-top:8px;font-size:11px;color:var(--muted);'>🤖 "+escHtml(d.model||"")+"</div>";
      result.style.display = "block";
      status.textContent = "✅ Ανάλυση ολοκληρώθηκε";
      saveDiv.style.display = "block";
    } else {
      status.textContent = "⚠️ " + (d.error||"Σφάλμα ανάλυσης");
    }
  } catch(e){
    status.textContent = "⚠️ " + e;
  }
}

async function fieldSaveAnalysis(){
  const title = document.getElementById("fieldSaveTitle").value.trim();
  if(!title){ alert("Δώσε τίτλο για την καταχώρηση."); return; }
  const lat = parseFloat(document.getElementById("fieldSaveLat").value)||null;
  const lon = parseFloat(document.getElementById("fieldSaveLon").value)||null;
  const atype = document.getElementById("fieldAnalysisType").value;
  const typeMap = {signs:"sign",terrain:"terrain",map:"note",rock:"sign",artifact:"find",general:"note"};
  const msg = document.getElementById("fieldSaveMsg");
  try {
    const r = await fetch("/field/add",{
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({
        title, note: _fieldLastAnalysis.substring(0,1000),
        lat, lon, entry_type: typeMap[atype]||"note",
        analysis: _fieldLastAnalysis, tags:["image_analysis"]
      })
    });
    const d = await r.json();
    if(d.ok){ msg.textContent="✅ Αποθηκεύτηκε στο ημερολόγιο!"; msg.style.display="block"; }
  } catch(e){ msg.textContent="⚠️ "+e; msg.style.display="block"; }
  setTimeout(()=>{ msg.style.display="none"; }, 3000);
}

function escHtml(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

async function fieldDiaryLoadRecent(){
  const el = document.getElementById("fieldRecentAnalyses");
  if(!el) return;
  try {
    const d = await getJson("/field/list?limit=5&type=sign");
    const items = (d.entries||[]).concat(await getJson("/field/list?limit=3&type=find").then(x=>x.entries||[]));
    if(!items.length){ el.textContent="Δεν υπάρχουν καταχωρήσεις ακόμα."; return; }
    el.innerHTML = items.slice(0,5).map(e=>`
      <div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);">
        <span style="font-size:18px;">${diaryTypeIcon(e.type)}</span>
        <div>
          <div style="font-weight:600;font-size:13px;">${escHtml(e.title)}</div>
          <div style="font-size:12px;color:var(--muted);">${(e.note||"").substring(0,80)}…</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px;">${e.timestamp.substring(0,10)}</div>
        </div>
      </div>`).join("");
  } catch(e){ el.textContent="—"; }
}

// ── Field Diary ──
function diaryTypeIcon(t){
  return {sign:"🔣",cache:"📦",frp:"📍",irp:"🗺️",terrain:"🏔️",anomaly:"⚡",find:"✨",note:"📝"}[t]||"📝";
}

async function fieldDiaryLoad(){
  const el = document.getElementById("diaryList");
  if(!el) return;
  el.innerHTML = "<div style='color:var(--muted);font-size:13px;'>⏳ Φόρτωση…</div>";
  const ft = document.getElementById("diaryFilterType");
  const typeQ = ft ? ft.value : "";
  try {
    const url = "/field/list?limit=80" + (typeQ ? "&type="+typeQ : "");
    const d = await getJson(url);
    const entries = d.entries||[];
    if(!entries.length){ el.innerHTML="<div style='color:var(--muted);font-size:13px;padding:12px 0;'>Δεν υπάρχουν καταχωρήσεις ακόμα.</div>"; return; }
    el.innerHTML = entries.map(e=>`
      <div style="background:var(--panel2);border-radius:10px;padding:10px 12px;margin-bottom:8px;border:1px solid var(--line);">
        <div style="display:flex;align-items:flex-start;gap:8px;">
          <span style="font-size:20px;flex-shrink:0;">${diaryTypeIcon(e.type)}</span>
          <div style="flex:1;min-width:0;">
            <div style="font-weight:700;font-size:13px;">${escHtml(e.title)}</div>
            ${e.note ? `<div style="font-size:12px;color:var(--muted);margin-top:2px;white-space:pre-wrap;">${escHtml(e.note.substring(0,200))}${e.note.length>200?"…":""}</div>` : ""}
            <div style="display:flex;gap:12px;margin-top:4px;flex-wrap:wrap;">
              ${e.lat!==null ? `<span style="font-size:11px;color:#22d3ee;">📍 ${e.lat.toFixed(5)}, ${e.lon.toFixed(5)}</span>` : ""}
              ${(e.tags||[]).map(t=>`<span class="pill">${escHtml(t)}</span>`).join("")}
              <span style="font-size:11px;color:var(--muted);">${e.timestamp.substring(0,16).replace("T"," ")}</span>
            </div>
          </div>
          <button onclick="fieldDiaryDelete('${e.id}')" style="padding:3px 8px;border-radius:6px;border:1px solid rgba(239,68,68,.3);background:rgba(239,68,68,.07);color:#ef4444;font-size:11px;cursor:pointer;flex-shrink:0;">✕</button>
        </div>
      </div>`).join("");
  } catch(e){ el.innerHTML="<div style='color:var(--bad);'>⚠️ "+escHtml(String(e))+"</div>"; }
}

async function fieldDiaryAdd(){
  const title = document.getElementById("diaryTitle").value.trim();
  if(!title){ alert("Δώσε τίτλο."); return; }
  const note  = document.getElementById("diaryNote").value.trim();
  const type  = document.getElementById("diaryType").value;
  const lat   = parseFloat(document.getElementById("diaryLat").value)||null;
  const lon   = parseFloat(document.getElementById("diaryLon").value)||null;
  const tags  = document.getElementById("diaryTags").value.split(",").map(s=>s.trim()).filter(Boolean);
  const msg   = document.getElementById("diaryAddMsg");
  try {
    const r = await fetch("/field/add",{
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({title, note, lat, lon, entry_type:type, tags})
    });
    const d = await r.json();
    if(d.ok){
      msg.textContent="✅ Αποθηκεύτηκε!"; msg.style.display="block";
      document.getElementById("diaryTitle").value="";
      document.getElementById("diaryNote").value="";
      document.getElementById("diaryTags").value="";
      fieldDiaryLoad();
      fieldMarkersLoad();
      setTimeout(()=>msg.style.display="none",2500);
    }
  } catch(e){ msg.textContent="⚠️ "+e; msg.style.display="block"; }
}

async function fieldDiaryDelete(id){
  if(!confirm("Διαγραφή καταχώρησης;")) return;
  await fetch("/field/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id})});
  fieldDiaryLoad();
  fieldMarkersLoad();
}

function fieldGetGPS(){
  if(!navigator.geolocation){ alert("GPS δεν υποστηρίζεται."); return; }
  navigator.geolocation.getCurrentPosition(pos=>{
    document.getElementById("diaryLat").value = pos.coords.latitude.toFixed(6);
    document.getElementById("diaryLon").value = pos.coords.longitude.toFixed(6);
  }, err=>alert("GPS σφάλμα: "+err.message));
}

// ── Leaflet Map ──
let _fieldMap = null;
let _fieldMarkers = [];

async function fieldMarkersLoad(){
  try {
    const d = await getJson("/field/markers");
    _fieldMarkers = d.markers||[];
    const el = document.getElementById("fieldMapSummary");
    if(el){
      const counts = {};
      _fieldMarkers.forEach(m=>{ counts[m.type]=(counts[m.type]||0)+1; });
      el.innerHTML = Object.entries(counts).map(([t,c])=>`<span class="pill">${diaryTypeIcon(t)} ${t}: <b>${c}</b></span>`).join(" ")
        + `<span class="pill" style="color:#22d3ee;">Σύνολο: <b>${_fieldMarkers.length}</b></span>`;
    }
    if(_fieldMap) _refreshMapMarkers();
  } catch(e){ console.error(e); }
}

function fieldInitMap(){
  if(_fieldMap) return;
  const el = document.getElementById("fieldMap");
  if(!el) return;
  // Load Leaflet CSS + JS dynamically
  if(!document.getElementById("leaflet-css")){
    const lnk = document.createElement("link");
    lnk.id="leaflet-css"; lnk.rel="stylesheet";
    lnk.href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(lnk);
  }
  if(!window.L){
    const sc = document.createElement("script");
    sc.src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    sc.onload = ()=>_buildMap();
    document.head.appendChild(sc);
  } else {
    _buildMap();
  }
}

function _buildMap(){
  const el = document.getElementById("fieldMap");
  if(!el||_fieldMap) return;
  // Center on Messenia, Greece
  _fieldMap = L.map("fieldMap").setView([37.05, 22.10], 10);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
    maxZoom:18,
    attribution:'© <a href="https://www.openstreetmap.org/copyright">OSM</a>'
  }).addTo(_fieldMap);
  _fieldMap.on("click", e=>{
    // Auto-fill lat/lon in diary form
    document.getElementById("diaryLat").value = e.latlng.lat.toFixed(6);
    document.getElementById("diaryLon").value = e.latlng.lng.toFixed(6);
  });
  _refreshMapMarkers();
}

function _refreshMapMarkers(){
  if(!_fieldMap) return;
  _fieldMap.eachLayer(l=>{ if(l instanceof L.Marker) _fieldMap.removeLayer(l); });
  const colorMap = {
    sign:"#22d3ee",cache:"#fbbf24",frp:"#a78bfa",irp:"#60a5fa",
    terrain:"#86efac",anomaly:"#f87171",find:"#fde68a",note:"#94a3b8"
  };
  _fieldMarkers.forEach(m=>{
    const color = colorMap[m.type]||"#94a3b8";
    const icon = L.divIcon({
      className:"",
      html:`<div style="background:${color};border-radius:50%;width:14px;height:14px;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;font-size:9px;">${m.icon}</div>`,
      iconSize:[18,18], iconAnchor:[9,9]
    });
    L.marker([m.lat,m.lon],{icon})
      .bindPopup(`<b>${escHtml(m.icon)} ${escHtml(m.title)}</b><br/><small style="color:#888;">${m.ts}</small>${m.note?`<br/><small>${escHtml(m.note)}</small>`:""}`)
      .addTo(_fieldMap);
  });
}

</script>

</body>
</html>'''
