import cv2
import numpy as np
import mediapipe as mp


class TransformacionesManos:
    def __init__(self):
        self.cap = None
        self.imagen = None
        self.imagen_original = None
        self.modo = 'traslacion'  # 'traslacion', 'escalamiento', 'rotacion'

        # Inicializar MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

        # Variables de transformación
        self.traslacion_acum = np.array([0.0, 0.0])
        self.escala_acum = 1.0
        self.rotacion_acum = 0.0

        # Posiciones anteriores para cálculo de movimiento
        self.prev_hand_center = None
        self.prev_hand_distance = None
        self.prev_hand_angle = None

        # Gestos para control
        self.gesto_activo = False
        self.dedos_levantados = []

    def crear_primitiva(self, tipo='complejo'):
        """Crea una primitiva de dibujo"""
        self.imagen = np.ones((480, 640, 3), dtype=np.uint8) * 255

        if tipo == 'circulo':
            cv2.circle(self.imagen, (320, 240), 80, (0, 0, 255), -1)
            cv2.circle(self.imagen, (320, 240), 40, (255, 255, 255), -1)
        elif tipo == 'rectangulo':
            cv2.rectangle(self.imagen, (220, 140), (420, 340), (255, 0, 0), -1)
            cv2.rectangle(self.imagen, (260, 180), (380, 300), (0, 255, 255), -1)
        elif tipo == 'triangulo':
            pts = np.array([[320, 160], [220, 320], [420, 320]], np.int32)
            cv2.fillPoly(self.imagen, [pts], (0, 255, 0))
        elif tipo == 'estrella':
            self.dibujar_estrella()
        elif tipo == 'complejo':
            # Cara feliz
            cv2.circle(self.imagen, (320, 240), 100, (255, 200, 0), -1)
            cv2.circle(self.imagen, (280, 210), 15, (0, 0, 0), -1)
            cv2.circle(self.imagen, (360, 210), 15, (0, 0, 0), -1)
            cv2.ellipse(self.imagen, (320, 260), (50, 30), 0, 0, 180, (0, 0, 0), 3)

        self.imagen_original = self.imagen.copy()

    def dibujar_estrella(self):
        """Dibuja una estrella de 5 puntas"""
        center = (320, 240)
        outer_radius = 100
        inner_radius = 40
        points = []

        for i in range(10):
            angle = i * np.pi / 5 - np.pi / 2
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            points.append([x, y])

        pts = np.array(points, np.int32)
        cv2.fillPoly(self.imagen, [pts], (255, 215, 0))

    def cargar_imagen(self, ruta_imagen):
        """Carga una imagen desde archivo"""
        self.imagen = cv2.imread(ruta_imagen)
        if self.imagen is None:
            self.crear_primitiva('complejo')
        else:
            self.imagen_original = self.imagen.copy()

    def contar_dedos_levantados(self, hand_landmarks):
        """Cuenta cuántos dedos están levantados"""
        dedos = []

        # Pulgar (comparar X)
        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
            dedos.append(1)
        else:
            dedos.append(0)

        # Otros dedos (comparar Y)
        tip_ids = [8, 12, 16, 20]
        for tip_id in tip_ids:
            if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
                dedos.append(1)
            else:
                dedos.append(0)

        return dedos

    def detectar_gesto(self, hand_landmarks):
        """Detecta gestos específicos con la mano"""
        dedos = self.contar_dedos_levantados(hand_landmarks)
        num_dedos = sum(dedos)

        # Puño cerrado = 0 dedos
        if num_dedos == 0:
            return 'puno'
        # Índice levantado = 1 dedo
        elif num_dedos == 1 and dedos[1] == 1:
            return 'indice'
        # Índice y medio = 2 dedos
        elif num_dedos == 2 and dedos[1] == 1 and dedos[2] == 1:
            return 'dos_dedos'
        # Mano abierta = 5 dedos
        elif num_dedos == 5:
            return 'mano_abierta'
        # Pulgar e índice (pinza)
        elif num_dedos == 2 and dedos[0] == 1 and dedos[1] == 1:
            return 'pinza'

        return 'otro'

    def obtener_centro_mano(self, hand_landmarks, frame_shape):
        """Obtiene el centro de la palma de la mano"""
        h, w = frame_shape[:2]
        # Usar la muñeca como punto de referencia
        x = int(hand_landmarks.landmark[9].x * w)
        y = int(hand_landmarks.landmark[9].y * h)
        return np.array([x, y], dtype=np.float32)

    def obtener_puntos_clave(self, hand_landmarks, frame_shape):
        """Obtiene puntos clave de la mano (pulgar e índice)"""
        h, w = frame_shape[:2]
        punto1 = np.array([
            hand_landmarks.landmark[4].x * w,  # Punta del pulgar
            hand_landmarks.landmark[4].y * h
        ])
        punto2 = np.array([
            hand_landmarks.landmark[8].x * w,  # Punta del índice
            hand_landmarks.landmark[8].y * h
        ])
        return punto1, punto2

    def aplicar_traslacion(self, dx, dy):
        """Aplica traslación a la imagen"""
        matriz = np.float32([[1, 0, dx], [0, 1, dy]])
        h, w = self.imagen_original.shape[:2]
        self.imagen = cv2.warpAffine(self.imagen_original, matriz, (w, h))

    def aplicar_escalamiento(self, factor):
        """Aplica escalamiento a la imagen"""
        h, w = self.imagen_original.shape[:2]
        centro = (w // 2, h // 2)
        matriz = cv2.getRotationMatrix2D(centro, 0, factor)
        self.imagen = cv2.warpAffine(self.imagen_original, matriz, (w, h))

    def aplicar_rotacion(self, angulo):
        """Aplica rotación a la imagen"""
        h, w = self.imagen_original.shape[:2]
        centro = (w // 2, h // 2)
        matriz = cv2.getRotationMatrix2D(centro, angulo, 1.0)
        self.imagen = cv2.warpAffine(self.imagen_original, matriz, (w, h))

    def procesar_mano(self, hand_landmarks, frame_shape):
        """Procesa los landmarks de la mano y aplica transformaciones"""
        gesto = self.detectar_gesto(hand_landmarks)
        centro_mano = self.obtener_centro_mano(hand_landmarks, frame_shape)
        punto1, punto2 = self.obtener_puntos_clave(hand_landmarks, frame_shape)

        if self.modo == 'traslacion':
            # Usar índice levantado para trasladar
            if gesto == 'indice':
                if self.prev_hand_center is not None:
                    desplazamiento = centro_mano - self.prev_hand_center
                    self.traslacion_acum += desplazamiento * 0.5
                    self.aplicar_traslacion(self.traslacion_acum[0], self.traslacion_acum[1])
                self.prev_hand_center = centro_mano
            else:
                self.prev_hand_center = None

        elif self.modo == 'escalamiento':
            # Usar pinza (pulgar e índice) para escalar
            if gesto == 'pinza' or gesto == 'dos_dedos':
                distancia_actual = np.linalg.norm(punto2 - punto1)

                if self.prev_hand_distance is not None and self.prev_hand_distance > 0:
                    factor_cambio = distancia_actual / self.prev_hand_distance
                    # Suavizar el cambio
                    factor_cambio = 1.0 + (factor_cambio - 1.0) * 0.1
                    self.escala_acum *= factor_cambio
                    self.escala_acum = np.clip(self.escala_acum, 0.2, 5.0)
                    self.aplicar_escalamiento(self.escala_acum)

                self.prev_hand_distance = distancia_actual
            else:
                self.prev_hand_distance = None

        elif self.modo == 'rotacion':
            # Usar dos dedos para rotar
            if gesto == 'dos_dedos' or gesto == 'pinza':
                vector_actual = punto2 - punto1
                angulo_actual = np.arctan2(vector_actual[1], vector_actual[0])

                if self.prev_hand_angle is not None:
                    delta_angulo = np.degrees(angulo_actual - self.prev_hand_angle)
                    # Suavizar rotación
                    delta_angulo *= 0.3
                    self.rotacion_acum += delta_angulo
                    self.aplicar_rotacion(self.rotacion_acum)

                self.prev_hand_angle = angulo_actual
            else:
                self.prev_hand_angle = None

        return gesto

    def inicializar_camara(self):
        """Inicializa la captura de video"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: No se puede abrir la cámara")
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return True

    def dibujar_interfaz(self, frame, gesto=None):
        """Dibuja la interfaz de usuario en el frame"""
        # Fondo semitransparente para texto
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 180), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Información del modo
        color_modo = (0, 255, 0) if gesto else (255, 255, 255)
        cv2.putText(frame, f"MODO: {self.modo.upper()}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_modo, 2)

        # Instrucciones según el modo
        if self.modo == 'traslacion':
            cv2.putText(frame, "Gesto: INDICE levantado", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Pos: ({self.traslacion_acum[0]:.0f}, {self.traslacion_acum[1]:.0f})",
                        (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        elif self.modo == 'escalamiento':
            cv2.putText(frame, "Gesto: PINZA (pulgar + indice)", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Escala: {self.escala_acum:.2f}x", (20, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        elif self.modo == 'rotacion':
            cv2.putText(frame, "Gesto: DOS DEDOS (indice + medio)", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Angulo: {self.rotacion_acum:.1f} grados", (20, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Controles
        cv2.putText(frame, "Controles:", (20, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, "1:Traslacion 2:Escala 3:Rotacion", (20, 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        cv2.putText(frame, "R:Reset C:Cambiar figura Q:Salir", (20, 165),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Gesto actual detectado
        if gesto:
            cv2.putText(frame, f"Gesto: {gesto}", (20, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    def ejecutar(self):
        """Ejecuta el programa principal"""
        if not self.inicializar_camara():
            return

        print("\n=== TRANSFORMACIONES CON DETECCION DE MANOS ===")
        print("\n📋 CONTROLES:")
        print("  Tecla '1': Modo Traslación")
        print("  Tecla '2': Modo Escalamiento")
        print("  Tecla '3': Modo Rotación")
        print("  Tecla 'r': Resetear transformaciones")
        print("  Tecla 'c': Cambiar primitiva")
        print("  Tecla 'q': Salir")
        print("\n✋ GESTOS:")
        print("  TRASLACION: Dedo índice levantado")
        print("  ESCALAMIENTO: Pinza (pulgar + índice)")
        print("  ROTACION: Dos dedos (índice + medio)")
        print("=" * 50 + "\n")

        tipos_primitivas = ['complejo', 'circulo', 'rectangulo', 'triangulo', 'estrella']
        indice_primitiva = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Voltear horizontalmente para efecto espejo
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Procesar detección de manos
            results = self.hands.process(frame_rgb)

            gesto_detectado = None

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Dibujar landmarks de la mano
                    self.mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                        self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                    )

                    # Procesar la mano y aplicar transformaciones
                    gesto_detectado = self.procesar_mano(hand_landmarks, frame.shape)

            # Dibujar interfaz
            self.dibujar_interfaz(frame, gesto_detectado)

            # Mostrar ventanas
            cv2.imshow('Camara - Deteccion de Manos', frame)
            cv2.imshow('Imagen Transformada', self.imagen)

            # Manejar teclas
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('1'):
                self.modo = 'traslacion'
                self.prev_hand_center = None
                print("✓ Modo: TRASLACIÓN - Usa dedo índice")
            elif key == ord('2'):
                self.modo = 'escalamiento'
                self.prev_hand_distance = None
                print("✓ Modo: ESCALAMIENTO - Usa pinza (pulgar + índice)")
            elif key == ord('3'):
                self.modo = 'rotacion'
                self.prev_hand_angle = None
                print("✓ Modo: ROTACIÓN - Usa dos dedos (índice + medio)")
            elif key == ord('r'):
                self.traslacion_acum = np.array([0.0, 0.0])
                self.escala_acum = 1.0
                self.rotacion_acum = 0.0
                self.imagen = self.imagen_original.copy()
                print("✓ Transformaciones reseteadas")
            elif key == ord('c'):
                indice_primitiva = (indice_primitiva + 1) % len(tipos_primitivas)
                self.crear_primitiva(tipos_primitivas[indice_primitiva])
                self.traslacion_acum = np.array([0.0, 0.0])
                self.escala_acum = 1.0
                self.rotacion_acum = 0.0
                print(f"✓ Primitiva: {tipos_primitivas[indice_primitiva]}")

        # Liberar recursos
        self.cap.release()
        cv2.destroyAllWindows()
        self.hands.close()


# Uso del programa
if __name__ == "__main__":
    app = TransformacionesManos()

    # Crear primitiva inicial
    app.crear_primitiva('complejo')

    # Para cargar una imagen en su lugar:
    # app.cargar_imagen('tu_imagen.jpg')

    # Ejecutar el programa
    app.ejecutar()