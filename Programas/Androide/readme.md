# Centroide en tiempo real 

## Explicación
```python
cap = cv2.VideoCapture(0)
````
Inicializar la cámara
```python
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
```
- Convertir a escala de grises
- Aplicar desenfoque para reducir ruido