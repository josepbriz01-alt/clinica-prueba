import sys, re
src='/home/claude/clinica/clinica.html'; out='/home/claude/web/index.html'
s=open(src,encoding='utf-8').read()
def rep(a,b,c=1):
    global s
    n=s.count(a)
    if n!=c: print("COUNT",n,repr(a[:100])); sys.exit(1)
    s=s.replace(a,b)
# 1) inicio de sesión
rep('''<div id="seed-ov" class="seedov" hidden><div class="card">''','''<div id="login-ov" class="seedov" hidden><form class="card" id="login-form">
  <h2>Clínica · Entrar</h2>
  <p class="hint">Entra con el usuario que te ha dado quien administra el sistema: un nombre (p. ej. <b>recepcion</b>) o tu correo.</p>
  <div class="field"><label class="lbl" for="login-email">Usuario o correo</label><input type="text" id="login-email" autocomplete="username" autocapitalize="none" spellcheck="false" required></div>
  <div class="field" style="margin-top:10px"><label class="lbl" for="login-pass">Contraseña</label><input type="password" id="login-pass" autocomplete="current-password" required></div>
  <p class="hint" id="login-err" style="color:var(--danger);min-height:1.2em"></p>
  <div class="row" style="justify-content:space-between"><button class="link" type="button" id="login-forgot">He olvidado la contraseña</button><button class="btn primary" type="submit">Entrar</button></div>
</form></div>
<div id="seed-ov" class="seedov" hidden><div class="card">''')
rep('''    <a href="#copia" data-v="copia" data-z="adm">Copia de seguridad <span class="n warn" id="n-bk"></span></a>
  </nav>''','''    <a href="#copia" data-v="copia" data-z="adm">Copia de seguridad <span class="n warn" id="n-bk"></span></a>
    <div class="who-am" id="who-am" hidden><span id="who-email"></span><button class="link" id="logout" type="button">Salir</button></div>
  </nav>''')
rep('[hidden]{display:none!important}','''[hidden]{display:none!important}
#login-ov{background:var(--bg)} #login-form{max-width:400px;display:flex;flex-direction:column;gap:4px}
.who-am{font-size:.75rem;color:var(--nav-muted,#9aa);padding:14px 16px 10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:auto}
.who-am .link{color:var(--nav-fg,#fff);font-size:.75rem}''')
# 2) Firebase
rep('''<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>''','''<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<script src="config.js"></script>''')
# 3) descargas del navegador
a=s.index('const DL = {async save(o){'); b=s.index('\n',a)
s=s[:a]+'''const DL = {async save({filename, data}){ const blob = data instanceof Blob ? data : new Blob([data], {type: "text/plain;charset=utf-8"}); const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = filename; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 2000); }};'''+s[b:]
rep('''const dl = window.claude ? await claude.use("downloads").catch(() => null) : null;''','''const dl = DL;''',2)
# 4) errores de Firebase
rep('''    toast(c === "invalid_argument" ? "No tienes permiso para hacer cambios aquí." :
          c === "quota_exceeded" ? "La base de datos está llena. Avisa a quien la administra." :''','''    toast(c === "invalid_argument" || c === "permission-denied" ? "No tienes permiso para hacer cambios aquí." :
          c === "quota_exceeded" || c === "resource-exhausted" ? "Se ha llegado al límite de uso de la base de datos por hoy. Avisa a quien la administra." :''')
rep('''Sin conexión con la base de datos compartida. Ábrelo desde claude.ai con tu cuenta.''','''Sin conexión con la base de datos. Comprueba internet y recarga la página.''')
# 5) arranque: iniciar sesión y conectar con Firestore
a=s.index('''(async () => {
  db = window.claude ? await claude.use("db").catch(() => null) : null;''')
