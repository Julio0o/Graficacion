import cv2
import numpy as np
import math


class PinturaVirtual:
    def __init__(self, color_hsv_bajo, color_hsv_alto, ancho=640, alto=480):

        self.color_hsv_bajo = np.array(color_hsv_bajo)
        self.color_hsv_alto = np.array(color_hsv_alto)

        # lienzo
        self.lienzo = np.ones((alto, ancho, 3), dtype=np.uint8) * 255

        # trazo
        self.punto_anterior = None
        self.dibujando = False

        # Configuracion del trazo
        self.color_trazo = (0, 0, 255)  # Rojo en BGR
        self.grosor_trazo = 5

        # ===== NUEVAS VARIABLES PARA MODO FIGURAS =====
        self.modo_figuras = False  # Alternar entre dibujo libre y figuras
        self.tipo_figura = 'circulo'  # 'circulo', 'rectangulo', 'triangulo', 'linea'
        self.tamanio_figura = 50  # Tamaño base de la figura
        self.angulo_figura = 0  # Ángulo de rotación en grados
        self.figura_fija = False  # Si True, la figura se "pega" al lienzo

        # Variables para controlar escalamiento y rotación
        self.punto_referencia = None  # Punto de referencia para calcular vectores
        self.distancia_inicial = None

    def detectar_landmark(self, frame):
        # BGR a HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # mascara del color
        mascara = cv2.inRange(hsv, self.color_hsv_bajo, self.color_hsv_alto)

        # limpia el ruido
        kernel = np.ones((5, 5), np.uint8)
        mascara = cv2.erode(mascara, kernel, iterations=1)
        mascara = cv2.dilate(mascara, kernel, iterations=2)

        # Encontrar contornos
        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)

        if contornos:
            # contorno mas grande
            contorno_max = max(contornos, key=cv2.contourArea)

            # checa si es suficiente el tamaño
            if cv2.contourArea(contorno_max) > 500:
                # centroide
                M = cv2.moments(contorno_max)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)

        return None

    def dibujar_trazo(self, punto_actual):
        """
        Dibuja una línea desde el punto anterior hasta el punto actual
        Args:
        punto actual: tuple (x, y) de la posición actual
        """
        if self.punto_anterior is not None and self.dibujando:
            # Dibujar linea en el lienzo
            cv2.line(self.lienzo, self.punto_anterior, punto_actual,
                     self.color_trazo, self.grosor_trazo)

        self.punto_anterior = punto_actual

    def calcular_escalamiento_rotacion(self, punto_actual):
        """
        Calcula el escalamiento y rotación basado en el movimiento del landmark
        """
        if self.punto_referencia is None:
            self.punto_referencia = punto_actual
            self.distancia_inicial = self.tamanio_figura
            return self.tamanio_figura, self.angulo_figura

        # Calcular vector de movimiento
        dx = punto_actual[0] - self.punto_referencia[0]
        dy = punto_actual[1] - self.punto_referencia[1]

        # Escalamiento basado en la distancia desde el punto de referencia
        distancia = math.sqrt(dx ** 2 + dy ** 2)
        factor_escala = 1 + (distancia / 100)  # Ajustar sensibilidad
        tamanio = int(self.tamanio_figura * factor_escala)
        tamanio = max(10, min(tamanio, 200))  # Limitar tamaño

        # Rotación basada en el ángulo del vector
        if dx != 0 or dy != 0:
            angulo = math.degrees(math.atan2(dy, dx))
        else:
            angulo = self.angulo_figura

        return tamanio, angulo

    def dibujar_figura(self, lienzo, punto, tamanio, angulo):
        """
        Dibuja la figura geométrica seleccionada en el lienzo
        """
        x, y = punto

        if self.tipo_figura == 'circulo':
            cv2.circle(lienzo, (x, y), tamanio, self.color_trazo, -1)

        elif self.tipo_figura == 'rectangulo':
            # Calcular puntos del rectángulo
            mitad = tamanio // 2
            pts = np.array([
                [-mitad, -mitad],
                [mitad, -mitad],
                [mitad, mitad],
                [-mitad, mitad]
            ], dtype=np.float32)

            # Aplicar rotación
            rad = math.radians(angulo)
            matriz_rot = np.array([
                [math.cos(rad), -math.sin(rad)],
                [math.sin(rad), math.cos(rad)]
            ])
            pts_rot = pts @ matriz_rot.T

            # Trasladar al punto
            pts_final = pts_rot + np.array([x, y])
            pts_final = pts_final.astype(np.int32)

            cv2.fillPoly(lienzo, [pts_final], self.color_trazo)

        elif self.tipo_figura == 'triangulo':
            # Triángulo equilátero
            altura = int(tamanio * math.sqrt(3) / 2)
            pts = np.array([
                [0, -altura * 2 // 3],
                [-tamanio, altura // 3],
                [tamanio, altura // 3]
            ], dtype=np.float32)

            # Aplicar rotación
            rad = math.radians(angulo)
            matriz_rot = np.array([
                [math.cos(rad), -math.sin(rad)],
                [math.sin(rad), math.cos(rad)]
            ])
            pts_rot = pts @ matriz_rot.T

            # Trasladar al punto
            pts_final = pts_rot + np.array([x, y])
            pts_final = pts_final.astype(np.int32)

            cv2.fillPoly(lienzo, [pts_final], self.color_trazo)

        elif self.tipo_figura == 'linea':
            # Línea desde el punto de referencia hasta el punto actual
            if self.punto_referencia is not None:
                cv2.line(lienzo, self.punto_referencia, punto,
                         self.color_trazo, self.grosor_trazo)

    def dibujar_figura_preview(self, frame, punto, tamanio, angulo):
        """
        Dibuja un preview de la figura en el frame de la cámara
        """
        # Crear una copia temporal para el preview
        overlay = frame.copy()
        self.dibujar_figura(overlay, punto, tamanio, angulo)
        # Mezclar con transparencia
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    def limpiar_lienzo(self):
        """Limpia el lienzo completamente"""
        self.lienzo.fill(255)
        self.punto_anterior = None
        self.punto_referencia = None

    def cambiar_color_trazo(self, color_bgr):
        """Cambia el color del trazo (formato BGR)"""
        self.color_trazo = color_bgr

    def cambiar_grosor(self, grosor):
        """Cambia el grosor del trazo"""
        self.grosor_trazo = grosor

    def ejecutar(self):
        """Loop principal de captura y procesamiento"""
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: No se pudo abrir la cámara")
            return

        # Configurar resolución de la cámara para que coincida con el lienzo
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.lienzo.shape[1])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.lienzo.shape[0])

        print("=" * 60)
        print("CONTROLES GENERALES:")
        print("  ESPACIO - Alternar dibujo ON/OFF")
        print("  M - Cambiar modo (Dibujo Libre / Figuras Geométricas)")
        print("  C - Limpiar lienzo")
        print("  R - Color rojo")
        print("  G - Color verde")
        print("  B - Color azul")
        print("  Q - Salir")
        print()
        print("MODO DIBUJO LIBRE:")
        print("  + - Aumentar grosor")
        print("  - - Disminuir grosor")
        print()
        print("MODO FIGURAS GEOMÉTRICAS:")
        print("  1 - Círculo")
        print("  2 - Rectángulo")
        print("  3 - Triángulo")
        print("  4 - Línea")
        print("  [ - Disminuir tamaño base")
        print("  ] - Aumentar tamaño base")
        print("  F - Fijar figura al lienzo (pegar)")
        print("  Z - Resetear punto de referencia (escala/rotación)")
        print("=" * 60)

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error al capturar frame")
                break

            # Voltear horizontalmente para efecto espejo
            frame = cv2.flip(frame, 1)

            # Redimensionar frame para que coincida con el lienzo
            frame = cv2.resize(frame, (self.lienzo.shape[1], self.lienzo.shape[0]))

            # Detectar el landmark (objeto de color)
            punto = self.detectar_landmark(frame)

            if punto is not None:
                # Dibujar círculo indicador en el video
                cv2.circle(frame, punto, 10, (0, 255, 0), -1)

                if self.modo_figuras:
                    # ===== MODO FIGURAS =====
                    tamanio, angulo = self.calcular_escalamiento_rotacion(punto)

                    # Dibujar preview en el frame
                    self.dibujar_figura_preview(frame, punto, tamanio, angulo)

                    # Si está dibujando, fijar la figura al lienzo
                    if self.figura_fija:
                        self.dibujar_figura(self.lienzo, punto, tamanio, angulo)
                        self.figura_fija = False
                        self.punto_referencia = None

                    # Información en pantalla
                    modo_texto = f"MODO: FIGURAS - {self.tipo_figura.upper()}"
                    cv2.putText(frame, modo_texto, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                    cv2.putText(frame, f"Tamaño: {tamanio} | Ángulo: {int(angulo)}°", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                else:
                    # ===== MODO DIBUJO LIBRE =====
                    if self.dibujando:
                        self.dibujar_trazo(punto)
                        cv2.putText(frame, "MODO: DIBUJO LIBRE - DIBUJANDO", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else:
                        self.punto_anterior = punto
                        cv2.putText(frame, "MODO: DIBUJO LIBRE - PAUSADO", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                # Si no se detecta, resetear punto anterior
                self.punto_anterior = None
                self.punto_referencia = None
                cv2.putText(frame, "NO DETECTADO", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # ventanas separadas
            cv2.imshow("Camara", frame)
            cv2.imshow("Lienzo Virtual", self.lienzo)

            # Botones
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord(' '):
                self.dibujando = not self.dibujando
                print(f"Dibujo: {'ON' if self.dibujando else 'OFF'}")
            elif key == ord('m'):
                self.modo_figuras = not self.modo_figuras
                self.punto_referencia = None
                modo = "FIGURAS GEOMÉTRICAS" if self.modo_figuras else "DIBUJO LIBRE"
                print(f"Modo cambiado a: {modo}")
            elif key == ord('c'):
                self.limpiar_lienzo()
                print("Lienzo limpiado")
            elif key == ord('r'):
                self.cambiar_color_trazo((0, 0, 255))
                print("Color: ROJO")
            elif key == ord('g'):
                self.cambiar_color_trazo((0, 255, 0))
                print("Color: VERDE")
            elif key == ord('b'):
                self.cambiar_color_trazo((255, 0, 0))
                print("Color: AZUL")

            # Controles específicos del modo
            if self.modo_figuras:
                # Controles de figuras
                if key == ord('1'):
                    self.tipo_figura = 'circulo'
                    print("Figura: CÍRCULO")
                elif key == ord('2'):
                    self.tipo_figura = 'rectangulo'
                    print("Figura: RECTÁNGULO")
                elif key == ord('3'):
                    self.tipo_figura = 'triangulo'
                    print("Figura: TRIÁNGULO")
                elif key == ord('4'):
                    self.tipo_figura = 'linea'
                    print("Figura: LÍNEA")
                elif key == ord('['):
                    self.tamanio_figura = max(self.tamanio_figura - 10, 10)
                    print(f"Tamaño base: {self.tamanio_figura}")
                elif key == ord(']'):
                    self.tamanio_figura = min(self.tamanio_figura + 10, 150)
                    print(f"Tamaño base: {self.tamanio_figura}")
                elif key == ord('f'):
                    self.figura_fija = True
                    print("Figura fijada al lienzo")
                elif key == ord('z'):
                    self.punto_referencia = None
                    print("Punto de referencia reseteado")
            else:
                # Controles de dibujo libre
                if key == ord('+') or key == ord('='):
                    self.grosor_trazo = min(self.grosor_trazo + 2, 30)
                    print(f"Grosor: {self.grosor_trazo}")
                elif key == ord('-'):
                    self.grosor_trazo = max(self.grosor_trazo - 2, 1)
                    print(f"Grosor: {self.grosor_trazo}")

        cap.release()
        cv2.destroyAllWindows()


# Ejemplo de uso
if __name__ == "__main__":
    #  AZUL:
    color_bajo = (100, 50, 50)
    color_alto = (130, 255, 255)

    #  VERDE:
    # color_bajo = (40, 50, 50)
    # color_alto = (80, 255, 255)

    # ROJO a naranja:
    # color_bajo = (0, 50, 50)
    # color_alto = (10, 255, 255)

    # ROJO a violeta:
    # color_bajo = (170, 50, 50)
    # color_alto = (180, 255, 255)

    pintura = PinturaVirtual(color_bajo, color_alto, ancho=640, alto=480)
    pintura.ejecutar()