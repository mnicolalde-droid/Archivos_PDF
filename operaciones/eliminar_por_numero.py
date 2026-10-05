import os
import fitz
from tkinter import filedialog, messagebox, simpledialog


# ============================================================
# SELECCIONAR PDF
# ============================================================

def seleccionar_pdf():

    archivo = filedialog.askopenfilename(
        title="Seleccionar archivo PDF",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    return archivo


# ============================================================
# INTERPRETAR PÁGINAS
# ============================================================

def interpretar_paginas(
    entrada,
    total_paginas
):

    entrada = entrada.replace(
        " ",
        ""
    )

    partes = entrada.split(",")

    paginas = set()

    for parte in partes:

        if not parte:
            continue

        if "-" in parte:

            extremos = parte.split("-")

            if len(extremos) != 2:

                raise ValueError(
                    f"Rango inválido: {parte}"
                )

            inicio = int(
                extremos[0]
            )

            fin = int(
                extremos[1]
            )

            if inicio > fin:

                raise ValueError(
                    f"El rango {parte} está invertido."
                )

            for numero in range(
                inicio,
                fin + 1
            ):

                if (
                    numero < 1
                    or numero > total_paginas
                ):

                    raise ValueError(
                        f"La página {numero} "
                        f"no existe."
                    )

                paginas.add(numero)

        else:

            numero = int(parte)

            if (
                numero < 1
                or numero > total_paginas
            ):

                raise ValueError(
                    f"La página {numero} "
                    f"no existe."
                )

            paginas.add(numero)

    return sorted(paginas)


# ============================================================
# ELIMINAR PÁGINAS
# ============================================================

def eliminar_por_numero():

    archivo = seleccionar_pdf()

    if not archivo:
        return

    try:

        documento = fitz.open(archivo)

        total_paginas = len(documento)

        entrada = simpledialog.askstring(
            "Eliminar páginas",
            f"El PDF tiene {total_paginas} páginas.\n\n"
            "Indique las páginas que desea eliminar.\n\n"
            "Ejemplos:\n"
            "5\n"
            "5,8,12\n"
            "5-10\n"
            "2,5,8-12,20"
        )

        if not entrada:

            documento.close()
            return

        try:

            paginas_eliminar = interpretar_paginas(
                entrada,
                total_paginas
            )

        except ValueError as error:

            documento.close()

            messagebox.showerror(
                "Entrada inválida",
                str(error)
            )

            return

        if len(paginas_eliminar) == total_paginas:

            documento.close()

            messagebox.showwarning(
                "Operación no permitida",
                "No se pueden eliminar todas "
                "las páginas del PDF."
            )

            return

        paginas_conservar = [

            numero

            for numero in range(
                1,
                total_paginas + 1
            )

            if numero not in paginas_eliminar
        ]

        confirmacion = messagebox.askyesno(
            "Confirmar operación",
            "Se eliminarán las siguientes páginas:\n\n"
            + ", ".join(
                map(
                    str,
                    paginas_eliminar
                )
            )
            + "\n\n¿Desea continuar?"
        )

        if not confirmacion:

            documento.close()
            return

        nombre, extension = os.path.splitext(
            archivo
        )

        archivo_salida = (
            f"{nombre}_paginas_eliminadas.pdf"
        )

        nuevo_documento = fitz.open()

        for numero in paginas_conservar:

            indice = numero - 1

            nuevo_documento.insert_pdf(
                documento,
                from_page=indice,
                to_page=indice
            )

        nuevo_documento.save(
            archivo_salida,
            garbage=4,
            deflate=True
        )

        nuevo_documento.close()
        documento.close()

        messagebox.showinfo(
            "Proceso terminado",
            f"PDF procesado correctamente.\n\n"
            f"Páginas originales: {total_paginas}\n"
            f"Páginas eliminadas: "
            f"{len(paginas_eliminar)}\n"
            f"Páginas restantes: "
            f"{len(paginas_conservar)}\n\n"
            f"Archivo generado:\n"
            f"{archivo_salida}"
        )

    except Exception as error:

        messagebox.showerror(
            "Error",
            f"No fue posible procesar el PDF.\n\n"
            f"{error}"
        )