b=s.index('''  if (!db) $("#offline").hidden = false;''',a)
s=s[:a]+'''/* ===== arranque con Firebase: primero iniciar sesión ===== */
function fbAdapter(fs){
  /* la aplicación usa «update» como mezcla profunda (y que cree el documento si no existe): en Firestore eso es set(..., {merge:true}) */
  const wrapDoc = r => ({id: r.id, get: () => r.get(), set: (d, o) => r.set(d, o), update: d => r.set(d, {merge: true}), delete: () => r.delete(), onSnapshot: (a, b) => r.onSnapshot(a, b)});
  return {doc: p => wrapDoc(fs.doc(p)), collection: c => fs.collection(c)};
}
/* usuario sin @ → usuario@clinica.local (usuarios de puesto, sin correo real); con @ → el correo tal cual */
const LOGIN_DOM = "clinica.local";
const loginEmail = t => { t = String(t || "").trim().toLowerCase(); return t.includes("@") ? t : t.normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").replace(/\\s+/g, "") + "@" + LOGIN_DOM; };
const isPuesto = em => String(em || "").toLowerCase().endsWith("@" + LOGIN_DOM);
function fbInit(){
  const cfg = window.FIREBASE_CONFIG;
  if (!window.firebase || !cfg || !cfg.apiKey || String(cfg.apiKey).includes("PEGA")){
    $("#offline").hidden = false; $("#offline .wrap").textContent = "Falta configurar Firebase: pega los datos de tu proyecto en el archivo config.js (paso 6 de la guía). Mientras, se ven datos de prueba solo en este ordenador.";
    startApp(null); return;
  }
  firebase.initializeApp(cfg);
  const fs = firebase.firestore();
  try { fs.settings({ignoreUndefinedProperties: true, merge: true}); } catch {}
  let started = false;
  firebase.auth().onAuthStateChanged(u => {
    if (!u){ if (started){ location.reload(); return; } $("#login-ov").hidden = false; setTimeout(() => $("#login-email").focus(), 50); return; }
    $("#login-ov").hidden = true; $("#who-am").hidden = false; $("#who-email").textContent = isPuesto(u.email) ? u.email.split("@")[0] : u.email;
    $("#logout").hidden = isPuesto(u.email);   /* los ordenadores de puesto no cierran sesión: la contraseña solo la sabe quien administra */
    if (!started){ started = true; startApp(fbAdapter(fs)); }
  });
}
$("#login-form").addEventListener("submit", async ev => {
  ev.preventDefault(); $("#login-err").textContent = "";
  try { await firebase.auth().signInWithEmailAndPassword(loginEmail($("#login-email").value), $("#login-pass").value); }
  catch (e){ const c = String((e && e.code) || ""); $("#login-err").textContent = /password|credential|user-not-found|invalid-email/.test(c) ? "Usuario o contraseña incorrectos." : /too-many/.test(c) ? "Demasiados intentos. Espera un momento." : /disabled/.test(c) ? "Este usuario está desactivado." : "No se pudo entrar. Comprueba la conexión."; }
});
$("#login-forgot").addEventListener("click", async () => {
  const raw = $("#login-email").value.trim(); if (!raw){ $("#login-err").textContent = "Escribe tu correo y vuelve a pulsar."; $("#login-email").focus(); return; }
  if (!raw.includes("@")){ $("#login-err").textContent = "Los usuarios de puesto no tienen correo: pide a quien administra que te cambie la contraseña."; return; }
  const em = raw;
  try { await firebase.auth().sendPasswordResetEmail(em); $("#login-err").textContent = "Si el correo existe, te llegará un enlace para cambiar la contraseña."; }
  catch { $("#login-err").textContent = "No se pudo enviar. Revisa el correo."; }
});
$("#logout").addEventListener("click", () => firebase.auth().signOut());
fbInit();
async function startApp(fdb){
  db = fdb;
'''+s[b:]
# cerrar la función async en vez de la IIFE
rep('''  subVisits(); subAgendaToday(); subAgendaView(); subHorario(); subNoShow(); subCatalogo();
  checkSeed();
})();''','''  subVisits(); subAgendaToday(); subAgendaView(); subHorario(); subNoShow(); subCatalogo();
  checkSeed();
}''')
assert 'claude.use' not in s, "queda claude.use"
open(out,'w',encoding='utf-8').write(s); print("ok", len(s))
exec(open('/home/claude/tools/web_post.py',encoding='utf-8').read())
