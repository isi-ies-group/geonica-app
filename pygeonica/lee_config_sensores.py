# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 17:22:31 2020

@author: Martin
"""
import yaml
from pathlib import Path
import os
from . import bbdd


module_path = os.path.dirname(__file__)
DEFAULT_PATH = str(Path(module_path, 'sensores_config.yaml'))

class lee_config:
    def __init__(self, path=DEFAULT_PATH):
        try: 
            with open(path,'r') as config_file:
                self.config_yaml = yaml.load(config_file, Loader = yaml.FullLoader) #Se utiliza el FullLoader para evitar un mensaje de advertencia, ver https://msg.pyyaml.org/load para mas información
                                                                        #No se utiliza el BasicLoader debido a que interpreta todo como strings, con FullLoader los valores numéricos los intrepreta como int o float
            
            self.estaciones = self.config_yaml['Estaciones']
            self.sensores = self.config_yaml['Sensores']
            self.servidor = self.config_yaml['Servidor']
            self.BBDD = self.config_yaml['BBDD']
            
        except yaml.YAMLError:
            print ("Error en el fichero de configuración")
        except:
            print("Error en la lectura del fichero")
        
#%% Lectura de los sensores del fichero de configuración

# Se obtiene la lista con los sensores disponibles
lista_sensores = lee_config().sensores

# Se inicializa el diccionario que contendrá la información de los sensores concetados 
# a cada estación
estaciones = {316:{}, 2169:{}}

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
                estaciones[sensor['NumEstacion']][canal_logico] = {'Canal_Fisico': can_fis, 'Nombre_Parametro': nom_param}
                
                # Finalmente se aumenta el valor de la variable auxiliar,
                # indicando que canal lógico añadir a continuación
                i += 1
        
        # En caso de que el sesor esté ocupando solo un canal lógico...
        else:
            canal_logico = sensor['NumCanal_Logico']
            can_fis = sensor['NumCanal_Fisico']
            nom_param = sensor['Nombre_Parametro']
            
            # Se añade la información al diccionario:
            estaciones[sensor['NumEstacion']][canal_logico] = {'Canal_Fisico': can_fis, 'Nombre_Parametro': nom_param}
    
        
#%% Lectura de los canales lógico, ordenados, de las estaciones:

canales = {}
for estacion in [316, 2169]:
    info_canales = bbdd.get_channels_config(estacion)['Abreviatura'].tolist()
    canales[estacion] = info_canales
        
#%% Comprobación que la configuración es correcta

config_OK = True

# Se recorre la lista de estaciones...
for estacion in canales.keys():
    # Se recorre los canales lógicos por cada estación...
    for canal_logico in estaciones[estacion].keys():
        # Se obtiene los valores que se van a comparar
        canal_logico = int(canal_logico)
        nom_param = estaciones[estacion][canal_logico]['Nombre_Parametro']
        # Si el nombre del canal no está en la lista de canales de la estación,
        # se indica al usuario que hay un error en el archivo de configuración
        if not nom_param in canales[estacion]:
            print('El canal ' + nom_param + ' no está en la lista de canales obenida por la base de datos. Comprobar el archivo de configuración.')
            config_OK = False
            break
        # El nombre del canal corresponde a la estación...
        else:
            # Se comprueba que el canal lógico es igual al obtenido a obtenido por la base de datos
            if canales[estacion][canal_logico - 1] != nom_param:
                print('El canal' + nom_param + 'no corresponde con el número de canal lógico obtenido por la estación. Comprobar el archivo de configuración.')
                config_OK = False
                break

# En el caso de que no se haya producido ningún error, se infroma al usuario de ello...
if config_OK:
    print('La configuración de los senores del archivo es igual a la obtenida por la base de datos.')
            
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

