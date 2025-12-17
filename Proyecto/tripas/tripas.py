"""
Entorno 3D Tipo Minecraft con OpenGL
Incluye modelos diferentes y control de cámara con transformaciones geométricas
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random

# Variables globales para la cámara
camera_x, camera_y, camera_z = 0, 5, 20
camera_rot_x, camera_rot_y = 0, 0
move_speed = 0.3
mouse_sensitivity = 0.2


def init_opengl():
    """Inicializa OpenGL con configuraciones básicas"""
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # Configurar luz
    glLightfv(GL_LIGHT0, GL_POSITION, (10, 20, 10, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))

    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 800 / 600, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)


def draw_cube(size=1):
    """Dibuja un cubo usando primitivas de OpenGL"""
    vertices = [
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
    ]
    vertices = [[v[0] * size / 2, v[1] * size / 2, v[2] * size / 2] for v in vertices]

    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
        (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)
    ]

    glBegin(GL_QUADS)
    for face in faces:
        for vertex in face:
            glVertex3fv(vertices[vertex])
    glEnd()


def draw_pyramid(size=1):
    """Dibuja una pirámide"""
    glBegin(GL_TRIANGLES)
    # Frente
    glVertex3f(0, size, 0)
    glVertex3f(-size / 2, 0, size / 2)
    glVertex3f(size / 2, 0, size / 2)
    # Derecha
    glVertex3f(0, size, 0)
    glVertex3f(size / 2, 0, size / 2)
    glVertex3f(size / 2, 0, -size / 2)
    # Atrás
    glVertex3f(0, size, 0)
    glVertex3f(size / 2, 0, -size / 2)
    glVertex3f(-size / 2, 0, -size / 2)
    # Izquierda
    glVertex3f(0, size, 0)
    glVertex3f(-size / 2, 0, -size / 2)
    glVertex3f(-size / 2, 0, size / 2)
    glEnd()

    # Base
    glBegin(GL_QUADS)
    glVertex3f(-size / 2, 0, size / 2)
    glVertex3f(size / 2, 0, size / 2)
    glVertex3f(size / 2, 0, -size / 2)
    glVertex3f(-size / 2, 0, -size / 2)
    glEnd()


def draw_cylinder(radius=0.5, height=2, slices=20):
    """Dibuja un cilindro"""
    # Tapa superior
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, height / 2, 0)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, height / 2, z)
    glEnd()

    # Tapa inferior
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, -height / 2, 0)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, -height / 2, z)
    glEnd()

    # Cuerpo
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, height / 2, z)
        glVertex3f(x, -height / 2, z)
    glEnd()


def draw_sphere(radius=1, slices=20, stacks=20):
    """Dibuja una esfera"""
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + i / stacks)
        z0 = radius * math.sin(lat0)
        r0 = radius * math.cos(lat0)

        lat1 = math.pi * (-0.5 + (i + 1) / stacks)
        z1 = radius * math.sin(lat1)
        r1 = radius * math.cos(lat1)

        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * j / slices
            x = math.cos(lng)
            y = math.sin(lng)

            glVertex3f(x * r0, y * r0, z0)
            glVertex3f(x * r1, y * r1, z1)
        glEnd()


def draw_tree(x, y, z):
    """Modelo 1: Árbol con tronco y copa"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Tronco
    glColor3f(0.4, 0.2, 0.1)
    draw_cylinder(0.3, 3, 10)

    # Copa (3 esferas)
    glColor3f(0.1, 0.6, 0.1)
    glTranslatef(0, 2, 0)
    draw_sphere(1.2)
    glTranslatef(0, 0.8, 0)
    draw_sphere(1.0)
    glTranslatef(0, 0.7, 0)
    draw_sphere(0.7)

    glPopMatrix()


