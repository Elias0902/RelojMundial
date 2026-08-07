========================================================
  RELOJ MUNDIAL - Widget de escritorio
  Venezuela · Chile · Espana
========================================================

Widget ligero en Python (Tkinter) que muestra la hora local
de las tres zonas al mismo tiempo. Consume muy pocos recursos
y se inicia solo al encender el equipo.


--------------------------------------------------------
REQUISITOS
--------------------------------------------------------
- Windows 10 u 11
- Python 3.9 o superior instalado y agregado al PATH
  Descarga: https://www.python.org/downloads/
  (Durante la instalacion, marca "Add Python to PATH")

No se necesitan librerias externas: solo Tkinter, que viene
incluido con Python. El instalador agrega "tzdata" para que
el horario de verano de Chile y Espana sea siempre correcto.


--------------------------------------------------------
INSTALACION
--------------------------------------------------------
1. Manten estos archivos juntos en una carpeta.
2. Haz doble clic en:  install.bat
3. Listo. El widget aparece y quedara configurado para
   arrancar automaticamente cada vez que inicies sesion.

Que hace el instalador:
  - Copia la app a  %LOCALAPPDATA%\RelojMundial
  - Instala tzdata (zonas horarias)
  - Crea un acceso directo en el Menu Inicio
  - Activa el arranque automatico
  - Registra la app en "Configuracion > Aplicaciones"
    (aparece como una aplicacion normal de Windows)


--------------------------------------------------------
USO
--------------------------------------------------------
BOTONES ARRIBA A LA DERECHA (sobre el widget):
  * Icono de lineas   -> abre el panel de AJUSTES.
  * Icono de esquinas -> PANTALLA COMPLETA (Esc para salir).
  * Cuadro pequeno    -> tamano PEQUENO.
  * Icono de barras   -> VISTA HORARIOS (fases del dia).

VISTA HORARIOS (fases del dia con animacion):
  Pulsa el boton de "barras" (arriba a la derecha), o la tecla H,
  para alternar entre el reloj normal y la vista HORARIOS. En ella:
    * Cada ciudad muestra su fase del dia segun su hora local y un
      CONSEJO para escribirle (los mismos mensajes que la web):
        0-6   -> "Esta durmiendo: no le escribas salvo emergencia"
        6-9   -> "Ya desperto: puedes escribirle"
        9-12  -> "Esta despierto: escribele sin problema"
        12-14 -> "Esta comiendo, pero despierto: puedes escribirle"
        14-19 -> "Esta despierto: buen momento para escribirle"
        19-22 -> "En casa, a punto de dormir: mejor esperar a manana"
        22-24 -> "Casi durmiendo: solo escribele si es una emergencia"
      El consejo se resalta en VERDE cuando conviene escribir y en
      AMBAR cuando es mejor esperar (porque duerme o esta por dormir).
    * Una barra de 24 horas con un punto luminoso que se mueve, late
      y toma el COLOR de la fase actual (con un halo suave), marcando
      en que momento del dia esta cada ciudad.
    * En CHILE, un bloque extra "ELIAS": muestra la cuenta regresiva
      hasta el 14 de agosto de 2026 (cuando Elias comienza a trabajar)
      y, a partir de esa fecha, su turno de 09:00 a 18:30 (hora de
      Venezuela) con una barra de progreso animada mientras trabaja.

OTROS GESTOS:
  * Arrastrar: clic izquierdo sostenido sobre el widget para moverlo.
  * Redimensionar a mano: arrastra el triangulo de la esquina
    inferior derecha (tamano manual).
  * Clic derecho: menu rapido (Ajustes, Pantalla completa,
    Pequeno, Ver horarios/reloj, Anclar al escritorio, Salir).

PANEL DE AJUSTES (estilo iPhone):
  * Tipo de letra: elige la tipografia tocando las muestras.
  * Grosor de la letra: slider de fina a gruesa.
  * Color del texto: arrastra el dedo/raton sobre la barra
    de arcoiris para elegir el tono; sliders de intensidad y
    brillo; ademas una fila de colores rapidos.
  * Fondo: toca un degradado para cambiar el fondo, o activa
    "Fondo transparente" para ver solo el texto sobre el wallpaper.
    Por defecto el widget usa un fondo NEUTRAL (Grafito, gris oscuro),
    a juego con el tema de la web; los demas degradados siguen
    disponibles en esta lista.
  * Opciones: banderas, segundos, fecha, formato 24h, anclar al
    escritorio, siempre encima.
  * Orientacion (vertical/horizontal) y tamano (pequeno, mediano,
    grande, pantalla completa).
  Todo se aplica al instante y se guarda solo.

