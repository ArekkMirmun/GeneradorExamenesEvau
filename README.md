# Generador de Examenes Selectividad

<p align="center">
  Crea exámenes personalizados de <b>Matematicas II</b>, <b>Matematicas Aplicadas a las Ciencias Sociales (CCSS)</b>,<b>Fisica</b> y <b>Quimica</b> en segundos.
</p>

<p align="center">
  <a href="https://arekkmirmun.github.io/GeneradorExamenesEvauMatematicas/">
    <img 
      src="https://raw.githubusercontent.com/ArekkMirmun/GeneradorExamenesEvauMatematicas/refs/heads/main/webSS.png" 
      alt="Vista previa del generador" 
      width="900">
  </a>
</p>

<p align="center">
  <a href="https://arekkmirmun.github.io/GeneradorExamenesEvauMatematicas/">
    <img 
      src="https://img.shields.io/badge/ABRIR%20GENERADOR-EXÁMENES%20EVAU%20-008080?style=for-the-badge&logo=github&logoColor=white" 
      alt="Ir al generador online" />
  </a>
</p>

Creada para el apoyo a los estudiantes a la hora de estudiar.

Soporta **Matematicas II**, **Matematicas Aplicadas a las Ciencias Sociales (CCSS)**, **Fisica** y **Quimica**, con ejercicios de convocatorias desde 2018 hasta 2025.

## Caracteristicas

- Generacion de examenes aleatorios con estructura oficial
- 3 pestañas: Matematicas, Fisica y Quimica
- Seleccion de asignatura matematica: Mat. II, Mat. CCSS, o ambas mezcladas
- Filtrado por temas con checkboxes
- Numeracion persistente de examenes (no se reinicia entre sesiones)
- Semilla opcional para resultados reproducibles
- Salida en formato A4 listo para imprimir
- Apertura automatica del PDF (1 examen) o carpeta (varios)
- 1586 ejercicios extraidos de examenes oficiales

## Estructura

```
app_publica.py                          # Aplicacion de escritorio (GUI)
motor_examenes.py                       # Motor de generacion de examenes
dividir_examenes_oficiales.py           # Extrae ejercicios de mates de examenes oficiales
dividir_examenes_oficiales_fisica.py    # Extrae ejercicios de fisica
dividir_examenes_oficiales_quimica.py   # Extrae ejercicios de quimica
organizar_examenes.py                   # Normaliza nombres de examenes oficiales
generar_plan_estudio.py                 # Genera plan de estudio diario
ejercicios/                             # Ejercicios individuales (sin soluciones)
  CII/                                  # Matematicas II (363 ejercicios)
    funciones/                           #   79 ejercicios
    integrales/                          #   93 ejercicios
    geometria/                           #   93 ejercicios
    sistemas/                            #   49 ejercicios
    matrices/                            #   43 ejercicios
  CCSS/                                  # Matematicas CCSS (374 ejercicios)
    teoria_muestras/                     #   95 ejercicios
    funciones/                           #   94 ejercicios
    probabilidad/                        #   92 ejercicios
    programacion_lineal/                 #   47 ejercicios
    matrices/                            #   43 ejercicios
  FISICA/                                # Fisica (353 ejercicios)
    campo_electrico_magnetico/           #   89 ejercicios
    campo_gravitatorio/                  #   88 ejercicios
    fisica_cuantica_nuclear/             #   88 ejercicios
    ondas/                               #   58 ejercicios
    optica_geometrica/                   #   30 ejercicios
  QUIMICA/                               # Quimica (496 ejercicios)
    estructura_atomo/                    #   76 ejercicios
    reacciones_redox/                    #   76 ejercicios
    acido_base/                          #   71 ejercicios
    equilibrio_quimico/                  #   71 ejercicios
    formulacion_quimica/                 #   54 ejercicios
    quimica_organica/                    #   49 ejercicios
    equilibrio_precipitacion/            #   46 ejercicios
    enlaces_quimicos/                    #   44 ejercicios
    energia_reacciones/                  #   9 ejercicios
Examenes/                                # Examenes oficiales completos (fuente)
examenes_generados/                      # Examenes generados (salida)
dist/                                    # Ejecutable empaquetado
```

## Uso rapido

### Descargar

Descarga el archivo ZIP desde la ultima release:

**[⬇ Descargar GeneradorExamenes.zip](https://github.com/ArekkMirmun/GeneradorExamenesEvauMatematicas/releases/latest)**

El ZIP contiene el ejecutable y la carpeta `ejercicios/` lista para usar. Descomprime y ejecuta `GeneradorExamenes_Publica.exe`.

Los ejercicios proceden de examenes oficiales de Selectividad de Andalucía, que son documentos publicos. Este repositorio no incluye soluciones ni material con copyright.
