import glfw
import cv2
import mediapipe as mp
import numpy as np
import math
from OpenGL.GL import *
from OpenGL.GLU import *

# ============================================================
# Configuración
# ============================================================
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
WINDOW_TITLE = "Filtro Cibernético AR - Snapchat Style"

# Variables globales para animaciones
animation_time = 0.0
pulse_phase = 0.0

# Conexiones faciales
CARA = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
             397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
             172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]

OJO_IZQUIERDO = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
OJO_DERECHO = [362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382]

CEJA_IZQUIERDA = [70, 63, 105, 66, 107]
CEJAS_DERECHA = [336, 296, 334, 293, 300]

LABIOS= [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]

def init_glfw():
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW")
    
    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, None, None)
    
    if not window:
        glfw.terminate()
        raise Exception("No se pudo crear la ventana GLFW")
    
    glfw.make_context_current(window)
    glfw.swap_interval(1)
    
    return window

def setup_opengl():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_POINT_SMOOTH)
    glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

def create_video_texture():
    video_tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, video_tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    return video_tex

def setup_lights():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Ajustar luces para proyección ortográfica
    glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 1, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1, 1, 1, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.4, 1))
    
    glLightfv(GL_LIGHT1, GL_POSITION, (0.5, 0.5, 0.5, 0))
    glLightfv(GL_LIGHT1, GL_DIFFUSE, (0.6, 0.6, 0.6, 1))

def norm_landmark(p):
    """Normaliza las coordenadas del landmark para que coincidan con la proyección"""
    return (p.x - 0.5, 0.5 - p.y, -p.z * 0.5)

def draw_sphere(x, y, z, radius, color=(1, 1, 1)):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)
    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, radius, 20, 20)
    gluDeleteQuadric(quad)
    glPopMatrix()

def draw_cylinder(x1, y1, z1, x2, y2, z2, radius, color=(1, 1, 1)):
    """Dibuja un cilindro entre dos puntos"""
    glPushMatrix()
    glColor3f(*color)
    
    # Calcular dirección y longitud
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    length = math.sqrt(dx*dx + dy*dy + dz*dz)
    
    if length > 0:
        glTranslatef(x1, y1, z1)
        
        # Rotar hacia el punto destino
        ax = math.degrees(math.atan2(dy, dx))
        ay = math.degrees(math.acos(dz / length))
        glRotatef(ay, -dy, dx, 0)
        
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluCylinder(quad, radius, radius, length, 12, 1)
        gluDeleteQuadric(quad)
    
    glPopMatrix()

def draw_glowing_line(points, color=(0, 1, 1), width=3.0, glow_intensity=1.0):
    """Dibuja una línea con efecto de brillo neón"""
    glDisable(GL_LIGHTING)
    
    # Capa de brillo exterior
    glLineWidth(width + 4)
    glColor4f(color[0] * 0.3, color[1] * 0.3, color[2] * 0.3, 0.3 * glow_intensity)
    glBegin(GL_LINE_STRIP)
    for p in points:
        glVertex3f(*p)
    glEnd()
    
    # Línea principal brillante
    glLineWidth(width)
    glColor4f(color[0], color[1], color[2], 0.9 * glow_intensity)
    glBegin(GL_LINE_STRIP)
    for p in points:
        glVertex3f(*p)
    glEnd()
    
    # Núcleo brillante
    glLineWidth(width * 0.4)
    glColor4f(1, 1, 1, 0.8 * glow_intensity)
    glBegin(GL_LINE_STRIP)
    for p in points:
        glVertex3f(*p)
    glEnd()
    
    glEnable(GL_LIGHTING)

def draw_circuit_pattern(lm, indices, offset_z=0.02, color=(0, 1, 1)):
    """Dibuja patrón de circuitos sobre el rostro"""
    global animation_time
    
    points = [norm_landmark(lm[idx]) for idx in indices]
    points_offset = [(p[0], p[1], p[2] + offset_z) for p in points]
    
    # Efecto de pulso en el brillo
    pulse = 0.7 + 0.3 * math.sin(animation_time * 3)
    draw_glowing_line(points_offset, color, width=2.5, glow_intensity=pulse)
    
    # Nodos en las intersecciones (cada 3 puntos)
    for i in range(0, len(points_offset), 3):
        if i < len(points_offset):
            px, py, pz = points_offset[i]
            node_pulse = 0.8 + 0.2 * math.sin(animation_time * 4 + i * 0.5)
            draw_sphere(px, py, pz, 0.008 * node_pulse, (color[0], color[1], color[2]))

