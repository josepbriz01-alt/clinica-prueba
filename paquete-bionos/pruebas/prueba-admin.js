const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1400,height:900}});
  const errs = []; p.on('pageerror', e => errs.push('PAGEERR ' + e.message));
  const fake = fs.readFileSync(__dirname + '/fakedb.js', 'utf8'), fx = fs.readFileSync(__dirname + '/fakexlsx2.js', 'utf8');
  await p.route('**/*', r => { const u = r.request().url();
    if (u.includes('firebase-app-compat')) return r.fulfill({body: fake, contentType: 'text/javascript'});
    if (u.includes('gstatic.com')) return r.fulfill({body: '', contentType: 'text/javascript'});
    if (u.includes('xlsx')) return r.fulfill({body: fx, contentType: 'text/javascript'});
    if (u.includes('version.txt')) return r.fulfill({body: '29990101000000', contentType: 'text/plain'});
    if (u.endsWith('/config.js')) return r.fulfill({body: 'window.FIREBASE_CONFIG={apiKey:"test",projectId:"x"};window.CLINICA_DEMO=true;', contentType: 'text/javascript'});
    if (u.startsWith('file://')) return r.continue();
    return r.abort(); });
  await p.clock.install({time: new Date('2026-11-17T10:30:00+01:00')});
  await p.goto('file://' + __dirname + '/web/index.html'); await p.clock.runFor(1500);
  await p.fill('#login-email', 'Ana@Bionos.es'); await p.fill('#login-pass', 'secreta'); await p.click('#login-form button[type=submit]'); await p.clock.runFor(2500);
  await p.evaluate(() => $('#seed-go').click());
  for (let i = 0; i < 200; i++){ await p.clock.runFor(1000); if (await p.evaluate(() => $('#seed-ov').hidden)) break; }
  await p.clock.runFor(2000);
  await p.evaluate(() => navTo('calendarizacion')); await p.clock.runFor(1500);
  const st = () => p.evaluate(() => ({admin: IS_ADMIN, noadm: document.body.classList.contains('noadm'), ro: getComputedStyle(document.querySelector('.noadm-only')).display,
    nuevo: getComputedStyle($('#cz-new')).display, editar: [...document.querySelectorAll('[data-cz-edit]')].filter(x => x.offsetParent).length + '/' + document.querySelectorAll('[data-cz-edit]').length,
    grid: $('#cz-grid').innerHTML.length, empForm: getComputedStyle($('#home-emp-form')).display, badge: !!document.querySelector('.who-am .adm')}));
  console.log('NO ADMIN', JSON.stringify(await st()));
  await p.screenshot({path: 'shot_adm_ro.png'});
  // intentar abrir calendarizar por código
  const w0 = await p.evaluate(() => window.__writes);
  await p.evaluate(() => { const e = ensayos[0]; openEnsForm(e.id, 'cal'); openCzNew(); openCat(); document.querySelector('[data-cz-pub]') && document.querySelector('[data-cz-pub]').click(); }); await p.clock.runFor(500);
  console.log('bloqueado', await p.evaluate(() => !$('#ens-dlg').open && !$('#cat-dlg').open), 'writes', (await p.evaluate(() => window.__writes)) - w0);
  // ver ficha de ensayo normal sí se puede
  await p.evaluate(() => openEnsForm(ensayos[0].id)); await p.clock.runFor(300);
  console.log('ficha normal abre', await p.evaluate(() => $('#ens-dlg').open), 'gocz oculto', await p.evaluate(() => getComputedStyle($('#e-gocz')).display));
  await p.evaluate(() => $('#ens-dlg').close());
  // hacerse admin (como si se añadiera en la consola)
  await p.evaluate(() => firebase.firestore().doc('admins/ana@bionos.es').set({admin: true})); await p.clock.runFor(800);
  console.log('ADMIN', JSON.stringify(await st()));
  await p.evaluate(() => openEnsForm(ensayos[0].id, 'cal')); await p.clock.runFor(300);
  console.log('admin abre calendarizar', await p.evaluate(() => $('#ens-dlg').open)); await p.evaluate(() => $('#ens-dlg').close());
  await p.screenshot({path: 'shot_adm_ok.png'});
  // puesto: nunca admin
  await p.evaluate(() => firebase.firestore().doc('admins/recepcion@clinica.local').set({admin: true}));
  await p.evaluate(() => firebase.auth().signOut()); await p.clock.runFor(1500);
  await p.fill('#login-email', 'recepcion'); await p.fill('#login-pass', 'secreta'); await p.click('#login-form button[type=submit]'); await p.clock.runFor(2500);
  console.log('PUESTO', await p.evaluate(() => IS_ADMIN + ' ' + document.body.classList.contains('noadm')));
  console.log(errs.join('\n') || 'sin errores'); await b.close();
})();
