# -*- coding: utf-8 -*-
"""

@author: Martin
"""
import pyodbc
import pandas as pd
import datetime as dt
import yaml
import csv
import os
import pytz
from pathlib import Path

# En el servidor SQL hay que habilitar el puerto TCP del servidor y abrirlo en el firewall
# https://docs.microsoft.com/es-es/sql/relational-databases/lesson-2-connecting-from-another-computer?view=sql-server-ver15

module_path = os.path.dirname(__file__)

try: 
    with open(str(Path(module_path, 'bbdd_config.yaml')),'r') as config_file:
        config = yaml.load(config_file, Loader = yaml.FullLoader) #Se utiliza el FullLoader para evitar un mensaje de advertencia, ver https://msg.pyyaml.org/load para mas información
        servidor = config['Servidor']                             #No se utiliza el BasicLoader debido a que interpreta todo como strings, con FullLoader los valores numéricos los intrepreta como int o float
        bbdd = config['BBDD']
        file = config['File']
        dict_renombrar = config['Dict_Rename']
        del config                       

except yaml.YAMLError:
    print ("Error in configuration file")

SERVER_ADDRESS = servidor['IP']  # IP PC Ruben: '138.4.46.139'      IP PC Martin: '138.4.46.164'      IP PC Server: '138.4.46.69'
PORT = str(servidor['Puerto'])              
DDBB_name = bbdd['Database']
database = bbdd['Nombre']    #Nombre por defecto que se le asigna a la base de datos
username = bbdd['Usuario']            #Usuario por defecto
password = bbdd['Contrasena']            #Contraseña por defecto

DEFAULT_NAME = file['Nombre']
DEFAUL_PATH = file['Path']
    

# pyodbc.drivers() # lista de drivers disponibles
# ['SQL Server',
#  'SQL Server Native Client 11.0',
#  'ODBC Driver 11 for SQL Server']

# Instalar driver (si no está ya al instalar GEONICA SUITE 4K)
# https://www.microsoft.com/en-us/download/details.aspx?id=36434

def _request_ddbb(server_address = SERVER_ADDRESS):                                            #request común a todas las funciones
    request = (                                                         
            'DRIVER={ODBC Driver 11 for SQL Server};'                   ##Se seleccion el driver a utilizar
            # la ; hace que falle si hay más campos
            f'SERVER={server_address},{PORT}\{DDBB_name};'          ##Dirrección IP del servidor dónde se encuentre la base de datos 
            f'DATABASE={database};'                                     ##Nombre de la base de datos en la que se encuentran los datos
            f'UID={username};'                                          ##Usuario con el que se accede a la base de datos
            f'PWD={password}'                                           ##Contreseña de acceso a la base de datos
    )
    return request;


def get_data_raw(numero_estacion, fecha_ini, fecha_fin = dt.date.today().strftime('%Y-%m-%d %H:%M')):
    '''
    Se obtienen los datos en bruto de una estacion deseada, 
        estos datos incluyen todos las funciones que estén configuradas en la estación.

    '''
    request = _request_ddbb()
    
    query_data = (
            "SELECT * FROM Datos "
            "WHERE NumEstacion = " + str(numero_estacion) + " AND "
            "Fecha >= '" + fecha_ini + "' AND "
            "Fecha < '" + fecha_fin + "'"
    ) #Se solicitan las medidas, junto son su correspondiende NumParámetro, de un periodo determinado
    
    data_raw = pd.read_sql(query_data, pyodbc.connect(request))#Se construye el DataFrame con los valores pedidos a la base de datos
    
    return data_raw


def get_parameters():
    '''
    Mediante esta función se obtienen las funciones que están disponibles en la estacion,
        junto con su número de parametro y unidad.

    '''
    request = _request_ddbb()
    
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
    request = _request_ddbb()
    
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
    
    request = _request_ddbb()
    
    query_functions = (
            'SELECT NumFuncion, Nombre FROM dbo.Funciones_MI '
            'WHERE Ididioma = 1034' #Se solicita en nombre de las funciones en español; 2057, para inglés
    )   
    
    funciones = (
            pd.read_sql(query_functions, pyodbc.connect(request))
    )
    
    funciones.set_index('NumFuncion', inplace = True)
    return funciones


