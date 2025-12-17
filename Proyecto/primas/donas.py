import cv2
import numpy as np
from collections import deque

# Configuración inicial
canvas = None
current_shape = 'circle'  # 'circle', 'rectangle', 'triangle', 'line', 'star', 'hexagon'
shape_size = 50
shape_rotation = 0
rotation_speed = 5  # Grados por tecla
scale_x = 1.0  # Escala en X
scale_y = 1.0  # Escala en Y
auto_rotate = False  # Rotación automática basada en movimiento
auto_scale = False  # Escalado automático basado en velocidad
movement_history = deque(maxlen=5)
shape_color = (0, 255, 0)  # Color de las figuras
fill_shape = False  # Rellenar o solo contorno

# Detección de color rojo/verde
lower_red1 = np.array([0, 120, 70])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 120, 70])
upper_red2 = np.array([180, 255, 255])
lower_green = np.array([40, 80, 80])
upper_green = np.array([80, 255, 255])

def detect_color_landmark(frame, hsv):
    """Detecta landmark de color rojo o verde"""
    # Detección de rojo
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    
    # Detección de verde
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    
    # Combinar máscaras
    mask_combined = cv2.bitwise_or(mask_red, mask_green)
    
    # Morfología
    kernel = np.ones((5, 5), np.uint8)
    mask_combined = cv2.morphologyEx(mask_combined, cv2.MORPH_OPEN, kernel)
    mask_combined = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel)
    
    # Encontrar contorno más grande
    contours, _ = cv2.findContours(mask_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 500:
            M = cv2.moments(largest)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                return (cx, cy), mask_combined
    
    return None, mask_combined

def calculate_motion_params(current_point):
    """Calcula parámetros de movimiento para transformaciones automáticas"""
    global movement_history
    
    movement_history.append(current_point)
    
    if len(movement_history) < 2:
        return 1.0, 0.0
    
    p1 = np.array(movement_history[-1])
    p2 = np.array(movement_history[0])
    motion_vector = p1 - p2
    
    # Magnitud para escalamiento
    magnitude = np.linalg.norm(motion_vector)
    scale_factor = 1.0 + (magnitude / 150.0)
    scale_factor = np.clip(scale_factor, 0.3, 3.0)
    
    # Ángulo para rotación
    if magnitude > 5:
        angle = np.arctan2(motion_vector[1], motion_vector[0])
        rotation = np.degrees(angle)
    else:
        rotation = 0.0
    
    return scale_factor, rotation

def transform_points(pts, center, scale_x, scale_y, rotation):
    """Aplica transformaciones a un conjunto de puntos"""
    # Escalar
    pts_scaled = pts * np.array([scale_x, scale_y])
    
    # Rotar
    angle_rad = np.radians(rotation)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    pts_rotated = pts_scaled @ rotation_matrix.T
    
    # Trasladar
    pts_final = pts_rotated + np.array(center)
    
    return pts_final.astype(np.int32)

def draw_circle(canvas, center, size, scale_x, scale_y, color, thickness):
    """Dibuja círculo/elipse"""
    radius_x = int(size * scale_x)
    radius_y = int(size * scale_y)
    if fill_shape:
        cv2.ellipse(canvas, center, (radius_x, radius_y), 0, 0, 360, color, -1)
    else:
        cv2.ellipse(canvas, center, (radius_x, radius_y), 0, 0, 360, color, thickness)

def draw_rectangle(canvas, center, size, scale_x, scale_y, rotation, color, thickness):
    """Dibuja rectángulo"""
    half_w = size * scale_x
    half_h = size * scale_y
    
    pts = np.array([
        [-half_w, -half_h],
        [half_w, -half_h],
        [half_w, half_h],
        [-half_w, half_h]
    ], dtype=np.float32)
    
    pts_transformed = transform_points(pts, center, 1, 1, rotation)
    
    if fill_shape:
        cv2.fillPoly(canvas, [pts_transformed], color)
    else:
        cv2.polylines(canvas, [pts_transformed], True, color, thickness)

def draw_triangle(canvas, center, size, scale_x, scale_y, rotation, color, thickness):
    """Dibuja triángulo"""
    height = size * 1.5
    
    pts = np.array([
        [0, -height],
        [-size * 0.866, height/2],
        [size * 0.866, height/2]
    ], dtype=np.float32)
    
    pts_transformed = transform_points(pts, center, scale_x, scale_y, rotation)
    
    if fill_shape:
        cv2.fillPoly(canvas, [pts_transformed], color)
    else:
        cv2.polylines(canvas, [pts_transformed], True, color, thickness)

def draw_star(canvas, center, size, scale_x, scale_y, rotation, color, thickness):
    """Dibuja estrella de 5 puntas"""
    angles = np.linspace(0, 2*np.pi, 11, endpoint=False)
    pts = []
    
    for i, angle in enumerate(angles):
        radius = size if i % 2 == 0 else size * 0.4
        x = radius * np.cos(angle - np.pi/2)
        y = radius * np.sin(angle - np.pi/2)
        pts.append([x, y])
    
    pts = np.array(pts, dtype=np.float32)
    pts_transformed = transform_points(pts, center, scale_x, scale_y, rotation)
    
    if fill_shape:
        cv2.fillPoly(canvas, [pts_transformed], color)
    else:
        cv2.polylines(canvas, [pts_transformed], True, color, thickness)

def draw_hexagon(canvas, center, size, scale_x, scale_y, rotation, color, thickness):
    """Dibuja hexágono"""
    angles = np.linspace(0, 2*np.pi, 7, endpoint=False)
    pts = []
    
    for angle in angles:
        x = size * np.cos(angle)
        y = size * np.sin(angle)
        pts.append([x, y])
    
    pts = np.array(pts, dtype=np.float32)
    pts_transformed = transform_points(pts, center, scale_x, scale_y, rotation)
    
    if fill_shape:
        cv2.fillPoly(canvas, [pts_transformed], color)
    else:
        cv2.polylines(canvas, [pts_transformed], True, color, thickness)

def draw_line(canvas, center, size, scale_x, scale_y, rotation, color, thickness):
    """Dibuja línea"""
    length = size * 2 * scale_x
    angle_rad = np.radians(rotation)
    
    start_x = int(center[0] - length/2 * np.cos(angle_rad))
    start_y = int(center[1] - length/2 * np.sin(angle_rad))
    end_x = int(center[0] + length/2 * np.cos(angle_rad))
    end_y = int(center[1] + length/2 * np.sin(angle_rad))
    
    cv2.line(canvas, (start_x, start_y), (end_x, end_y), color, int(thickness * scale_y))

def draw_shape(canvas, center, shape_type, size, scale_x, scale_y, rotation, color):
    """Dibuja la figura seleccionada con transformaciones"""
    thickness = 2
    
    if shape_type == 'circle':
        draw_circle(canvas, center, size, scale_x, scale_y, color, thickness)
    elif shape_type == 'rectangle':
        draw_rectangle(canvas, center, size, scale_x, scale_y, rotation, color, thickness)
    elif shape_type == 'triangle':
        draw_triangle(canvas, center, size, scale_x, scale_y, rotation, color, thickness)
    elif shape_type == 'star':
        draw_star(canvas, center, size, scale_x, scale_y, rotation, color, thickness)
    elif shape_type == 'hexagon':
        draw_hexagon(canvas, center, size, scale_x, scale_y, rotation, color, thickness)
    elif shape_type == 'line':
        draw_line(canvas, center, size, scale_x, scale_y, rotation, color, thickness)

def show_ui(frame):
    """Muestra información de la UI"""
    global current_shape, shape_size, shape_rotation, scale_x, scale_y
    global auto_rotate, auto_scale, fill_shape
    
    # Título con figura actual
    cv2.putText(frame, f"FIGURA: {current_shape.upper()}", 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    # Parámetros
    y_pos = 60
    params = [
        f"Tamano: {shape_size}",
        f"Rotacion: {shape_rotation:.0f}°",
        f"Escala X: {scale_x:.2f}",
        f"Escala Y: {scale_y:.2f}",
        f"Auto-Rotar: {'ON' if auto_rotate else 'OFF'}",
        f"Auto-Escalar: {'ON' if auto_scale else 'OFF'}",
        f"Relleno: {'ON' if fill_shape else 'OFF'}"
    ]
    
    for param in params:
        cv2.putText(frame, param, (10, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_pos += 25
    
    # Instrucciones
    instructions = [
        "1-6: Figuras | Q/E: Rotar | +/-: Tamano",
        "W/S: Escala Y | A/D: Escala X | R: Reset",
        "T: Auto-Rotar | Y: Auto-Escalar | F: Relleno",
        "C: Limpiar | ESC: Salir"
    ]
    
    y_pos = frame.shape[0] - 110
    for instruction in instructions:
        cv2.putText(frame, instruction, (10, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        y_pos += 25

def main():
    global canvas, current_shape, shape_size, shape_rotation
    global scale_x, scale_y, auto_rotate, auto_scale, fill_shape
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: No se puede acceder a la cámara")
        return
    
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        canvas = np.zeros_like(frame)
    
    print("=== CONTROL DE FIGURAS GEOMÉTRICAS ===")
    print("\nFiguras:")
    print("  1: Círculo   | 2: Rectángulo | 3: Triángulo")
    print("  4: Estrella  | 5: Hexágono   | 6: Línea")
    print("\nTransformaciones:")
    print("  Q/E: Rotar ±5° | +/-: Tamaño")
    print("  W/S: Escala Y  | A/D: Escala X")
    print("  R: Reset transformaciones")
    print("\nModos Automáticos:")
    print("  T: Toggle Auto-Rotación (según movimiento)")
    print("  Y: Toggle Auto-Escalado (según velocidad)")
    print("  F: Toggle Relleno")
    print("\nGeneral:")
    print("  C: Limpiar canvas | ESC: Salir")
    print("======================================")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detectar landmark
        point, mask = detect_color_landmark(frame, hsv)
        
        if point:
            # Dibujar indicador de landmark
            cv2.circle(frame, point, 12, (255, 0, 255), 2)
            cv2.circle(frame, point, 3, (255, 255, 255), -1)
            
            # Calcular transformaciones automáticas si están activas
            final_rotation = shape_rotation
            final_scale = 1.0
            
            if auto_rotate or auto_scale:
                motion_scale, motion_rotation = calculate_motion_params(point)
                
                if auto_rotate:
                    final_rotation = motion_rotation
                
                if auto_scale:
                    final_scale = motion_scale
            else:
                movement_history.clear()
            
            # Dibujar figura con todas las transformaciones
            adjusted_size = int(shape_size * final_scale)
            final_scale_x = scale_x * (final_scale if auto_scale else 1.0)
            final_scale_y = scale_y * (final_scale if auto_scale else 1.0)
            
            draw_shape(canvas, point, current_shape, adjusted_size, 
                      final_scale_x, final_scale_y, final_rotation, shape_color)
        else:
            movement_history.clear()
        
        # Combinar frame con canvas
        result = cv2.addWeighted(frame, 0.5, canvas, 0.5, 0)
        show_ui(result)
        
        cv2.imshow('Control de Figuras Geometricas', result)
        cv2.imshow('Deteccion', mask)
        
        # Controles
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            break
        elif key == ord('c'):
            canvas = np.zeros_like(frame)
        
        # Selección de figuras
        elif key == ord('1'):
            current_shape = 'circle'
        elif key == ord('2'):
            current_shape = 'rectangle'
        elif key == ord('3'):
            current_shape = 'triangle'
        elif key == ord('4'):
            current_shape = 'star'
        elif key == ord('5'):
            current_shape = 'hexagon'
        elif key == ord('6'):
            current_shape = 'line'
        
        # Rotación manual
        elif key == ord('q'):
            shape_rotation = (shape_rotation - rotation_speed) % 360
        elif key == ord('e'):
            shape_rotation = (shape_rotation + rotation_speed) % 360
        
        # Tamaño
        elif key == ord('+') or key == ord('='):
            shape_size = min(shape_size + 5, 200)
        elif key == ord('-') or key == ord('_'):
            shape_size = max(shape_size - 5, 10)
        
        # Escala X
        elif key == ord('a'):
            scale_x = max(scale_x - 0.1, 0.1)
        elif key == ord('d'):
            scale_x = min(scale_x + 0.1, 5.0)
        
        # Escala Y
        elif key == ord('w'):
            scale_y = min(scale_y + 0.1, 5.0)
        elif key == ord('s'):
            scale_y = max(scale_y - 0.1, 0.1)
        
        # Reset transformaciones
        elif key == ord('r'):
            shape_rotation = 0
            scale_x = 1.0
            scale_y = 1.0
            shape_size = 50
            print("Transformaciones reseteadas")
        
        # Modos automáticos
        elif key == ord('t'):
            auto_rotate = not auto_rotate
            print(f"Auto-Rotación: {'ON' if auto_rotate else 'OFF'}")
        elif key == ord('y'):
            auto_scale = not auto_scale
            print(f"Auto-Escalado: {'ON' if auto_scale else 'OFF'}")
        
        # Relleno
        elif key == ord('f'):
            fill_shape = not fill_shape
            print(f"Relleno: {'ON' if fill_shape else 'OFF'}")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()