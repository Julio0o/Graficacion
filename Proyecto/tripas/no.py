import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random

# Variables de cámara controladas por teclado
camera_x, camera_y, camera_z = 0.0, 10.0, 40.0
camera_rot_x, camera_rot_y = 0.0, 0.0
move_speed = 0.5
rot_speed = 2.0

# 30 objetos móviles únicos con diferentes modelos y animaciones
mobile_objects = []
object_types = ['house', 'snowman', 'tree', 'cactus', 'well', 'lamp', 'fountain', 'bench', 
                'bush', 'rock', 'tower', 'bridge', 'windmill', 'flower', 'campfire']

for i in range(30):
    obj_type = random.choice(object_types)
    obj_x = random.uniform(-35, 35)
    obj_z = random.uniform(-35, 35)
    obj_y = 0.0
    obj_rotation = random.uniform(0, 360)
    obj_scale = random.uniform(0.7, 1.8)
    obj_speed = random.uniform(0.01, 0.06)
    obj_anim_phase = random.uniform(0, math.pi * 2)
    mobile_objects.append({
        'type': obj_type,
        'x': obj_x, 'y': obj_y, 'z': obj_z,
        'rotation': obj_rotation, 'scale': obj_scale,
        'speed': obj_speed, 'direction': random.choice([-1, 1]),
        'anim_phase': obj_anim_phase
    })

global_time = 0.0

# Funciones geométricas básicas [file:1][file:3]
def draw_cube(size=1):
    vertices = [
        [-size/2, -size/2, -size/2], [size/2, -size/2, -size/2],
        [size/2, size/2, -size/2], [-size/2, size/2, -size/2],
        [-size/2, -size/2, size/2], [size/2, -size/2, size/2],
        [size/2, size/2, size/2], [-size/2, size/2, size/2]
    ]
    faces = [[0,1,2,3], [3,2,6,7], [7,6,5,4], [4,5,1,0], [1,5,6,2], [4,0,3,7]]
    glBegin(GL_QUADS)
    for face in faces:
        for vertex in face:
            glVertex3fv(vertices[vertex])
    glEnd()

def draw_pyramid(size=1):
    glBegin(GL_TRIANGLES)
    glVertex3f(0, size/2, 0)
    glVertex3f(-size/2, -size/2, size/2)
    glVertex3f(size/2, -size/2, size/2)
    glVertex3f(0, size/2, 0)
    glVertex3f(size/2, -size/2, size/2)
    glVertex3f(size/2, -size/2, -size/2)
    glVertex3f(0, size/2, 0)
    glVertex3f(size/2, -size/2, -size/2)
    glVertex3f(-size/2, -size/2, -size/2)
    glVertex3f(0, size/2, 0)
    glVertex3f(-size/2, -size/2, -size/2)
    glVertex3f(-size/2, -size/2, size/2)
    glEnd()

def draw_sphere(radius=1, slices=16, stacks=12):
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + i / stacks)
        z0 = radius * math.sin(lat0)
        r0 = radius * math.cos(lat0)
        lat1 = math.pi * (-0.5 + (i+1) / stacks)
        z1 = radius * math.sin(lat1)
        r1 = radius * math.cos(lat1)
        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * (j / slices)
            x = math.cos(lng)
            y = math.sin(lng)
            glVertex3f(x * r0, y * r0, z0)
            glVertex3f(x * r1, y * r1, z1)
        glEnd()

def draw_cylinder(radius=0.5, height=2, slices=16):
    # Base superior
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, height/2, 0)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, height/2, z)
    glEnd()
    # Base inferior
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, -height/2, 0)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, -height/2, z)
    glEnd()
    # Laterales
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, height/2, z)
        glVertex3f(x, -height/2, z)
    glEnd()