def lee_dia_geonica_ddbb(dia, numero_estacion, lista_campos=None):
    #    INPUT:    dia (datetime.date)
    #            lista_campos (lista con campos a obtener de la BBDD)
    #    OUTPUT:    datos (pandas.DataFrame)
    #    CONFIG:    numero_estacion
    #            path_mdb, fichero_mdb
    #            driver

    #Si el usuario no especifica ninguna lista de campos deseados, por defecto de le devuelven todos los canales
    # disponibles de la estación
    if lista_campos == None:
        lista_campos = ['yyyy/mm/dd hh:mm']
        canales = get_channels_config(numero_estacion)['Abreviatura'].tolist()
        lista_campos += canales
    
    dia_datetime = dt.datetime.combine(dia, dt.datetime.min.time())
    formato_tiempo = '%Y-%m-%d %H:%M'
    
    # Como se lee hora UTC y la civil necesita de valores del día anterior, se leen minutos del día anterior
    # El dataset tiene 1 día + 2 horas, que luego al convertir a hora civil se tomarán solo los minutos del día en cuestión
    fecha_ini = (dia_datetime - dt.timedelta(hours=2)).strftime(formato_tiempo)
    fecha_fin = (dia_datetime + dt.timedelta(hours=24)).strftime(formato_tiempo)
                                                    
    # https://docs.microsoft.com/es-es/sql/relational-databases/lesson-2-connecting-from-another-computer?view=sql-server-ver15
    
    data = get_data_raw(numero_estacion, fecha_ini, fecha_fin)
    
    # Se procesa data solo si hay contenido
    if len(data) != 0:
        # dict_estacion tiene como indice el numero_estacion y contenido 'nombre_parametro_ficheros' y 'mtype'
        # nombre, mtype
        #   'mtype'     Measurement type: Enter an integer to determine which
        #               information on each one minute interval to return.  Options are.
        #               0       1   2   3   4   5
        #               Ins.    Med Acu Int Max Min
               
        dict_estacion = get_channels_config(numero_estacion).set_index('NumParametro');
           
        def tipo_medida(d):
            try:
                return dict_estacion.loc[d]['NumFuncion']
            except:
                pass        
            
        # Selecciona las filas que tienen NumFuncion == el tipo de medida dado el NumParametro
        data = data[data['NumFuncion'] ==
                    data['NumParametro'].apply(tipo_medida)]

        # Conversion de parametros en filas a columnas del Dataframe
        data = data.pivot_table(index='Fecha', columns=[
                                'NumParametro'], values='Valor')

        # Si los valores son medias (mtype==1), sería el valor de hace 30 seg. Por lo tanto se toma el que realmente le corresponde.
        # samplea cada 30seg, se interpola para que haya valor, se desplazan los valores 30seg para cuadrar y se reajusta de nuevo con el indice original.
        
        def adapta(columna):
            try:
                #if dict_estacion[columna.name][1] == 1: Se sustituye por:
                if dict_estacion.loc[columna.name]['NumFuncion'] == 1:
                    return columna.resample('30S').interpolate(method='linear').shift(periods=-30, freq='S').reindex(data.index)
                else:
                    return columna
            except:
                pass

        data = data.apply(adapta, axis=0)
        # El ultimo valor si se ha ajustado, se queda en NaN. Se arregla tomando el penultimo + diff
        data.iloc[-1] = data.iloc[-2] + (data.diff().mean())

        # Cambia codigo NumParametro de BBDD a su nombre de fichero
        
        data_channels = get_parameters().set_index('NumParametro') #Se obtienen los números de los parámetros...
        data.rename(columns = data_channels['Abreviatura'], inplace=True) #... y se sustituye el NumParametro por el Nombre
        
    # cambia index a hora civil
    data.index = (data.index.tz_localize(pytz.utc).
                  tz_convert(pytz.timezone('Europe/Madrid')).
                  tz_localize(None))
    
    # filtra y se queda solo con los minutos del dia en cuestion, una vez ya se han convertido a hora civil
    data = data[str(dia)]
    
    # Si data está vacio, se crea con valores NaN
    indice_fecha = pd.Index(pd.date_range(
        start=dia, end=dt.datetime.combine(dia, dt.time(23, 59)), freq='1T'))
    if len(data) == 0:
        data = pd.DataFrame(index=indice_fecha, columns=lista_campos)

    # En caso de que el indice esté incompleto, se reindexa para que añada nuevos con valores NaN
    if len(data) != len(indice_fecha):
        data = data.reindex(index=indice_fecha)

    # En caso de que el columns esté incompleto, se reindexa para que añada nuevos con valores NaN

    lista_campos_corta = lista_campos.copy()
    lista_campos_corta.remove('yyyy/mm/dd hh:mm')
    # lista_campos_corta.remove('yyyy/mm/dd')
    if set(lista_campos_corta).issuperset(data.columns):
        data = data.reindex(columns=lista_campos)
    
    # # Separa y crea en 2 columnas fecha y hora
    # # tambien valdría data.index.strftime('%Y/%m/%d')
    # data['yyyy/mm/dd'] = [d.strftime('%Y/%m/%d') for d in data.index]
    # data['hh:mm'] = [d.strftime('%H:%M') for d in data.index]
    data['yyyy/mm/dd hh:mm'] = [d.strftime('%Y/%m/%d %H:%M') for d in data.index]

    return data


