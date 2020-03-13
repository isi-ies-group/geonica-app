# -*- coding: utf-8 -*-
"""
Created on Sat Jun 23 17:28:23 2018

@author: ruben
"""
import datetime as dt
import struct

BYTEORDER = 'big'
PASS = 'geonica '


def cabecera(numero_estacion, numero_usuario):  #La cabecera de todos los mensajes recibidos por el sistema de medición
    DLE = bytes(chr(16), encoding='ascii')                  #Data Link Escape
    SYN = bytes(chr(22), encoding='ascii')                  #Syncronos Idle
    SOH = bytes(chr(1), encoding='ascii')                   #Start of Heading
    E = numero_estacion.to_bytes(2, byteorder=BYTEORDER)    #Numero de la estacion de la que se reciben los datos
    U = numero_usuario.to_bytes(2, byteorder=BYTEORDER)     #Numero del usuario que ha solicitado los datos
    #C = b'\x00'                                            #Número de comando que se ha solicitado
    
    CABECERA = DLE + SYN + DLE + SOH + E + U #+ C
    return CABECERA

'''
def trama_sincronizar(numero_estacion, numero_usuario):
    ahora = dt.datetime.now()
    
    DLE = bytes(chr(16), encoding='ascii')
    SYN = bytes(chr(22), encoding='ascii')
    E = numero_estacion.to_bytes(2, byteorder=BYTEORDER)
    comando_sinc = bytes(chr(0), encoding='ascii') # 0: codigo sync hora
    U = numero_usuario.to_bytes(2, byteorder=BYTEORDER)
    A = (ahora.year - 2000).to_bytes(1, byteorder=BYTEORDER)        
    M = ahora.month.to_bytes(1, byteorder=BYTEORDER)
    D = ahora.day.to_bytes(1, byteorder=BYTEORDER)
    d = ahora.isoweekday().to_bytes(1, byteorder=BYTEORDER)
    H = ahora.hour.to_bytes(1, byteorder=BYTEORDER)
    m = ahora.minute.to_bytes(1, byteorder=BYTEORDER)
    s = ahora.second.to_bytes(1, byteorder=BYTEORDER)
    X = 7 * b'\x00'
    ctrl = b'\xFF' +  b'\xFF'# Verificación de la configuración (CRC16, standard ITU-TSS) 0xFFFF evita verificación
    pasw = bytes(PASS, encoding='ascii')
    ENQ = bytes(chr(5), encoding='ascii')
    
    trama = DLE + SYN + E + comando_sinc + U + A + M + D + d + H + m + s + X + ctrl + pasw + ENQ
#    trama_bin = bin(int.from_bytes(trama, byteorder=BYTEORDER))
#    print(trama_bin)
    
    return trama
'''
def decodificar_recepcion(trama_bytes, numero_estacion, numero_usuario): #Se obtiene un booleano( o un entero) indicando si se ha producido algun error:
                                                                              # True: Recepcion correcta
                                                                              # False: Recepcion de bytes incorrecta
                                                                              # Entero: Indica el codigo del error producido (Mirar página 9 del Protocolo de comunicaciones de Geonica Meteodata 3000)
    trama = bytearray(trama_bytes)
    bytes_recibidos = len(trama)
    estado = bool()
    
    if bytes_recibidos == 13:                                           #Respuesta indicando sincronizacion completada o error en la comunicación
        if trama[:8] == cabecera(numero_estacion, numero_usuario):          #Comporbación de que la cabecera recibida es la correcta
            if (trama[11] == 4):                                                #Bits indicando el fin de la transmisión, sincronización completada
                estado = True                                                         #Se devuelve un booleano indicando sincronización completada
            elif (trama[11] == 21):                                             #Error en la sincronización
                return int.from_bytes(trama[10])                                    #Se devuelve el indicador del estado del error            
    elif bytes_recibidos == 193:            #Respuesta indicando las mediciones pedidas
        if trama[:8] == cabecera(numero_estacion, numero_usuario):          #Comporbación de que la cabecera recibida es la correcta
                estado = True
    else:
        estado = False                                                    #Estado de error
        
    return estado

