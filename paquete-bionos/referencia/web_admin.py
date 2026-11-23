# cuarta pasada de la versión web: administradores
# - quién es administrador: colección «admins» de Firestore, un documento por persona con su correo como ID (se añade desde la consola de Firebase)
# - solo administradores: calendarizar (crear ensayos, fechas, visitas, circuitos, publicar/quitar, catálogo de medidas) y poner/quitar empleados
# - los demás ven Calendarización en modo solo lectura (calendario y saturación) y la lista de empleados sin botones
# - las reglas de Firestore lo bloquean también en la base de datos (ver reglas-firestore.txt)
rep('<section id="v-calendarizacion" hidden>', '<section id="v-calendarizacion" hidden>\n        <p class="callout noadm-only" style="margin:0 0 12px">👁 <b>Solo lectura.</b> Puedes ver el calendario y la saturación de los box; para calendarizar ensayos hace falta ser administrador.</p>')
rep('[hidden]{display:none!important}', '''[hidden]{display:none!important}
.noadm-only{display:none} body.noadm .noadm-only{display:block}
body.noadm #cz-new, body.noadm #cz-cat, body.noadm [data-cz-edit], body.noadm [data-cz-pub], body.noadm [data-cz-unpub], body.noadm [data-cz-redate],
body.noadm #e-gocz, body.noadm #home-emp-form, body.noadm [data-empdel]{display:none!important}
.who-am .adm{background:var(--nav-fg,#fff);color:var(--nav,#123);border-radius:6px;padding:0 5px;font-weight:700;font-size:.65rem}''')
JS = r'''
/* ===== administradores (colección «admins» en Firestore: ID del documento = correo) ===== */
let IS_ADMIN = false, admUnsub = null;
const NOADM_MSG = "Solo los administradores pueden hacer esto.";
function setAdmin(v){
  IS_ADMIN = !!v; document.body.classList.toggle("noadm", !IS_ADMIN);
  const w = $("#who-email"); if (w){ const b = w.querySelector(".adm"); if (IS_ADMIN && !b) w.insertAdjacentHTML("beforeend", ' <span class="adm">ADMIN</span>'); if (!IS_ADMIN && b) b.remove(); }
  if (typeof view !== "undefined" && view === "calendarizacion" && typeof renderCalendarizacion === "function") renderCalendarizacion();
}
function watchAdmin(u){
  if (admUnsub){ admUnsub(); admUnsub = null; }
  setAdmin(false);   /* hasta saberlo, sin permisos */
  if (!u || isPuesto(u.email)) return;   /* los puestos nunca son administradores */
  admUnsub = firebase.firestore().collection("admins").doc(String(u.email).toLowerCase()).onSnapshot(d => setAdmin(d.exists), () => setAdmin(false));
}
document.body.classList.add("noadm");
/* lo que solo pueden hacer los administradores: se bloquea aunque se llegue por otro camino */
{ const _oef = openEnsForm; openEnsForm = function(id, mode){ if (!IS_ADMIN && (mode === "cal" || !id)){ toast(NOADM_MSG); return; } return _oef.apply(this, arguments); }; }
{ const _ocn = openCzNew; openCzNew = function(){ if (!IS_ADMIN){ toast(NOADM_MSG); return; } return _ocn.apply(this, arguments); }; }
{ const _oc = openCat; openCat = function(){ if (!IS_ADMIN){ toast(NOADM_MSG); return; } return _oc.apply(this, arguments); }; }
document.addEventListener("click", ev => {
  if (IS_ADMIN) return;
  const t = ev.target.closest && ev.target.closest("#cz-new, #cz-cat, [data-cz-edit], [data-cz-pub], [data-cz-unpub], [data-cz-redate], #e-gocz, [data-empdel]");
  if (t){ ev.preventDefault(); ev.stopImmediatePropagation(); toast(NOADM_MSG); }
}, true);
document.addEventListener("submit", ev => { if (!IS_ADMIN && ev.target.id === "home-emp-form"){ ev.preventDefault(); ev.stopImmediatePropagation(); toast(NOADM_MSG); } }, true);
'''
rep('$("#logout").addEventListener("click", () => firebase.auth().signOut());', '$("#logout").addEventListener("click", () => firebase.auth().signOut());' + JS)
# al iniciar sesión, mirar si es administrador
rep('''    $("#logout").hidden = isPuesto(u.email);''', '''    $("#logout").hidden = isPuesto(u.email);
    watchAdmin(u);''')
