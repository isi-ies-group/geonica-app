# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 11:22:11 2020

@author: Martin
"""
import tramas_geonica
import serial
import socket
import time



class Estacion:
    def __init__(self, num_estacion, Config_Serial = None, Config_Socket = None, tiempo_espera_datos = 0.5, tiempo_rts_activo = 0.1):
        self.numero_estacion = num_estacion
        self.tiempo_espera_datos = tiempo_espera_datos
        self.tiempo_rts_activo = tiempo_rts_activo
        self.address = ["",""]
        
        #Configuracion del puerto serie con los valores por defecto de la configurqacion de la estacion
        if (Config_Serial == None):
            self.ser = serial.Serial(
                port=None,
                baudrate=57600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            self.ser.close()
        else:
            self.ser = Config_Serial
            
        if (Config_Socket == None):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.bind(('',4096))
            except:
                print('Socket ya conectado.')
        else:
            try:
                self.sock = Config_Socket
                self.sock.bind(('',4096))
            except:
                print('Socket ya conectado.')
            
    def __del_(self):
        self.sock.close()
        self.ser.close()
            
    def set_address(self, ip_address, port):
        try:
            self.address = (ip_address, port)
            self.sock.connect(self.address)
            return True
        except: 
            return False
        
    def set_serial_port(self, Port):
        try:
            self.ser.port = Port
            return True 
        except:
            return False
        
    def close_connection(self):
        try:
            self.ser.close()
            self.sock.close()
            return True
        except:
            return False
    
    def medidas_no_intantaneas(self, num_usuario, tipo_medida):
        "COMUNICACIÓN POR EL PUERTO SERIE"
        if (self.ser.port != None):
            try:
                self.ser.open()
            except:
                pass
            print("Comunicando por puerto Serie...")
            # Debe activarse la linea RTS 1seg. antes del envio para que el dispositivo se prepare, si esta en modo ahorro,
            ## Mantener nivel alto durante 100ms y descactivar es suficiente  Referencia: Protocolo de comunicaciones Geonica Meteodata 3000 Página 3 Apartado 2.a.ii
            self.ser.rts = True
            time.sleep(self.tiempo_rts_activo)
            self.ser.rts = False
            time.sleep(self.tiempo_espera_datos)
            
            #Se escribe en el buffer de salida la trama deseada y se espera un tiempo para que la estacion responda
            self.ser.write(tramas_geonica.trama_medidas_no_instantaneas(self.numero_estacion, num_usuario, tipo_medida))      #Trama para recibir valores NO instantáneos
            time.sleep(self.tiempo_espera_datos)
            
            #Se lee el buffer de entrada donde debería estar la informacion recibida
            lectura = self.ser.read_all()
            
        else:   #COMUNICACIÓN POR SOCKETS
            self.sock.sendall(tramas_geonica.trama_medidas_no_instantaneas(self.numero_estacion, num_usuario, tipo_medida))
            print("Comunicando por sockets...")
            time.sleep(self.tiempo_espera_datos)
            lectura = self.sock.recv(193)
        
        #Se comprueba si la transmisión ha sido correcta
        estado_recepcion = tramas_geonica.decodificar_recepcion(lectura, self.numero_estacion, num_usuario)
        '''
        En caso de que se produzca un error, se devuelve el número del error
        Si el estado de la recepcion es correcto se devuelve un True
        En cualquier otro caso, p.ej. el número de bytes recibidos no es el esperado, el valor devuelto es un False
        ''' 
        if estado_recepcion != True:
            print("Error en la comunicacion con la estación")
            return estado_recepcion
        
        if lectura:
            #Obtencion de la fecha de la estación
            fecha = tramas_geonica.decodificar_FechayHora(lectura)
            print('La fecha de la estación es: ')
            print(fecha)
            
            #Obtencion de las medidas instantáneas
            medidas = tramas_geonica.decodificar_IEEE32bit(tramas_geonica.decodificar_medidas(lectura))
            print('Las medidas obtenidas son:')
            print(medidas)
            
        else:
            print("Error en la recepción")
            
        #Se cierra el puerto serie al finalizar la comunicación
        self.ser.close()
        return [fecha, medidas]
    
    def medidas_tendentes(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 12)          #Código de comando para medidas tendentes(Valor medio del ultimo periodo, en caso de estar configurado, sino valor acumulado, o en su defecto, el instantáneo)
    
    def medidas_ultimas_almacenadas(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 13)          #Código de comando para medidas almacendas en ultima posicion
    
    def medidas_medias(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 14)          #Código de comando para medidas medias
    
    def medidas_acumuladas(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 15)          #Código de comando para medidas acumuladas

    def medidas_integradas(self, numero_usuario): 
        return self.medidas_no_intantáneas(numero_usuario, 16)          #Código de comando para medidas integradas
        
    def medidas_maximas(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 17)          #Código de comando para medidas maximas
    
    def medidas_minimas(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 18)          #Código de comando para medidas minimas
    
    def datos_desvaicion_estandar(self, numero_usuario):
       return self.medidas_no_intantáneas(numero_usuario, 19)          #Código de comando para datos de la desviacion típica
        
    def datos_incremento(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 20)          #Código de comando para valores de incremento
    
    def datos_estado_alarma(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 21)          #Código de comando para estado de alarma
        
    def datos_operacion_OR(self, numero_usuario):
        return self.medidas_no_intantáneas(numero_usuario, 22)          #Código de comando para operacion OR de todos los valores
        
    def medidas_instantaneas(self, num_usuario):
        "COMUNICACIÓN POR EL PUERTO SERIE"
        if (self.ser.port != None):
            try:
                self.ser.open()
            except:
                pass
            print("Comunicando por puerto Serie...")
            # Debe activarse la linea RTS 1seg. antes del envio para que el dispositivo se prepare, si esta en modo ahorro,
            ## Mantener nivel alto durante 100ms y descactivar es suficiente  Referencia: Protocolo de comunicaciones Geonica Meteodata 3000 Página 3 Apartado 2.a.ii
            self.ser.rts = True
            time.sleep(self.tiempo_rts_activo)
            self.ser.rts = False
            time.sleep(self.tiempo_espera_datos)
            
            #Se escribe en el buffer de salida la trama deseada y se espera un tiempo para que la estacion responda
            self.ser.write(tramas_geonica.trama_medidas_instantaneas(self.numero_estacion, num_usuario))      #Trama para recibir valores instantáneos
            time.sleep(self.tiempo_espera_datos)
            
            #Se lee el buffer de entrada donde debería estar la informacion recibida
            lectura = self.ser.read_all()
        else:   #COMUNICACIÓN POR SOCKETS
            self.sock.sendall(tramas_geonica.trama_medidas_instantaneas(self.numero_estacion, num_usuario))
            print("Comunicando por sockets...")
            time.sleep(self.tiempo_espera_datos)
            lectura = self.sock.recv(193)
            
        estado_recepcion = tramas_geonica.decodificar_recepcion(lectura, self.numero_estacion, num_usuario)
        if estado_recepcion != True:
            print("Error en la comunicacion con la estación")
            return estado_recepcion
        
        if lectura:
            #Obtencion de la fecha de la estación
            fecha = tramas_geonica.decodificar_FechayHora(lectura)
            print('La fecha de la estación es: ')
            print(fecha)
            
            #Obtencion de las medidas instantáneas
            medidas = tramas_geonica.decodificar_IEEE32bit(tramas_geonica.decodificar_medidas(lectura))
            print('Las medidas obtenidas son:')
            print(medidas)
            
        else:
            print("Error en la recepción")
            
        #Se cierra el puerto al finalizar la comunicación
        self.ser.close()
        return [fecha, medidas]
        
    def sincronizar(self, num_usuario):
        "COMUNICACIÓN POR EL PUERTO SERIE"
        if (self.ser.port != None):
            try:
                self.ser.open();
            except:
                pass
            print("Comunicando por puerto Serie...")
            # Debe activarse la linea RTS 1seg. antes del envio para que el dispositivo se prepare, si esta en modo ahorro,
            ## Mantener nivel alto durante 100ms y descactivar es suficiente  Referencia: Protocolo de comunicaciones Geonica Meteodata 3000 Página 3 Apartado 2.a.ii
            self.ser.rts = True
            time.sleep(self.tiempo_rts_activo)
            self.ser.rts = False
            time.sleep(self.tiempo_espera_datos)
            
            #Se escribe en el buffer de salida la trama deseada y se espera un tiempo para que la estacion responda
            self.ser.write(tramas_geonica.trama_sincronizar(self.numero_estacion, num_usuario))      #Trama para recibir valores instantáneos
            time.sleep(self.tiempo_espera_datos)
            
            #Se lee el buffer de entrada donde debería estar la informacion recibida
            lectura = self.ser.read_all()
        else:   #COMUNICACIÓN POR SOCKETS
            self.sock.sendall(tramas_geonica.trama_sincronizar(self.numero_estacion, num_usuario))
            print("Comunicando por sockets...")
            time.sleep(self.tiempo_espera_datos)
            lectura = self.sock.recv(13)
        
        estado_recepcion = tramas_geonica.decodificar_recepcion(lectura, self.numero_estacion, num_usuario)
        if estado_recepcion != True:
            print("Error en la comunicacion con la estación")
        else:
            print('Fecha sincronicada.')
        
        #Se cierra el puerto al finalizar la comunicación
        self.ser.close()
        return estado_recepcion