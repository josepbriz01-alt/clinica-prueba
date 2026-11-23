const { chromium } = require('playwright'); const fs = require('fs');
async function page(b, demo){
  const p = await b.newPage({viewport:{width:1400,height:900}, acceptDownloads: true});
  p.errs = []; p.on('pageerror', e => p.errs.push('PAGEERR ' + e.message));
  const fake = fs.readFileSync(__dirname + '/fakedb.js', 'utf8'), fx = fs.readFileSync(__dirname + '/fakexlsx2.js', 'utf8');
  await p.route('**/*', r => { const u = r.request().url();
    if (u.includes('firebase-app-compat')) return r.fulfill({body: fake, contentType: 'text/javascript'});
    if (u.includes('gstatic.com')) return r.fulfill({body: '', contentType: 'text/javascript'});
    if (u.includes('xlsx')) return r.fulfill({body: fx, contentType: 'text/javascript'});
    if (u.includes('version.txt')) return r.fulfill({body: '29990101000000', contentType: 'text/plain'});
    if (u.endsWith('/config.js')) return r.fulfill({body: 'window.FIREBASE_CONFIG={apiKey:"test",projectId:"x"};' + (demo ? 'window.CLINICA_DEMO=true;' : ''), contentType: 'text/javascript'});
    if (u.startsWith('file://')) return r.continue();
    return r.abort(); });
  await p.clock.install({time: new Date('2026-11-17T10:30:00+01:00')});
  await p.goto('file://' + __dirname + '/web/index.html'); await p.clock.runFor(1500);
  await p.fill('#login-email', 'admin'); await p.fill('#login-pass', 'secreta'); await p.click('#login-form button[type=submit]'); await p.clock.runFor(2500);
  return p;
}
(async () => {
  const b = await chromium.launch();
  // 1) origen: web de prueba con datos de demostración → copia completa
  const a = await page(b, true);
  console.log('A seed ov visible', await a.evaluate(() => !$('#seed-ov').hidden), await a.evaluate(() => $('#seed-ov h2').textContent));
  await a.evaluate(() => $('#seed-go').click());
  for (let i = 0; i < 200; i++){ await a.clock.runFor(1000); if (await a.evaluate(() => $('#seed-ov').hidden)) break; }
  await a.clock.runFor(3000);
  console.log('A loaded', await a.evaluate(() => 'vols ' + vols.size + ' ens ' + ensayos.length + ' docs ' + window.__store.size));
  await a.evaluate(() => navTo('copia')); await a.clock.runFor(800);
  const [dl] = await Promise.all([a.waitForEvent('download'), (async () => { await a.evaluate(() => $('#full-dl').click()); for (let i = 0; i < 20; i++) await a.clock.runFor(500); })()]);
  const file = __dirname + '/copia_test.xlsx'; await dl.saveAs(file);
  const srcCounts = await a.evaluate(() => { const o = {}; for (const k of window.__store.keys()){ const c = k.split('/')[0]; o[c] = (o[c]||0)+1; } return o; });
  console.log('A file', dl.suggestedFilename(), fs.statSync(file).size, JSON.stringify(srcCounts));
  // 2) destino: web de la empresa vacía
  const p = await page(b, false);
  console.log('B seed ov', await p.evaluate(() => !$('#seed-ov').hidden), await p.evaluate(() => $('#seed-ov .card').textContent.slice(0, 80)));
  await p.click('#seed-imp'); await p.clock.runFor(800);
  console.log('B view', await p.evaluate(() => view), await p.evaluate(() => !!$('#imp-file')));
  await p.screenshot({path: 'shot_imp0.png'});
  await p.setInputFiles('#imp-file', file); for (let i = 0; i < 20; i++){ await p.clock.runFor(500); if (await p.evaluate(() => imp && imp.estado !== 'subiendo')) break; }
  console.log('B listo', await p.evaluate(() => imp && imp.estado + ' total ' + imp.total + ' ' + JSON.stringify(imp.cuentas)));
  await p.screenshot({path: 'shot_imp1.png'});
  // corte a mitad (límite) y continuar
  await p.evaluate(() => { window.__failBatch = 2; }); await p.click('#imp-go');
  for (let i = 0; i < 60; i++){ await p.clock.runFor(500); if (await p.evaluate(() => imp.estado !== 'subiendo')) break; }
  console.log('B corte', await p.evaluate(() => imp.estado + ' ' + imp.hecho + ' | ' + imp.msg));
  await p.setInputFiles('#imp-file', file); for (let i = 0; i < 20; i++){ await p.clock.runFor(500); if (await p.evaluate(() => imp && imp.estado === 'listo')) break; }
  console.log('B continuar', await p.evaluate(() => imp.estado + ' cont ' + imp.continuar));
  await p.click('#imp-go');
  for (let i = 0; i < 120; i++){ await p.clock.runFor(500); if (await p.evaluate(() => imp.estado !== 'subiendo')) break; }
  console.log('B hecho', await p.evaluate(() => imp.estado + ' ' + JSON.stringify(imp.verif)));
  await p.screenshot({path: 'shot_imp2.png'});
  const dstCounts = await p.evaluate(() => { const o = {}; for (const k of window.__store.keys()){ const c = k.split('/')[0]; o[c] = (o[c]||0)+1; } return o; });
  console.log('B store', JSON.stringify(dstCounts));
  // igualdad exacta de documentos (salvo config de control)
  const same = await (async () => { const A = await a.evaluate(() => JSON.stringify([...window.__store].filter(([k]) => !/^config\/(demo|limpieza|reset|espacio|importacion|copiaCompleta)/.test(k)).sort())); const B = await p.evaluate(() => JSON.stringify([...window.__store].filter(([k]) => !/^config\/(demo|limpieza|reset|espacio|importacion|copiaCompleta)/.test(k)).sort())); return A === B ? 'IGUAL' : 'DISTINTO ' + A.length + ' ' + B.length; })();
  console.log('B datos', same);
  // 3) segunda importación sobre base con datos → rechazo
  await p.evaluate(() => S.set('config', 'importacion', {estado: 'hecho'})); await p.clock.runFor(300);
  await p.evaluate(() => { imp = null; impRender(); });
  await p.evaluate(() => { const l = document.createElement('input'); l.type='file'; l.id='imp-file'; l.hidden=true; document.body.appendChild(l); });
  await p.setInputFiles('#imp-file', file); for (let i = 0; i < 20; i++){ await p.clock.runFor(500); if (await p.evaluate(() => imp)) break; }
  console.log('B rechazo', await p.evaluate(() => imp.estado + ' | ' + imp.msg));
  // recargar y ver la app con datos
  console.log('errores', a.errs.concat(p.errs).join('\n') || 'ninguno');
  await b.close();
})();