MODO ESCRITORIO / ANCLADO (por defecto):
  El widget se comporta como parte del fondo del escritorio:
    - Queda al FONDO DE TODO, por debajo de las demas ventanas
      (no es una ventana emergente; no sale en la barra de tareas
      ni en Alt+Tab y no roba el foco al hacer clic).
    - Se ve "VACIO": fondo transparente, solo el reloj sobre tu
      wallpaper (sin caja ni degradado).
    - Queda FIJO A LA DERECHA de la pantalla, centrado en vertical,
      y NO se puede mover ni redimensionar por accidente.
  Al usar "Mostrar escritorio" (Win+D) queda a la vista sobre el
  wallpaper.

  Si prefieres una ventana con fondo (el neutral Grafito) que puedas
  MOVER y redimensionar y que flote encima de todo, abre Ajustes y
  desactiva "Anclado al escritorio" (modo flotante); alli tambien
  puedes activar "Siempre encima". El acceso directo del Menu Inicio
  y iniciar.bat abren el widget en modo flotante y al frente.

FIJAR AL FONDO DE PANTALLA (pegado al wallpaper):
  Opcion extra (Ajustes -> "Fijar al fondo de pantalla", o clic derecho
  -> "Fijar al fondo de pantalla / Quitar"). Pega el reloj a la capa del
  wallpaper: queda SOLO en el escritorio y CUALQUIER ventana que abras o
  cierres queda por encima; ni siquiera vuelve al frente al arrancar.
  IMPORTANTE: en este modo el reloj es decorativo y NO se puede hacer
  clic sobre el (los clics van al escritorio). Para volver a una ventana
  normal ejecuta  flotante.bat  (lo cierra y lo reabre movible). Es una
  funcion de Windows; si tu sistema no lo permite, el widget seguira en
  el modo anclado normal (al fondo, pero por encima del wallpaper).

CONSEJO: si en modo escritorio queda tapado por otra ventana y no lo
encuentras, pulsa Win+D (mostrar escritorio) para verlo, o cierra la
ventana que lo cubre. Al arrancar aparece unos segundos AL FRENTE y
luego pasa al fondo, para que siempre notes que abrio.

Toda la configuracion se guarda sola en:
  %APPDATA%\RelojMundial\config.json


--------------------------------------------------------
SI NO ABRE / SOLUCION DE PROBLEMAS
--------------------------------------------------------
1) iniciar.bat  -> abre el widget SIEMPRE al frente (visible).
   Uselo si "no aparece nada". Esta en esta carpeta y tambien en
   %LOCALAPPDATA%\RelojMundial

1b) flotante.bat -> si lo "fijaste al fondo de pantalla" y ya no puedes
   hacerle clic, esto lo devuelve a una ventana normal y movible.

2) diagnostico.bat -> ejecuta el widget con una consola visible.
   Si hay algun error, se vera en pantalla (compartelo para
   solucionarlo).

3) Si hubo un fallo, se guarda el detalle en:
   %APPDATA%\RelojMundial\error.log

Recuerda: en el modo por defecto (anclado al escritorio) el widget
queda por DEBAJO de las demas ventanas. Si tienes algo abierto en
pantalla completa, no lo veras hasta pulsar Win+D. Para que flote
siempre encima, abre Ajustes y activa "Siempre encima" (desactivando
"Anclado al escritorio").


--------------------------------------------------------
DESINSTALACION
--------------------------------------------------------
Opcion A: Configuracion > Aplicaciones > Reloj Mundial > Desinstalar
Opcion B: ejecuta  uninstall.bat
          (esta tanto en esta carpeta como en
           %LOCALAPPDATA%\RelojMundial)

