import fitz  # PyMuPDF
import os
import sys
from PIL import Image
import io


# ============================================================
# CONFIGURACIÓN
# ============================================================

# Resolución utilizada para analizar las páginas.
# 100-150 DPI suele ser suficiente para detectar contenido.
DPI = 120

# Umbral de blanco.
#
# Un píxel con valor >= 245 se considera prácticamente blanco.
#
# 255 = blanco puro
# 245 = blanco casi puro
# 230 = gris muy claro
#
# Si el escaneo tiene mucho ruido, podemos aumentar/disminuir
# este valor posteriormente.
UMBRAL_BLANCO = 245

# Porcentaje mínimo de píxeles NO blancos para considerar
# que una página tiene contenido.
#
# Ejemplo:
#
# 0.05 = 0.05%
# 0.10 = 0.10%
# 0.50 = 0.50%
#
# Empezamos con un valor bastante pequeño para evitar eliminar
# páginas que tengan texto pequeño o firmas.
PORCENTAJE_MINIMO_CONTENIDO = 0.10


# ============================================================
# ANALIZAR UNA PÁGINA
# ============================================================

def analizar_pagina(pagina):
    """
    Convierte una página PDF en imagen y analiza sus píxeles.

    Retorna:
        porcentaje_contenido
        tiene_contenido
    """

    # Obtener matriz de píxeles de la página
    zoom = DPI / 72

    matriz = fitz.Matrix(zoom, zoom)

    pix = pagina.get_pixmap(
        matrix=matriz,
        colorspace=fitz.csGRAY,
        alpha=False
    )

    # Convertir los datos del PDF a imagen PIL
    imagen = Image.open(
        io.BytesIO(pix.tobytes("png"))
    )

    # Asegurar escala de grises
    imagen = imagen.convert("L")

    # Obtener los píxeles
    pixeles = list(imagen.getdata())

    total_pixeles = len(pixeles)

    # Contar píxeles que NO son blancos
    pixeles_contenido = sum(
        1
        for pixel in pixeles
        if pixel < UMBRAL_BLANCO
    )

    # Calcular porcentaje
    porcentaje_contenido = (
        pixeles_contenido / total_pixeles
    ) * 100

    tiene_contenido = (
        porcentaje_contenido >= PORCENTAJE_MINIMO_CONTENIDO
    )

    return porcentaje_contenido, tiene_contenido


# ============================================================
# PROCESAR PDF
# ============================================================

def procesar_pdf(pdf_entrada, pdf_salida):

    if not os.path.exists(pdf_entrada):

        print()
        print("ERROR: No se encontró el archivo.")
        print(pdf_entrada)
        return False

    try:
        documento = fitz.open(pdf_entrada)

    except Exception as e:

        print()
        print("ERROR: No se pudo abrir el PDF.")
        print(e)
        return False

    paginas_contenido = []
    paginas_vacias = []

    print()
    print("=" * 70)
    print(" ANALIZADOR DE PDF ESCANEADO")
    print("=" * 70)
    print()
    print(f"Archivo: {os.path.basename(pdf_entrada)}")
    print(f"Total de páginas: {len(documento)}")
    print()
    print(
        f"Resolución de análisis: {DPI} DPI"
    )
    print(
        f"Umbral de blanco: {UMBRAL_BLANCO}"
    )
    print(
        f"Contenido mínimo: {PORCENTAJE_MINIMO_CONTENIDO}%"
    )
    print()
    print("-" * 70)

    # ========================================================
    # ANALIZAR CADA PÁGINA
    # ========================================================

    for numero, pagina in enumerate(documento, start=1):

        porcentaje, tiene_contenido = analizar_pagina(
            pagina
        )

        if tiene_contenido:

            paginas_contenido.append(numero - 1)

            print(
                f"[CONSERVAR] Página {numero:4d} | "
                f"Contenido detectado: "
                f"{porcentaje:.4f}%"
            )

        else:

            paginas_vacias.append(numero - 1)

            print(
                f"[ELIMINAR ] Página {numero:4d} | "
                f"Contenido detectado: "
                f"{porcentaje:.4f}%"
            )

    print()
    print("-" * 70)

    print(
        f"Páginas conservadas : {len(paginas_contenido)}"
    )

    print(
        f"Páginas eliminadas  : {len(paginas_vacias)}"
    )

    print("-" * 70)

    # ========================================================
    # SI NO HAY PÁGINAS CON CONTENIDO
    # ========================================================

    if not paginas_contenido:

        print()
        print(
            "ADVERTENCIA: No se detectó contenido "
            "en ninguna página."
        )

        documento.close()

        return False

    # ========================================================
    # CREAR NUEVO PDF
    # ========================================================

    try:

        nuevo_documento = fitz.open()

        for numero_pagina in paginas_contenido:

            nuevo_documento.insert_pdf(
                documento,
                from_page=numero_pagina,
                to_page=numero_pagina
            )

        nuevo_documento.save(
            pdf_salida,
            garbage=4,
            deflate=True
        )

        nuevo_documento.close()
        documento.close()

    except Exception as e:

        documento.close()

        print()
        print(
            "ERROR: No se pudo generar el PDF."
        )

        print(e)

        return False

    # ========================================================
    # RESULTADO
    # ========================================================

    print()
    print("=" * 70)
    print(" PROCESO COMPLETADO")
    print("=" * 70)
    print()

    print(
        f"PDF generado:"
    )

    print(pdf_salida)

    print()

    print(
        f"Páginas originales : "
        f"{len(paginas_contenido) + len(paginas_vacias)}"
    )

    print(
        f"Páginas conservadas: "
        f"{len(paginas_contenido)}"
    )

    print(
        f"Páginas eliminadas : "
        f"{len(paginas_vacias)}"
    )

    print()
    print("=" * 70)

    return True


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 70)
    print(" ELIMINADOR DE HOJAS BLANCAS - PDF ESCANEADO")
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Si se proporciona el PDF como argumento:
    #
    # python eliminar_paginas_vacias.py documento.pdf
    # --------------------------------------------------------

    if len(sys.argv) > 1:

        pdf_entrada = sys.argv[1]

    else:

        pdf_entrada = input(
            "Ingrese la ruta completa del archivo PDF:\n> "
        ).strip().strip('"')

    # --------------------------------------------------------
    # Validar extensión
    # --------------------------------------------------------

    if not pdf_entrada.lower().endswith(".pdf"):

        print()
        print(
            "ERROR: El archivo seleccionado "
            "no tiene extensión PDF."
        )

        input(
            "\nPresione ENTER para salir..."
        )

        return

    # --------------------------------------------------------
    # Generar nombre de salida
    # --------------------------------------------------------

    carpeta = os.path.dirname(
        os.path.abspath(pdf_entrada)
    )

    nombre = os.path.splitext(
        os.path.basename(pdf_entrada)
    )[0]

    pdf_salida = os.path.join(
        carpeta,
        f"{nombre}_sin_paginas_vacias.pdf"
    )

    # --------------------------------------------------------
    # Procesar
    # --------------------------------------------------------

    resultado = procesar_pdf(
        pdf_entrada,
        pdf_salida
    )

    print()

    if resultado:

        print(
            "El nuevo PDF se generó correctamente."
        )

        print()
        print(
            "Ubicación:"
        )

        print(pdf_salida)

    else:

        print(
            "No fue posible completar el proceso."
        )

    print()

    input(
        "Presione ENTER para salir..."
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()