def draw_house(x, y, z):
    """Modelo 2: Casa con techo"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Paredes
    glColor3f(0.8, 0.7, 0.5)
    glScalef(3, 2, 3)
    draw_cube()

    # Techo
    glLoadIdentity()
    glTranslatef(x, y + 2, z)
    glColor3f(0.6, 0.2, 0.1)
    glScalef(3.5, 1.5, 3.5)
    draw_pyramid()

    # Puerta
    glLoadIdentity()
    glTranslatef(x, y - 0.5, z + 1.51)
    glColor3f(0.4, 0.2, 0.1)
    glScalef(0.8, 1.2, 0.1)
    draw_cube()

    glPopMatrix()


def draw_well(x, y, z):
    """Modelo 3: Pozo de agua"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Base circular
    glColor3f(0.5, 0.5, 0.5)
    draw_cylinder(1.2, 0.5, 20)

    # Paredes
    glTranslatef(0, 0.5, 0)
    glColor3f(0.6, 0.6, 0.6)
    draw_cylinder(1.0, 1.0, 20)

    # Postes
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(-0.8, 1, 0)
    draw_cylinder(0.1, 2, 8)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.8, 1, 0)
    draw_cylinder(0.1, 2, 8)
    glPopMatrix()

    # Techo del pozo
    glTranslatef(0, 2, 0)
    glColor3f(0.6, 0.3, 0.1)
    glScalef(2, 0.3, 2)
    draw_pyramid()

    glPopMatrix()


def draw_fence(x, y, z, length=5):
    """Modelo 4: Cerca"""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.5, 0.3, 0.1)

    for i in range(int(length)):
        glPushMatrix()
        glTranslatef(i, 0, 0)
        draw_cylinder(0.1, 1.5, 6)
        glPopMatrix()

    # Barras horizontales
    glPushMatrix()
    glTranslatef(length / 2, 0.3, 0)
    glScalef(length, 0.1, 0.1)
    draw_cube()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(length / 2, 0.7, 0)
    glScalef(length, 0.1, 0.1)
    draw_cube()
    glPopMatrix()

    glPopMatrix()


def draw_lamp(x, y, z):
    """Modelo 5: Lámpara de calle"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Poste
    glColor3f(0.3, 0.3, 0.3)
    draw_cylinder(0.15, 4, 12)

    # Brazo
    glTranslatef(0, 2, 0)
    glRotatef(90, 0, 0, 1)
    draw_cylinder(0.1, 1.5, 10)

    # Luz
    glTranslatef(0, 0, 1.5)
    glColor3f(1, 1, 0.5)
    draw_sphere(0.3, 12, 12)

    glPopMatrix()


def draw_fountain(x, y, z):
    """Modelo 6: Fuente"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Base
    glColor3f(0.6, 0.6, 0.7)
    draw_cylinder(2, 0.3, 20)

    # Nivel medio
    glTranslatef(0, 0.3, 0)
    draw_cylinder(1.5, 0.3, 20)

    # Columna central
    glColor3f(0.7, 0.7, 0.8)
    draw_cylinder(0.3, 2, 15)

    # Esfera superior
    glTranslatef(0, 1.5, 0)
    glColor3f(0.5, 0.7, 0.9)
    draw_sphere(0.5)

    glPopMatrix()


def draw_bench(x, y, z):
    """Modelo 7: Banca"""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.5, 0.3, 0.1)

    # Asiento
    glPushMatrix()
    glTranslatef(0, 0.5, 0)
    glScalef(2, 0.2, 0.8)
    draw_cube()
    glPopMatrix()

    # Respaldo
    glPushMatrix()
    glTranslatef(0, 1, -0.3)
    glScalef(2, 1, 0.2)
    draw_cube()
    glPopMatrix()

    # Patas
    for i in [-0.8, 0.8]:
        for j in [-0.3, 0.3]:
            glPushMatrix()
            glTranslatef(i, 0, j)
            draw_cylinder(0.1, 0.5, 8)
            glPopMatrix()

    glPopMatrix()


def draw_bush(x, y, z):
    """Modelo 8: Arbusto"""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.2, 0.5, 0.2)

    # Varias esferas formando el arbusto
    for i in range(5):
        angle = 2 * math.pi * i / 5
        offset_x = 0.3 * math.cos(angle)
        offset_z = 0.3 * math.sin(angle)
        glPushMatrix()
        glTranslatef(offset_x, 0, offset_z)
        draw_sphere(0.5, 12, 12)
        glPopMatrix()

    glPopMatrix()


def draw_rock(x, y, z):
    """Modelo 9: Roca"""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.5, 0.5, 0.5)
    glScalef(1, 0.7, 1.2)
    draw_sphere(0.8, 10, 8)
    glPopMatrix()


