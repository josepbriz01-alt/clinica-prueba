# tercera pasada de la versión web: pasar los datos desde la «copia completa» (Excel) a Firebase
# - en Copia de seguridad: «Pasar datos a esta web» (solo con la base vacía, o para continuar una importación cortada)
# - con la base vacía, el aviso de inicio ya no ofrece datos de demostración (salvo window.CLINICA_DEMO = true en config.js)
rep('''      <button class="btn primary" id="full-dl"${bkBusy ? " disabled" : ""}>Descargar copia completa</button></div></div>`;''',
'''      <button class="btn primary" id="full-dl"${bkBusy ? " disabled" : ""}>Descargar copia completa</button></div>
    <div class="col" style="gap:6px;min-width:260px" id="imp-box">${impHtml()}</div></div>`;''')

JS = r'''
/* ===== pasar los datos a esta web desde una «copia completa» (Excel con la hoja «Datos completos») ===== */
const IMP_COLS = ["vol", "ensayos", "medidas", "panel", "agenda", "visitas", "capacidad", "config"];
const IMP_SKIP_CFG = id => /^demo/.test(id) || ["limpieza", "reset", "espacio", "importacion"].includes(id);
let imp = null;   /* {raw, nombre, cuentas, total, estado: "listo"|"subiendo"|"hecho"|"error", hecho, msg, verif} */
const impN = n => Number(n || 0).toLocaleString("es-ES");
const impLbl = {vol: "Panelistas", ensayos: "Ensayos", medidas: "Medidas", panel: "Paneles", agenda: "Citas", visitas: "Visitas", capacidad: "Capacidad", config: "Configuración"};
function impHtml(){
  const head = `<h2>Pasar datos a esta web</h2>`;
  if (!imp) return head + `<span class="hint">Para traer los datos desde la aplicación de Claude: allí haz <b>Descargar copia completa</b> y elige aquí ese Excel. Solo funciona con esta base vacía. La aplicación de Claude no se toca.</span>
    <label class="btn" style="align-self:flex-start;cursor:pointer">Elegir la copia completa (Excel)<input type="file" id="imp-file" accept=".xlsx" hidden></label>`;
  if (imp.estado === "error") return head + `<span class="hint" style="color:var(--danger)">${esc(imp.msg)}</span>${imp.raw ? `<span class="hint">Se pasaron ${impN(imp.hecho)} de ${impN(imp.total)}. Puedes volver a elegir el mismo Excel para continuar.</span>` : ""}
    <label class="btn" style="align-self:flex-start;cursor:pointer">Elegir el Excel<input type="file" id="imp-file" accept=".xlsx" hidden></label>`;
  const tabla = `<table class="imp-t"><tr><th></th><th>En el Excel</th>${imp.verif ? "<th>En la web</th>" : ""}</tr>${IMP_COLS.map(c => { const a = imp.cuentas[c] || 0, b = imp.verif ? imp.verif[c] : null;
      return `<tr><td>${impLbl[c]}</td><td>${impN(a)}</td>${imp.verif ? `<td style="color:${b === a ? "var(--ok,#2a7)" : "var(--danger)"}">${impN(b)} ${b === a ? "✓" : "✗"}</td>` : ""}</tr>`; }).join("")}</table>`;
  if (imp.estado === "listo") return head + `<span class="hint">Archivo: <b>${esc(imp.nombre)}</b> · copia del ${esc(dm(String(imp.raw.copia || "").slice(0, 10)))}</span>${tabla}
    <span class="hint">Se escribirán ${impN(imp.total)} registros${imp.total > 18000 ? ` <b style="color:var(--warn)">(más de lo que permite el plan gratuito en un día: activa antes el plan de pago)</b>` : ""}. ${imp.continuar ? "<b>Continúa una importación que se cortó</b>: lo ya pasado se vuelve a escribir igual, no se duplica." : ""}</span>
    <div class="row" style="gap:8px"><button class="btn primary" id="imp-go">Pasar los datos ahora</button><button class="btn" id="imp-cancel">Cancelar</button></div>`;
  if (imp.estado === "subiendo") return head + `<span class="hint">Pasando datos… <b>${impN(imp.hecho)} de ${impN(imp.total)}</b>. No cierres esta página.</span><div class="seedbar"><i style="width:${Math.round(imp.hecho / imp.total * 100)}%"></i></div>`;
  const ok = imp.verif && IMP_COLS.every(c => imp.verif[c] === (imp.cuentas[c] || 0));
  return head + `<span class="hint">${ok ? "✅ <b>Datos pasados y comprobados.</b> Recarga la página en todos los ordenadores." : "⚠️ Terminado, pero algún número no coincide: revisa la tabla antes de usar la web."}</span>${tabla}
    <button class="btn primary" id="imp-reload" style="align-self:flex-start">Recargar la página</button>`;
}
const impRender = () => { const b = $("#imp-box"); if (b) b.innerHTML = impHtml(); };
/* Firestore no admite listas dentro de listas, campos vacíos ni nombres «__…__» */
function impBad(v, path){
  if (Array.isArray(v)){ for (let i = 0; i < v.length; i++){ if (Array.isArray(v[i])) return path + "[" + i + "] (lista dentro de lista)"; const r = impBad(v[i], path + "[" + i + "]"); if (r) return r; } return ""; }
  if (v && typeof v === "object"){ for (const k of Object.keys(v)){ if (!k) return path + " (campo sin nombre)"; if (/^__.*__$/.test(k)) return path + "." + k + " (nombre reservado)"; const r = impBad(v[k], path + "." + k); if (r) return r; } }
  return "";
}
async function impFile(f){
  imp = null; impRender();
  try {
    if (!window.XLSX) throw new Error("No se pudo cargar el lector de Excel. Recarga la página.");
    const wb = XLSX.read(await f.arrayBuffer(), {type: "array"}), sh = wb.Sheets["Datos completos"];
    if (!sh) throw new Error("Este Excel no tiene la hoja «Datos completos». Tiene que ser la «copia completa» de Copia de seguridad.");
    const rows = XLSX.utils.sheet_to_json(sh, {header: 1, raw: true, defval: ""});
    let raw; try { raw = JSON.parse(rows.slice(1).map(r => String(r[0] || "")).join("")); } catch { throw new Error("La hoja «Datos completos» está incompleta o dañada. Descarga otra copia completa."); }
    if (!raw || !Array.isArray(raw.vol) || !Array.isArray(raw.ensayos)) throw new Error("La copia no tiene el formato esperado.");
    const cuentas = {}; let total = 0;
    for (const c of IMP_COLS){ const l = (raw[c] || []).filter(d => d && d.id && !(c === "config" && IMP_SKIP_CFG(d.id))); raw[c] = l; cuentas[c] = l.length; total += l.length;
      for (const d of l){ if (String(d.id).includes("/")) throw new Error(`Hay un registro con un nombre no válido (${c}/${d.id}).`); const bad = impBad(d, c + "/" + d.id); if (bad) throw new Error("Firebase no admite este dato: " + bad + ". Pide al Claude del trabajo que lo revise."); } }
    /* ¿base vacía? (o importación anterior a medias) */
    const prev = await S.getDoc("config", "importacion").catch(() => null);
    const continuar = !!(prev && prev.estado === "subiendo");
    if (!continuar){ for (const c of ["vol", "ensayos", "agenda", "visitas"]){ const q = await db.collection(c).limit(1).get(); if (!q.empty) throw new Error("Esta web ya tiene datos: solo se puede pasar una copia a una base vacía (para no mezclar ni duplicar nada)."); } }
    imp = {raw, nombre: f.name, cuentas, total, estado: "listo", hecho: 0, continuar};
  } catch (e){ imp = {estado: "error", msg: e.message || String(e), hecho: 0, total: 0}; }
  impRender();
}
async function impGo(){
  if (!imp || imp.estado !== "listo") return;
  const fs = firebase.firestore(), raw = imp.raw;
  imp.estado = "subiendo"; seeding = true; impRender();
  try {
    await S.set("config", "importacion", {estado: "subiendo", desde: new Date().toISOString(), archivo: imp.nombre, total: imp.total});
    const all = []; for (const c of IMP_COLS) for (const d of raw[c]) all.push([c, d]);
    for (let i = 0; i < all.length; i += 400){
      const b = fs.batch();
      for (const [c, d] of all.slice(i, i + 400)){ const {id, ...rest} = d; b.set(fs.collection(c).doc(String(id)), rest); }
      await b.commit(); imp.hecho = Math.min(all.length, i + 400); impRender();
    }
    /* comprobar: contar lo que hay ahora en la web */
    const verif = {};
    for (const c of IMP_COLS){ const docs = (await db.collection(c).get()).docs; verif[c] = c === "config" ? docs.filter(d => !IMP_SKIP_CFG(d.id)).length : docs.length; }
    imp.verif = verif; imp.estado = "hecho";
    await S.set("config", "importacion", {estado: "hecho", fecha: new Date().toISOString(), archivo: imp.nombre, cuentas: imp.cuentas, total: imp.total});
  } catch (e){
    const c = String((e && e.code) || "");
    imp.estado = "error"; imp.msg = /exhausted|quota/.test(c) ? "Se ha llegado al límite de escrituras del plan gratuito por hoy. Activa el plan de pago o continúa mañana después de las 9:00 con el mismo Excel." : /permission/.test(c) ? "Firebase no deja escribir: revisa las reglas de Firestore (paso 3 de la guía)." : "Se cortó la conexión o hubo un error: " + (e.message || c);
  }
  seeding = false; impRender();
}
document.addEventListener("change", ev => { if (ev.target.id === "imp-file" && ev.target.files[0]) impFile(ev.target.files[0]); });
document.addEventListener("click", ev => {
  const id = ev.target.id;
  if (id === "imp-go") impGo();
  else if (id === "imp-cancel"){ imp = null; impRender(); }
  else if (id === "imp-reload") location.reload();
  else if (id === "seed-imp"){ $("#seed-ov").hidden = true; navTo("copia"); }
});
'''
rep('$("#logout").addEventListener("click", () => firebase.auth().signOut());', '$("#logout").addEventListener("click", () => firebase.auth().signOut());' + JS)
rep('[hidden]{display:none!important}', '[hidden]{display:none!important}\n.imp-t{border-collapse:collapse;font-size:.82rem}.imp-t td,.imp-t th{padding:2px 10px 2px 0;text-align:left}.imp-t td:not(:first-child),.imp-t th:not(:first-child){text-align:right}')
# base vacía en la web de la empresa: en vez de ofrecer datos inventados, se explica cómo pasar los datos reales
rep('''  if (ensayos.length || vols.size) return;
  const ov = $("#seed-ov"); ov.hidden = false;''', '''  if (ensayos.length || vols.size) return;
  const ov = $("#seed-ov"); ov.hidden = false;
  if (!window.CLINICA_DEMO){ ov.querySelector(".card").innerHTML = `<h2>Base de datos vacía</h2><p class="hint">Todavía no hay datos en esta web. Para traer los de la aplicación de Claude: allí, en <b>Copia de seguridad</b>, pulsa <b>Descargar copia completa</b>; aquí, en <b>Copia de seguridad → Pasar datos a esta web</b>, elige ese Excel.</p><div class="row" style="gap:8px"><button class="btn primary" id="seed-imp" type="button">Ir a pasar los datos</button><button class="btn" type="button" onclick="document.getElementById('seed-ov').hidden=true">Cerrar</button></div>`; return; }''')