# Modelos únicos con animaciones geométricas [file:1][file:2][file:3]
def draw_house(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    # Base pulsante
    glColor3f(0.8, 0.7, 0.5)
    pulse = 1 + 0.1 * math.sin(time * 3)
    glPushMatrix(); glScalef(1, pulse, 1); draw_cube(3); glPopMatrix()
    # Techo rotatorio
    glColor3f(0.6, 0.2, 0.1)
    glPushMatrix(); glRotatef(time * 40, 0, 1, 0); glTranslatef(0, 2.5, 0); draw_pyramid(3.5); glPopMatrix()
    glPopMatrix()

def draw_snowman(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    stretch = 1 + 0.15 * math.sin(time * 4)
    glColor3f(1, 1, 1)
    draw_sphere(1.0 * stretch, 16, 16)
    glTranslatef(0, 1.2, 0); draw_sphere(0.75 * stretch)
    glTranslatef(0, 1.0, 0); draw_sphere(0.5 * stretch)
    glColor3f(0, 0, 0)
    glPushMatrix(); glTranslatef(-0.15, 2.3, 0.4); glRotatef(time * 60, 0, 1, 0); draw_sphere(0.05); glPopMatrix()
    glPushMatrix(); glTranslatef(0.15, 2.3, 0.4); glRotatef(-time * 60, 0, 1, 0); draw_sphere(0.05); glPopMatrix()
    glPopMatrix()

def draw_tree(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.4, 0.2, 0.1)
    glRotatef(math.sin(time * 2) * 15, 0, 1, 0)
    draw_cylinder(0.3, 3, 10)
    glColor3f(0.1, 0.6, 0.1); glTranslatef(0, 2, 0)
    sway = 1.2 + 0.2 * math.sin(time * 3)
    glPushMatrix(); glScalef(sway, sway, sway); draw_sphere(1.2); glPopMatrix()
    glPopMatrix()

def draw_cactus(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.2, 0.6, 0.2)
    deform_x = 0.4 + 0.15 * math.sin(time * 2.5)
    deform_z = 0.4 + 0.15 * math.cos(time * 2.5)
    glPushMatrix(); glScalef(deform_x, 2, deform_z); draw_sphere(1); glPopMatrix()
    glTranslatef(0.5, 1.5, 0); glRotatef(45, 0, 0, 1); draw_cylinder(0.2, 1.2, 10)
    glPopMatrix()

def draw_well(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.5, 0.5, 0.5); draw_cylinder(1.2, 0.5, 20)
    glTranslatef(0, 0.5, 0); glColor3f(0.6, 0.6, 0.6); draw_cylinder(1.0, 1.0, 20)
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix(); glTranslatef(-0.8, 1, 0); draw_cylinder(0.1, 2, 8); glPopMatrix()
    glPushMatrix(); glTranslatef(0.8, 1, 0); draw_cylinder(0.1, 2, 8); glPopMatrix()
    glTranslatef(0, 2, 0); glScalef(2, 0.3, 2); draw_pyramid()
    glPopMatrix()

def draw_lamp(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.3, 0.3, 0.3); draw_cylinder(0.15, 4, 12)
    glTranslatef(0, 2, 0); glRotatef(90, 0, 0, 1); draw_cylinder(0.1, 1.5, 10)
    glTranslatef(0, 0, 1.5); glow = 0.3 + 0.2 * math.sin(time * 5); glColor3f(1, 1, 0.5 * glow)
    draw_sphere(glow, 12, 12)
    glPopMatrix()

def draw_fountain(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.6, 0.6, 0.7); draw_cylinder(2, 0.3, 20)
    glTranslatef(0, 0.3, 0); draw_cylinder(1.5, 0.3, 20)
    glColor3f(0.7, 0.7, 0.8); draw_cylinder(0.3, 2, 15)
    glTranslatef(0, 1.5, 0); glColor3f(0.5, 0.7, 0.9); draw_sphere(0.5)
    glPopMatrix()

def draw_bench(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.5, 0.3, 0.1)
    glPushMatrix(); glTranslatef(0, 0.5, 0); glScalef(2, 0.2, 0.8); draw_cube(); glPopMatrix()
    glPushMatrix(); glTranslatef(0, 1, -0.3); glScalef(2, 1, 0.2); draw_cube(); glPopMatrix()
    glPopMatrix()

def draw_bush(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.2, 0.5, 0.2)
    for i in range(5):
        angle = 2 * math.pi * i / 5
        offset_x = 0.3 * math.cos(angle)
        offset_z = 0.3 * math.sin(angle)
        glPushMatrix(); glTranslatef(offset_x, 0, offset_z)
        glScalef(1 + 0.2 * math.sin(time + i), 1, 1 + 0.2 * math.cos(time + i))
        draw_sphere(0.5); glPopMatrix()
    glPopMatrix()

def draw_rock(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.5, 0.5, 0.5)
    deform = [1 + 0.1 * math.sin(time * 1.5), 0.7 + 0.1 * math.cos(time), 1.2 + 0.15 * math.sin(time * 2)]
    glScalef(*deform); draw_sphere(0.8); glPopMatrix()

def draw_tower(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.6, 0.6, 0.6); glScalef(2, 6, 2); draw_cube()
    glTranslatef(0, 4, 0); glColor3f(0.5, 0.2, 0.1); glScalef(2.5, 1.5, 2.5); draw_pyramid()
    glPopMatrix()

def draw_bridge(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.4, 0.3, 0.2); glScalef(4, 0.2, 2); draw_cube()
    glPopMatrix()

def draw_windmill(x, y, z, rotation=0, scale=1.0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.9, 0.9, 0.9); draw_cylinder(1, 5, 12)
    glTranslatef(0, 3, 0); glColor3f(0.6, 0.3, 0.1); draw_cylinder(0.5, 1, 12)
    glTranslatef(0, 0, 1); glRotatef(rotation, 0, 0, 1)
    glColor3f(0.7, 0.7, 0.7)
    for i in range(4):
        glPushMatrix(); glRotatef(90 * i, 0, 0, 1); glTranslatef(0, 1.5, 0)
        glScalef(0.3, 3, 0.1); draw_cube(); glPopMatrix()
    glPopMatrix()

def draw_flower(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.2, 0.6, 0.2); draw_cylinder(0.05, 1, 8)
    glTranslatef(0, 0.5, 0)
    colors = [(1,0,0), (1,0.5,0), (1,1,0), (0,1,0), (0,1,1)]
    for i in range(6):
        glColor3f(*colors[i%5])
        glPushMatrix(); angle = 60 * i + time * 30
        glRotatef(angle, 0, 1, 0); glTranslatef(0, 0, 0.2)
        glScalef(1 + 0.3 * math.sin(time * 4 + i), 1, 1)
        draw_sphere(0.15); glPopMatrix()
    glPopMatrix()

def draw_campfire(x, y, z, scale=1.0, time=0):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(scale, scale, scale)
    glColor3f(0.4, 0.4, 0.4)
    for i in range(8):
        angle = 2 * math.pi * i / 8
        px = 0.8 * math.cos(angle)
        pz = 0.8 * math.sin(angle)
        glPushMatrix(); glTranslatef(px, 0, pz)
        glScalef(0.3, 0.2 + 0.1 * math.sin(time * 6 + i), 0.3); draw_cube(); glPopMatrix()
    glColor3f(1, 0.5, 0); glTranslatef(0, 0.5, 0); glScalef(0.4, 1.2, 0.4); draw_pyramid()
    glPopMatrix()

# Dibujar todos los objetos móviles
def draw_mobile_objects(time):
    for obj in mobile_objects:
        glPushMatrix()
        # Movimiento patrol
        obj['x'] += obj['speed'] * obj['direction'] * math.cos(time * 0.5)
        obj['z'] += obj['speed'] * obj['direction'] * math.sin(time * 0.5)
        if abs(obj['x']) > 35 or abs(obj['z']) > 35:
            obj['direction'] *= -1
        
        obj['rotation'] += 2
        obj['anim_phase'] += 0.1
        if obj['rotation'] > 360: obj['rotation'] = 0
        
        glTranslatef(obj['x'], obj['y'], obj['z'])
        glRotatef(obj['rotation'], 0, 1, 0)
        
        obj_type = obj['type']
        if obj_type == 'house': draw_house(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'snowman': draw_snowman(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'tree': draw_tree(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'cactus': draw_cactus(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'well': draw_well(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'lamp': draw_lamp(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'fountain': draw_fountain(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'bench': draw_bench(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'bush': draw_bush(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'rock': draw_rock(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'tower': draw_tower(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'bridge': draw_bridge(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'windmill': draw_windmill(0, 0, 0, obj['rotation'] * 3, obj['scale'])
        elif obj_type == 'flower': draw_flower(0, 0, 0, obj['scale'], obj['anim_phase'])
        elif obj_type == 'campfire': draw_campfire(0, 0, 0, obj['scale'], obj['anim_phase'])
        
        glPopMatrix()

def draw_ground():
    glColor3f(0.2, 0.4, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-60, -1, -60)
    glVertex3f(60, -1, -60)
    glVertex3f(60, -1, 60)
    glVertex3f(-60, -1, 60)
    glEnd()

def handle_camera_keys(keys):
    global camera_x, camera_y, camera_z, camera_rot_x, camera_rot_y
    
    forward_x = math.sin(math.radians(camera_rot_y))
    forward_z = -math.cos(math.radians(camera_rot_y))
    right_x = math.cos(math.radians(camera_rot_y))
    right_z = math.sin(math.radians(camera_rot_y))
    
    if keys[K_w]: camera_x += forward_x * move_speed; camera_z += forward_z * move_speed
    if keys[K_s]: camera_x -= forward_x * move_speed; camera_z -= forward_z * move_speed
    if keys[K_a]: camera_x -= right_x * move_speed; camera_z -= right_z * move_speed
    if keys[K_d]: camera_x += right_x * move_speed; camera_z += right_z * move_speed
    if keys[K_SPACE]: camera_y += move_speed
    if keys[K_LSHIFT]: camera_y -= move_speed
    if keys[K_UP]: camera_rot_x = max(-89, camera_rot_x - rot_speed)
    if keys[K_DOWN]: camera_rot_x = min(89, camera_rot_x + rot_speed)
    if keys[K_LEFT]: camera_rot_y -= rot_speed
    if keys[K_RIGHT]: camera_rot_y += rot_speed

def init_opengl(width, height):
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    glLightfv(GL_LIGHT0, GL_POSITION, [10, 20, 10, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    
    glClearColor(0.5, 0.8, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(70, width/height, 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)

def main():
    global global_time
    
    pygame.init()
    display = (1200, 800)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("CIUDAD 3D - 30 Objetos Únicos Animados")
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    init_opengl(1200, 800)
    clock = pygame.time.Clock()
    
    print("=== CONTROLES TECLADO ===")
    print("WASD: Mover cámara")
    print("Flechas: Rotar vista")
    print("ESPACIO: Subir")
    print("SHIFT: Bajar")
    print("ESC: Salir")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
        
        keys = pygame.key.get_pressed()
        handle_camera_keys(keys)
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # gluLookAt con controles de teclado
        eye_x = camera_x
        eye_y = camera_y
        eye_z = camera_z
        center_x = camera_x + math.sin(math.radians(camera_rot_y)) * 50
        center_y = camera_y - math.sin(math.radians(camera_rot_x)) * 20
        center_z = camera_z - math.cos(math.radians(camera_rot_y)) * 50
        
        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 1, 0)
        
        draw_ground()
        draw_mobile_objects(global_time)
        
        pygame.display.flip()
        clock.tick(60)
        global_time += 0.05
    
    pygame.quit()

if __name__ == "__main__":
    main()
