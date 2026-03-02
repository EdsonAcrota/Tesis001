from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional


@dataclass
class Materiales:
    fc: float  # MPa
    fy: float  # MPa
    Es: float = 200000.0  # MPa


@dataclass
class GeometriaColumna:
    b: float  # mm
    h: float  # mm
    recubrimiento: float  # mm
    k: float
    lu: float  # mm
    r: float  # mm
    arriostrada: bool = True


@dataclass
class CapaAcero:
    As: float  # mm2
    d: float  # mm desde la cara comprimida


@dataclass
class Solicitacion:
    Pu: float  # N
    Mux: float  # Nmm
    Muy: float = 0.0  # Nmm


class DisenoColumna:
    def __init__(self, materiales: Materiales, geometria: GeometriaColumna, capas: List[CapaAcero], phi: float = 0.65):
        self.mat = materiales
        self.geo = geometria
        self.capas = capas
        self.phi = phi

    @property
    def Ag(self) -> float:
        return self.geo.b * self.geo.h

    @property
    def Ast(self) -> float:
        return sum(c.As for c in self.capas)

    def beta1(self) -> float:
        fc = self.mat.fc
        if fc <= 28:
            return 0.85
        if fc >= 56:
            return 0.65
        return 0.85 - 0.05 * ((fc - 28) / 7)

    def verificar_esbeltez(self, M1: float, M2: float) -> Dict[str, float | bool]:
        razon = self.geo.k * self.geo.lu / self.geo.r
        if self.geo.arriostrada:
            limite = min(34.0 + 12.0 * (M1 / M2 if M2 != 0 else 0.0), 40.0)
        else:
            limite = 22.0
        return {"klu_r": razon, "limite": limite, "esbelta": razon > limite}

    def _estado_para_c(self, c: float) -> Tuple[float, float]:
        b = self.geo.b
        h = self.geo.h
        beta1 = self.beta1()
        a = min(beta1 * c, h)

        Cc = 0.85 * self.mat.fc * b * a
        yc = a / 2.0
        ycg = h / 2.0
        Mc = Cc * (ycg - yc)

        Pn = Cc
        Mn = Mc

        for capa in self.capas:
            eps_s = (0.003 / c) * (c - capa.d)
            fi = max(min(eps_s * self.mat.Es, self.mat.fy), -self.mat.fy)
            Fi = capa.As * fi
            Mi = Fi * (ycg - capa.d)
            Pn += Fi
            Mn += Mi

        return Pn, Mn

    def diagrama_interaccion_uniaxial(self, n_puntos: int = 60) -> List[Dict[str, float]]:
        h = self.geo.h
        c_min = max(1.0, min(c.d for c in self.capas) * 0.1)
        c_max = 2.0 * h

        puntos = []
        for i in range(n_puntos):
            c = c_min + (c_max - c_min) * (i / (n_puntos - 1))
            Pn, Mn = self._estado_para_c(c)
            Pn_max = 0.85 * self.mat.fc * (self.Ag - self.Ast) + self.Ast * self.mat.fy
            Pn = min(Pn, Pn_max)
            puntos.append(
                {
                    "c": c,
                    "Pn": Pn,
                    "Mn": Mn,
                    "phiPn": self.phi * Pn,
                    "phiMn": self.phi * Mn,
                }
            )

        puntos.sort(key=lambda x: x["phiPn"])
        return puntos

    @staticmethod
    def interseccion_recta_demanda_capacidad(Pu: float, Mu: float, p1: Tuple[float, float], p2: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        Mi, Pi = p1
        Mj, Pj = p2
        if abs(Mu) < 1e-9 or abs(Mj - Mi) < 1e-9:
            return None

        pendiente_demanda = Pu / Mu
        pendiente_borde = (Pj - Pi) / (Mj - Mi)
        denom = pendiente_demanda - pendiente_borde
        if abs(denom) < 1e-12:
            return None

        Mn = (Pj + ((Pi - Pj) / (Mj - Mi)) * Mj) / denom
        Pn = pendiente_demanda * Mn
        return Pn, Mn

    @staticmethod
    def bresler_pr(P_rx: float, P_ry: float, P_oc: float) -> float:
        return 1.0 / ((1.0 / P_rx) + (1.0 / P_ry) - (1.0 / P_oc))

    @staticmethod
    def criterio_baja_carga(Mux: float, Muy: float, Mrx: float, Mry: float) -> bool:
        return (Mux / Mrx) + (Muy / Mry) <= 1.0

    @staticmethod
    def demanda_capacidad(demanda: float, capacidad: float) -> float:
        return demanda / capacidad

    def verificar_cuantia(self) -> Dict[str, float | bool]:
        rho = self.Ast / self.Ag
        return {"rho": rho, "cumple": 0.01 <= rho <= 0.06}


def ejemplo_uso() -> None:
    mat = Materiales(fc=28, fy=420)
    geo = GeometriaColumna(b=400, h=400, recubrimiento=40, k=1.0, lu=3000, r=115, arriostrada=True)
    capas = [
        CapaAcero(As=600, d=60),
        CapaAcero(As=600, d=60),
        CapaAcero(As=600, d=340),
        CapaAcero(As=600, d=340),
    ]

    diseno = DisenoColumna(mat, geo, capas, phi=0.65)

    print("Esbeltez:", diseno.verificar_esbeltez(M1=40e6, M2=90e6))
    diagrama = diseno.diagrama_interaccion_uniaxial(n_puntos=40)
    print("Primeros 5 puntos del diagrama de diseño (phiPn, phiMn):")
    for p in diagrama[:5]:
        print(round(p["phiPn"], 2), round(p["phiMn"], 2))

    punto1 = (diagrama[10]["phiMn"], diagrama[10]["phiPn"])
    punto2 = (diagrama[11]["phiMn"], diagrama[11]["phiPn"])
    capacidad = diseno.interseccion_recta_demanda_capacidad(Pu=1200e3, Mu=120e6, p1=punto1, p2=punto2)
    print("Capacidad por intersección:", capacidad)

    P_oc = 0.85 * mat.fc * (geo.b * geo.h)
    Pr = diseno.bresler_pr(P_rx=2400e3, P_ry=2100e3, P_oc=P_oc)
    print("Bresler PR:", round(Pr, 2))
    print("Cumple baja carga:", diseno.criterio_baja_carga(Mux=80e6, Muy=60e6, Mrx=140e6, Mry=120e6))

    dc = diseno.demanda_capacidad(0.9 * 120e6, capacidad[1] if capacidad else 1.0)
    print("D/C:", round(dc, 4))
    print("Cuantía:", diseno.verificar_cuantia())


if __name__ == "__main__":
    ejemplo_uso()
