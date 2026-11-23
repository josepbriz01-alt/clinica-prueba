# segunda pasada de la versión web: aviso de versión nueva (no gasta nada de Firebase: mira version.txt en GitHub)
import sys, time
out='/home/claude/web/index.html'
s=open(out,encoding='utf-8').read()
def rep(a,b,c=1):
    global s
    n=s.count(a)
    if n!=c: print("COUNT",n,repr(a[:100])); sys.exit(1)
    s=s.replace(a,b)
VER=time.strftime("%Y%m%d%H%M%S")
rep('<div id="login-ov" class="seedov" hidden>','<div id="newver" class="newver" hidden role="status"><span>🔄 Hay una versión nueva de la aplicación.</span><button type="button" class="btn sm primary" id="newver-go">Recargar</button><button type="button" class="link" id="newver-later">Más tarde</button></div>\n<div id="login-ov" class="seedov" hidden>')
rep('[hidden]{display:none!important}','[hidden]{display:none!important}\n.newver{position:fixed;left:50%;transform:translateX(-50%);bottom:18px;z-index:60;display:flex;gap:12px;align-items:center;background:var(--nav);color:var(--nav-fg);border-radius:12px;padding:10px 14px;box-shadow:0 6px 24px rgb(0 0 0/.25);font-weight:600}\n.newver .link{color:var(--nav-muted)}')
JS='''
/* ===== versión nueva: se mira version.txt cada 5 min; se recarga al pulsar o sola de madrugada si no hay nada a medio hacer ===== */
const APP_VERSION = "__VER__";
let newVer = null, newVerLater = 0;
function unsaved(){
  if (document.querySelector("dialog[open]")) return "Hay una ventana abierta: termínala o ciérrala antes de recargar.";
  const ae = document.activeElement; if (ae && ae.matches && ae.matches("input,textarea,select") && !ae.closest("#login-ov")) return "Estás escribiendo en un campo: termina y guárdalo antes de recargar.";
  if ([...document.querySelectorAll("textarea")].some(t => t.value.trim() && t.offsetParent)) return "Hay un texto escrito sin guardar en esta pantalla: guárdalo antes de recargar.";
  if (typeof seeding !== "undefined" && seeding) return "Se están escribiendo datos: espera a que termine.";
  return "";
}
async function checkVersion(){
  try { const r = await fetch("version.txt?t=" + Date.now(), {cache: "no-store"}); if (r.ok){ const v = (await r.text()).trim(); if (v && v !== APP_VERSION){ newVer = v; if (Date.now() > newVerLater) $("#newver").hidden = false; } } } catch {}
  const h = new Date().getHours();
  if (newVer && h >= 2 && h < 5 && !unsaved()) location.reload();   /* de madrugada, si no hay nada abierto */
}
$("#newver-go").addEventListener("click", () => { const why = unsaved(); if (why){ toast(why); return; } location.reload(); });
$("#newver-later").addEventListener("click", () => { $("#newver").hidden = true; newVerLater = Date.now() + 30 * 60000; });
setInterval(checkVersion, 5 * 60000); setTimeout(checkVersion, 20000);
'''.replace("__VER__", VER)
rep('$("#logout").addEventListener("click", () => firebase.auth().signOut());','$("#logout").addEventListener("click", () => firebase.auth().signOut());'+JS)
# espacio: en Firebase no hay límite de 25.000 registros (eso es de Claude); el límite gratuito es 1 GB de datos
rep('const dbPct = () => dbUse ? Math.round(dbUse.n / DB_MAX * 100) : null;', 'const DB_GB = 1073741824, fmtMB = b => b >= 1048576 ? (b / 1048576).toFixed(1).replace(".", ",") + " MB" : Math.max(1, Math.round(b / 1024)) + " KB";\nconst dbPct = () => dbUse && dbUse.bytes ? dbUse.bytes / DB_GB * 100 : null;   /* en Firebase el límite gratuito es 1 GB de datos (no hay tope de registros) */')
# al contar, también se estima cuánto ocupa (datos + índices, aproximado) y se guarda para que lo vean todos los ordenadores
rep('  for (const c of DB_COLS){ try { by[c] = db ? (await db.collection(c).get()).docs.length : memCol(c).size; } catch { by[c] = 0; } }\n  dbUse = {n: Object.values(by).reduce((a, b) => a + b, 0), by, fecha: new Date().toISOString()};',
    '  let bytes = 0;\n  for (const c of DB_COLS){ try { const docs = db ? (await db.collection(c).get()).docs : []; by[c] = docs.length; docs.forEach(d => { bytes += 2 * (JSON.stringify(d.data()).length + c.length + d.id.length + 48); }); } catch { by[c] = 0; } }\n  dbUse = {n: Object.values(by).reduce((a, b) => a + b, 0), by, bytes, fecha: new Date().toISOString()};\n  if (db) S.set("config", "espacio", dbUse).catch(() => {});')
