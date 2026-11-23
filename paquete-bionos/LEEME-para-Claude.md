# Web de la clínica (Bionos): instrucciones para el Claude del trabajo

Este paquete lo ha preparado el Claude con el que se montó y se probó la **web de prueba**: https://josepbriz01-alt.github.io/clinica-prueba/ (Firebase + GitHub, con datos inventados). Funciona: inicio de sesión, tiempo real entre ordenadores, aviso de versión nueva y paso de datos.

Ahora hay que hacer lo mismo con **tu versión** de la aplicación, que es la que tiene todos los cambios de la clínica y los datos reales, y publicarla en el Firebase de Bionos.

**Importante:** tu código no es idéntico al mío. Los scripts de `referencia/` son los que yo aplico a **mi** archivo, y buscan trozos de texto exactos; si uno no aparece, el script se para con `COUNT 0 '...'`. Úsalos como **guía de qué cambiar y por qué**, y adapta cada cambio a tu código. No los ejecutes a ciegas.

## Lo que ya está hecho (lo hizo la usuaria en la consola)

- **Proyecto de Firebase de Bionos**: Firestore en Europa, en modo producción.
- **Reglas de Firestore**: `allow read, write: if request.auth != null;`
- **Authentication**: solo correo y contraseña. Usuarios creados: el suyo y `recepcion@clinica.local`.
- **App web registrada.** La usuaria te dará el **`config.js`** con `window.FIREBASE_CONFIG = {...}`.
- **Hosting activado.** Dirección: `https://<projectId>.web.app`.
- **Repositorio privado de GitHub `clinica`**, con el secreto `FIREBASE_SERVICE_ACCOUNT_CLINICA_BIONOS`. Es la clave de una cuenta de servicio con el rol **Administrador de Firebase Hosting**: solo puede publicar, no tocar los datos.

## Qué tienes que hacer

### 1. Convertir tu aplicación en web (`public/index.html`)

Parte del HTML actual de tu aplicación (tu artifact) y aplica estos cambios. El detalle exacto está en `referencia/`:

**`build_web.py`: lo básico**
1. **Pantalla de inicio de sesión** (`#login-ov`). Si se escribe un usuario sin `@`, se convierte en `usuario@clinica.local`, sin tildes ni espacios (`loginEmail`). Los usuarios de puesto (`@clinica.local`) **no ven el botón Salir** (`isPuesto`). Incluye el enlace "He olvidado la contraseña", que solo sirve para correos reales.
2. **SDK de Firebase compat 10.12.2** desde gstatic, más `<script src="config.js">`.
3. **Adaptador** `fbAdapter(fs)`. Tu app usa `update` como **mezcla profunda que crea el documento si no existe**; en Firestore eso es `set(datos, {merge: true})`. Además, `fs.settings({ignoreUndefinedProperties: true, merge: true})`. Sin esto fallan muchas escrituras.
4. **Descargas por el navegador**: `DL.save` pasa a ser Blob + `<a download>`, en lugar de `claude.use("downloads")`. Hay que cambiarlo **en todos los sitios** que usan descargas.
5. **Mensajes de error de Firebase**: `permission-denied` y `resource-exhausted`.
6. **Arranque**: primero se inicia sesión y después `startApp(db)`, que es lo que antes hacía tu IIFE de arranque. Al final no puede quedar ningún `claude.use`.

**`web_post.py`: ajustes de la web**
7. **Aviso de versión nueva**: cada 5 minutos se mira `version.txt`. Si ha cambiado, sale un aviso con "Recargar". De madrugada (2:00–5:00) se recarga sola, solo si no hay nada a medio hacer (`unsaved()`). **Cada vez que publiques, escribe una versión nueva en `version.txt`.**
8. **Espacio**: en Firebase no hay límite de 25.000 registros. La barra pasa a ser **sobre 1 GB** (estimado) y el recuento **no se hace solo**, solo con el botón, porque cada recuento lee toda la base y cuesta lecturas. El resultado se guarda en `config/espacio`.
9. **`<!DOCTYPE html>`, `meta charset` y `viewport`** al principio.

**`web_import.py`: pasar los datos reales (nuevo)**
10. En **Copia de seguridad** aparece la tarjeta **"Pasar datos a esta web"**. Lee el Excel de la **copia completa** (hoja **"Datos completos"**, el JSON de toda la base partido en filas de 30.000 caracteres) y lo escribe en Firestore en lotes de 400.
    - **Solo funciona con la base vacía**, sin `vol`, `ensayos`, `agenda` ni `visitas`. Así no se puede duplicar ni mezclar nada.
    - Si se corta (por ejemplo, por el límite de escrituras del plan gratuito), se puede **continuar** con el mismo Excel. `config/importacion` guarda el estado, y se reescriben los mismos ids, así que no se duplica nada.
    - Al terminar, **cuenta lo que hay en la web y lo compara con el Excel**, colección por colección.
    - No pasa los `config` de control: `demo*`, `limpieza`, `reset`, `espacio`, `importacion`.
    - Antes de escribir, comprueba que no haya **listas dentro de listas**, campos sin nombre ni nombres `__x__`, porque Firestore no los admite. Si encuentra alguno, se para y dice cuál.
11. Con la base vacía, el aviso de inicio **ya no ofrece datos de demostración**: explica cómo pasar los datos reales. Solo los ofrece si `config.js` lleva `window.CLINICA_DEMO = true`, cosa que la web de Bionos **no** debe llevar.

