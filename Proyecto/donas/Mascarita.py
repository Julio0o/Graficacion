import glfw
import cv2
import mediapipe as mp
import numpy as np
import math
from OpenGL.GL import *
from OpenGL.GLU import *

#Ventana
ANCHO_VENTANA = 640
ALTO_VENTANA = 480
TITULO_VENTANA = "filtro"

# animaciones
tiempo_animacion = 0.0
fase_pulso = 0.0

# Conexiones de la cara
CARA = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
        397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
        172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]

OJO_IZQUIERDO = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
OJO_DERECHO = [362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382]

CEJA_IZQUIERDA = [70, 63, 105, 66, 107]
CEJA_DERECHA = [336, 296, 334, 293, 300]

LABIOS = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]

def inicializar_glfw():
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW")
    
    ventana = glfw.create_window(ANCHO_VENTANA, ALTO_VENTANA, TITULO_VENTANA, None, None)
    
    if not ventana:
        glfw.terminate()
        raise Exception("No se pudo crear la ventana GLFW")
    
    glfw.make_context_current(ventana)
    glfw.swap_interval(1)
    
    return ventana

def configurar_opengl():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_POINT_SMOOTH)
    glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

def crear_textura_video():
    textura_video = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textura_video)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    return textura_video

def configurar_luces():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # luces 
    glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 1, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1, 1, 1, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.4, 1))
    
    glLightfv(GL_LIGHT1, GL_POSITION, (0.5, 0.5, 0.5, 0))
    glLightfv(GL_LIGHT1, GL_DIFFUSE, (0.6, 0.6, 0.6, 1))

def normalizar_punto(punto):
    #Coordenadas landmark para coincidir con la luz
    return (punto.x - 0.5, 0.5 - punto.y, -punto.z * 0.5)

def dibujar_esfera(x, y, z, radio, color=(1, 1, 1)):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)
    cuadrico = gluNewQuadric()
    gluQuadricNormals(cuadrico, GLU_SMOOTH)
    gluSphere(cuadrico, radio, 20, 20)
    gluDeleteQuadric(cuadrico)
    glPopMatrix()

def dibujar_cilindro(x1, y1, z1, x2, y2, z2, radio, color=(1, 1, 1)):
   #Cilindro 
    glPushMatrix()
    glColor3f(*color)
    
    #  direccion y longitud
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    longitud = math.sqrt(dx*dx + dy*dy + dz*dz)
    
    if longitud > 0:
        glTranslatef(x1, y1, z1)
        
        # Rotar 
        angulo_x = math.degrees(math.atan2(dy, dx))
        angulo_y = math.degrees(math.acos(dz / longitud))
        glRotatef(angulo_y, -dy, dx, 0)
        
        cuadrico = gluNewQuadric()
        gluQuadricNormals(cuadrico, GLU_SMOOTH)
        gluCylinder(cuadrico, radio, radio, longitud, 12, 1)
        gluDeleteQuadric(cuadrico)
    
    glPopMatrix()

def dibujar_linea_brillante(puntos, color=(0, 1, 1), ancho=3.0, intensidad_brillo=1.0):
    #lineas neon
    glDisable(GL_LIGHTING)
    
    # Capa de brillo exterior
    glLineWidth(ancho + 4)
    glColor4f(color[0] * 0.3, color[1] * 0.3, color[2] * 0.3, 0.3 * intensidad_brillo)
    glBegin(GL_LINE_STRIP)
    for punto in puntos:
        glVertex3f(*punto)
    glEnd()
    
    # Linea principal brillante
    glLineWidth(ancho)
    glColor4f(color[0], color[1], color[2], 0.9 * intensidad_brillo)
    glBegin(GL_LINE_STRIP)
    for punto in puntos:
        glVertex3f(*punto)
    glEnd()
    
    # Nucleo brillante
    glLineWidth(ancho * 0.4)
    glColor4f(1, 1, 1, 0.8 * intensidad_brillo)
    glBegin(GL_LINE_STRIP)
    for punto in puntos:
        glVertex3f(*punto)
    glEnd()
    
    glEnable(GL_LIGHTING)

def circuito(puntos_referencia, indices, desplazamiento_z=0.02, color=(0, 1, 1)):
    #intento de animacion 
    global tiempo_animacion
    
    puntos = [normalizar_punto(puntos_referencia[idx]) for idx in indices]
    puntos_desplazados = [(p[0], p[1], p[2] + desplazamiento_z) for p in puntos]
    
    # Animacion pulso 
    pulso = 0.7 + 0.3 * math.sin(tiempo_animacion * 3)
    dibujar_linea_brillante(puntos_desplazados, color, ancho=2.5, intensidad_brillo=pulso)
    
    # intersecciones
    for i in range(0, len(puntos_desplazados), 3):
        if i < len(puntos_desplazados):
            px, py, pz = puntos_desplazados[i]
            pulso_nodo = 0.8 + 0.2 * math.sin(tiempo_animacion * 4 + i * 0.5)
            dibujar_esfera(px, py, pz, 0.008 * pulso_nodo, (color[0], color[1], color[2]))

