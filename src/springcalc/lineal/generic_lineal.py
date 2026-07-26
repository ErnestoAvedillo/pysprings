from typing import Callable, Optional
from pint import Quantity
import numpy as np
from pydantic import ConfigDict, field_validator
from ..pymodels.units import ureg
from .constants import WAHL_FACTOR_CONSTANTS, TIPOS_FINAL_MUELLE_COMPRESION
from ..pymodels.wire_characteristics import WireCharacteristics
from typing import Optional
from pint import Quantity
from ..pymodels.units import ureg
from pydantic import field_validator, ConfigDict
import numpy as np
from scipy.integrate import quad
from scipy.optimize import fsolve

# (Conserva tus otras importaciones: ureg, WireCharacteristics, Material, etc.)


class MuelleLineal(WireCharacteristics):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)
    
    # --- Parámetros base del muelle genérico ---
    longitud_libre: Quantity = 0.0 * ureg.mm
    numero_espiras_utiles: float = 0.0
    shot_peening: bool = False
    revestimiento: Optional[str] = None
    indice_muelle: float = 0.0  # Nota: En geometrías variables, este índice varía localmente.
    
    # --- NUEVO: Atributos funcionales para Geometría Variable ---
    # Almacenan funciones que reciben la altura 'h' (Quantity) y devuelven Quantity
    f_diametro_medio: Callable[[Quantity], Quantity] = lambda h: 0.0 * ureg.mm
    f_pitch: Callable[[Quantity], Quantity] = lambda h: 0.0 * ureg.mm

    # Guardamos límites físicos para inicializaciones rápidas
    diametro_ini_medio: Quantity = 0.0 * ureg.mm
    pitch_constante: Quantity = 0.0 * ureg.mm
    longitud_hilo: Quantity = 0.0 * ureg.mm
    tipo_final: str = "rectificado"
    tipo_conformado: str = "frio"
    theta_max: float = 0.0  # Ángulo total de rotación de la hélice (radianes)

    # --- Tus validadores se mantienen igual (reducidos aquí por espacio) ---
    @field_validator('longitud_libre', mode='before')
    @classmethod
    def validate_dimensions(cls, v):
        if v is not None:
            if isinstance(v, Quantity):
                return v.to('mm')
            return float(v) * ureg.mm
        return v

    def __init__(self, material, diametro_hilo: float, **data):
        super().__init__(material, diametro_hilo, **data)
        
        # Por defecto, si no se pasan funciones personalizadas, inicializar como lineal constante
        if 'f_diametro_medio' not in data:
            self.f_diametro_medio = lambda h: self.diametro_ini_medio
        if 'f_pitch' not in data:
            self.f_pitch = lambda h: self.pitch_constante

    def establecer_funciones_geometricas(self, func_D: Callable[[Quantity], Quantity], func_p: Callable[[Quantity], Quantity]):
        """Permite inyectar cualquier geometría variable al muelle"""
        self.f_diametro_medio = func_D
        self.f_pitch = func_p

    def calcular_indice_muelle_local(self, h: Quantity) -> float:
        """El índice de muelle ahora depende de en qué parte (h) del muelle midas"""
        D_local = self.f_diametro_medio(h)
        return float(D_local.to('mm').magnitude / self.diametro_hilo.to('mm').magnitude)

    def calcular_theta_max(self) -> float:
        """
        Determina theta_max integrando: d_theta = (2*pi / p(h)) * dh
        desde h = 0 hasta longitud_libre.
        """
        H_val = self.longitud_libre.to('mm').magnitude

        # Función integranda: extrae la magnitud en mm del paso local
        def integrando(h_mm):
            pitch_local = self.f_pitch(h_mm * ureg.mm).to('mm').magnitude
            if pitch_local <= 0:
                raise ValueError("El paso (pitch) en cualquier punto de h debe ser mayor que cero.")
            return (2 * np.pi) / pitch_local

        theta_max, _ = quad(integrando, 0, H_val)
        self.theta_max = theta_max
        # Actualizar número de espiras totales
        self.numero_espiras = theta_max / (2 * np.pi)
        return self.theta_max

    def obtener_desarrollo_h_theta(self, num_puntos=500):
        """
        Resuelve la correspondencia entre el ángulo theta y la altura h.
        Devuelve arrays de numpy en milímetros.
        """
        if self.theta_max == 0:
            self.calcular_theta_max()
            
        thetas = np.linspace(0, self.theta_max, num_puntos)
        zs = np.zeros(num_puntos)
       
        # Resolvemos numéricamente la integral acumulada para cada ángulo
        for i, theta in enumerate(thetas):
            if i == 0:
                zs[i] = 0.0
                continue
            
            def ecuacion(z_test):
                # Integral desde 0 hasta z_test de (2*pi / p(h)) dh
                val, _ = quad(lambda h: (2 * np.pi) / self.f_pitch(h * ureg.mm).to('mm').magnitude, 0, z_test)
                return val - theta
            
            # Buscamos la raíz (estimación inicial = punto anterior)
            zs[i] = fsolve(ecuacion, zs[i-1])[0]
            
        return thetas, zs

 
    def calcular_longitud_hilo(self, num_puntos=500) -> Quantity:
        """Calcula la longitud del alambre mediante integración del diferencial de arco (ds)"""
        thetas, zs = self.obtener_desarrollo_h_theta(num_puntos)
        
        # Obtener diámetros en cada paso de z
        Ds = np.array([self.f_diametro_medio(z * ureg.mm).to('mm').magnitude for z in zs])
        radios = Ds / 2.0
        
        # Coordenadas cartesianas 3D del eje
        xs = radios * np.cos(thetas)
        ys = radios * np.sin(thetas)
        
        # Derivadas numéricas respecto a theta
        dtheta = thetas[1] - thetas[0]
        dx_dtheta = np.gradient(xs, dtheta)
        dy_dtheta = np.gradient(ys, dtheta)
        dz_dtheta = np.gradient(zs, dtheta)
        
        # ds = sqrt( dx^2 + dy^2 + dz^2 )
        ds = np.sqrt(dx_dtheta**2 + dy_dtheta**2 + dz_dtheta**2)
        
        # Longitud total integrada
        L_mm = np.trapz(ds, thetas)
        self.longitud_hilo = L_mm * ureg.mm
        return self.longitud_hilo


    
    def calcular_constante_muelle(self, num_puntos=500) -> Quantity:
        """
        Calcula la rigidez del muelle equivalente (K) considerando las espiras en serie.
        1/K = integral_0^theta_max [ 8 * D(theta)^3 / (G * d^4 * 2*pi) ] dtheta
        """
        thetas, zs = self.obtener_desarrollo_h_theta(num_puntos)
        Ds = np.array([self.f_diametro_medio(z * ureg.mm).to('mm').magnitude for z in zs])
        
        d_val = self.diametro_hilo.to('mm').magnitude
        # Acceder al módulo de corte del material (asegura que esté en MPa o N/mm²)
        G_val = self.material.shear_modulus.to('N/mm**2').magnitude 
        
        # Función integranda para la flexibilidad local (1/dK)
        flexibilidad_local = (8 * Ds**3) / (G_val * (d_val**4) * 2 * np.pi)
        
        # Integral numérica mediante regla del trapecio
        flexibilidad_total = np.trapz(flexibilidad_local, thetas)
        
        K_val = 1.0 / flexibilidad_total  # N/mm
        self.constante_muelle = K_val * (ureg.N / ureg.mm)
        return self.constante_muelle

    def simular_compresion_progresiva(self, deflexion_max: Quantity, pasos: int = 100, num_puntos: int = 500):
        """
        Simula la compresión paso a paso considerando el contacto oblicuo entre espiras.
        Retorna la curva de fuerza vs deformación y la evolución de la rigidez instantánea.
        """
        # 1. Obtener la trayectoria inicial en estado libre (sin carga)
        thetas, zs_libre = self.obtener_desarrollo_h_theta(num_puntos)
        Ds = np.array([self.f_diametro_medio(z * ureg.mm).to('mm').magnitude for z in zs_libre])
        radios = Ds / 2.0
        
        d_val = self.diametro_hilo.to('mm').magnitude
        G_val = self.material.shear_modulus.to('N/mm**2').magnitude
        
        # Guardaremos el estado de compresión en cada paso
        historial_deflexion = []
        historial_fuerza = []
        historial_K = []
        
        # El paso angular para una vuelta completa (para comparar espiras adyacentes)
        # Buscamos cuántos puntos de la discretización equivalen a 2*pi radianes
        dtheta = thetas[1] - thetas[0]
        puntos_una_vuelta = int(round((2 * np.pi) / dtheta))
        
        # Inicializamos la fuerza acumulada y la deformación
        fuerza_actual = 0.0 # Newtons
        # Deformación de cada punto del eje z
        delta_y = np.zeros_like(zs_libre)
        
        deflexion_objetivo_max = deflexion_max.to('mm').magnitude
        paso_deflexion = deflexion_objetivo_max / pasos
        
        for paso in range(pasos + 1):
            deflexion_actual = paso * paso_deflexion
            
            # --- DETECCIÓN DE CONTACTO OBLICUO ---
            # Creamos una máscara de zonas activas (1.0 = activa, 0.0 = colisionada/bloqueada)
            es_activa = np.ones_like(thetas)
            
            for i in range(len(thetas) - puntos_una_vuelta):
                # Índice de la espira superior adyacente
                i_sup = i + puntos_una_vuelta
                
                # Distancia vertical actual en mm
                z_inf_actual = zs_libre[i] - delta_y[i]
                z_sup_actual = zs_libre[i_sup] - delta_y[i_sup]
                Pz_actual = abs(z_sup_actual - z_inf_actual)
                
                # Diferencia de radios (geometría variable)
                delta_R = abs(radios[i_sup] - radios[i])
                
                # Condición de colisión
                if delta_R < d_val:
                    # Límite oblicuo de colisión física
                    Pz_limite = np.sqrt(d_val**2 - delta_R**2)
                    if Pz_actual <= Pz_limite:
                        # Si colisionan, ambas secciones y las intermedias se desactivan
                        es_activa[i:i_sup+1] = 0.0
                else:
                    # Si delta_R >= d, hay telescopaje. No hay colisión directa por encima,
                    # pero hay que vigilar si llega al plano del suelo del muelle si se aplasta del todo.
                    pass
            
            # --- CÁLCULO DE LA RIGIDEZ INSTANTÁNEA K_inst ---
            # Flexibilidad local diferencial: si no es activa, su flexibilidad es 0 (rigidez infinita)
            flexibilidad_local = (8 * Ds**3) / (G_val * (d_val**4) * 2 * np.pi)
            flexibilidad_local_activa = flexibilidad_local * es_activa
            
            flex_total = np.trapz(flexibilidad_local_activa, thetas)
            
            if flex_total <= 1e-9:
                # El muelle ha llegado al bloqueo completo (solid height)
                K_inst = float('inf')
            else:
                K_inst = 1.0 / flex_total
            
            # --- ACTUALIZAR FUERZA Y DEFORMACIÓN ---
            if paso > 0:
                # dF = K_inst * d_deflexion
                incremento_fuerza = K_inst * paso_deflexion if K_inst != float('inf') else 0.0
                fuerza_actual += incremento_fuerza
                
                # Distribuir la deformación diferencial localmente. 
                # Las zonas más flexibles (mayor diámetro o activas) se deforman más.
                if K_inst != float('inf'):
                    # La deformación local proporcional a la flexibilidad local
                    factor_deformacion = flexibilidad_local_activa / flex_total
                    delta_y += factor_deformacion * paso_deflexion
            
            historial_deflexion.append(deflexion_actual)
            historial_fuerza.append(fuerza_actual)
            historial_K.append(K_inst)
            
            if K_inst == float('inf'):
                # Si se bloquea por completo el muelle, terminamos la simulación
                break

        return (np.array(historial_deflexion) * ureg.mm, 
                np.array(historial_fuerza) * ureg.N, 
                np.array(historial_K) * (ureg.N / ureg.mm))