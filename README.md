# Generador de Examenes Selectividad (Publico)

Herramienta para generar examenes de practica de Selectividad (EvAU/EBAU) de Andalucía a partir de ejercicios oficiales.

Creada para el apoyo a los estudiantes a la hora de estudiar.

Soporta **Matematicas II** y **Matematicas Aplicadas a las Ciencias Sociales (CCSS)**, con ejercicios de convocatorias desde 2018 hasta 2025.

## Caracteristicas

- Generacion de examenes aleatorios con estructura oficial (bloques obligatorios/optativos)
- Seleccion de asignatura: Mat. II, Mat. CCSS, o ambas mezcladas
- Filtrado por temas con checkboxes
- Numeracion persistente de examenes (no se reinicia entre sesiones)
- Semilla opcional para resultados reproducibles
- Salida en formato A4 listo para imprimir
- Apertura automatica del PDF (1 examen) o carpeta (varios)
- 737 ejercicios extraidos de examenes oficiales

## Estructura

```
app_publica.py                 # Aplicacion de escritorio (GUI)
motor_examenes.py              # Motor de generacion de examenes
dividir_examenes_oficiales.py  # Extrae ejercicios de examenes oficiales completos
organizar_examenes.py          # Normaliza nombres de examenes oficiales
generar_plan_estudio.py        # Genera plan de estudio diario
ejercicios/                    # Ejercicios individuales (sin soluciones)
  CII/                         # Matematicas II (363 ejercicios)
    funciones/                 #   79 ejercicios
    integrales/                #   93 ejercicios
    geometria/                 #   93 ejercicios
    sistemas/                  #   49 ejercicios
    matrices/                  #   43 ejercicios
    distribucion/              #   3 ejercicios
    probabilidad/              #   3 ejercicios
  CCSS/                        # Matematicas CCSS (374 ejercicios)
    teoria_muestras/           #   95 ejercicios
    funciones/                 #   94 ejercicios
    probabilidad/              #   92 ejercicios
    programacion_lineal/       #   47 ejercicios
    matrices/                  #   43 ejercicios
    distribucion_binomial/     #   2 ejercicios
    sistemas/                  #   1 ejercicio
Examenes/                      # Examenes oficiales completos (fuente)
examenes_generados/            # Examenes generados (salida)
dist/                          # Ejecutable empaquetado
```

## Uso rapido

### Descargar

Descarga el archivo ZIP desde la ultima release:

**[⬇ Descargar GeneradorExamenMates.zip](https://github.com/ArekkMirmun/GeneradorExamenesEvauMatematicas/releases/download/RELEASE/GeneradorExamenMates.zip)**

El ZIP contiene el ejecutable y la carpeta `ejercicios/` lista para usar. Unzip y ejecuta `GeneradorExamenes_Publica.exe`.

Este proyecto esta licenciado bajo [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — puedes usar, compartir y adaptar libremente, siempre que sea **sin fines comerciales** y mantengas la misma licencia.

Los ejercicios proceden de examenes oficiales de Selectividad de Andalucía, que son documentos publicos. Este repositorio no incluye soluciones ni material con copyright.