def dibujar_ojo_cibernetico(puntos_referencia, indices_ojo, es_izquierdo=True):
    #animacion del ojo
    global tiempo_animacion
    
    # Centro del ojo usando landmarks 
    if es_izquierdo:
        centro_ojo = puntos_referencia[159]  # Centro ojo izquierdo
    else:
        centro_ojo = puntos_referencia[386]  # Centro ojo derecho
    
    cx, cy, cz = normalizar_punto(centro_ojo)
    
    # Anillo exterior
    escala_anillo = 1.0 + 0.15 * math.sin(tiempo_animacion * 2.5)
    glDisable(GL_LIGHTING)
    glLineWidth(2.5)
    glColor4f(0, 1, 1, 0.7)
    glBegin(GL_LINE_LOOP)
    segmentos = 24
    for i in range(segmentos):
        angulo = 2 * math.pi * i / segmentos
        x = cx + 0.035 * escala_anillo * math.cos(angulo)
        y = cy + 0.035 * escala_anillo * math.sin(angulo)
        glVertex3f(x, y, cz + 0.03)
    glEnd()
    
    # animacion abrir y cerrar 
    angulo_escaneo = tiempo_animacion * 2
    for i in range(3):
        angulo = angulo_escaneo + i * (2 * math.pi / 3)
        x1 = cx
        y1 = cy
        x2 = cx + 0.03 * math.cos(angulo)
        y2 = cy + 0.03 * math.sin(angulo)
        
        glLineWidth(1.5)
        glColor4f(0, 1, 1, 0.6)
        glBegin(GL_LINES)
        glVertex3f(x1, y1, cz + 0.03)
        glVertex3f(x2, y2, cz + 0.03)
        glEnd()
    
    # centro 
    pulso_nucleo = 0.015 + 0.005 * math.sin(tiempo_animacion * 5)
    glEnable(GL_LIGHTING)
    dibujar_esfera(cx, cy, cz + 0.03, pulso_nucleo, (0, 1, 1))
    dibujar_esfera(cx, cy, cz + 0.035, pulso_nucleo * 0.5, (1, 1, 1))


def boca(puntos_referencia):
    #animacion de la boca 
    global tiempo_animacion
    
    # Puntos de la boca
    puntos_boca = [normalizar_punto(puntos_referencia[idx]) for idx in LABIOS]
    
    # Calcular apertura de boca para reactividad
    labio_superior = normalizar_punto(puntos_referencia[13])
    labio_inferior = normalizar_punto(puntos_referencia[14])
    apertura_boca = abs(labio_superior[1] - labio_inferior[1])
    
    # Color reactivo a la apertura
    intensidad = min(1.0, apertura_boca * 15)
    color = (intensidad, 0.5 + 0.5 * intensidad, 1)
    
    desplazamiento_z = 0.025
    boca_desplazada = [(p[0], p[1], p[2] + desplazamiento_z) for p in puntos_boca]
    
    # Lineaas de la boca
    dibujar_linea_brillante(boca_desplazada, color, ancho=3, intensidad_brillo=0.7 + 0.3 * intensidad)
    
    # lineas cunado abre la boca 
    if apertura_boca > 0.02:
        esquina_izquierda = boca_desplazada[0]
        esquina_derecha = boca_desplazada[10]
        
        glDisable(GL_LIGHTING)
        for i in range(3):
            t = i / 3.0
            px = esquina_izquierda[0] * (1 - t) + esquina_derecha[0] * t
            py_superior = labio_superior[1]
            py_inferior = labio_inferior[1]
            pz = esquina_izquierda[2]
            
            glLineWidth(1.5)
            alfa = 0.4 + 0.2 * math.sin(tiempo_animacion * 6 + i)
            glColor4f(0, 1, 1, alfa)
            glBegin(GL_LINES)
            glVertex3f(px, py_superior, pz)
            glVertex3f(px, py_inferior, pz)
            glEnd()
        glEnable(GL_LIGHTING)

def dibujar_particulas_datos(puntos_referencia):
    #animacion particulas 
    global tiempo_animacion
    
    # Centro de la cara
    nariz = normalizar_punto(puntos_referencia[1])
    
    glDisable(GL_LIGHTING)
    glPointSize(4.0)
    
    # Generar particulas orbitantes
    cantidad_particulas = 20
    for i in range(cantidad_particulas):
        angulo = (tiempo_animacion * 1.5 + i * 2 * math.pi / cantidad_particulas)
        radio = 0.15 + 0.03 * math.sin(tiempo_animacion * 2 + i)
        altura = 0.1 * math.sin(tiempo_animacion * 3 + i)
        
        px = nariz[0] + radio * math.cos(angulo)
        py = nariz[1] + altura 
        pz = nariz[2] + radio * math.sin(angulo) 
        
        # Color cian con variacion
        brillo = 0.5 + 0.5 * math.sin(tiempo_animacion * 4 + i)
        glColor4f(0, brillo, 1, 0.7)
        
        glBegin(GL_POINTS)
        glVertex3f(px, py, pz)
        glEnd()
        

    
    glEnable(GL_LIGHTING)

