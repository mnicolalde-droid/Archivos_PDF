import tkinter as tk
from tkinter import messagebox

from operaciones.eliminar_paginas_vacias import (
    eliminar_paginas_vacias
)

from operaciones.eliminar_por_numero import (
    eliminar_por_numero
)

from operaciones.unir_pdfs import (
    unir_pdfs
)

from operaciones.numerar_pdf import (
    numerar_pdf
)


# ============================================================
# SALIR
# ============================================================

def salir():

    respuesta = messagebox.askyesno(
        "Salir",
        "¿Desea cerrar la aplicación?"
    )

    if respuesta:

        ventana_principal.destroy()


# ============================================================
# VENTANA PRINCIPAL
# ============================================================

ventana_principal = tk.Tk()

ventana_principal.title(
    "Herramientas para PDF"
)

ventana_principal.geometry(
    "600x500"
)

ventana_principal.resizable(
    False,
    False
)


# ============================================================
# TÍTULO
# ============================================================

tk.Label(
    ventana_principal,
    text="Herramientas para PDF",
    font=("Arial", 18, "bold")
).pack(
    pady=(30, 10)
)

tk.Label(
    ventana_principal,
    text="Seleccione la operación que desea realizar",
    font=("Arial", 10)
).pack(
    pady=(0, 25)
)


# ============================================================
# OPCIÓN 1
# ============================================================

tk.Button(
    ventana_principal,
    text="1. Eliminar páginas vacías",
    width=35,
    height=2,
    command=eliminar_paginas_vacias
).pack(
    pady=7
)


# ============================================================
# OPCIÓN 2
# ============================================================

tk.Button(
    ventana_principal,
    text="2. Eliminar páginas por número",
    width=35,
    height=2,
    command=eliminar_por_numero
).pack(
    pady=7
)


# ============================================================
# OPCIÓN 3
# ============================================================

tk.Button(
    ventana_principal,
    text="3. Unir PDFs",
    width=35,
    height=2,
    command=lambda: unir_pdfs(
        ventana_principal
    )
).pack(
    pady=7
)


# ============================================================
# OPCIÓN 4
# ============================================================

tk.Button(
    ventana_principal,
    text="4. Agregar numeración",
    width=35,
    height=2,
    command=lambda: numerar_pdf(
        ventana_principal
    )
).pack(
    pady=7
)


# ============================================================
# OPCIÓN 5
# ============================================================

tk.Button(
    ventana_principal,
    text="5. Salir",
    width=35,
    height=2,
    command=salir
).pack(
    pady=15
)


# ============================================================
# EJECUTAR
# ============================================================

ventana_principal.mainloop()
