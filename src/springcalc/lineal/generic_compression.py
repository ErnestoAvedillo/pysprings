from pint import Quantity
from ..pymodels.units import ureg
from .generic_lineal import MuelleLineal


class MuelleCompresionGeneral(MuelleLineal):
    longitud_bloqueo: Quantity = 0.0 * ureg.mm

    def calcular_longitud_bloqueo(self) -> Quantity:
        """
        En un muelle de geometría variable (como uno cónico), las espiras pueden 
        anidarse unas dentro de otras (telescoping). 
        """
        # Si el muelle se aloja plano (diámetros muy distintos): d_bloqueo = d_alambre
        # Si es un muelle de compresión estándar donde chocan: d_bloqueo = N_espiras * d_alambre
        # Añadimos una comprobación básica de "anidamiento" o "telescopaje"
        H_val = self.longitud_libre.to('mm').magnitude
        D_inicio = self.f_diametro_medio(0 * ureg.mm).to('mm').magnitude
        D_fin = self.f_diametro_medio(self.longitud_libre).to('mm').magnitude
        d_filo = self.diametro_hilo.to('mm').magnitude
        
        # Si la diferencia de radios es mayor que el diámetro del alambre por espira, se "anida"
        if abs(D_inicio - D_fin) >= (self.numero_espiras * d_filo):
            # Caso límite de telescopaje perfecto (todas entran dentro de otras)
            self.longitud_bloqueo = d_filo * ureg.mm
        else:
            # Caso convencional: chocan una encima de otra
            self.longitud_bloqueo = self.numero_espiras * self.diametro_hilo
            
        return self.longitud_bloqueo