def draw_cyber_eye(lm, eye_indices, is_left=True):
    """Dibuja ojo cibernético con animación de escaneo"""
    global animation_time
    
    # Centro del ojo usando landmarks correctos
    if is_left:
        eye_center = lm[159]  # Centro ojo izquierdo
    else:
        eye_center = lm[386]  # Centro ojo derecho
    
    cx, cy, cz = norm_landmark(eye_center)
    
    # Anillo exterior pulsante
    ring_scale = 1.0 + 0.15 * math.sin(animation_time * 2.5)
    glDisable(GL_LIGHTING)
    glLineWidth(2.5)
    glColor4f(0, 1, 1, 0.7)
    glBegin(GL_LINE_LOOP)
    segments = 24
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = cx + 0.035 * ring_scale * math.cos(angle)
        y = cy + 0.035 * ring_scale * math.sin(angle)
        glVertex3f(x, y, cz + 0.03)
    glEnd()
    
    # Líneas de escaneo rotantes
    scan_angle = animation_time * 2
    for i in range(3):
        angle = scan_angle + i * (2 * math.pi / 3)
        x1 = cx
        y1 = cy
        x2 = cx + 0.03 * math.cos(angle)
        y2 = cy + 0.03 * math.sin(angle)
        
        glLineWidth(1.5)
        glColor4f(0, 1, 1, 0.6)
        glBegin(GL_LINES)
        glVertex3f(x1, y1, cz + 0.03)
        glVertex3f(x2, y2, cz + 0.03)
        glEnd()
    
    # Núcleo brillante central
    core_pulse = 0.015 + 0.005 * math.sin(animation_time * 5)
    glEnable(GL_LIGHTING)
    draw_sphere(cx, cy, cz + 0.03, core_pulse, (0, 1, 1))
    draw_sphere(cx, cy, cz + 0.035, core_pulse * 0.5, (1, 1, 1))

def draw_holographic_visor(lm):
    """Dibuja visor holográfico sobre los ojos"""
    global animation_time
    
    # Puntos clave para el visor
    left_temple = norm_landmark(lm[234])
    right_temple = norm_landmark(lm[454])
    left_eye_outer = norm_landmark(lm[33])
    right_eye_outer = norm_landmark(lm[263])
    nose_bridge = norm_landmark(lm[6])
    
    offset_z = 0.04
    
    # Estructura del visor
    visor_points = [
        (left_temple[0], left_temple[1], left_temple[2] + offset_z),
        (left_eye_outer[0], left_eye_outer[1], left_eye_outer[2] + offset_z),
        (nose_bridge[0], nose_bridge[1], nose_bridge[2] + offset_z),
        (right_eye_outer[0], right_eye_outer[1], right_eye_outer[2] + offset_z),
        (right_temple[0], right_temple[1], right_temple[2] + offset_z)
    ]
    
    # Efecto de energía fluyendo
    energy_flow = math.sin(animation_time * 4) * 0.5 + 0.5
    color = (0, 0.7 + 0.3 * energy_flow, 1)
    
    draw_glowing_line(visor_points, color, width=3.5, glow_intensity=1.0)
    
    # Conectores laterales
    for temple, eye_outer in [(left_temple, left_eye_outer), (right_temple, right_eye_outer)]:
        tx, ty, tz = temple
        ex, ey, ez = eye_outer
        draw_cylinder(tx, ty, tz + offset_z, ex, ey, ez + offset_z, 0.003, color)

def draw_cyber_mouth(lm):
    """Dibuja boca cibernética con animación reactiva"""
    global animation_time
    
    # Puntos de la boca
    mouth_points = [norm_landmark(lm[idx]) for idx in LABIOS]
    
    # Calcular apertura de boca para reactividad
    top_lip = norm_landmark(lm[13])
    bottom_lip = norm_landmark(lm[14])
    mouth_opening = abs(top_lip[1] - bottom_lip[1])
    
    # Color reactivo a la apertura
    intensity = min(1.0, mouth_opening * 15)
    color = (intensity, 0.5 + 0.5 * intensity, 1)
    
    offset_z = 0.025
    mouth_offset = [(p[0], p[1], p[2] + offset_z) for p in mouth_points]
    
    # Línea de boca con brillo
    draw_glowing_line(mouth_offset, color, width=3.0, glow_intensity=0.7 + 0.3 * intensity)
    
    # Líneas de energía vertical cuando la boca se abre
    if mouth_opening > 0.02:
        left_corner = mouth_offset[0]
        right_corner = mouth_offset[10]
        
        glDisable(GL_LIGHTING)
        for i in range(3):
            t = i / 3.0
            px = left_corner[0] * (1 - t) + right_corner[0] * t
            py_top = top_lip[1]
            py_bottom = bottom_lip[1]
            pz = left_corner[2]
            
            glLineWidth(1.5)
            alpha = 0.4 + 0.2 * math.sin(animation_time * 6 + i)
            glColor4f(0, 1, 1, alpha)
            glBegin(GL_LINES)
            glVertex3f(px, py_top, pz)
            glVertex3f(px, py_bottom, pz)
            glEnd()
        glEnable(GL_LIGHTING)