def visulizar_trama(trama_bytes):
    '''
    Este método decodifica la trama recibida de la estación, el caso expuesto a continución se produce cuando se
    solicitan los valores intanstáneos de la estación. En el caso de que se soliciten otro tipo de valores, 
    los bytes del 117(trama_bytes[116]) al 188(trama_bytes[187]) no contienen ninguna información relevante.

    '''
    trama = []
    #CABECERA
    trama.append(trama_bytes[0])                                                        #Data Link Escape
    trama.append(trama_bytes[1])                                                        #Syncronos Idle
    trama.append(trama_bytes[2])                                                        #Data Link Escape
    trama.append(trama_bytes[3])                                                        #Start of Heading
    trama.append(int.from_bytes(trama_bytes[4:6], byteorder = BYTEORDER))               #Número de
    trama.append(int.from_bytes(trama_bytes[6:8], byteorder = BYTEORDER))               #   estación
    trama.append(trama_bytes[8])                                                        #Comando solicitado
    trama.append(int.from_bytes(trama_bytes[9:11], byteorder = BYTEORDER))              #Longitud de bytes de datos a entregar
    trama.append(trama_bytes[11])                                                       #Número de canales configurados
    trama.append(trama_bytes[12])                                                       #Año...
    trama.append(trama_bytes[13])                                                       #Mes...
    trama.append(trama_bytes[14])                                                       #Día...
    trama.append(trama_bytes[15])                                                       #Hora...
    trama.append(trama_bytes[16])                                                       #Minuto...
    trama.append(trama_bytes[17])                                                       #Segundo de la estación
    trama.append(trama_bytes[18])                                                       #Data Link Escape
    trama.append(trama_bytes[19])                                                       #Start of Text
    trama = trama + decodificar_IEEE32bit(decodificar_medidas(trama_bytes))             #Datos recibidos de los canales, y codificados en formato flotante IEEE 754 32bit(4 bytes por dato)
    
    lista1 = []                                                                         
    for i in range(48 - 1):                                                             #Número de muestra correspondiente desde el incio del perido
        inicio = 116 + i                                                                #de cálculo
        lista1.append(int.from_bytes(trama_bytes[inicio:(inicio + 2)], byteorder = BYTEORDER))
    trama.append(lista1)
    
    lista2 = []
    for i in range(24 - 1):                                                             #Indicador del estado del canal:
        lista2.append(trama_bytes[164 + i])                                             # 0:Normal 1:Alarma por umbral superior 2:Alarma por umbral inferior
    trama.append(lista2)
        
    trama.append(trama_bytes[188])                                                      #Data Link Escape
    trama.append(trama_bytes[189])                                                      #Enf of Text
    trama.append(bytearray(trama_bytes[190:192]))                                       #Checksum, equivale al XOR de los bytes pares e impares de datos, por separado; para más info ver página 11 protocolo de comunicaciones geonica
    trama.append(trama_bytes[192])                                                      #Enquiring
    
    return trama

def trama_medidas_instantaneas(numero_estacion, numero_usuario):
    
    DLE = bytes(chr(16), encoding='ascii')
    SYN = bytes(chr(22), encoding='ascii')
    E = numero_estacion.to_bytes(2, byteorder=BYTEORDER)
    comando_sinc = bytes(chr(1), encoding='ascii') # 1: codigo sync petición de medidas instantáneas
    U = numero_usuario.to_bytes(2, byteorder=BYTEORDER)
    X = 14 * b'\x00'
    ctrl = b'\xFF' +  b'\xFF'# Verificación de la configuración (CRC16, standard ITU-TSS) 0xFFFF evita verificación
    pasw = bytes(PASS, encoding='ascii')
    ENQ = bytes(chr(5), encoding='ascii')
    
    trama = DLE + SYN + E + comando_sinc + U + X + ctrl + pasw + ENQ

    return trama

def trama_medidas_no_instantaneas(numero_estacion, numero_usuario, comando):
    
    DLE = bytes(chr(16), encoding='ascii')
    SYN = bytes(chr(22), encoding='ascii')
    E = numero_estacion.to_bytes(2, byteorder=BYTEORDER)
    comando_sinc = bytes(chr(comando), encoding='ascii') # 12-21: codigo del comando, ver página 12 del Protocolo de comunicaciones de Geonica Meteodata 3000
    U = numero_usuario.to_bytes(2, byteorder=BYTEORDER)
    X = 14 * b'\x00'
    ctrl = b'\xFF' +  b'\xFF' # Verificación de la configuración (CRC16, standard ITU-TSS) 0xFFFF evita verificación
    pasw = bytes(PASS, encoding='ascii')
    ENQ = bytes(chr(5), encoding='ascii')
    
    trama = DLE + SYN + E + comando_sinc + U + X + ctrl + pasw + ENQ

    return trama

def decodificar_medidas(trama_bytes):
    trama = bytearray(trama_bytes)
    medidas = []
    canales_configurados = trama_bytes[11]                    #Bytes indicando el numero de canales configurados
    
    for i in range(canales_configurados):                          
        byte_comienzo_muestra = 20 + (4 * i)                                  #Comienzo de los bytes de datos
        byte_fin_muestra = byte_comienzo_muestra + 4                         #Longitud de cada muestra de 4bytes
        medidas.append(trama[byte_comienzo_muestra:byte_fin_muestra])   #Se añade a la lista de medidas la medida del siguiente canal   
        
    return medidas

def decodificar_IEEE32bit(num_hex):
    medida = []
    num_medidas = len(num_hex)                                  #Se obtiene la longitud del array de medidas, o lo que es lo mismo, el numero de canales configurados
    for i in range(num_medidas):                                #Se atraviese el array 
        medida.append(struct.unpack('>f', num_hex[i])[0])           #Por cada canal configurado, se transforma a float la medicion, actualmente codificado en IEEE 754 32bit
    
    return medida

def decodificar_FechayHora(trama_bytes):
    #class datetime.datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0)  #Constructor de la clase datetime
    date = dt.datetime(trama_bytes[12] + 2000, trama_bytes[13], trama_bytes[14], trama_bytes[15], trama_bytes[16], trama_bytes[17])
    
    '''
    La trama contiene la siguiente información:
    
    date.day = trama_bytes[14]
    date.month = trama_bytes[13]
    date.year = trama_bytes[12] + 2000                  #Se le suma 2000, ya que la estación solo se almacena la centena en la que nos encontramos
    
    date.hour = trama_bytes[15]
    date.minute = trama_bytes[16]
    date.second = trama_bytes[17]
    '''
    
    return date