def draw_tower(x, y, z):
    """Modelo 10: Torre de vigilancia"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Base
    glColor3f(0.6, 0.6, 0.6)
    glScalef(2, 6, 2)
    draw_cube()

    # Techo
    glLoadIdentity()
    glTranslatef(x, y + 4, z)
    glColor3f(0.5, 0.2, 0.1)
    glScalef(2.5, 1.5, 2.5)
    draw_pyramid()

    glPopMatrix()


def draw_bridge(x, y, z):
    """Modelo 11: Puente pequeño"""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.4, 0.3, 0.2)

    # Plataforma
    glScalef(4, 0.2, 2)
    draw_cube()

    glPopMatrix()


def draw_windmill(x, y, z, rotation):
    """Modelo 12: Molino de viento"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Torre
    glColor3f(0.9, 0.9, 0.9)
    draw_cylinder(1, 5, 12)

    # Techo cónico
    glTranslatef(0, 3, 0)
    glColor3f(0.6, 0.3, 0.1)
    draw_cylinder(0.5, 1, 12)

    # Aspas (rotación animada)
    glTranslatef(0, 0, 1)
    glRotatef(rotation, 0, 0, 1)
    glColor3f(0.7, 0.7, 0.7)

    for i in range(4):
        glPushMatrix()
        glRotatef(90 * i, 0, 0, 1)
        glTranslatef(0, 1.5, 0)
        glScalef(0.3, 3, 0.1)
        draw_cube()
        glPopMatrix()

    glPopMatrix()


