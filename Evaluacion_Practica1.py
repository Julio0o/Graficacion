import cv2 as cv
import os

# Usar el clasificador incluido en OpenCV
cascade_path = cv.data.haarcascades + 'haarcascade_frontalface_alt.xml'
rostro = cv.CascadeClassifier(cascade_path)

# Verificar que se cargó correctamente
if rostro.empty():
    print("Error: No se pudo cargar el clasificador")
    exit()

cap = cv.VideoCapture(0)

while True:
    ret, img = cap.read()
    if not ret:
        break

    gris = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    rostros = rostro.detectMultiScale(gris, 1.3, 5)

    for (x, y, w, h) in rostros:
        #  tamaño de los ojos basado en el rostro
        tamaño_ojo_exterior = int(w * 0.08)  # 8% del ancho del rostro
        tamaño_ojo_blanco = int(w * 0.075)  # 7.5% del ancho del rostro
        tamaño_pupila = int(w * 0.02)  # 2% del ancho del rostro

        # Rectángulo azul alrededor del rostro
        img = cv.rectangle(img, (x, y), (x + w, y + h), (234, 23, 23), 5)

        # Rectángulo verde en la mitad inferior
        img = cv.rectangle(img, (x, int(y + h / 2)), (x + w, y + h), (0, 255, 0), 5)

        # Ojo izquierdo
        img = cv.circle(img, (x + int(w * 0.3), y + int(h * 0.4)), tamaño_ojo_exterior, (0, 0, 0), 2)
        img = cv.circle(img, (x + int(w * 0.3), y + int(h * 0.4)), tamaño_ojo_blanco, (255, 255, 255), -1)
        img = cv.circle(img, (x + int(w * 0.3), y + int(h * 0.4)), tamaño_pupila, (0, 0, 255), -1)

        # Ojo derecho
        img = cv.circle(img, (x + int(w * 0.7), y + int(h * 0.4)), tamaño_ojo_exterior, (0, 0, 0), 2)
        img = cv.circle(img, (x + int(w * 0.7), y + int(h * 0.4)), tamaño_ojo_blanco, (255, 255, 255), -1)
        img = cv.circle(img, (x + int(w * 0.7), y + int(h * 0.4)), tamaño_pupila, (0, 0, 255), -1)

    cv.imshow('Detección de Rostros', img)
    if cv.waitKey(1) == ord('q'):
        break

cap.release()
cv.destroyAllWindows()