El desinstalador cierra el widget, quita el arranque
automatico, borra los accesos directos, las entradas del
registro y todos los archivos.


--------------------------------------------------------
NOTAS
--------------------------------------------------------
- Zonas horarias usadas:
    Venezuela -> America/Caracas
    Chile     -> America/Santiago
    Espana    -> Europe/Madrid
  El cambio de horario de verano se aplica automaticamente.
- Si no se instala tzdata, el widget seguira funcionando con
  un offset fijo y mostrara "(aprox.)" junto a la fecha.


--------------------------------------------------------
LANDING / WIDGET WEB  (GitHub Pages)
--------------------------------------------------------
Ademas del widget de escritorio, el proyecto incluye una pagina
web (index.html + assets/) que funciona como LANDING y como WIDGET
en el navegador. Muestra:
  * Las 3 ciudades con su hora en vivo, banderas y fecha.
  * La personalizacion del dia ANIMADA: sol y luna recorriendo el
    cielo segun la hora local de cada ciudad (7 despiertos,
    12 hora de comer, 20 a punto de dormir) y una barra de 24h
    con un punto que se mueve.
  * CONSEJO PARA ESCRIBIR: cada ciudad avisa si puedes escribirle:
    si duermen ("Esta durmiendo: no le escribas salvo emergencia")
    o si estan despiertos ("Esta despierto: escribele sin problema"),
    resaltado en verde (escribe) o ambar (mejor espera).
  * El widget de ELIAS en Chile (cuenta regresiva al 14 de agosto
    de 2026 y su turno 09:00-18:30 hora Venezuela con progreso).
  * Icono de reloj animado con manecillas en hora real (Caracas).
  * Estilo cinematografico: tema neutral (gris grafito), intro con
    cortina, grano de pelicula, vinetas, movimiento Ken Burns,
    destellos en las tarjetas y amanecer/atardecer con sol y luna.
  * "Modo widget": boton arriba a la derecha (o la URL ?widget)
    que compacta la pagina a una columna tipo widget.

PARA PUBLICARLA (GitHub Pages):
  1. Sube el proyecto a GitHub.
  2. Repositorio > Settings > Pages.
  3. Source: "Deploy from a branch" > Rama: main > Carpeta: / (root).
  4. Listo: la landing queda en  https://TU-USUARIO.github.io/REPO

SEPARACION LANDING / WIDGET DE ESCRITORIO:
  El archivo .gitignore evita subir archivos locales del widget
  de escritorio (config.json, error.log, __pycache__/, *.pyc...).
  La pagina web va en la raiz del repositorio; la aplicacion de
  escritorio (worldclock.pyw y los .bat) se mantiene junto a ella
  para instalar el widget en Windows.

--------------------------------------------------------
NOVEDADES (2.1.0)
--------------------------------------------------------
- Widget de escritorio: fondo NEUTRAL (Grafito) por defecto en
  lugar del degradado azul/morado.
- Mensajes de "escribir / no escribir" iguales a los de la web,
  resaltados en verde (conviene escribir) o ambar (mejor espera).
- Vista Horarios mas cinematografica: el punto de cada ciudad late
  con un halo suave y toma el color de su fase del dia.
- Bloque de ELIAS rediseniado: temporizador en fuente monoespaciada
  (los digitos ya no "bailan"), etiqueta con acento de color segun
  estado y barra de progreso solo cuando esta trabajando (se quita
  la barra gris vacia de la cuenta regresiva).
- Modo ANCLADO al escritorio mejorado: queda al fondo de todo, con
  fondo transparente ("vacio", solo el reloj), fijo a la derecha de
  la pantalla y sin poder moverse. El modo flotante sigue siendo
  movible y con fondo Grafito.
- Nueva opcion "Fijar al fondo de pantalla": pega el reloj a la capa
  del wallpaper, de modo que TODO lo que abras o cierres queda por
  encima. En ese modo es decorativo (no clickeable); usa flotante.bat
  para volver a una ventana normal.

NOTA: si ya usabas el widget, tu color de fondo guardado se
respeta. Para ver el nuevo fondo neutral, abre Ajustes y elige
"Grafito", o borra el archivo de configuracion:
  %APPDATA%\RelojMundial\config.json

Version 2.1.0
