"""
Sistema de Análisis de Rutas Aéreas
Laboratorio 2 - Estructura de Datos II
Universidad del Norte

Autores: [Nombres de los integrantes del equipo]
Fecha: Octubre 2025
"""

import csv
import math
from typing import Dict, List, Tuple, Set, Optional
import heapq
import folium


class Aeropuerto:
    """Clase que representa un aeropuerto con su información geográfica"""
    
    def __init__(self, codigo: str, nombre: str, ciudad: str, pais: str, 
                 latitud: float, longitud: float):
        self.codigo = codigo
        self.nombre = nombre
        self.ciudad = ciudad
        self.pais = pais
        self.latitud = latitud
        self.longitud = longitud
    
    def __str__(self):
        return (f"Código: {self.codigo}\n"
                f"Nombre: {self.nombre}\n"
                f"Ciudad: {self.ciudad}\n"
                f"País: {self.pais}\n"
                f"Latitud: {self.latitud}\n"
                f"Longitud: {self.longitud}")
    
    def __repr__(self):
        return f"Aeropuerto({self.codigo})"


class GrafoAereo:
    """
    Clase que representa el grafo de rutas aéreas.
    Grafo simple, no dirigido y ponderado.
    """
    
    def __init__(self):
        # Diccionario de aeropuertos: codigo -> Aeropuerto
        self.aeropuertos: Dict[str, Aeropuerto] = {}
        # Lista de adyacencia: codigo -> [(codigo_vecino, distancia)]
        self.adyacencias: Dict[str, List[Tuple[str, float]]] = {}
    
    @staticmethod
    def calcular_distancia_haversine(lat1: float, lon1: float, 
                                     lat2: float, lon2: float) -> float:
        """
        Calcula la distancia entre dos coordenadas geográficas usando la fórmula de Haversine.
        
        Args:
            lat1, lon1: Coordenadas del primer punto (latitud, longitud)
            lat2, lon2: Coordenadas del segundo punto (latitud, longitud)
        
        Returns:
            Distancia en kilómetros
        """
        # Radio de la Tierra en kilómetros
        R = 6371.0
        
        # Convertir grados a radianes
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Diferencias
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Fórmula de Haversine
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distancia = R * c
        return distancia
    
    def agregar_aeropuerto(self, aeropuerto: Aeropuerto):
        """Agrega un aeropuerto al grafo"""
        if aeropuerto.codigo not in self.aeropuertos:
            self.aeropuertos[aeropuerto.codigo] = aeropuerto
            self.adyacencias[aeropuerto.codigo] = []
    
    def agregar_ruta(self, codigo_origen: str, codigo_destino: str):
        """
        Agrega una ruta entre dos aeropuertos.
        Calcula automáticamente la distancia usando coordenadas geográficas.
        """
        if codigo_origen in self.aeropuertos and codigo_destino in self.aeropuertos:
            origen = self.aeropuertos[codigo_origen]
            destino = self.aeropuertos[codigo_destino]
            
            distancia = self.calcular_distancia_haversine(
                origen.latitud, origen.longitud,
                destino.latitud, destino.longitud
            )
            
            # Grafo no dirigido: agregar en ambas direcciones
            # Verificar que no exista ya la arista
            if not any(vecino == codigo_destino for vecino, _ in self.adyacencias[codigo_origen]):
                self.adyacencias[codigo_origen].append((codigo_destino, distancia))
            
            if not any(vecino == codigo_origen for vecino, _ in self.adyacencias[codigo_destino]):
                self.adyacencias[codigo_destino].append((codigo_origen, distancia))
    
    def cargar_desde_csv(self, ruta_csv: str):
        """
        Carga los datos desde el archivo CSV
        
        Args:
            ruta_csv: Ruta al archivo flights_final.csv
        """
        aeropuertos_vistos = set()
        
        with open(ruta_csv, 'r', encoding='utf-8') as archivo:
            lector = csv.DictReader(archivo)
            
            for fila in lector:
                # Agregar aeropuerto origen
                codigo_origen = fila['Source Airport Code'].strip()
                if codigo_origen not in aeropuertos_vistos:
                    aeropuerto_origen = Aeropuerto(
                        codigo=codigo_origen,
                        nombre=fila['Source Airport Name'].strip(),
                        ciudad=fila['Source Airport City'].strip(),
                        pais=fila['Source Airport Country'].strip(),
                        latitud=float(fila['Source Airport Latitude']),
                        longitud=float(fila['Source Airport Longitude'])
                    )
                    self.agregar_aeropuerto(aeropuerto_origen)
                    aeropuertos_vistos.add(codigo_origen)
                
                # Agregar aeropuerto destino
                codigo_destino = fila['Destination Airport Code'].strip()
                if codigo_destino not in aeropuertos_vistos:
                    aeropuerto_destino = Aeropuerto(
                        codigo=codigo_destino,
                        nombre=fila['Destination Airport Name'].strip(),
                        ciudad=fila['Destination Airport City'].strip(),
                        pais=fila['Destination Airport Country'].strip(),
                        latitud=float(fila['Destination Airport Latitude']),
                        longitud=float(fila['Destination Airport Longitude'])
                    )
                    self.agregar_aeropuerto(aeropuerto_destino)
                    aeropuertos_vistos.add(codigo_destino)
                
                # Agregar la ruta
                self.agregar_ruta(codigo_origen, codigo_destino)
    
    def es_conexo(self) -> Tuple[bool, int, List[List[str]]]:
        """
        Determina si el grafo es conexo usando DFS.
        
        Returns:
            (es_conexo, num_componentes, lista_de_componentes)
            donde lista_de_componentes es una lista de listas con los códigos de aeropuertos
        """
        if not self.aeropuertos:
            return True, 0, []
        
        visitados = set()
        componentes = []
        
        def dfs(nodo: str, componente_actual: List[str]):
            """DFS recursivo para encontrar componentes"""
            visitados.add(nodo)
            componente_actual.append(nodo)
            
            for vecino, _ in self.adyacencias[nodo]:
                if vecino not in visitados:
                    dfs(vecino, componente_actual)
        
        # Encontrar todas las componentes conexas
        for aeropuerto in self.aeropuertos:
            if aeropuerto not in visitados:
                componente_actual = []
                dfs(aeropuerto, componente_actual)
                componentes.append(componente_actual)
        
        num_componentes = len(componentes)
        es_conexo = num_componentes == 1
        
        return es_conexo, num_componentes, componentes
    
    def arbol_expansion_minima_prim(self, componente: List[str] = None) -> float:
        """
        Calcula el peso del árbol de expansión mínima usando el algoritmo de Prim.
        Implementación propia sin usar librerías externas.
        
        Args:
            componente: Lista de códigos de aeropuertos de la componente.
                       Si es None, usa todos los aeropuertos del grafo.
        
        Returns:
            Peso total del árbol de expansión mínima
        """
        if componente is None:
            componente = list(self.aeropuertos.keys())
        
        if not componente:
            return 0.0
        
        # Conjunto de nodos en el árbol
        en_arbol = set()
        # Heap de aristas: (peso, nodo_en_arbol, nodo_fuera_arbol)
        heap_aristas = []
        peso_total = 0.0
        
        # Comenzar con el primer nodo de la componente
        nodo_inicial = componente[0]
        en_arbol.add(nodo_inicial)
        
        # Agregar todas las aristas del nodo inicial al heap
        for vecino, peso in self.adyacencias[nodo_inicial]:
            if vecino in componente:
                heapq.heappush(heap_aristas, (peso, nodo_inicial, vecino))
        
        # Mientras no hayamos agregado todos los nodos
        while len(en_arbol) < len(componente) and heap_aristas:
            peso, nodo_en_arbol, nodo_fuera = heapq.heappop(heap_aristas)
            
            # Si el nodo ya está en el árbol, ignorar esta arista
            if nodo_fuera in en_arbol:
                continue
            
            # Agregar el nodo al árbol
            en_arbol.add(nodo_fuera)
            peso_total += peso
            
            # Agregar todas las aristas del nuevo nodo al heap
            for vecino, peso_arista in self.adyacencias[nodo_fuera]:
                if vecino in componente and vecino not in en_arbol:
                    heapq.heappush(heap_aristas, (peso_arista, nodo_fuera, vecino))
        
        return peso_total
    
    def dijkstra(self, origen: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
        """
        Implementación del algoritmo de Dijkstra para encontrar caminos mínimos.
        Implementación propia sin usar librerías externas.
        
        Args:
            origen: Código del aeropuerto origen
        
        Returns:
            (distancias, predecesores)
            - distancias: dict con la distancia mínima desde el origen a cada nodo
            - predecesores: dict con el predecesor de cada nodo en el camino mínimo
        """
        # Inicializar distancias con infinito
        distancias = {aeropuerto: float('infinity') for aeropuerto in self.aeropuertos}
        distancias[origen] = 0.0
        
        # Predecesores para reconstruir el camino
        predecesores = {aeropuerto: None for aeropuerto in self.aeropuertos}
        
        # Heap de prioridad: (distancia, nodo)
        heap = [(0.0, origen)]
        visitados = set()
        
        while heap:
            distancia_actual, nodo_actual = heapq.heappop(heap)
            
            # Si ya visitamos este nodo, continuar
            if nodo_actual in visitados:
                continue
            
            visitados.add(nodo_actual)
            
            # Revisar todos los vecinos
            for vecino, peso in self.adyacencias[nodo_actual]:
                if vecino in visitados:
                    continue
                
                nueva_distancia = distancia_actual + peso
                
                # Si encontramos un camino más corto, actualizamos
                if nueva_distancia < distancias[vecino]:
                    distancias[vecino] = nueva_distancia
                    predecesores[vecino] = nodo_actual
                    heapq.heappush(heap, (nueva_distancia, vecino))
        
        return distancias, predecesores
    
    def reconstruir_camino(self, predecesores: Dict[str, Optional[str]], 
                          destino: str) -> List[str]:
        """
        Reconstruye el camino desde el origen hasta el destino usando los predecesores.
        
        Args:
            predecesores: Diccionario de predecesores del algoritmo de Dijkstra
            destino: Código del aeropuerto destino
        
        Returns:
            Lista con los códigos de aeropuertos en el camino (desde origen a destino)
        """
        camino = []
        nodo_actual = destino
        
        # Reconstruir el camino hacia atrás
        while nodo_actual is not None:
            camino.append(nodo_actual)
            nodo_actual = predecesores[nodo_actual]
        
        # Invertir para tener el camino desde origen a destino
        camino.reverse()
        
        return camino
    
    def obtener_aeropuertos_mas_lejanos(self, codigo_origen: str, 
                                        cantidad: int = 10) -> List[Tuple[str, float]]:
        """
        Obtiene los aeropuertos cuyos caminos mínimos desde el origen son los más largos.
        
        Args:
            codigo_origen: Código del aeropuerto origen
            cantidad: Número de aeropuertos a retornar
        
        Returns:
            Lista de tuplas (codigo_aeropuerto, distancia) ordenada de mayor a menor distancia
        """
        distancias, _ = self.dijkstra(codigo_origen)
        
        # Filtrar las distancias infinitas (nodos no alcanzables)
        distancias_alcanzables = [(codigo, dist) for codigo, dist in distancias.items() 
                                  if dist != float('infinity') and codigo != codigo_origen]
        
        # Ordenar por distancia descendente
        distancias_alcanzables.sort(key=lambda x: x[1], reverse=True)
        
        return distancias_alcanzables[:cantidad]
    
    def crear_mapa(self, ruta_salida: str = "mapa_aeropuertos.html"):
        """
        Crea un mapa interactivo con todos los aeropuertos usando Folium.
        
        Args:
            ruta_salida: Ruta donde se guardará el archivo HTML del mapa
        """
        # Calcular el centro del mapa (promedio de coordenadas)
        lat_promedio = sum(a.latitud for a in self.aeropuertos.values()) / len(self.aeropuertos)
        lon_promedio = sum(a.longitud for a in self.aeropuertos.values()) / len(self.aeropuertos)
        
        # Crear el mapa
        mapa = folium.Map(location=[lat_promedio, lon_promedio], zoom_start=3)
        
        # Agregar marcadores para cada aeropuerto
        for aeropuerto in self.aeropuertos.values():
            folium.Marker(
                location=[aeropuerto.latitud, aeropuerto.longitud],
                popup=f"{aeropuerto.codigo}: {aeropuerto.nombre}<br>{aeropuerto.ciudad}, {aeropuerto.pais}",
                tooltip=aeropuerto.codigo,
                icon=folium.Icon(color='blue', icon='plane', prefix='fa')
            ).add_to(mapa)
        
        # Guardar el mapa
        mapa.save(ruta_salida)
        print(f"Mapa guardado en: {ruta_salida}")
    
    def dibujar_camino_en_mapa(self, camino: List[str], 
                               ruta_salida: str = "mapa_camino.html"):
        """
        Dibuja un camino específico en el mapa.
        
        Args:
            camino: Lista de códigos de aeropuertos que forman el camino
            ruta_salida: Ruta donde se guardará el archivo HTML del mapa
        """
        if not camino:
            print("No hay camino para dibujar")
            return
        
        # Obtener coordenadas del camino
        coordenadas = []
        for codigo in camino:
            if codigo in self.aeropuertos:
                aeropuerto = self.aeropuertos[codigo]
                coordenadas.append([aeropuerto.latitud, aeropuerto.longitud])
        
        # Calcular centro del mapa
        lat_promedio = sum(coord[0] for coord in coordenadas) / len(coordenadas)
        lon_promedio = sum(coord[1] for coord in coordenadas) / len(coordenadas)
        
        # Crear el mapa
        mapa = folium.Map(location=[lat_promedio, lon_promedio], zoom_start=4)
        
        # Dibujar la línea del camino
        folium.PolyLine(
            coordenadas,
            color='red',
            weight=3,
            opacity=0.8
        ).add_to(mapa)
        
        # Agregar marcadores para los aeropuertos en el camino
        for i, codigo in enumerate(camino):
            aeropuerto = self.aeropuertos[codigo]
            color = 'green' if i == 0 else ('red' if i == len(camino) - 1 else 'blue')
            label = 'Origen' if i == 0 else ('Destino' if i == len(camino) - 1 else f'Escala {i}')
            
            folium.Marker(
                location=[aeropuerto.latitud, aeropuerto.longitud],
                popup=f"{label}<br>{aeropuerto.codigo}: {aeropuerto.nombre}<br>{aeropuerto.ciudad}, {aeropuerto.pais}",
                tooltip=f"{codigo} ({label})",
                icon=folium.Icon(color=color, icon='plane', prefix='fa')
            ).add_to(mapa)
        
        # Guardar el mapa
        mapa.save(ruta_salida)
        print(f"Mapa del camino guardado en: {ruta_salida}")


def menu_principal():
    """Menú interactivo principal del sistema"""
    print("="*60)
    print("SISTEMA DE ANÁLISIS DE RUTAS AÉREAS")
    print("Laboratorio 2 - Estructura de Datos II")
    print("="*60)
    
    # Cargar el grafo
    print("\nCargando datos desde flights_final.csv...")
    grafo = GrafoAereo()
    
    try:
        grafo.cargar_desde_csv('flights_final.csv')
        print(f"✓ Datos cargados exitosamente")
        print(f"  - Total de aeropuertos: {len(grafo.aeropuertos)}")
        print(f"  - Total de rutas: {sum(len(adj) for adj in grafo.adyacencias.values()) // 2}")
    except FileNotFoundError:
        print("✗ Error: No se encontró el archivo flights_final.csv")
        return
    except Exception as e:
        print(f"✗ Error al cargar datos: {e}")
        return
    
    # Generar mapa inicial
    print("\nGenerando mapa de aeropuertos...")
    grafo.crear_mapa()
    
    primer_vertice = None
    
    while True:
        print("\n" + "="*60)
        print("MENÚ PRINCIPAL")
        print("="*60)
        print("1. Verificar si el grafo es conexo")
        print("2. Calcular peso del árbol de expansión mínima")
        print("3. Seleccionar primer vértice (aeropuerto)")
        print("4. Seleccionar segundo vértice y mostrar camino mínimo")
        print("5. Salir")
        print("="*60)
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            print("\nVerificando conectividad del grafo...")
            es_conexo, num_componentes, componentes = grafo.es_conexo()
            
            if es_conexo:
                print("✓ El grafo ES CONEXO")
            else:
                print(f"✗ El grafo NO es conexo")
                print(f"  Número de componentes: {num_componentes}")
                for i, componente in enumerate(componentes, 1):
                    print(f"  Componente {i}: {len(componente)} aeropuertos")
        
        elif opcion == '2':
            print("\nCalculando árbol de expansión mínima...")
            es_conexo, num_componentes, componentes = grafo.es_conexo()
            
            if es_conexo:
                peso = grafo.arbol_expansion_minima_prim()
                print(f"✓ Peso del árbol de expansión mínima: {peso:.2f} km")
            else:
                print(f"El grafo tiene {num_componentes} componentes.")
                print("Calculando MST para cada componente:\n")
                for i, componente in enumerate(componentes, 1):
                    peso = grafo.arbol_expansion_minima_prim(componente)
                    print(f"  Componente {i} ({len(componente)} aeropuertos): {peso:.2f} km")
        
        elif opcion == '3':
            codigo = input("\nIngrese el código del aeropuerto: ").strip().upper()
            
            if codigo not in grafo.aeropuertos:
                print(f"✗ Error: El aeropuerto '{codigo}' no existe en el sistema")
            else:
                primer_vertice = codigo
                aeropuerto = grafo.aeropuertos[codigo]
                print(f"\n✓ Primer vértice seleccionado:\n")
                print(aeropuerto)
                
                # Mostrar los 10 aeropuertos más lejanos
                print("\n10 aeropuertos con caminos mínimos más largos:")
                print("-" * 80)
                aeropuertos_lejanos = grafo.obtener_aeropuertos_mas_lejanos(codigo, 10)
                
                for i, (codigo_lejano, distancia) in enumerate(aeropuertos_lejanos, 1):
                    aeropuerto_lejano = grafo.aeropuertos[codigo_lejano]
                    print(f"\n{i}. {codigo_lejano} - {aeropuerto_lejano.nombre}")
                    print(f"   Ciudad: {aeropuerto_lejano.ciudad}, {aeropuerto_lejano.pais}")
                    print(f"   Coordenadas: ({aeropuerto_lejano.latitud}, {aeropuerto_lejano.longitud})")
                    print(f"   Distancia del camino mínimo: {distancia:.2f} km")
        
        elif opcion == '4':
            if primer_vertice is None:
                print("\n✗ Error: Primero debe seleccionar un primer vértice (opción 3)")
            else:
                codigo = input("\nIngrese el código del segundo aeropuerto: ").strip().upper()
                
                if codigo not in grafo.aeropuertos:
                    print(f"✗ Error: El aeropuerto '{codigo}' no existe en el sistema")
                else:
                    # Calcular camino mínimo
                    distancias, predecesores = grafo.dijkstra(primer_vertice)
                    
                    if distancias[codigo] == float('infinity'):
                        print(f"\n✗ No existe un camino entre {primer_vertice} y {codigo}")
                    else:
                        camino = grafo.reconstruir_camino(predecesores, codigo)
                        
                        print(f"\n✓ Camino mínimo de {primer_vertice} a {codigo}:")
                        print(f"  Distancia total: {distancias[codigo]:.2f} km")
                        print(f"  Número de escalas: {len(camino) - 2}")
                        print(f"\nRuta detallada:")
                        print("-" * 80)
                        
                        for i, codigo_aeropuerto in enumerate(camino):
                            aeropuerto = grafo.aeropuertos[codigo_aeropuerto]
                            etiqueta = "ORIGEN" if i == 0 else ("DESTINO" if i == len(camino) - 1 else f"ESCALA {i}")
                            print(f"\n{etiqueta}: {codigo_aeropuerto}")
                            print(aeropuerto)
                        
                        # Dibujar camino en el mapa
                        print("\nGenerando mapa del camino...")
                        grafo.dibujar_camino_en_mapa(camino)
        
        elif opcion == '5':
            print("\n¡Hasta luego!")
            break
        
        else:
            print("\n✗ Opción inválida. Por favor intente de nuevo.")

if __name__ == "__main__":
    menu_principal()