**Antes de nada, comprueba en tu versión:**
- Que tu **"Descargar copia completa"** genera la hoja **"Datos completos"** con `{copia, vol:[{id,...}], ensayos:[...], medidas, panel, agenda, visitas, capacidad, config}`. Mira cómo se hace en `fullDownload` en `referencia/index-web-prueba.html`. Si tu versión no la tiene, **añádela a tu app de Claude** y publícala: es lo que permite pasar los datos.
- Que tus **colecciones** son esas ocho. Si has añadido alguna, inclúyela en `DB_COLS` (copia completa) y en `IMP_COLS` (importar).
- Que tus datos no tienen **listas dentro de listas**. Si las hay, hay que cambiar cómo se guardan antes del traspaso.

`referencia/index-web-prueba.html` es el resultado final de la web de prueba (mi versión), por si quieres ver cómo queda cada cosa ya montada.

### 2. Probar antes de publicar

En `pruebas/` hay un Firebase falso (`fakedb.js`, contraseña `secreta`) y un XLSX falso (`fakexlsx2.js`). Con Playwright se pueden servir en lugar de gstatic y jsdelivr para probar en local: entrar, escribir y leer, y hacer la copia completa → importar en otra página vacía → comparar. Si no puedes ejecutar pruebas, al menos `node --check` del script extraído.

### 3. Subirlo al repositorio `clinica`

Necesitas acceso de escritura a `clinica`. Pídelo con tu herramienta de repositorios; a la usuaria le saldrá el enlace para instalar la app de Claude en GitHub, **solo para ese repositorio**. Estructura:

```
firebase.json                        ← publicar/firebase.json
.github/workflows/publicar.yml       ← publicar/.github/workflows/publicar.yml (pon el projectId de config.js)
public/index.html                    ← la web
public/config.js                     ← el que te da la usuaria
public/version.txt                   ← p. ej. 20261123130000
README.md
```

Cada `push` a `main` publica solo, con GitHub Actions y Firebase Hosting. Comprueba en la pestaña **Actions** que el trabajo sale en verde y abre `https://<projectId>.web.app`.

Si Actions falla por **permisos**, el error lo dice. Normalmente se arregla dando a la cuenta de servicio `github-publicar` el rol **"Lector de claves de API"** (y, si lo pide, **"Consumidor de Service Usage"**) en Google Cloud → IAM. Eso lo hace la usuaria: dile exactamente qué rol añadir.

### 4. Comprobar con la usuaria

- Entrar como `recepcion` (sin `@`): no debe aparecer "Salir". Entrar con su correo: sí aparece.
- Base vacía: sale el aviso de "pasar los datos", **no** el de demostración.
- Dos ordenadores a la vez: un cambio en uno aparece en el otro.

### 5. El día del traspaso (cuando la usuaria lo decida, al acabar la jornada)

1. En tu app de Claude: **Descargar copia completa**. Ese mismo Excel es la copia de seguridad.
2. En la web: **Copia de seguridad → Pasar datos a esta web** → elegir ese Excel → revisar los números → **Pasar los datos ahora**.
3. Comprobar que todos los números salen con ✓ y recargar la web en todos los ordenadores.
4. Desde ese momento se trabaja **solo en la web**. **No borres nada de la app de Claude**: se queda como respaldo.

Ahora mismo son ~2.771 panelistas y 4 ensayos, unas 3.000–4.000 escrituras, así que cabe en el plan gratuito (20.000 al día). Si algún día se pasan muchos ensayos de golpe y la tarjeta avisa de que son más de 18.000 registros, antes hay que activar el plan de pago (Blaze).

### 6. Cambios futuros (muy importante)

La usuaria va a seguir pidiéndote cambios, y tienen que llegar a la web. Para que sea siempre igual y no dependa de la memoria de una conversación:

- **Guarda en el repositorio tu conversor ya adaptado**, por ejemplo `herramientas/convertir_web.py`: el que convierte el HTML de tu app en `public/index.html`. Añade también un `herramientas/NOTAS.md` con cómo se usa.
- Cada cambio se hace así:
  1. Haces el cambio en tu app (el artifact).
  2. Ejecutas el conversor.
  3. Pruebas.
  4. Escribes una versión nueva en `public/version.txt`.
  5. Haces `push`.
- Así la app de Claude y la web siempre tienen el mismo código. Desde el traspaso, **los datos buenos están en la web**: la app de Claude solo sirve para preparar y probar cambios con datos de prueba. No hay que volver a trabajar con datos reales en ella.

### 7. Después

- **Usuarios**: los crea la usuaria en Firebase → Authentication. Para los puestos: `box1@clinica.local`, `sala@clinica.local`…
- **Dominio de Bionos**: Firebase → Hosting → *Añadir dominio personalizado*. El informático añade los registros DNS que indique Firebase. Después se añade ese dominio en Authentication → Ajustes → *Dominios autorizados*.
- **Cada cambio futuro** en tu app: aplícalo también a `public/index.html` (o vuelve a generarlo) y escribe una versión nueva en `version.txt`. Al subirlo, en todos los ordenadores saldrá "Hay una versión nueva".

## Coste esperado

Plan gratuito para montar y probar. Para el uso diario en todos los ordenadores, el plan de pago (Blaze): sin cuota fija, unos 1–5 € al mes en lecturas como mucho. El espacio sale gratis, porque los ensayos terminados se sacan a Excel y se borran.