def draw_data_particles(lm):
    """Dibuja partículas de datos flotantes alrededor de la cara"""
    global animation_time
    
    # Centro de la cara
    nose = norm_landmark(lm[1])
    
    glDisable(GL_LIGHTING)
    glPointSize(4.0)
    
    # Generar partículas orbitantes
    num_particles = 15
    for i in range(num_particles):
        angle = (animation_time * 1.5 + i * 2 * math.pi / num_particles)
        radius = 0.15 + 0.03 * math.sin(animation_time * 2 + i)
        height = 0.1 * math.sin(animation_time * 3 + i)
        
        px = nose[0] + radius * math.cos(angle)
        py = nose[1] + height
        pz = nose[2] + radius * math.sin(angle) * 0.2
        
        # Color cian con variación
        brightness = 0.5 + 0.5 * math.sin(animation_time * 4 + i)
        glColor4f(0, brightness, 1, 0.7)
        
        glBegin(GL_POINTS)
        glVertex3f(px, py, pz)
        glEnd()
        
        # Pequeña estela
        if i % 3 == 0:
            glLineWidth(1.0)
            glColor4f(0, brightness * 0.5, 1, 0.3)
            glBegin(GL_LINES)
            glVertex3f(px, py, pz)
            trail_angle = angle - 0.3
            trail_x = nose[0] + radius * 0.9 * math.cos(trail_angle)
            trail_y = py - 0.015
            trail_z = nose[2] + radius * 0.9 * math.sin(trail_angle) * 0.2
            glVertex3f(trail_x, trail_y, trail_z)
            glEnd()
    
    glEnable(GL_LIGHTING)

def render_video_background(frame_rgb, video_tex):
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1, 0, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glBindTexture(GL_TEXTURE_2D, video_tex)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 
                 frame_rgb.shape[1], frame_rgb.shape[0],
                 0, GL_RGB, GL_UNSIGNED_BYTE, frame_rgb)
    
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

def render_cyber_filter(face_landmarks):
    """Renderiza el filtro cibernético completo"""
    global animation_time
    
    glEnable(GL_DEPTH_TEST)
    glClear(GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # Usar proyección ortográfica para mejor seguimiento
    aspect = WINDOW_WIDTH / WINDOW_HEIGHT
    glOrtho(-0.5 * aspect, 0.5 * aspect, -0.5, 0.5, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    setup_lights()
    
    lm = face_landmarks.landmark
    
    # 1. Contorno de circuitos en el rostro
    draw_circuit_pattern(lm, CARA, offset_z=0.02, color=(0, 1, 1))
    
    # 2. Visor holográfico
    draw_holographic_visor(lm)
    
    # 3. Ojos cibernéticos con escaneo
    draw_cyber_eye(lm, OJO_IZQUIERDO, is_left=True)
    draw_cyber_eye(lm, OJO_DERECHO, is_left=False)
    
    # 4. Cejas con circuitos
    draw_circuit_pattern(lm, CEJA_IZQUIERDA, offset_z=0.025, color=(0, 0.8, 1))
    draw_circuit_pattern(lm, CEJAS_DERECHA, offset_z=0.025, color=(0, 0.8, 1))
    
    # 5. Boca cibernética reactiva
    draw_cyber_mouth(lm)
    
    # 6. Partículas de datos flotantes
    draw_data_particles(lm)
    
    # Restaurar matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def main():
    global animation_time
    
    try:
        window = init_glfw()
    except Exception as e:
        print(f"Error al inicializar GLFW: {e}")
        return
    
    setup_opengl()
    video_tex = create_video_texture()
    
    mp_face = mp.solutions.face_mesh
    face_mesh = mp_face.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se pudo abrir la cámara")
        glfw.terminate()
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)
    print("Cámara inicializada - Filtro Cibernético AR activado")
    print("Presiona ESC para salir")
    
    frame_count = 0
    fps_timer = glfw.get_time()
    start_time = glfw.get_time()
    
    try:
        while not glfw.window_should_close(window):
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = face_mesh.process(frame_rgb)
            
            # Actualizar tiempo de animación
            animation_time = glfw.get_time() - start_time
            
            glfw.poll_events()
            
            if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
                break
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            render_video_background(frame_rgb, video_tex)
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    render_cyber_filter(face_landmarks)
            
            glfw.swap_buffers(window)
            
            frame_count += 1
            current_time = glfw.get_time()
            if current_time - fps_timer >= 1.0:
                fps = frame_count / (current_time - fps_timer)
                glfw.set_window_title(window, f"{WINDOW_TITLE} - FPS: {fps:.1f}")
                frame_count = 0
                fps_timer = current_time
    
    except Exception as e:
        print(f"Error en el loop principal: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nCerrando aplicación...")
        cap.release()
        face_mesh.close()
        glfw.terminate()

if __name__ == "__main__":
    main()