def draw_flower(x, y, z):
    """Modelo 13: Flor"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Tallo
    glColor3f(0.2, 0.6, 0.2)
    draw_cylinder(0.05, 1, 8)

    # Pétalos
    glTranslatef(0, 0.5, 0)
    colors = [(1, 0, 0), (1, 0.5, 0), (1, 1, 0), (1, 0, 1), (0.5, 0, 1)]
    color = random.choice(colors)
    glColor3f(*color)

    for i in range(6):
        glPushMatrix()
        angle = 60 * i
        glRotatef(angle, 0, 1, 0)
        glTranslatef(0, 0, 0.2)
        draw_sphere(0.15, 8, 8)
        glPopMatrix()

    # Centro
    glColor3f(1, 1, 0)
    draw_sphere(0.15, 10, 10)

    glPopMatrix()


def draw_campfire(x, y, z):
    """Modelo 14: Fogata"""
    glPushMatrix()
    glTranslatef(x, y, z)

    # Piedras alrededor
    glColor3f(0.4, 0.4, 0.4)
    for i in range(8):
        angle = 2 * math.pi * i / 8
        px = 0.8 * math.cos(angle)
        pz = 0.8 * math.sin(angle)
        glPushMatrix()
        glTranslatef(px, 0, pz)
        glScalef(0.3, 0.2, 0.3)
        draw_cube()
        glPopMatrix()

    # Leños
    glColor3f(0.3, 0.2, 0.1)
    for i in range(4):
        glPushMatrix()
        glRotatef(45 * i, 0, 1, 0)
        glTranslatef(0, 0.2, 0)
        glRotatef(90, 0, 0, 1)
        draw_cylinder(0.1, 1, 8)
        glPopMatrix()

    # Fuego (pirámide roja-amarilla)
    glTranslatef(0, 0.5, 0)
    glColor3f(1, 0.5, 0)
    draw_pyramid(0.5)

    glPopMatrix()


def draw_cactus(x, y, z):
    """Modelo 15: Cactus"""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.2, 0.6, 0.2)

    # Tronco principal
    draw_cylinder(0.3, 3, 12)

    # Brazo izquierdo
    glPushMatrix()
    glTranslatef(-0.5, 1, 0)
    glRotatef(-45, 0, 0, 1)
    draw_cylinder(0.2, 1.5, 10)
    glPopMatrix()

    # Brazo derecho
    glPushMatrix()
    glTranslatef(0.5, 1.5, 0)
    glRotatef(45, 0, 0, 1)
    draw_cylinder(0.2, 1.2, 10)
    glPopMatrix()

    glPopMatrix()


def draw_ground():
    """Dibuja el suelo"""
    glColor3f(0.3, 0.6, 0.3)
    glBegin(GL_QUADS)
    glVertex3f(-50, 0, -50)
    glVertex3f(50, 0, -50)
    glVertex3f(50, 0, 50)
    glVertex3f(-50, 0, 50)
    glEnd()


def draw_scene(rotation):
    """Dibuja toda la escena con todos los modelos"""
    draw_ground()

    # Árboles
    draw_tree(-10, 0, -10)
    draw_tree(-8, 0, -15)
    draw_tree(12, 0, -8)
    draw_tree(15, 0, -12)
    draw_tree(-15, 0, 10)

    # Casa
    draw_house(0, 1, 0)

    # Pozo
    draw_well(-8, 0, 5)

    # Cercas
    draw_fence(-15, 0, -5, 8)
    draw_fence(8, 0, 8, 6)

    # Lámparas
    draw_lamp(-5, 0, 10)
    draw_lamp(10, 0, -15)

    # Fuente
    draw_fountain(15, 0, 8)

    # Bancas
    draw_bench(-12, 0, 12)
    draw_bench(5, 0, 15)

    # Arbustos
    draw_bush(-6, 0, -8)
    draw_bush(8, 0, 12)
    draw_bush(-13, 0, 2)

    # Rocas
    draw_rock(-15, 0, -12)
    draw_rock(18, 0, 5)
    draw_rock(-10, 0, 15)

    # Torre
    draw_tower(-18, 0, -18)

    # Puente
    draw_bridge(0, 0.1, -18)

    # Molino con rotación
    draw_windmill(18, 0, -15, rotation)

    # Flores
    draw_flower(-3, 0, 8)
    draw_flower(-2, 0, 9)
    draw_flower(-4, 0, 9)
    draw_flower(12, 0, 12)
    draw_flower(13, 0, 11)

    # Fogata
    draw_campfire(6, 0, -5)

    # Cactus
    draw_cactus(20, 0, 15)
    draw_cactus(22, 0, 18)


def handle_camera(keys):
    """Maneja el movimiento de la cámara"""
    global camera_x, camera_y, camera_z, camera_rot_y

    # Calcular vectores de dirección
    forward_x = math.sin(math.radians(camera_rot_y))
    forward_z = -math.cos(math.radians(camera_rot_y))
    right_x = math.cos(math.radians(camera_rot_y))
    right_z = math.sin(math.radians(camera_rot_y))

    # Movimiento WASD
    if keys[pygame.K_w]:
        camera_x += forward_x * move_speed
        camera_z += forward_z * move_speed
    if keys[pygame.K_s]:
        camera_x -= forward_x * move_speed
        camera_z -= forward_z * move_speed
    if keys[pygame.K_a]:
        camera_x -= right_x * move_speed
        camera_z -= right_z * move_speed
    if keys[pygame.K_d]:
        camera_x += right_x * move_speed
        camera_z += right_z * move_speed

    # Movimiento vertical
    if keys[pygame.K_SPACE]:
        camera_y += move_speed
    if keys[pygame.K_LSHIFT]:
        camera_y -= move_speed


def main():
    global camera_rot_x, camera_rot_y

    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Mundo Minecraft - OpenGL")
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    init_opengl()

    clock = pygame.time.Clock()
    rotation = 0

    print("=== CONTROLES ===")
    print("WASD: Mover cámara")
    print("Mouse: Rotar vista")
    print("Espacio: Subir")
    print("Shift: Bajar")
    print("ESC: Salir")
    print("================")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEMOTION:
                camera_rot_y += event.rel[0] * mouse_sensitivity
                camera_rot_x -= event.rel[1] * mouse_sensitivity
                camera_rot_x = max(-89, min(89, camera_rot_x))

        keys = pygame.key.get_pressed()
        handle_camera(keys)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Aplicar rotación de cámara
        glRotatef(camera_rot_x, 1, 0, 0)
        glRotatef(camera_rot_y, 0, 1, 0)

        # Aplicar posición de cámara (traslación)
        glTranslatef(-camera_x, -camera_y, -camera_z)

        # Dibujar escena con rotación para el molino
        draw_scene(rotation)
        rotation += 1

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()