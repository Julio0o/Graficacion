# Pintura Virtual con OpenCV

## Descripción

Este proyecto implementa un sistema de pintura virtual interactiva utilizando Python y OpenCV. El usuario controla el dibujo mediante la detección de un objeto de color en tiempo real, permitiendo tanto dibujo libre como la creación de figuras geométricas con soporte de escalamiento y rotación.

El sistema está diseñado con un enfoque modular, encapsulando toda la lógica dentro de una clase principal para facilitar su comprensión, mantenimiento y reutilización.

---

## Imports

* Python 3
* OpenCV (cv2)
* NumPy
* Biblioteca estándar math

---


## Detección por color (HSV)

El sistema detecta un objeto específico utilizando un rango de color en el espacio HSV. Este enfoque es más robusto que RGB frente a cambios de iluminación.

Ejemplo de configuración para detección de color azul:

```python
color_bajo = (100, 50, 50)
color_alto = (130, 255, 255)
```

---

## Estructura y explicación técnica del código

### Importaciones

```python
import cv2
import numpy as np
import math
```

* cv2: captura de video, procesamiento de imágenes y dibujo de primitivas.
* numpy: creación y manipulación del lienzo como matriz de píxeles.
* math: cálculos matemáticos para distancia, ángulos y rotaciones.

---

### Clase Pintura Virtual

```python
class PinturaVirtual:
```

La clase encapsula todo el comportamiento del sistema: captura de video, detección, dibujo, manejo de estados y control por teclado.

---

### Constructor (**init**)

Inicializa los parámetros principales del sistema:

* Rango de color HSV para la detección
* Lienzo de dibujo como una imagen blanca
* Variables de estado para dibujo libre
* Configuración del trazo (color y grosor)
* Variables de control para figuras geométricas
* Variables auxiliares para escalamiento y rotación

Ejemplo:

```python
self.lienzo = np.ones((alto, ancho, 3), dtype=np.uint8) * 255
```

Crea un lienzo blanco donde los dibujos se almacenan de forma permanente.

---

### Detección del objeto (detectar_landmark)

Este método localiza el objeto de color dentro del frame capturado por la cámara.

Flujo de procesamiento:

1. Conversión del frame de BGR a HSV
2. Creación de una máscara binaria por rango de color
3. Eliminación de ruido mediante erosión y dilatación
4. Detección de contornos
5. Selección del contorno de mayor área
6. Cálculo del centroide usando momentos

El método retorna una tupla (x, y) con la posición del objeto o None si no se detecta.

---

### Dibujo libre (dibujar_trazo)

Este método implementa el dibujo continuo uniendo el punto anterior con el punto actual detectado:

```python
cv2.line(self.lienzo, self.punto_anterior, punto_actual, self.color_trazo, self.grosor_trazo)
```

El dibujo se realiza directamente sobre el lienzo, por lo que el trazo permanece visible.

---

### Escalamiento y rotación (calcular_escalamiento_rotacion)

Calcula dinámicamente el tamaño y la orientación de una figura geométrica basándose en el movimiento del objeto detectado.

* La distancia euclidiana controla el factor de escala
* El ángulo del vector de desplazamiento controla la rotación

```python
angulo = math.degrees(math.atan2(dy, dx))
```

---

### Dibujo de figuras geométricas (dibujar_figura)

Dibuja la figura seleccionada según el modo activo:

* Círculo: cv2.circle
* Rectángulo: cálculo de vértices + matriz de rotación 2D
* Triángulo: geometría básica + rotación
* Línea: unión entre puntos de referencia

Las rotaciones se aplican mediante una matriz de rotación bidimensional.

---

### Previsualización de figuras (dibujar_figura_preview)

Permite mostrar una figura de manera temporal y semitransparente sobre el frame de la cámara antes de fijarla al lienzo.

```python
cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
```

---

### Limpieza y configuración

* limpiar_lienzo(): reinicia el lienzo a color blanco
* cambiar_color_trazo(): modifica el color del trazo
* cambiar_grosor(): ajusta el grosor de la línea

---

### Loop principal (ejecutar)

Este método contiene el ciclo principal del programa.

Responsabilidades:

* Captura continua de frames desde la cámara
* Detección del objeto de color
* Actualización del lienzo según el modo activo
* Renderizado de ventanas
* Gestión de eventos del teclado

El loop finaliza cuando el usuario presiona la tecla Q.

---

### Control por teclado

El teclado permite:

* Alternar entre dibujo libre y modo figuras
* Seleccionar el tipo de figura
* Modificar tamaño, color y grosor
* Fijar figuras al lienzo
* Limpiar el lienzo y finalizar la ejecución

---

### Punto de entrada del programa

```python
if __name__ == "__main__":
```

Define el flujo de ejecución:

1. Configuración del rango de color
2. Instanciación de la clase PinturaVirtual
3. Ejecución del método principal ejecutar()

# Evidencia y guia de uso
El programa detecta distintiso tipos de:
- Azul (de oscuro a claros)
- Verdes 
- Rojos (rojo a narajna)
- rojo (rojo a violeta)
![azul](azul.png)
--- 
como se ve en la imagen utlizo un color azul que detecta el programa, saca su centroide (su punto ma ancho) y de ahi comienza a escribir 

![rojo](rojo.png)
mismo caso con el color azul 

# Uso de la figura geometricas
para ese ejemplo utilice el color azul (sirve para los demas colores dichos)

es cencillo, cambias el modo con la letra 'M', el programa te dira en que modo estas y dependiendo que numero elijas (entre el 1 y el 4) sera la figuras que quieras plasmar en el lienzo

![figuras](figuras_geometricas.png)
 
 como se ve en la imagen logre coocar varias piezas con controles especificos

 - cuando el programa detecte el colo y cambies el modo
 - El numero 1 sera para el circulo
 - El numero 2 para el cuadrado 
 - El numero 3 para el Rectangulo 
 
 ### Paara cambiar de colores 

 - Presiona el (R,G,B) segun sea el color que quiera
 - R = Rojo
 - G = verde
 - B = Azul 
