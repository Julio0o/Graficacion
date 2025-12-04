import cv2

cap = cv2.VideoCapture(0)

def encontrar_centroides(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Umbralización adaptiva para mejor detección
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )

    # Encontrar contornos
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Crear una copia del frame para dibujar
    resultado = frame.copy()

    for contorno in contornos:
        # Filtrar contornos muy pequeños
        area = cv2.contourArea(contorno)
        if area > 500:  # Área mínima
            # Calcular momentos
            M = cv2.moments(contorno)

            # Calcular centroide
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Dibujar el contorno
                cv2.drawContours(resultado, [contorno], -1, (0, 255, 0), 2)

                # Dibujar el centroide
                cv2.circle(resultado, (cx, cy), 8, (255, 0, 0), -1)
                cv2.circle(resultado, (cx, cy), 3, (255, 255, 255), -1)

                # Mostrar coordenadas del centroide
                cv2.putText(
                    resultado,
                    f"({cx},{cy})",
                    (cx - 50, cy - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )

                # Mostrar área
                cv2.putText(
                    resultado,
                    f"Area: {int(area)}",
                    (cx - 50, cy + 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 255),
                    1,
                )

    return resultado, thresh


print("Presiona 'q' para salir")
print("Instrucciones: Coloca objetos frente a la cámara para detectar sus centroides")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al capturar video")
        break

    # Voltear horizontalmente para efecto espejo
    frame = cv2.flip(frame, 1)

    # Encontrar y mostrar centroides
    resultado, thresh = encontrar_centroides(frame)

    # Mostrar ventanas
    cv2.imshow("Detector de Centroides", resultado)
    cv2.imshow("Umbralización", thresh)

    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Limpiar recursos
cap.release()
cv2.destroyAllWindows()