rep('<div class="bar"><i style="width:${Math.min(100, pct)}%"></i></div><span>${pct} %</span></div>', '<div class="bar"><i style="width:${Math.max(1.5, Math.min(100, pct))}%"></i></div><span>${pct < 1 ? pct.toFixed(2).replace(".", ",") : Math.round(pct)} %</span></div>')
rep('${dbUse.n.toLocaleString("es-ES")} de ${DB_MAX.toLocaleString("es-ES")} registros', '≈ ${fmtMB(dbUse.bytes)} de 1 GB (estimado) · ${dbUse.n.toLocaleString("es-ES")} registros')
# al entrar en Copia de seguridad, se trae el último recuento guardado (lo haya hecho quien sea)
rep('function bkTopHtml(){', 'let espLoaded = false;\nfunction bkTopHtml(){\n  if (!espLoaded && db){ espLoaded = true; S.getDoc("config", "espacio").then(d => { if (d && d.bytes && (!dbUse || !dbUse.bytes || d.fecha > dbUse.fecha)){ dbUse = d; if (view === "copia") renderBackup(); } }).catch(() => {}); }')
rep('${pct === null ? `<span class="hint">Calculando…</span>` :', '${pct === null ? `<span class="hint">En esta web los datos están en <b>Firebase</b>: no hay límite de registros. El plan gratuito permite <b>1 GB</b> de datos, y con vuestro volumen estáis muy lejos (cada registro ocupa unos pocos KB). El uso real se ve en Firebase → Firestore → <b>Uso</b>.</span><span class="hint">${dbUse ? `Hay ${dbUse.n.toLocaleString("es-ES")} registros · citas ${(dbUse.by.agenda || 0).toLocaleString("es-ES")} · visitas ${(dbUse.by.visitas || 0).toLocaleString("es-ES")} · contado el ${esc(dm(dbUse.fecha.slice(0, 10)))} a las ${hm(dbUse.fecha)}. ` : ""}<button class="link" id="db-recount">${dbUse ? "Volver a calcular" : "Calcular el espacio usado"}</button> (lee toda la base: hazlo de vez en cuando, por ejemplo una vez al mes)</span>` :')
# en Firebase no hay límite de 25.000 documentos (eso es de Claude) y contar leyendo toda la base cuesta lecturas: no se cuenta solo
rep('setTimeout(() => countDb(false), 20000);','/* (en la web no se cuenta la base sola: cada recuento lee todos los documentos) */')
rep('if (!dbUse && !dbCounting) countDb(false);','/* recuento solo con el botón */')
exec(open('/home/claude/tools/web_import.py',encoding='utf-8').read())
exec(open('/home/claude/tools/web_admin.py',encoding='utf-8').read())
if not s.lstrip().lower().startswith('<!doctype'): s = '<!DOCTYPE html>\n<html lang="es">\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + s
open(out,'w',encoding='utf-8').write(s)
open('/home/claude/web/version.txt','w').write(VER+"\n")
print("post ok", VER)