def renderizar_fondo_video(cuadro_rgb, textura_video):
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1, 0, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glBindTexture(GL_TEXTURE_2D, textura_video)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 
                 cuadro_rgb.shape[1], cuadro_rgb.shape[0],
                 0, GL_RGB, GL_UNSIGNED_BYTE, cuadro_rgb)
    
    glColor3f(1.0, 1.0, 1.0)
    
    glEnable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 1); glVertex2f(0, 0)
    glTexCoord2f(1, 1); glVertex2f(1, 0)
    glTexCoord2f(1, 0); glVertex2f(1, 1)
    glTexCoord2f(0, 0); glVertex2f(0, 1)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def renderizar_filtro_cibernetico(puntos_faciales):
    #renderizado
    global tiempo_animacion
    
    glEnable(GL_DEPTH_TEST)
    glClear(GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # "mejorar el seguimiento"
    aspecto = ANCHO_VENTANA / ALTO_VENTANA
    glOrtho(-0.5 * aspecto, 0.5 * aspecto, -0.5, 0.5, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    configurar_luces()
    
    puntos_ref = puntos_faciales.landmark
    
    # 1. Contorno de circuitos en el rostro
    circuito(puntos_ref, CARA, desplazamiento_z=0.02, color=(0, 1, 1))
    
    # 2. Visor holografico
    #visor(puntos_ref)
    
    # 3. Ojos ciberneticos con escaneo
    dibujar_ojo_cibernetico(puntos_ref, OJO_IZQUIERDO, es_izquierdo=True)
    dibujar_ojo_cibernetico(puntos_ref, OJO_DERECHO, es_izquierdo=False)
    
    # 4. Cejas con circuitos
    circuito(puntos_ref, CEJA_IZQUIERDA, desplazamiento_z=0.025, color=(0, 0.8, 1))
    circuito(puntos_ref, CEJA_DERECHA, desplazamiento_z=0.025, color=(0, 0.8, 1))
    
    # 5. Boca cibernetica reactiva
    boca(puntos_ref)
    
    # 6. Particulas de datos flotantes
    dibujar_particulas_datos(puntos_ref)
    
    # Restaurar matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def principal():
    global tiempo_animacion
    
    try:
        ventana = inicializar_glfw()
    except Exception as error:
        print(f"Error al inicializar GLFW: {error}")
        return
    
    configurar_opengl()
    textura_video = crear_textura_video()
    
    solucion_mp_cara = mp.solutions.face_mesh
    malla_facial = solucion_mp_cara.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    captura = cv2.VideoCapture(0)

    
    captura.set(cv2.CAP_PROP_FRAME_WIDTH, ANCHO_VENTANA)
    captura.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTO_VENTANA)
    
    contador_cuadros = 0
    temporizador_fps = glfw.get_time()
    tiempo_inicio = glfw.get_time()
    
    try:
        while not glfw.window_should_close(ventana):
            resultado, cuadro = captura.read()
            if not resultado:
                break
            
            cuadro = cv2.flip(cuadro, 1)
            cuadro_rgb = cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB)
            
            resultados = malla_facial.process(cuadro_rgb)
            
            # Actualizar tiempo de animacion
            tiempo_animacion = glfw.get_time() - tiempo_inicio
            
            glfw.poll_events()
            
            if glfw.get_key(ventana, glfw.KEY_ESCAPE) == glfw.PRESS:
                break
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            renderizar_fondo_video(cuadro_rgb, textura_video)
            
            if resultados.multi_face_landmarks:
                for puntos_faciales in resultados.multi_face_landmarks:
                    renderizar_filtro_cibernetico(puntos_faciales)
            
            glfw.swap_buffers(ventana)
            
            contador_cuadros += 1
            tiempo_actual = glfw.get_time()
            if tiempo_actual - temporizador_fps >= 1.0:
                fps = contador_cuadros / (tiempo_actual - temporizador_fps)
                glfw.set_window_title(ventana, f"{TITULO_VENTANA} - FPS: {fps:.1f}")
                contador_cuadros = 0
                temporizador_fps = tiempo_actual
    
    except Exception as error:
        print(f"Error en el loop principal: {error}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nCerrando aplicacion...")
        captura.release()
        malla_facial.close()
        glfw.terminate()

if __name__ == "__main__":
    principal()