def genera_fichero_meteo(dia_inicial, dia_final=None, nombre_fichero=None, path_fichero=DEFAUL_PATH):
    '''
    
    Parameters
    ----------
    dia_inicial : str(AAAA-MM-DD) o datetime-like
    dia_final : str(AAAA-MM-DD) o datetime-like, optional
        Por defecto es el día antetior.
    nombre_fichero : string, optional
        Por defecto es: meteoAAAA_MM_DD
    path : string, optional
        Rellenar en el caso de que el usuario
        del script no sea el servidor.

    Returns
    -------
    bool
        True: Fichero creado correctamente
        False: Error en la función

    '''
    
    #Si no se indica fecha del final del peridod deseado,
    #se reciben los datos hasta el día anterior
    if dia_final == None:
        dia_final = dt.date.today() - dt.timedelta(days=1)

    #En caso de no indicarse ningun nombre de fichero:
    if nombre_fichero == None:
        nombre_fichero = DEFAULT_NAME
    
    
    # %% Generación fichero llamando a función lee_dia_geonica_ddbb(dia, lista_campos)
    
    # Se llama tantas veces a la funcion lee_dia_geonica_ddbb() como días haya en el perido indicado
    frames = []
    for d in pd.date_range(start=dia_inicial, end=dia_final):
        dia = d.date()
        
        # Lee BBDD y obtiene datos del dia
        data_316 = lee_dia_geonica_ddbb(dia, 316)
        data_2169 = lee_dia_geonica_ddbb(dia, 2169)
        #Para que no se produzcan errorres, se asigna el sufijo "_2" a los parámetros de la estacion 2169 que se repetan en ambas estaciones.
        data_i = data_316.join(data_2169, rsuffix='_2')
        
        frames.append(data_i)
    
    #Finalmente se concatenan los datos de cada día para formar el DataFrame del periodo completo
    data = pd.concat(frames)
    #Como la fecha y la hora son columnas compartidas, e idénticas, se elimina los duplicados y canales innecesarios.
    data.drop(columns={'yyyy/mm/dd hh:mm_2', 'VRef Ext.', 'Bateria', 'Bateria_2', 'Est.Geo3K', 'Est.Geo3K_2'}, inplace=True)
    
    data.rename(columns=dict_renombrar, inplace=True)
    
    # Crear fichero .txt
    # Escribe la cabecera. Pandas utiliza el index standard de tipo datenum y solo
    # crea una columna y no dos como se usa normalmente con estos ficheros, por lo
    # que se escribe antes manualmente
    formato_fecha = '%Y_%m_%d'
    nombre_fichero_texto = path_fichero + nombre_fichero + \
        dia.strftime(formato_fecha) + '.txt'
    
    with open(nombre_fichero_texto, 'w', newline='') as f:
        a = csv.writer(f, delimiter='\t')
        a.writerow(data.columns)
    
    # Escribe los datos seleccionados en cols en modo append sin cabecera ni index
    data.to_csv(nombre_fichero_texto, columns=data.columns, mode='a', sep='\t',
                float_format='%.3f', header=False, index=False, na_rep='NaN')
    
    print('Ha escrito fichero ' + nombre_fichero_texto)
    
    # %% Grafica
    '''
    plt.figure(figsize=(8, 6))
    plt.title('DNI+isotpyes - ' + nombre_fichero +
              dia.strftime(formato_fecha))
    plt.grid(which='minor')
    plt.ylabel('Irradiance $\mathregular{[W·m^{-2}]}$')
    data.Top.plot(legend=True)
    data.Mid.plot(legend=True)
    data.Bot.plot(legend=True)
    data.Rad_Dir.plot(legend=True)
    plt.ylim([0, 1100])
    
    nombre_fichero_imagen = path_fichero + 'img/' + \
        nombre_fichero + dia.strftime(formato_fecha) + '.png'
    plt.savefig(nombre_fichero_imagen)
    
    print('Ha escrito fichero ' + nombre_fichero_imagen)
    '''
    
    return True