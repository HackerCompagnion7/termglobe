#!/usr/bin/env python3
"""Generate termglobe design document PDF - straightforward."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# --- Fonts ---
pdfmetrics.registerFont(TTFont('Carlito', '/usr/share/fonts/truetype/english/Carlito-Regular.ttf'))
pdfmetrics.registerFont(TTFont('CarlitoB', '/usr/share/fonts/truetype/english/Carlito-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSerif', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSerifB', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuMono', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuMonoB', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'))
registerFontFamily('Carlito', normal='Carlito', bold='CarlitoB')
registerFontFamily('DejaVuSerif', normal='DejaVuSerif', bold='DejaVuSerifB')
registerFontFamily('DejaVuMono', normal='DejaVuMono', bold='DejaVuMonoB')

# --- Colors ---
C_ACCENT = colors.HexColor('#1e7694')
C_DARK = colors.HexColor('#181a1b')
C_MUTED = colors.HexColor('#858b90')
C_SURFACE = colors.HexColor('#dde2e6')
C_BG = colors.HexColor('#eef0f2')

# --- Styles ---
s_title = ParagraphStyle('Title', fontName='Carlito', fontSize=28, leading=34,
                         textColor=C_ACCENT, alignment=TA_CENTER, spaceAfter=6)
s_subtitle = ParagraphStyle('Subtitle', fontName='Carlito', fontSize=14, leading=18,
                            textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=20)
s_h1 = ParagraphStyle('H1', fontName='Carlito', fontSize=18, leading=22,
                      textColor=C_ACCENT, spaceBefore=18, spaceAfter=8)
s_h2 = ParagraphStyle('H2', fontName='Carlito', fontSize=14, leading=18,
                      textColor=C_DARK, spaceBefore=12, spaceAfter=6)
s_h3 = ParagraphStyle('H3', fontName='Carlito', fontSize=12, leading=15,
                      textColor=C_DARK, spaceBefore=8, spaceAfter=4)
s_body = ParagraphStyle('Body', fontName='DejaVuSerif', fontSize=10.5, leading=16,
                        textColor=C_DARK, alignment=TA_JUSTIFY, spaceAfter=6)
s_code = ParagraphStyle('Code', fontName='DejaVuMono', fontSize=9, leading=13,
                        textColor=colors.HexColor('#2d2d2d'), backColor=colors.HexColor('#f4f4f4'),
                        leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=4,
                        borderPadding=(6,6,6,6))
s_bullet = ParagraphStyle('Bullet', fontName='DejaVuSerif', fontSize=10.5, leading=16,
                          textColor=C_DARK, leftIndent=20, bulletIndent=8,
                          spaceAfter=3)
s_table_header = ParagraphStyle('TH', fontName='Carlito', fontSize=10, leading=13,
                                textColor=colors.white, alignment=TA_CENTER)
s_table_cell = ParagraphStyle('TC', fontName='DejaVuSerif', fontSize=9.5, leading=13,
                              textColor=C_DARK, alignment=TA_LEFT)
s_table_cell_c = ParagraphStyle('TCC', fontName='DejaVuSerif', fontSize=9.5, leading=13,
                                textColor=C_DARK, alignment=TA_CENTER)

OUTPUT = '/home/z/my-project/download/termglobe_diseno.pdf'

doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2*cm, bottomMargin=2*cm)

story = []

def h1(t): story.append(Paragraph(f'<b>{t}</b>', s_h1))
def h2(t): story.append(Paragraph(f'<b>{t}</b>', s_h2))
def h3(t): story.append(Paragraph(f'<b>{t}</b>', s_h3))
def p(t): story.append(Paragraph(t, s_body))
def code(t): story.append(Paragraph(t.replace('\n','<br/>').replace(' ','&nbsp;'), s_code))
def bullet(t): story.append(Paragraph(f'&#8226;&nbsp;{t}', s_bullet))
def hr(): story.append(HRFlowable(width='100%', thickness=0.5, color=C_ACCENT, spaceAfter=8, spaceBefore=8))
def spacer(h=8): story.append(Spacer(1, h))

def make_table(headers, rows, col_widths=None):
    aw = A4[0] - 4*cm
    if not col_widths:
        n = len(headers)
        col_widths = [aw/n]*n
    data = [[Paragraph(f'<b>{h}</b>', s_table_header) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), s_table_cell) for c in row])
    t = Table(data, colWidths=col_widths, hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_ACCENT),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG]),
        ('GRID', (0,0), (-1,-1), 0.5, C_MUTED),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    spacer(6)

# ============================================================
# COVER
# ============================================================
story.append(Spacer(1, 120))
story.append(Paragraph('<b>termglobe</b>', ParagraphStyle('BigTitle', fontName='Carlito',
    fontSize=48, leading=56, textColor=C_ACCENT, alignment=TA_CENTER)))
spacer(12)
story.append(Paragraph('Motor de renderizado 3D en terminal (ASCII)', s_subtitle))
spacer(30)
story.append(HRFlowable(width='60%', thickness=2, color=C_ACCENT, spaceAfter=20, spaceBefore=0))
spacer(10)
story.append(Paragraph('Documento de diseno tecnico y arquitectonico', ParagraphStyle('Desc',
    fontName='DejaVuSerif', fontSize=12, leading=16, textColor=C_MUTED, alignment=TA_CENTER)))
spacer(40)
story.append(Paragraph('Fase: Analisis y diseno (sin codigo)', ParagraphStyle('Meta',
    fontName='DejaVuSerif', fontSize=11, leading=14, textColor=C_MUTED, alignment=TA_CENTER)))
story.append(Paragraph('Fecha: Abril 2026', ParagraphStyle('Meta2',
    fontName='DejaVuSerif', fontSize=11, leading=14, textColor=C_MUTED, alignment=TA_CENTER)))
story.append(PageBreak())

# ============================================================
# 1. VISION GENERAL
# ============================================================
h1('1. Vision General')
p('<b>termglobe</b> es una biblioteca ligera de renderizado 3D en terminal que utiliza caracteres ASCII para desplegar un globo terraqueo rotatorio. El objetivo es lograr una experiencia visual fluida (minimo 20 FPS) en terminales ANSI estandar, Linux nativo o Termux en Android, sin dependencias graficas pesadas ni OpenGL. La biblioteca convierte coordenadas geograficas (latitud/longitud) en puntos 3D sobre una esfera, los proyecta a 2D mediante proyeccion perspectiva, y renderiza el resultado usando un gradiente ASCII que simula profundidad e iluminacion.')
p('El diseno prioriza la eficiencia computacional: cada frame debe procesarse en menos de 50 ms en hardware modesto. Se evita el flickering mediante double buffering con secuencias de escape ANSI, y el rendering se adapta automaticamente al tamano del terminal detectado en tiempo de ejecucion.')

h2('1.1 Requisitos del MVP')
bullet('Globo rotando automaticamente sobre el eje Y')
bullet('Posibilidad de detener/reanudar la rotacion')
bullet('Colocar marcadores (pins) mediante coordenadas lat/lon')
bullet('Render estable sin parpadeo en terminal')
bullet('Adaptacion automatica al tamano de pantalla')
bullet('Minimo 20 FPS en hardware modesto')

h2('1.2 Restricciones')
bullet('Sin librerias graficas externas (no OpenGL, no SDL, no ncurses obligatorio)')
bullet('Sin texturas reales en la primera version')
bullet('Diseno modular y extensible, sin sobreingenieria')
bullet('CPU y memoria minimas')

hr()

# ============================================================
# 2. FUNDAMENTOS MATEMATICOS
# ============================================================
h1('2. Fundamentos Matematicos')

h2('2.1 Representacion de la esfera')
p('Un punto en la superficie de una esfera de radio r se describe con dos angulos: la latitud (phi) medida desde el ecuador (-pi/2 a pi/2) y la longitud (lambda) medida desde el meridiano de referencia (0 a 2pi). La conversion a coordenadas cartesianas 3D es directa y se computa con operaciones trigonometricas elementales:')

code('x = r * cos(phi) * cos(lambda)')
code('y = r * sin(phi)')
code('z = r * cos(phi) * sin(lambda)')

p('Esta formulacion situa el ecuador en el plano XZ y el polo norte en +Y. El costo por punto es de 2 cosenos y 1 seno, que se optimiza precomputando cos(phi) y almacenandolo como variable temporal, reduciendo a 1 coseno, 1 seno y 1 multiplicacion extra.')

h2('2.2 Rotacion en el eje Y')
p('La rotacion de un angulo theta alrededor del eje Y se expresa como multiplicacion matricial. La matriz de rotacion 3x3 es:')

code('| cos(theta)&nbsp;&nbsp;0&nbsp;&nbsp;sin(theta) |')
code('|&nbsp;&nbsp;&nbsp;0&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;1&nbsp;&nbsp;&nbsp;&nbsp;0&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|')
code('| -sin(theta)&nbsp;&nbsp;0&nbsp;&nbsp;cos(theta) |')

p('Aplicada a un punto (x, y, z), el resultado es: x\' = x*cos(theta) + z*sin(theta), y\' = y (inalterado), z\' = -x*sin(theta) + z*cos(theta). Esto exige 4 multiplicaciones y 2 sumas por punto, que es extremadamente barato. Para la extension futura a rotacion en X y Z, se aplican matrices analogas en secuencia.')

h2('2.3 Proyeccion perspectiva')
p('Se utiliza una proyeccion perspectiva simple con distancia focal d (profundidad de la camara). Dado un punto 3D (x, y, z) ya rotado, las coordenadas proyectadas 2D son:')

code("x' = x / (z + d)")
code("y' = y / (z + d)")

p('El parametro d controla la intensidad del efecto perspectiva. Un valor grande (d >> r) se aproxima a proyeccion ortografica (sin deformacion); un valor cercano a r produce una perspectiva dramatica. Se recomienda d = 3r como valor inicial, equilibrando visibilidad y naturalidad. Es critico descartar puntos donde z + d sea menor o igual a cero, ya que estan detras de la camara y generarian divisiones invalidas.')

h2('2.4 Conversion lat/lon a 3D')
p('La conversion directa de coordenadas geograficas a cartesianas sigue la misma formula de la esfera, donde phi = lat * pi/180 y lambda = lon * pi/180. La latitud geografica se mide desde el ecuador (igual que phi), y la longitud desde Greenwich (igual que lambda). No se requiere conversion de datum ni elipsoide en esta version: la esfera es perfecta y el radio se normaliza a 1 para luego escalar al tamano del terminal.')

h2('2.5 Manejo de profundidad (Z-buffer aproximado)')
p('El problema central es determinar que puntos de la esfera son visibles (mirando hacia el observador) y cuales estan ocultos (detras del globo). Un z-buffer por pixel seria costoso en memoria. En su lugar, se usa la <b>prueba de visibilidad por normal</b>: un punto es visible si su vector normal (que en una esfera unitaria es el propio punto) tiene componente Z positiva tras la rotacion, es decir, z_rotado > 0. Esto elimina exactamente la mitad de los puntos (los del hemisferio trasero) con una unica comparacion, sin overhead de memoria.')
p('Para resolver conflictos cuando multiples puntos proyectan al mismo caracter del terminal, se usa un <b>depth buffer discreto</b>: un array 2D de flotantes con dimensiones (cols, rows) que almacena el valor z mas cercano visto hasta el momento. Si un nuevo punto proyecta a la misma celda pero tiene z mayor (mas lejos), se descarta. Si tiene z menor (mas cerca), se sobrescribe. Este buffer se reinicia cada frame y su tamano es O(cols * rows), tipicamente menos de 10 KB.')

hr()

# ============================================================
# 3. ARQUITECTURA MODULAR
# ============================================================
h1('3. Arquitectura Modular')
p('La biblioteca se divide en 5 modulos con responsabilidades claras y dependencias unidireccionales. Cada modulo expone una API minima y no depende de los detalles internos de los demas. El flujo de datos va desde la entrada (lat/lon) hasta la salida (caracteres en terminal), pasando por transformaciones matematicas y el motor de renderizado.')

h2('3.1 math_core')
p('Modulo fundamental que encapsula toda la matematica geometrica. No depende de ningun otro modulo y es la base sobre la que construyen globe_model y renderer.')

make_table(
    ['Componente', 'Responsabilidad', 'Complejidad'],
    [
        ['vec3(x, y, z)', 'Vector 3D basico con operaciones aritmeticas', 'O(1)'],
        ['rot_y(vec3, theta)', 'Rotacion alrededor del eje Y', 'O(1)'],
        ['rot_x(vec3, theta)', 'Rotacion alrededor del eje X (extension)', 'O(1)'],
        ['project(vec3, d)', 'Proyeccion perspectiva a 2D', 'O(1)'],
        ['latlon_to_xyz(lat, lon, r)', 'Conversion geografica a cartesiano', 'O(1)'],
    ],
    [6*cm, 7*cm, 3.5*cm]
)

h2('3.2 renderer')
p('Modulo de dibujo en terminal. Mantiene el double buffer, el depth buffer discreto y el sistema de caracteres ASCII con shading. Se encarga de la presentacion final sin conocer la geometria del globo.')

make_table(
    ['Componente', 'Responsabilidad', 'Complejidad'],
    [
        ['Buffer2D(cols, rows)', 'Double buffer de caracteres + depth buffer', 'O(cols*rows)'],
        ['clear()', 'Limpia buffer y depth buffer para nuevo frame', 'O(cols*rows)'],
        ['set_pixel(col, row, z, char)', 'Escribe pixel si es mas cercano (z-test)', 'O(1)'],
        ['flush()', 'Emite buffer a stdout via escape ANSI', 'O(cols*rows)'],
        ['resize(cols, rows)', 'Re dimensiona buffers al cambiar terminal', 'O(cols*rows)'],
    ],
    [6*cm, 7*cm, 3.5*cm]
)

p('El shading ASCII mapea la profundidad z (normalizada entre 0 y 1) a una cadena de caracteres de luminosidad creciente. La cadena por defecto es <b>`.:-=+*#%@</b>`, donde `.` representa la zona mas profunda (lejos del observador) y `@` la mas cercana (frontal). Esto crea una ilusion de volumen sin necesidad de iluminacion real.')

h2('3.3 globe_model')
p('Modulo que representa la esfera y sus marcadores. Genera la nube de puntos, aplica la conversion lat/lon y mantiene la lista de pins.')

make_table(
    ['Componente', 'Responsabilidad', 'Complejidad'],
    [
        ['generate_points(res)', 'Genera puntos de esfera con resolucion dada', 'O(res<super>2</super>)'],
        ['add_pin(lat, lon, label)', 'Agrega marcador geografico', 'O(1)'],
        ['remove_pin(id)', 'Elimina marcador por identificador', 'O(n_pins)'],
        ['get_points()', 'Retorna puntos + pins como lista de vec3', 'O(res<super>2</super>+n_pins)'],
    ],
    [6*cm, 7*cm, 3.5*cm]
)

p('La resolucion (res) define cuantos puntos se generan: res pasos en latitud por 2*res pasos en longitud, dando ~2*res<super>2</super> puntos. Con res=20 se obtienen 800 puntos, suficiente para un globo legible en 80 columnas. Con res=30 se obtienen 1800 puntos para terminales mas anchos.')

h2('3.4 engine')
p('Modulo orquestador que une todo. Controla el loop de render, el estado de rotacion, el timing de FPS y la coordenacion entre modulos.')

make_table(
    ['Componente', 'Responsabilidad', 'Complejidad'],
    [
        ['init()', 'Inicializa modulos, detecta terminal', 'O(1)'],
        ['run()', 'Loop principal con control de FPS', 'O(1) por iteracion'],
        ['stop()', 'Detiene rotacion (no el programa)', 'O(1)'],
        ['set_fps(target)', 'Ajusta FPS objetivo', 'O(1)'],
        ['tick()', 'Un paso de render: rotar + proyectar + dibujar', 'O(n_points)'],
    ],
    [5*cm, 8*cm, 3.5*cm]
)

h2('3.5 cli_adapter')
p('Capa de integracion con herramientas externas tipo geo-cli. Permite recibir comandos desde linea de comandos o tuberias (pipes) para agregar marcadores, cambiar rotacion, o consultar estado. Este modulo es opcional en el MVP y se implementa como un parser simple de stdin o argumentos de argparse.')

make_table(
    ['Comando', 'Efecto'],
    [
        ['--pin LAT LON [LABEL]', 'Agrega marcador en coordenadas dadas'],
        ['--stop', 'Detiene rotacion'],
        ['--resume', 'Reanuda rotacion'],
        ['--fps N', 'Cambia FPS objetivo'],
        ['--axis [x|y|z]', 'Cambia eje de rotacion'],
    ],
    [5.5*cm, 11*cm]
)

hr()

# ============================================================
# 4. FLUJO DE DATOS
# ============================================================
h1('4. Flujo de Datos: de lat/lon al terminal')
p('El flujo completo desde la entrada de coordenadas geograficas hasta el render en terminal sigue un pipeline de 6 etapas secuenciales. Cada etapa transforma los datos sin retroalimentacion, lo que simplifica el diseno y garantiza prediccion de rendimiento.')

h2('4.1 Pipeline por frame')

make_table(
    ['Etapa', 'Input', 'Output', 'Operacion', 'Costo'],
    [
        ['1. Generacion', 'res, pins', 'puntos_3d[]', 'latlon_to_xyz para cada punto y pin', 'O(n)'],
        ['2. Rotacion', 'puntos_3d[], theta', 'puntos_rot[]', 'rot_y(p, theta) para cada punto', 'O(n)'],
        ['3. Visibilidad', 'puntos_rot[]', 'puntos_vis[]', 'Filtrar z_rot > 0', 'O(n)'],
        ['4. Proyeccion', 'puntos_vis[], d', 'puntos_2d[], z_depth[]', 'project(p, d) para cada visible', 'O(n/2)'],
        ['5. Rasterizacion', 'puntos_2d[], z_depth[]', 'buffer[col][row]', 'set_pixel con z-test', 'O(n/2)'],
        ['6. Flush', 'buffer', 'stdout', 'Escritura con escape ANSI', 'O(w*h)'],
    ],
    [2.5*cm, 2.5*cm, 2.5*cm, 4.5*cm, 2*cm]
)

p('Donde n es el numero total de puntos generados (~2*res<super>2</super> + n_pins), w y h son las columnas y filas del terminal. El costo total por frame es O(n + w*h), lineal en ambos parametros, sin operaciones cuadraticas ni exponenciales.')

h2('4.2 Estrategia anti-flicker')
p('El flickering se produce cuando se limpia la pantalla y se redibuja, creando un flash visible. La solucion es el <b>double buffering con reemplazo en sitio</b>: en lugar de limpiar y redibujar todo, se mueve el cursor al inicio (secuencia ESC[H) y se sobrescriben los caracteres existentes con los nuevos. Como ANSI es secuencial, el reemplazo es atomico desde la perspectiva del usuario: siempre ve un frame completo, nunca un estado intermedio. Adicionalmente, se puede usar la secuencia ESC[?25l para ocultar el cursor durante el render y ESC[?25h para restaurarlo al salir.')

h2('4.3 Adaptacion al terminal')
p('Cada frame (o al detectar una senal SIGWINCH) se consulta el tamano del terminal mediante os.get_terminal_size() (Python) o ioctl TIOCGWINSZ (C/Rust). El radio del globo se calcula como min(cols, rows) / 2 - padding, y los buffers se redimensionan si las dimensiones cambiaron. Esto garantiza que el globo siempre quepa en la pantalla, incluso si el usuario redimensiona la ventana.')

hr()

# ============================================================
# 5. ANALISIS DE RENDIMIENTO
# ============================================================
h1('5. Analisis de Rendimiento')

h2('5.1 Complejidad computacional por frame')
p('El costo total por frame es la suma de todas las etapas del pipeline. Con resolucion res=20 (800 puntos) y terminal de 80x24 (1920 celdas):')

make_table(
    ['Etapa', 'Operaciones', 'Estimado (res=20)'],
    [
        ['Generacion de puntos', '4 trig + 3 mul por punto', '6400 ops'],
        ['Rotacion Y', '4 mul + 2 add por punto', '4800 ops'],
        ['Test visibilidad', '1 comparacion por punto', '800 ops'],
        ['Proyeccion perspectiva', '2 div + 2 add por visible', '1600 ops'],
        ['Rasterizacion + z-test', '1 comp + 1 write por visible', '800 ops'],
        ['Flush ANSI', '1 write por celda', '1920 chars'],
    ],
    [4*cm, 5*cm, 4*cm]
)

p('<b>Total estimado: ~14,400 operaciones aritmeticas + 1,920 caracteres de salida.</b> En un procesador moderno ejecutando Python, esto es menos de 1 ms de CPU. Incluso con res=30 (1,800 puntos), el costo apenas alcanza ~32,000 operaciones. El cuello de botella real no es la CPU sino la velocidad de escritura a stdout, que se mitiga emitiendo una unica cadena concatenada por frame.')

h2('5.2 Uso de memoria')
p('El consumo de memoria es constante y predecible:')

make_table(
    ['Estructura', 'Tamano', 'Ejemplo (80x24)'],
    [
        ['Buffer de caracteres', 'cols * rows * 1 byte', '1,920 B'],
        ['Depth buffer', 'cols * rows * 4 bytes (float)', '7,680 B'],
        ['Puntos de esfera', 'n * 3 * 8 bytes (3 floats)', '19,200 B (res=20)'],
        ['Marcadores', 'n_pins * 32 bytes (aprox)', '~256 B (8 pins)'],
        ['Total', '', '~29 KB'],
    ],
    [4*cm, 5*cm, 4*cm]
)

p('Menos de 30 KB para la estructura completa. En Termux con 256 MB de RAM disponibles, esto es irrelevante. No hay allocations dinamicas durante el loop de render; todo se pre-aloca en la inicializacion.')

h2('5.3 Cuellos de botella y mitigaciones')
bullet('<b>stdout lento:</b> Se emite todo el frame como un unico string.write() en vez de multiples prints. Se concatena en un StringBuilder y se escribe una sola vez.')
bullet('<b>Trigonometricas:</b> Se precomputa cos(phi) y sin(phi) una vez por fila de latitud. La tabla de cosenos/senos por resolucion se almacena en cache entre frames.')
bullet('<b>Deteccion de resize:</b> Se consulta terminal size cada N frames (no cada frame) para amortizar el costo del syscall, con manejo inmediato de SIGWINCH.')

hr()

# ============================================================
# 6. SISTEMA VISUAL
# ============================================================
h1('6. Sistema Visual')

h2('6.1 Gradiente ASCII y shading')
p('El gradiente ASCII mapea la profundidad z normalizada a caracteres con diferente "densidad visual". La normalizacion toma z_rotado (que va de 0 a r tras el test de visibilidad) y lo escala a [0, 1]:')

code('z_norm = (z_rotado - 0) / r&nbsp;&nbsp;# r es el radio')
code('index&nbsp;&nbsp;= int(z_norm * (len(shade) - 1))')
code('char&nbsp;&nbsp;&nbsp;= shade[index]')

p('La tabla de shading por defecto es: <b>`.:-=+*#%@</b>` (10 niveles). Puntos en el borde del globo (z cercano a 0, perfil) reciben caracteres claros (`.`), mientras que los frontales (z cercano a r) reciben caracteres densos (`@`). Esto simula una fuente de luz en la posicion del observador.')

h2('6.2 Marcadores (pins)')
p('Los marcadores se representan con el caracter <b>●</b> (U+25CF, circulo lleno). Tras la proyeccion, si un pin cae en una celda del buffer, se sobrescribe cualquier caracter de shading con el simbolo del pin. Los pins siempre tienen prioridad sobre la superficie, independientemente de la profundidad, para garantizar visibilidad. En futuras versiones se puede agregar una etiqueta de texto junto al pin.')

h2('6.3 Lineas de meridiano/paralelo (extension)')
p('Para dar sensacion de estructura al globo, se pueden generar puntos extras a lo largo de meridianos y paralelos clave (ecuador, tropicos, meridiano de Greenwich, etc.) marcandolos con un caracter diferente, por ejemplo `+` o `-`. Estos puntos se mezclan con los de la superficie y siguen el mismo pipeline de proyeccion y z-test. El costo adicional es proporcional al numero de lineas dibujadas (tipicamente 6-12 lineas = ~200 puntos extra).')

hr()

# ============================================================
# 7. EXTENSIBILIDAD
# ============================================================
h1('7. Extensibilidad')
p('El diseno modular permite extensiones futuras sin modificar los modulos existentes, siguiendo el principio de abierto/cerrado:')

make_table(
    ['Extension', 'Modulo afectado', 'Cambios requeridos'],
    [
        ['Multiples marcadores', 'globe_model', 'Lista de pins ya soportada; solo agregar UI'],
        ['Interaccion por teclado', 'engine', 'Agregar listener de stdin en thread separado'],
        ['Colores ANSI', 'renderer', 'Buffer almacena (char, color); flush emite ESC[38;5;Nm'],
        ['Rotacion en X y Z', 'math_core', 'Agregar rot_x(), rot_z(); engine selecciona eje'],
        ['Otros objetos 3D', 'globe_model', 'Interfaz generica SceneObject con get_points()'],
        ['Zoom', 'engine', 'Ajustar parametro d de proyeccion'],
        ['Iluminacion Phong', 'math_core', 'Calcular dot(normal, light_dir) para shading'],
        ['Lineas de costa', 'globe_model', 'Cargar dataset GeoJSON simplificado como polilineas'],
    ],
    [4*cm, 3.5*cm, 9*cm]
)

hr()

# ============================================================
# 8. ESTRUCTURA DE LA BIBLIOTECA
# ============================================================
h1('8. Estructura de la Biblioteca')
p('La organizacion de archivos refleja la separacion modular y facilita la importacion selectiva:')

code('termglobe/')
code('&nbsp;&nbsp;__init__.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Exporta API publica')
code('&nbsp;&nbsp;math_core.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# vec3, rotaciones, proyeccion')
code('&nbsp;&nbsp;renderer.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Buffer2D, shading, flush')
code('&nbsp;&nbsp;globe_model.py&nbsp;&nbsp;&nbsp;&nbsp;# Esfera, pins, puntos')
code('&nbsp;&nbsp;engine.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Loop de render, FPS, estado')
code('&nbsp;&nbsp;cli_adapter.py&nbsp;&nbsp;&nbsp;&nbsp;# Argumentos, comandos interactivos')

p('La API publica desde __init__.py expone unicamente: Globe (facade que combina globe_model + engine), Renderer, y las funciones de conveniencia run() y add_pin(). Los detalles internos de math_core no se exponen al usuario final.')

hr()

# ============================================================
# 9. DECISIONES TECNICAS JUSTIFICADAS
# ============================================================
h1('9. Decisiones Tecnicas Justificadas')

make_table(
    ['Decision', 'Alternativa descartada', 'Justificacion'],
    [
        ['Normal-based visibility', 'Z-buffer por pixel completo',
         'O(1) por punto vs O(w*h) por frame; la esfera es convexa, la normal basta'],
        ['Double buffer + ESC[H', 'ncurses o alt screen buffer',
         'Sin dependencias; ESC[H es universal en ANSI; mas simple que ncurses'],
        ['Proyeccion perspectiva', 'Proyeccion ortografica',
         'Perspectiva da sensacion de profundidad con costo identico (1 division mas)'],
        ['ASCII shading por profundidad', 'Iluminacion Phong',
         'Phong requiere calcular normales rotadas y dot products; shading por z es O(1) por punto'],
        ['Precomputacion de trig', 'Calculo en cada frame',
         'cos(phi) y sin(phi) son constantes; se calculan una vez en generate_points()'],
        ['Escribir frame como un string', 'Multiples stdout.write()',
         'Un solo write() reduce syscalls y evita tearing parcial en terminal'],
        ['Parametro d=3r', 'd variable o d=r',
         'd=3r balancea perspectiva visible sin distorsion extrema; d=r produce deformacion excesiva'],
    ],
    [4*cm, 4*cm, 8.5*cm]
)

# ============================================================
# BUILD
# ============================================================
doc.build(story)
print(f'PDF generado: {OUTPUT}')
