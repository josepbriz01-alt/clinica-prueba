# Administradores: instrucciones para el Claude del trabajo

Esto se añade a la web que ya está publicada. Es solo de la web: en la app de Claude no hay inicio de sesión, así que allí todos siguen pudiendo hacerlo todo.

## Qué quiere la usuaria

- **Solo los administradores** pueden **calendarizar**:
  - crear ensayos;
  - cambiar fechas, visitas, circuitos y reparto;
  - publicar y quitar del calendario;
  - poner nueva fecha;
  - tocar el catálogo de medidas.
- **Solo los administradores** pueden **poner y quitar empleados**.
- Los demás **sí ven Calendarización**, pero en **solo lectura**: el calendario, la saturación por box, la vista por día y las listas. Lo que no ven es ningún botón para cambiar nada. La lista de empleados la ven, pero sin el formulario para añadir ni las ✕ para quitar.
- **Quién es administrador lo decide ella desde la consola de Firebase.** Es la colección **`admins`**, con un documento por persona cuyo ID es su **correo en minúsculas**. Desde la web nadie puede cambiarlo.
- Los **usuarios de puesto** (`…@clinica.local`) **nunca** son administradores.

## Cómo está hecho en la referencia

Ver `referencia/web_admin.py`: es la cuarta pasada, después de `web_import.py`. Hace esto:

1. **Comprueba si es administrador.** Al iniciar sesión, escucha `admins/{correo}` con `onSnapshot`, así que el cambio se aplica en directo. Mientras no lo sabe, trata a la persona como no administradora.
2. **`body.noadm`** con CSS que oculta: `#cz-new`, `#cz-cat`, `[data-cz-edit]`, `[data-cz-pub]`, `[data-cz-unpub]`, `[data-cz-redate]`, `#e-gocz` (el "ir a Calendarización" de la ficha del ensayo), `#home-emp-form` y `[data-empdel]`. En Calendarización sale el aviso "👁 Solo lectura…".
3. **Bloqueos por código**, por si se llega por otro camino:
   - envuelve `openEnsForm` (bloquea el modo `"cal"` y crear ensayos nuevos), `openCzNew` y `openCat`;
   - pone un `click` en fase de captura sobre esos mismos botones;
   - pone un `submit` en fase de captura sobre el formulario de empleados.
4. En la esquina, junto al usuario, sale **ADMIN** si lo es.

**Adapta los nombres a tu código.** Si en tu versión hay más sitios desde donde se calendariza, como accesos desde Ensayos, Paneles o Inicio, bloquéalos también.

## Las reglas de Firestore (`referencia/reglas-firestore.txt`)

Hacen que la base de datos lo rechace de verdad. Si alguien lo intenta saltándose la web, recibe `permission-denied`.

- `admins`: se puede leer, pero no escribir desde la web.
- `ensayos`: **crear** solo administradores; **cambiar** `cal`, `inicio` o `fin` solo administradores. El resto de cambios de un ensayo (reclutamiento, estado, participantes…) los puede hacer todo el mundo.
- `config/empleados` y `config/catalogo`: solo administradores.
- Todo lo demás: cualquier usuario que haya entrado.

**Comprueba con tu código** que ningún flujo normal, de alguien que no es administrador, cambia `cal`, `inicio` o `fin` de un ensayo, ni crea ensayos. Si alguno lo hace (por ejemplo, algo automático que guarde `cal.nuevo`), hay que ajustar la regla o ese flujo. Si no, a esa persona le saldrá "No tienes permiso".

`medidas` (fechas de las visitas y circuitos) queda abierta en las reglas, porque la ficha normal del ensayo también guarda ahí. En la web está bloqueado por la interfaz.

## Orden para no quedarse sin permisos

1. **La usuaria se añade como administradora** en Firestore: colección `admins`, documento con su correo en minúsculas, campo `admin` = true.
2. Publicas la web con lo de administradores.
3. **La usuaria pega las reglas nuevas** en Firestore → Reglas → Publicar. Dale el texto de `reglas-firestore.txt`.
4. Probad juntas:
   - con su usuario sale ADMIN y puede calendarizar;
   - con `recepcion` ve Calendarización en solo lectura y no puede tocar empleados.

**Importante para el traspaso de datos:** con las reglas nuevas, la importación crea ensayos y `config/empleados`, así que **la tiene que hacer una administradora**.
