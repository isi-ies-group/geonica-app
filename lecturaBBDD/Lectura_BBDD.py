# -*- coding: utf-8 -*-
"""

@author: Martin
"""
import pyodbc
import pandas as pd
import datetime as dt
import yaml
import os
from pathlib import Path

# En el servidor SQL hay que habilitar el puerto TCP del servidor y abrirlo en el firewall
# https://docs.microsoft.com/es-es/sql/relational-databases/lesson-2-connecting-from-another-computer?view=sql-server-ver15

module_path = os.path.dirname(__file__)

try: 
    with open(str(Path(module_path, 'config_BBDD.yaml')),'r') as config_file:
        config = yaml.load(config_file, Loader = yaml.FullLoader) #Se utiliza el FullLoader para evitar un mensaje de advertencia, ver https://msg.pyyaml.org/load para mas información
        servidor = config['Servidor']                             #No se utiliza el BasicLoader debido a que interpreta todo como strings, con FullLoader los valores numéricos los intrepreta como int o float
        bbdd = config['BBDD']
        del config                       

except yaml.YAMLError:
    print ("Error in configuration file")

server = servidor['IP']  # IP PC Ruben: '138.4.46.139'      IP PC Martin: '138.4.46.164'      IP PC Server: '138.4.46.69'
port = str(servidor['Puerto'])              
DDBB_name = bbdd['Database']
database = bbdd['Nombre']    #Nombre por defecto que se le asigna a la base de datos
username = bbdd['Usuario']            #Usuario por defecto
password = bbdd['Contrasena']            #Contraseña por defecto
    
    

# pyodbc.drivers() # lista de drivers disponibles
# ['SQL Server',
#  'SQL Server Native Client 11.0',
#  'ODBC Driver 11 for SQL Server']

# Instalar driver (si no está ya al instalar GEONICA SUITE 4K)
# https://www.microsoft.com/en-us/download/details.aspx?id=36434

def request_ddbb(server_address = server):                                            #request común a todas las funciones
    request = (                                                         
            'DRIVER={ODBC Driver 11 for SQL Server};'                   ##Se seleccion el driver a utilizar
            # la ; hace que falle si hay más campos
            f'SERVER={server_address},{port}\{DDBB_name};'          ##Dirrección IP del servidor dónde se encuentre la base de datos 
            f'DATABASE={database};'                                     ##Nombre de la base de datos en la que se encuentran los datos
            f'UID={username};'                                          ##Usuario con el que se accede a la base de datos
            f'PWD={password}'                                           ##Contreseña de acceso a la base de datos
    )
    return request;


def get_data_raw(numero_estacion, fecha_desde, fecha_hasta = dt.date.today()):
    '''
    Se obtienen los datos en bruto de una estacion deseada, 
        estos datos incluyen todos las funciones que estén configuradas en la estación.

    '''
    request = request_ddbb()
    
    query_data = (
            'SELECT Fecha, Valor, NumParametro FROM Datos '
            'WHERE NumEstacion = ' + str(numero_estacion) + ' AND '
            f"Fecha >= '{fecha_desde}' AND Fecha < '{fecha_hasta}' "
    ) #Se solicitan las medidas, junto son su correspondiende NumParámetro, de un periodo determinado
    
    data_raw = (
            pd.read_sql(query_data, pyodbc.connect(request))
            .pivot_table(index='Fecha', columns=['NumParametro'], values='Valor')
    ) #Se construye el DataFrame con los valores pedidos a la base de datos
    
    data_channels = get_parameters().set_index('NumParametro') #Se obtienen los números de los parámetros...
    datos = data_raw.rename(columns = data_channels['Abreviatura']) #... y se sustituye el NumParametro por el Nombre
    return datos

def get_parameters():
    '''
    Mediante esta función se obtienen las funciones que están disponibles en la estacion,
        junto con su número de parametro y unidad.

    '''
    request = request_ddbb()
    
    query_parameters = (
            'SELECT NumParametro, Nombre, Abreviatura, Unidad FROM Parametros_spanish '
    )
    
    data_parameters = (
            pd.read_sql(query_parameters, pyodbc.connect(request))
    )
    
    #parametros = data_parameters.set_index('NumParametro')
    return data_parameters
    

def get_channels_config(numero_estacion):
    '''
    Devuelve una lista de los canales configurasdos en la estación indicada,
    estos canales estan ordenados en el mismo orden en el que los deveulve la estación
    cuando se le solicita (mediante puerto Serie, conexión IP, etc. ) los datos de los canales.
    '''
    request = request_ddbb()
    
    query_channels_config = (
            'SELECT Canales.NumFuncion, Canales.Canal, Parametros_spanish.Abreviatura, Parametros_spanish.NumParametro '
            'FROM Canales '
            'INNER JOIN Parametros_spanish ON Canales.NumParametro = Parametros_spanish.NumParametro '
            'INNER JOIN Funciones ON Funciones.NumFuncion = Canales.NumFuncion '
            'WHERE NumEstacion = ' + str(numero_estacion)
    )
    
    data_channels_config = (
            pd.read_sql(query_channels_config, pyodbc.connect(request))
     )
    
    data_channels_config.set_index('Canal', inplace = True)
    data_channels_config.sort_values(by = 'Canal', inplace= True)
    canales = data_channels_config.drop_duplicates(subset='Abreviatura').reset_index().drop(columns='Canal')
    return canales

def get_functions():
    '''
    Devuelve una lista con el número correspondiente a la función.
    '''
    
    request = request_ddbb()
    
    query_functions = (
            'SELECT NumFuncion, Nombre FROM dbo.Funciones_MI '
            'WHERE Ididioma = 1034' #Se solicita en nombre de las funciones en español; 2057, para inglés
    )   
    
    funciones = (
            pd.read_sql(query_functions, pyodbc.connect(request))
    )
    
    funciones.set_index('NumFuncion', inplace = True)
    return funciones

#%%

#Test de las funciones definidas anteriormente:


#funciones = get_functions()
#canales = get_channels_config(2169)
#params = get_parameters()
# datos = get_data_raw(2169, "2020-01-20")

