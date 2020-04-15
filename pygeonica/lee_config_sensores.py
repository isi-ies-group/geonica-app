# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 17:22:31 2020

@author: Martin
"""
import yaml
from pathlib import Path
import os
import bbdd


#%% Lectura de la configuración del archivo YAML
module_path = os.path.dirname(__file__)
DEFAULT_PATH = str(Path(module_path, 'sensores_config.yaml'))

def lee_config(dato, path=DEFAULT_PATH):
    '''
    Lee del archuvo de configuración los datos que desee el usuario.

    Parameters
    ----------
    dato : str
        Opciones: Estaciones, Sensores, Servidor, BBDD
    path : str, optional
        Ruta al archivo de configuración. 
        Por defecto es el archivo sensores_config.yaml que se encuentra
        en la misma carpeta que el script.

    Returns
    -------
    Dict
        Diccionario con la configuración. Varía según la información solicitada.
    '''
    
    try: 
        with open(path,'r') as config_file:
            config_yaml = yaml.load(config_file, Loader = yaml.FullLoader) #Se utiliza el FullLoader para evitar un mensaje de advertencia, ver https://msg.pyyaml.org/load para mas información
                                                                    #No se utiliza el BasicLoader debido a que interpreta todo como strings, con FullLoader los valores numéricos los intrepreta como int o float
        return config_yaml[dato]
    except yaml.YAMLError:
        print ("Error en el fichero de configuración")
    except:
        print("Error en la lectura del fichero")
    
        
#%% Lectura de los sensores del fichero de configuración
def lee_canales_sensores():
    '''
    Returns
    -------
    info : dict
        Diccionarioque contiene la información sobre los canales, lógicos y físicos, obtenidos
        del archivo YAML.
        El diccionario de cada estación está ordenado por el número de canal lógico.En cada estación,
        hay un diccionario por cada sensor. 
        El diciconario de cada sensor está formado por el nombre del canal lógico(su Abreviatura en la bbdd) y 
        el número de canal fisico del sensor.

    '''
    
    # Se obtiene la lista con los sensores disponibles
    lista_sensores = lee_config('Sensores')
    
    # Se inicializa el diccionario que contendrá la información de los sensores concetados 
    # a cada estación
    info = {316:{}, 2169:{}}
    
    # Se recorre la lista de los sensores
    for sensor in lista_sensores:
        # Si el sensores está colocado en alguna estación...
        if sensor['NumEstacion'] != None:
            # Hay sensores que necesitan dos canales de medida...
            if type(sensor['NumCanal_Logico']) == str:
                # Variable auxiliar necesaria para conocer que canal estamos añadiendo a la lista
                i = 0
                # Se crea una lista con los número de los canales lógicos utilizdos por el sensor
                canales_logicos = sensor['NumCanal_Logico'].split(', ')
                # En caso de que el sensor no esté conectado a ningún canal físico, 
                # p.ej. sensor de viento concetado al puerto serie, se crea un a lista con Valores None,
                #  indicando que este canal lógico no corresponde a ningún canal físico
                if sensor['NumCanal_Fisico'] != None:
                    canales_fisicos = sensor['NumCanal_Fisico'].split(', ')
                else:
                    canales_fisicos = []
                    for j in range(len(canales_logicos)):
                        canales_fisicos.append(None)
                # Se crea una lista con los nombres de los parámetros asociados a cada canal lógico
                nombres = sensor['Nombre_Parametro'].split(', ')
                # Se recorre la lista de canales lógicos, y se añade al diccionario de la correspondiente estación
                #  la información del canal lógico
                for canal_logico in canales_logicos:
                    canal_logico = int(canal_logico)
                    can_fis = canales_fisicos[i]
                    nom_param = nombres[i]
                    
                     # Se añade la información al diccionario:
                    if not canal_logico in info[sensor['NumEstacion']]:
                        info[sensor['NumEstacion']][canal_logico] = {'Canal_Fisico': can_fis, 'Nombre_Parametro': nom_param}
                    else:
                        print('Los canales lógicos de dos sensores coinciden, comprobar el archivo de configuración.')
                        print('El canal lógico Nº ' + str(canal_logico) + ' tiene configurado dos sensores: ' + info[sensor['NumEstacion']][canal_logico]['Nombre_Parametro'] + ' y ' + nom_param + '.')
                    
                    # Finalmente se aumenta el valor de la variable auxiliar,
                    # indicando que canal lógico añadir a continuación
                    i += 1
            
            # En caso de que el sesor esté ocupando solo un canal lógico...
            else:
                canal_logico = sensor['NumCanal_Logico']
                can_fis = sensor['NumCanal_Fisico']
                nom_param = sensor['Nombre_Parametro']
                
                # Se añade la información al diccionario:
                if not canal_logico in info[sensor['NumEstacion']]:
                    info[sensor['NumEstacion']][canal_logico] = {'Canal_Fisico': can_fis, 'Nombre_Parametro': nom_param}
                else:
                    print('Los canales lógicos de dos sensores coinciden, comprobar el archivo de configuración.')
                    print('El canal lógico Nº ' + str(canal_logico) + ' de la estación ' + str(sensor['NumEstacion']) + ' tiene configurado dos sensores: ' + info[sensor['NumEstacion']][canal_logico]['Nombre_Parametro'] + ' y ' + nom_param + '.')
                    print('El sensor ' + nom_param + ' no se va añadir a la lista de sensores. Si quieres mantener este sensor en la lista, corrija el archivo de configuración.')
    return info
        
#%% Lectura de los canales lógico, ordenados, de las estaciones:
def lee_canales_estacion():
    '''
    Returns
    -------
    canales : dict
        Diccionario que contiene los canales lógicos configurados por cada estación.
        Por cada estación, identificada por su número, hay una lista que contiene los nombres
        de los canales lógicos, ordenados, que se encuentran en la estación.
    '''
    
    canales = {}
    estaciones = []
    
    # Se obtiene el numero de estaciones configuradas
    config_estaciones = lee_config('Estaciones')
    for elemento in config_estaciones:
        estaciones.append(int(elemento['Numero']))
        
    # Se obtienen los canles configurados por cada estación 
    for estacion in estaciones:
        info_canales = bbdd.get_channels_config(estacion)['Abreviatura'].tolist()
        canales[estacion] = info_canales
    
    return canales
        
#%% Comprobación que la configuración es correcta
def comprueba_canales():

    pertenencia_OK = True
    orden_OK = True
    
    #
    canales_estacion = lee_canales_estacion()
    canales_sensores = lee_canales_sensores()

    # Se recorre la lista de estaciones...
    for estacion in canales_estacion.keys():
        # Se recorre los canales lógicos por cada estación...
        for canal_logico in canales_sensores[estacion].keys():
            # Se obtiene los valores que se van a comparar
            canal_logico = int(canal_logico)
            nom_param = canales_sensores[estacion][canal_logico]['Nombre_Parametro']
            # Si el nombre del canal no está en la lista de canales de la estación,
            # se indica al usuario que hay un error en el archivo de configuración
            if not nom_param in canales_estacion[estacion]:
                print('El canal ' + nom_param + ' no está en la lista de canales obtenida por la base de datos de la estación ' + str(estacion) + '. Comprobar el archivo de configuración.')
                pertenencia_OK = False
                break
            # El nombre del canal corresponde a la estación...
            else:
                # Se comprueba que el canal lógico es igual al obtenido a obtenido por la base de datos
                if canales_estacion[estacion][canal_logico - 1] != nom_param:
                    print('El canal ' + nom_param + ' no corresponde con el número de canal lógico obtenido en la estación ' + str(estacion) + '. Comprobar el archivo de configuración.')
                    orden_OK = False
                    break
    
    # En el caso de que no se haya producido ningún error, se infroma al usuario de ello...
    if orden_OK & pertenencia_OK:
        print('La configuración de los senores del archivo es igual a la obtenida por la base de datos.')
    
    return pertenencia_OK, orden_OK        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

