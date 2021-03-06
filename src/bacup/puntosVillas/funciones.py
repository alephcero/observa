import pandas as pd
import numpy as np
import geopandas as gpd
import googlemaps
import os
import datetime
import matplotlib.pyplot as plt
from shapely.geometry import Point


def googDirections(origins, destinations, transit_routing_preference = False, mode="transit"):
    #docs https://developers.google.com/maps/documentation/directions/intro#DirectionsRequests
    #transit_routing_preference: less_walking o fewer_transfers
    
    gmaps = googlemaps.Client(key=os.getenv('GOOGLEAPIACYA'))
    travel = gmaps.directions(origins,destinations,mode,transit_routing_preference=transit_routing_preference,alternatives=False)
    
     
    return travel


def cantidadDeTramos(googleDict):
    '''
    Esta funcion toma un diccionario de la API de google y 
    devuelve la cantidad de tramos de un viaje
    '''
    try:
        return len(googleDict[0]['legs'][0]['steps'])
    except:
        return np.nan

def distancia(googleDict):
    '''
    Esta funcion toma un diccionario de la API de google y 
    devuelve la distancia entre origen y destino en metros
    '''
    try:
        return googleDict[0]['legs'][0]['distance']['value']
    except:
        return np.nan
    
def costo(googleDict):
    '''
    Esta funcion toma un diccionario de la API de google y 
    devuelve el costo del viaje en pesos ARG
    '''
    try:
        return googleDict[0]['fare']['value']    
    except:
        return np.nan
    
def tiempoTotal(googleDict):
    '''
    Esta funcion toma un diccionario de la API de google y 
    devuelve el tiempo total de viaje en segundos
    '''
    try:
        return googleDict[0]['legs'][0]['duration']['value']
    except:
        return np.nan
    
def modos(googleDict):
    '''
    Esta funcion toma un diccionario de la API de google y 
    devuelve la lista de modos que tomo
    '''
    try:
        pasos = googleDict[0]['legs'][0]['steps']
        #listaModos = [pasos[i]['travel_mode'] for i in range(len(pasos))]
        diccio = {}



        try:
            for i in range(len(pasos)):
                paso = pasos[i]
                modo = paso['travel_mode']
                #diccio.update({i: pasos[i]['travel_mode']})
                if modo == 'WALKING':
                    agregar = {'tipo':modo,
                               'distancia':paso['distance']['value'],
                               'duracion':paso['duration']['value'],
                              'vehiculo':modo}

                elif modo == 'TRANSIT':

                    vehiculo = paso['transit_details']['line']['vehicle']
                    agregar = {'tipo':modo,
                               'distancia':paso['distance']['value'],
                               'duracion':paso['duration']['value'],
                               'vehiculo':vehiculo['name'] + ' - ' + vehiculo['type']}
                else:
                    agregar = np.nan

                diccio.update({i:agregar})
            return diccio
        except:
            return np.nan
    except:
        return np.nan
    
    
def trasbordo(googleDict):
    '''
    Esta funcion toma un diccionario de la API de google y 
    devuelve si en ese viaje hubo trasbordo
    '''
    try:
        return len(googleDict[0]['legs'][0]['steps'])  > 3
    except:
        return np.nan
    
def ingreso(modo,metrica):
    '''
    Esta funcion toma un modo generado por la funcion modos(googleDict)
    y devuelve:
    - tiempo de ingreso caminando al sistema
    - distancia de caminata para ingreso al sistema
    '''
    try:
        if len(modo) == 1:
            return 0
        elif modo[0]['tipo'] == 'WALKING':
            if metrica == 'duracion':
                return modo[0]['duracion']
            elif metrica == 'distancia':
                return modo[0]['distancia']

        else:
            return 0
    except:
        return np.nan
    
def egreso(modo,metrica):   
    '''
    Esta funcion toma un modo generado por la funcion modos(googleDict)
    y devuelve:
    - tiempo de egreso del sistema caminando 
    - distancia de egreso del sistema caminado 
    '''
    try:
        ultimoModo = len(modo) - 1

        if len(modo) == 1:
            return 0    
        elif modo[ultimoModo]['tipo'] == 'WALKING':
            if metrica == 'duracion':
                return modo[ultimoModo]['duracion']
            elif metrica == 'distancia':
                return modo[ultimoModo]['distancia']

        else:
            return 0
    except:
        return np.nan
    
    
def descripcionViaje(modo):
    '''
    Esta funcion toma un modo generado por la funcion modos(googleDict)
    y devuelve una descripcion del viaje 
    '''
    try:
        respuesta = [modo[i]['tipo'] for i in range(len(modo))]
    except:
        respuesta = np.nan
    return respuesta 

def generarConsulta(data,destino,transit_routing_preference=False):
    cantidadFilas = range(data.shape[0])
    #fewer transfers o less walking
    consultas = [googDirections(origins = (data.iloc[i].Y,data.iloc[i].X),
                                    destinations = destino,
                                    transit_routing_preference = transit_routing_preference,
                                   mode="transit") for i in cantidadFilas]

    
    data['consulta'] = consultas    
    return data

   
def extraerDataConsulta(data,destino,transit_routing_preference):
    data['fechaCorrida'] = str(datetime.datetime.now())
    data['destino'] = str(destino)
    data['preferenciasConsulta'] = transit_routing_preference
    
    data['tramos'] = [cantidadDeTramos(i) for i in data.consulta]
    data['distancia'] = [distancia(i) for i in data.consulta]
    data['costo'] = [costo(i) for i in data.consulta]
    data['tiempoTotal'] = [tiempoTotal(i) for i in data.consulta]
    data['modos'] = [modos(i) for i in data.consulta]
    data['descripcion'] = [descripcionViaje(i) for i in data.modos]
    data['duracionIngreso'] = [ingreso(i,'duracion') for i in data.modos]
    data['distanciaIngreso'] = [ingreso(i,'distancia') for i in data.modos]
    data['duracionEgreso'] = [egreso(i,'duracion') for i in data.modos]
    data['distanciaEgreso'] = [egreso(i,'distancia') for i in data.modos]
    data['tiempoEnSistema'] = data.tiempoTotal - data.duracionEgreso - data.duracionIngreso
    return data

def mapear(dataset,variable,destino,archivo,titulo):
    
    f, ax = plt.subplots(figsize=(8,8))
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    if variable == 'descripcion':
        dataset[variable] = dataset[variable].map(str)
        dataset.plot(column=variable,
             alpha=1,
             linewidth=0.2,
             ax=ax,
             cmap = 'Set2',
                     legend = True)
    else:
        dataset.plot(column=variable,
                 alpha=1,
                 linewidth=0.2,
                 ax=ax,
                 cmap = 'RdYlGn_r',
                 scheme='QUANTILES',
                      legend = True)
    ax.plot([destino[1]],[destino[0]],'bo')
    plt.title(titulo)
    plt.savefig(archivo)

    
def generarDistancia(dataset,destino):
    #proyecto a posgar 2007 banda 3
    dataset = dataset.to_crs(epsg=5345)
    dataset['distanciaLineal'] = dataset.geometry.distance(Point(destino))
    return dataset
    
def guardarData(dataset,nombre):
        
    dataset.descripcion = dataset.descripcion.map(str)
    dataset.modos = dataset.modos.map(str)
    dataset.consulta = dataset.consulta.map(str)

    
    dataset.to_file('resultados/'+str(nombre))
    dataset.to_csv('resultados/'+str(nombre)+'/'+str(nombre)+'.csv')