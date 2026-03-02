from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Any, List

from flask import Flask, render_template, request

from column_design import (
    Materiales,
    GeometriaColumna,
    CapaAcero,
    DisenoColumna,
)

app = Flask(__name__)


def _to_float(form: Dict[str, str], key: str, default: float = 0.0) -> float:
    value = form.get(key, "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    resultado: Dict[str, Any] | None = None
    error: str | None = None

    if request.method == "POST":
        try:
            fc = _to_float(request.form, "fc", 28.0)
            fy = _to_float(request.form, "fy", 420.0)
            Es = _to_float(request.form, "Es", 200000.0)
            phi = _to_float(request.form, "phi", 0.65)

            b = _to_float(request.form, "b", 400.0)
            h = _to_float(request.form, "h", 400.0)
            recubrimiento = _to_float(request.form, "recubrimiento", 40.0)
            k = _to_float(request.form, "k", 1.0)
            lu = _to_float(request.form, "lu", 3000.0)
            r = _to_float(request.form, "r", 115.0)
            arriostrada = request.form.get("arriostrada", "si") == "si"

            M1 = _to_float(request.form, "M1", 40e6)
            M2 = _to_float(request.form, "M2", 90e6)
            Pu = _to_float(request.form, "Pu", 1200e3)
            Mu = _to_float(request.form, "Mu", 120e6)

            n_barras = int(_to_float(request.form, "n_barras", 4))
            As_barra = _to_float(request.form, "As_barra", 600.0)
            d_sup = _to_float(request.form, "d_sup", 60.0)
            d_inf = _to_float(request.form, "d_inf", 340.0)

            capas: List[CapaAcero] = []
            mitad = max(1, n_barras // 2)
            for _ in range(mitad):
                capas.append(CapaAcero(As=As_barra, d=d_sup))
            for _ in range(n_barras - mitad):
                capas.append(CapaAcero(As=As_barra, d=d_inf))

            mat = Materiales(fc=fc, fy=fy, Es=Es)
            geo = GeometriaColumna(
                b=b,
                h=h,
                recubrimiento=recubrimiento,
                k=k,
                lu=lu,
                r=r,
                arriostrada=arriostrada,
            )
            diseno = DisenoColumna(mat, geo, capas, phi=phi)

            esbeltez = diseno.verificar_esbeltez(M1=M1, M2=M2)
            diagrama = diseno.diagrama_interaccion_uniaxial(n_puntos=50)

            p1 = (diagrama[20]["phiMn"], diagrama[20]["phiPn"])
            p2 = (diagrama[21]["phiMn"], diagrama[21]["phiPn"])
            capacidad = diseno.interseccion_recta_demanda_capacidad(Pu=Pu, Mu=Mu, p1=p1, p2=p2)

            if capacidad is None:
                dc = None
            else:
                _, Mn = capacidad
                dc = diseno.demanda_capacidad(Mu, Mn) if abs(Mn) > 1e-9 else None

            cuantia = diseno.verificar_cuantia()

            resultado = {
                "esbeltez": esbeltez,
                "cuantia": cuantia,
                "dc": dc,
                "capacidad": capacidad,
                "diagrama": diagrama[:10],
                "materiales": asdict(mat),
                "geometria": asdict(geo),
            }
        except Exception as exc:
            error = f"Error al procesar datos: {exc}"

    return render_template("index.html", resultado=resultado, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
