(function(){
  const store = new Map(), subs = new Set(); let user = null; const authCbs = [];
  const clone = x => JSON.parse(JSON.stringify(x));
  const merge = (a, b) => { const o = {...a}; for (const k in b){ const v = b[k]; o[k] = v && typeof v === "object" && !Array.isArray(v) && o[k] && typeof o[k] === "object" && !Array.isArray(o[k]) ? merge(o[k], v) : v; } return o; };
  const fire = () => setTimeout(() => subs.forEach(s => s()), 0);
  const snapDoc = (path) => ({exists: store.has(path), id: path.split("/").pop(), data: () => clone(store.get(path))});
  function docRef(path){ return {id: path.split("/").pop(),
    async get(){ return snapDoc(path); },
    async set(d, o){ store.set(path, o && o.merge ? merge(store.get(path) || {}, clone(d)) : clone(d)); window.__writes = (window.__writes||0)+1; fire(); },
    async delete(){ store.delete(path); fire(); },
    async update(d){ if (!store.has(path)){ const e = new Error("nf"); e.code = "invalid_argument"; throw e; } store.set(path, merge(store.get(path), clone(d))); fire(); },
    onSnapshot(cb){ const s = () => cb(snapDoc(path)); subs.add(s); s(); return () => subs.delete(s); } }; }
  function query(col, filters, lim){
    const run = () => { let docs = [...store.keys()].filter(k => k.startsWith(col + "/") && k.split("/").length === 2).map(k => ({id: k.split("/")[1], v: store.get(k)}));
      filters.forEach(([f, op, val]) => { docs = docs.filter(d => { const x = d.v[f]; return op === "==" ? x === val : op === "in" ? val.includes(x) : op === ">=" ? x >= val : op === "<=" ? x <= val : true; }); });
      if (lim) docs = docs.slice(0, lim);
      return {empty: !docs.length, docs: docs.map(d => ({id: d.id, data: () => clone(d.v)}))}; };
    return { where: (f, op, v) => query(col, [...filters, [f, op, v]], lim), limit: n => query(col, filters, n),
      async get(){ return run(); }, onSnapshot(cb){ const s = () => cb(run()); subs.add(s); s(); return () => subs.delete(s); },
      doc: id => docRef(col + "/" + (id || Math.random().toString(36).slice(2))),
      async add(d){ const id = Math.random().toString(36).slice(2); await docRef(col + "/" + id).set(d); return {id}; } };
  }
  const fs = {collection: c => query(c, []), doc: p => docRef(p), enablePersistence: async () => {}, settings(){},
    batch(){ const ops = []; return {set(ref, d){ ops.push([ref, d]); }, async commit(){ if (window.__failBatch && --window.__failBatch === 0){ const e = new Error("quota"); e.code = "resource-exhausted"; throw e; } for (const [r, d] of ops) await r.set(d); window.__batches = (window.__batches||0)+1; }}; }};
  window.firebase = {initializeApp(){}, firestore: () => fs,
    auth: () => ({onAuthStateChanged(cb){ authCbs.push(cb); setTimeout(() => cb(user), 10); },
      async signInWithEmailAndPassword(e, p){ if (p !== "secreta"){ const er = new Error("bad"); er.code = "auth/wrong-password"; throw er; } user = {email: e}; authCbs.forEach(cb => cb(user)); },
      async signOut(){ user = null; authCbs.forEach(cb => cb(null)); }})};
  window.__store = store;
})();
