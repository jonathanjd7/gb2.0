# 📝 Plantillas de Mensajes para WhatsApp Sender
# Archivo con plantillas predefinidas que puedes usar o modificar

# Plantilla PRINCIPAL de GO BARAJAS
CITA= """Hola *{nombre}* 😁,

Le recordamos que tiene una reserva en *GO BARAJAS* para el día de *mañana* a las *{hora}h*.
Matrícula registrada: *{matricula}*
👥 Número de ocupantes: *{ocupantes}*

📆 Por favor, confirme su asistencia respondiendo a este mensaje.
*(Avísenos si viene con alguna mascota 🐶😼)*

📍 Dirección: Ver ubicación en Google Maps:
https://goo.gl/maps/bH9XgxPZE4ze8Yaf9

🅿 Elija una plaza libre, recuerde el número de su plaza y pase por la oficina.

📞 Teléfono de contacto: *+34 919 23 73 78*
Le recomendamos guardarlo en su agenda.

Gracias por su confianza. ¡Le esperamos!"""



RECOGIDASTARDES= """Hola buenas Tardes, 
Les recordamos que hoy les  recogemos **ARRIBA EN LA PLATAFORMA DE SALIDAS de  la Terminal* *1 Puerta 3* || *T2- Puerta 7* || *T4 Puerta 5*|| 🚪 
Cuando recoja todo el equipaje de la cinta o este de camino al punto de encuentro nos tiene que llamar  *+34 919 237 378* ( *Llamada Normal* 📞,NO WHATSAPP). Gracias.
(*Avisen si necesitan sillita para niño/bebe* 👶) """

RECOGIDAMANANA= """Hola buenos dias, 
Les recordamos que hoy les  recogemos **ARRIBA EN LA PLATAFORMA DE SALIDAS de  la Terminal* *1 Puerta 3* || *T2- Puerta 7* || *T4 Puerta 5*|| 🚪 
Cuando recoja todo el equipaje de la cinta o este de camino al punto de encuentro nos tiene que llamar  *+34 919 237 378* ( *Llamada Normal* 📞,NO WHATSAPP). Gracias.
(*Avisen si necesitan sillita para niño/bebe* 👶) """

#PLANTILLA PREMIUM
PREMIUM= """Hola, le recordamos que en el día de mañana tiene una reserva en Go Barajas a las *{hora}* , se le recogerá el vehículo en la *Terminal* *{servicios}.* 
El día de su reserva llámenos 20 - 15 minutos antes de llegar a la Terminal desde la que viaja y en la plataforma de "SALIDAS", uno de nuestros chóferes adecuadamente identificado (chaleco amarillo y logotipo de nuestra empresa) recogerá su coche.
Adjuntamos nuestro teléfono *+34 919 237 378* . 
Muchas gracias 🙂  """

#PLANTILLA PARA MÚLTIPLES VEHÍCULOS (CONSOLIDADA)
CITA_MULTIPLE= """Hola *{nombre}* 😁

Le recordamos que tiene *{reservas_count} reservas* en *GO BARAJAS* para el día de *mañana* a las *{hora}h*.

🚗 *Vehículos registrados:*
{matricula}

👥 *Total de ocupantes:* *{ocupantes}*

📆 Por favor, confirme su asistencia respondiendo a este mensaje.
*(Avísenos si viene con alguna mascota 🐶😼)*

📍 Dirección: Ver ubicación en Google Maps:
https://goo.gl/maps/bH9XgxPZE4ze8Yaf9

🅿 Una vez aparcado, recuerde el número de su plaza y pase por la oficina.

📞 Teléfono de contacto: *+34 919 23 73 78*
Le recomendamos guardarlo en su agenda.

Gracias por su confianza. ¡Le esperamos!"""

# Diccionario con todas las plantillas
PLANTILLAS_DISPONIBLES = {
    "RecordatorioCita": CITA,
    "RecogidaTardes": RECOGIDASTARDES,
    "RecogidaMañana": RECOGIDAMANANA,
    "PREMIUM": PREMIUM,
    "CitaMultiple": CITA_MULTIPLE
}

# Variables disponibles en todas las plantillas
VARIABLES_DISPONIBLES = {
    "{nombre}": "Nombre del cliente",
    "{matricula}": "Matrícula del vehículo (o múltiples matrículas si está consolidado)",
    "{hora}": "Hora de la reserva",
    "{fecha_actual}": "Fecha actual (dd-mm-yyyy)",
    "{ocupantes}": "Número de ocupantes del vehículo (o total si está consolidado)",
    "{reservas_count}": "Número de reservas (solo para contactos consolidados)",
    "{servicios}": "Servicios específicos (solo para plantilla PREMIUM)"
}

def obtener_plantilla(nombre):
    """Obtener una plantilla por nombre"""
    return PLANTILLAS_DISPONIBLES.get(nombre, CITA)

def listar_plantillas():
    """Listar todas las plantillas disponibles"""
    return list(PLANTILLAS_DISPONIBLES.keys())

def obtener_variables():
    """Obtener información sobre las variables disponibles"""
    return VARIABLES_DISPONIBLES.copy()

def crear_mensaje_ejemplo(plantilla, nombre="Juan Pérez", matricula="1234ABC", hora="14:30", ocupantes="3"):
    """Crear un mensaje de ejemplo con datos de prueba"""
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%d-%m-%Y")
    
    try:
        return plantilla.format(
            nombre=nombre,
            matricula=matricula,
            hora=hora,
            fecha_actual=fecha_actual,
            ocupantes=ocupantes
        )
    except KeyError as e:
        return f"Error en la plantilla: variable {e} no encontrada"

if __name__ == "__main__":
    # Ejemplo de uso
    print("📝 Plantillas disponibles:")
    for nombre in listar_plantillas():
        print(f"  - {nombre}")
    
    print("\n🔧 Variables disponibles:")
    for variable, descripcion in obtener_variables().items():
        print(f"  {variable}: {descripcion}")
    
    print("\n📋 Ejemplo de mensaje:")
    ejemplo = crear_mensaje_ejemplo(CITA)
    print(ejemplo) 