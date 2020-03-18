# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 17:22:31 2020

@author: Martin
"""
import yaml

DEFAULT_PATH = 'sensores_config.yaml'

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
        

#%%

config = lee_config()

print(config.servidor)
print(config.estaciones)
#print(config.sensores)     
    

