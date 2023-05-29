# pygeonica

Para instalarlo como paquete:
`pip install --force-reinstall --no-deps git+https://github.com/isi-ies-group/pygeonica.git`

Prueba código leer canales estación
Si no se da lista de canales los lee directamente de la BBDD
```
import pygeonica as geo
lista_canales = ['Temp. Ai 1', 'R.Directa1', 'PIRAN.1', 'PIRAN.2', 'Celula Top', 'Celula Mid', 'Celula Bot', 'Top - Cal ', 'Mid - Cal ', 'Bot - Cal ', 'Presion', 'V.Vien.1', 'D.Vien.1', 'Bateria', 'Elev.Sol', 'Orient.Sol', 'Est.Geo3K']
datos_estacion = geo.estacion.lee_canales(num_estacion=316, canales=lista_canales) # 316, 2169
```
