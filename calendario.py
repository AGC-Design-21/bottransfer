###########################################
####  BOT DE IMPRESIONES DE RESET V.3  ####
###########################################
### Creado por Montse DCD para Reset <3 ###
###########################################
######## Versión 3 por Álvaro G-CP ########
###########################################

###########################################
################## vAPIs ##################
#### Python Telegram Bot API: V 12.5.1 ####
########### Google API: V 1.8.0 ###########
###### Google OAuth Library: V 0.4.1 ######
############ Dateutil: V 2.8.1 ############
###########################################

##Estas librerias tiene que ir las primeras
from __future__ import print_function
import pickle

import os
path = os.path.dirname(os.path.abspath(__file__))


#Importacion de librerias datetime/dateutil
from datetime import datetime, time, timedelta
from dateutil import tz

##Importacion de librerias de TLG aqui
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram.ext import ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


##Liberias de google calendar
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

##Para deteccion de errores
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


##Para permitir que luego el calendario se pueda leer y modificar
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


##------------------------------------------------------------------------------------------------------------------##


##Variables para marcar las impresoras rotas

hephestos_rota=0

prusamk_rota=0

witbox_rota=0

ender_rota=0

##Variables para conversacion
#Convo ppal
DURACION, DIA, HORA, IMPRESORA, CATEGORIA, RESERVAR = range(6)
#Convo borrar
BORRAR_ID = range(1)
#Convo rota
ROTA_ID = range(1)
#Convo arreglada
ARREGLADA_ID = range (1)

MANTENIMIENTO_ID = range (1)


##------------------------------------------------------------------------------------------------------------------##

##Funcion para construir un menu
def build_menu(buttons,n_cols,header_buttons=None,footer_buttons=None):
	menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
	if header_buttons:
		menu.insert(0, header_buttons)
	if footer_buttons:
		menu.append(footer_buttons)
	return menu


##Funcion para leer archivos
def leer_archivo():
    global witbox_rota
    global hephestos_rota
    global prusamk_rota
    global ender_rota

    #Open the file back and read the contents
    f=open(path+"/impresoras.txt", "r")
    if f.mode == 'r':
        #contents =f.readlines()
        contents =list(f)

        cont_hep=contents[0].split()
        cont_st=contents[1].split()
        cont_wit=contents[2].split()
        cont_end=contents[3].split()

        if cont_hep[0] is 'H':
           hephestos_rota=cont_hep[1]
        else:
           hephestos_rota='nan'

        if cont_st[0] is 'P':
           prusamk_rota=cont_st[1]
        else:
           prusamk_rota='nan'

        if cont_wit[0] is 'W':
           witbox_rota=cont_wit[1]
        else:
           witbox_rota='nan'

        if cont_end[0] is 'E':
           ender_rota=cont_end[1]
        else:
           ender_rota='nan'


        #print(hephestos_rota, witbox_rota, prusamk_rota)
    f.close()



##Funcion para escribir en archivos
def escribir_archivo():
    global witbox_rota
    global hephestos_rota
    global prusamk_rota
    global ender_rota

    texto="H "+str(hephestos_rota)+"\n"
    texto=texto+"P "+str(prusamk_rota)+"\n"
    texto=texto+"W "+str(witbox_rota)+"\n"
    texto=texto+"E "+str(ender_rota)+"\n"

    f=open(path+"/impresoras.txt", "w+")
    f.write(texto)
    f.close()
    #print("escrito")





##------------------------------------------------------------------------------------------------------------------##

## START

def start(update, context):
	sticker_resetlogo_id='CAACAgQAAxkBAAEK3lRlaakvmn7nb_szE7dQYynt2ZDP8gAC_hIAAsKsUFMEo4Bbf2P7zzME'
	update.message.reply_sticker(sticker=sticker_resetlogo_id)
	update.message.reply_text(text=("Bienvenido al Bot de impresiones de Reset. "
									"Puedes poner /impresion para poner en el calendario una impresión, "
									"/futuras para ver las 10 siguientes impresiones programadas "
									"o /borrar para quitar una impresión tuya del calendario. "
									"También se puede comunicar que una impresora está fuera de servicio con "
									"/rota o que está funcional con /arreglada. Si quieres saber que impresoras funcionan usa /estado"))
	update.message.reply_text(text=("IMPORTANTE! De momento el bot "
									"no detecta solapamientos entre eventos, revisa las impresiones /futuras "
									"antes de poner la tuya para asegurarte de que no se solapa con nadie."))
	update.message.reply_text(text=("IMPORTANTE! Para Imprimir con la Ender 3 V3 SE deberás usar el"
									" entorno de impresión remota OctoPrint. Es imprescindible haber completado el taller de OctoPrint para imprimir en esta máquina"))

	return ConversationHandler.END


## CONVERSACION PRINCIPAL (impresion, duracion,dia, hora, impresora, categoria, reservar)

def impresion(update, context):
	key=update.message.from_user.id
	context.chat_data[key]=dict(impresion=0,reservar=0, rota=0, arreglada=0, borrar=0,nombre='',
								alias='',fecha_pedido='',duracion_h_impresion=0,duracion_min_impresion=0,
								dia_impresion=0,mes_impresion=0,hora_impresion=0,minuto_impresion=0,
								impresora='', categoria='')

	leer_archivo()
	if witbox_rota=='1' and prusamk_rota=='1' and hephestos_rota=='1' and ender_rota=='1':
		update.message.reply_text(text="Ahora mismo están todas las impresoras rotas :(")

	else:
		context.chat_data[key]['nombre']=update.message.from_user.first_name
		##Miramos username y apellido por si fuera un nombre comun
		if type(update.message.from_user.last_name) is str:
		 	context.chat_data[key]['alias']=update.message.from_user.last_name
		elif type(update.message.from_user.username) is str:
			context.chat_data[key]['alias']=update.message.from_user.username
		else:
			context.chat_data[key]['alias']="?"

		context.chat_data[key]['impresion']=1

		update.message.reply_text(text=("Hola, "+context.chat_data[key]['nombre']+ " . "
										"Espero que hayas revisado las impresiones /futuras "
										"para no colisionar con nadie. Primero dime cuántas horas "
										"dura tu impresión [horas:minutos]. Redondea para arriba "
										"y recuerda tener en cuenta el tiempo de carga y descarga."))

		return DURACION

def duracion(update, context):
	key=update.message.from_user.id
	#Recogemos el momento en que se reserva por si hubiera conflictos
	context.chat_data[key]['fecha_pedido']=update.message.date

	#Le decimos la zona horaria en la que estamos para que haga solito el cambio de horar de verano
	MAD=tz.gettz('Europe/Madrid')
	context.chat_data[key]['fecha_pedido']=context.chat_data[key]['fecha_pedido'].replace(tzinfo=MAD)

	#Procesamos el mensaje de las horas de impresion que ha mandado antes
	tiempo=update.message.text.split(":")
	context.chat_data[key]['duracion_h_impresion']=int(tiempo[0])
	if len(tiempo)==1:
		context.chat_data[key]['duracion_min_impresion']=0
	elif len(tiempo)==2:
		context.chat_data[key]['duracion_min_impresion']=int(tiempo[1])

	update.message.reply_text(text="Ahora dime qué día quieres ponerlo [dia/mes]")
	return DIA



def dia(update, context):
	key=update.message.from_user.id
	fecha_impresion=update.message.text.split("/")
	context.chat_data[key]['dia_impresion']=int(fecha_impresion[0])
	context.chat_data[key]['mes_impresion']=int(fecha_impresion[1])

	###Filtro para no poder poner impresiones en fechas pasadas

	#Caso 1: Mes anterior a la fecha actual (NO VALIDO)
	if context.chat_data[key]['mes_impresion']<context.chat_data[key]['fecha_pedido'].month:
		update.message.reply_text(text="Eso no es causal, dime una fecha en el futuro [dia/mes]")
		return DIA

	#Caso 2: Mismo mes
	elif context.chat_data[key]['mes_impresion']==context.chat_data[key]['fecha_pedido'].month:
		#Caso 2.1: Dia anterior a la fecha actual (NO VALIDO)
		if context.chat_data[key]['dia_impresion']<context.chat_data[key]['fecha_pedido'].day:
			update.message.reply_text(text="Eso no es causal, dime una fecha en el futuro [dia/mes]")
			return DIA
		#Caso 2.2: Dia igual o mayor a la fecha actual (VALIDO)
		else:
			update.message.reply_text(text="Y la hora a la que quieres imprimir? [horas:minutos]")
			return HORA
	#Caso 3: Mes mayor que el mes actual (VALIDO)
	else:
		update.message.reply_text(text="Y la hora a la que quieres imprimir? [horas:minutos]")
		return HORA

def hora(update,context):
	global witbox_rota
	global hephestos_rota
	global prusamk_rota
	global ender_rota
	leer_archivo()
	ender_estado = ""
	witbox_estado = ""
	prusa_estado = ""
	hephestos_estado = ""

	if hephestos_rota == '2':
		hephestos_estado = "Hephestos 2, "
	if witbox_rota == '2':
		witbox_estado = "Witbox 2, "
	if prusamk_rota == '2':
		prusa_estado = "Prusa MK3S, "
	if ender_rota == '2':
		ender_estado = "Ender 3 V3 SE, "

	key=update.message.from_user.id
	momento_impresion=update.message.text.split(":")
	context.chat_data[key]['hora_impresion']=int(momento_impresion[0])
	if len(momento_impresion)==1:
		context.chat_data[key]['minuto_impresion']=0
	elif len(momento_impresion)==2:
		context.chat_data[key]['minuto_impresion']=int(momento_impresion[1])

	##Hacemos el menu de las impresoras para que solo muestre las que no están rotas

	button_list = []

	if ender_rota == '0':
		button_list.append(InlineKeyboardButton("Ender 3 V3 SE", callback_data="Ender 3 V3 SE"))

	if witbox_rota == '0':
		button_list.append(InlineKeyboardButton("Witbox 2", callback_data="Witbox 2"))

	if prusamk_rota == '0':
		button_list.append(InlineKeyboardButton("Prusa MK3S", callback_data="Prusa MK3S"))

	if hephestos_rota == '0':
		button_list.append(InlineKeyboardButton("Hephestos 2", callback_data="Hephestos 2"))

	#InlineKeyboardButton(("Prusa MK3S" + str(prusamk_estado)), callback_data="Prusa MK3S"),
	#InlineKeyboardButton(("Hephestos 2" + str(hephestos_estado)), callback_data="Hephestos 2"),
	#InlineKeyboardButton(("Witbox 2" + str(witbox_estado)), callback_data="Witbox 2"),
	#InlineKeyboardButton(("Ender 3 V3 SE" + str(ender_estado)), callback_data="Ender 3 V3 SE")
	
	reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

	##Filtro para no poner en horas pasadas del mismo dia
	#Caso 1:impresion en el dia y mes actual
	if context.chat_data[key]['dia_impresion']==context.chat_data[key]['fecha_pedido'].day and context.chat_data[key]['mes_impresion']==context.chat_data[key]['fecha_pedido'].month:
		#Caso 1.1: hora menor a la actual (NO VALIDO)
		if context.chat_data[key]['hora_impresion']<context.chat_data[key]['fecha_pedido'].hour:
			update.message.reply_text(text="Eso no es causal, dime una hora en el futuro [horas:minutos]")
			return HORA
		#Caso 1.2: hora igual a la actual
		elif context.chat_data[key]['hora_impresion']==context.chat_data[key]['fecha_pedido'].hour:
			#Caso 1.2.1: misma hora, minuto menor al actual (NO VALIDO)
			if chat_data[key]['minuto_impresion']<chat_data[key]['fecha_pedido'].minute:
				update.message.reply_text(text="Eso no es causal, dime una hora en el futuro [horas:minutos]")
				return HORA
			#Caso 1.2.2: misma hora, mismo minuto o minuto mayor al actual (VALIDO)
			else:
				update.message.reply_text(text="Ahora, dime qué impresora quieres usar", reply_markup=reply_markup)
				return IMPRESORA
		#Caso 1.3: hora mayor a la actual (VALIDO)
		else:
			update.message.reply_text(text="Ahora, dime qué impresora quieres usar", reply_markup=reply_markup)
			return IMPRESORA
	#Caso 2: impresion en otro dia (mayor, ya se ha comprobado antes) (VALIDO)
	else:
		update.message.reply_text(text="Ahora, dime qué impresora quieres usar", reply_markup=reply_markup)
		if hephestos_rota == '2' or witbox_rota == '2' or prusamk_rota == '2' or ender_rota == '2':
			update.message.reply_text(text="La(s) impresora(s) " + ender_estado + prusa_estado + witbox_estado + hephestos_estado + "están en mantenimiento, no están rotas, cuando terminemos de trabajar con ella(s) volverán a estar disponibles")
		return IMPRESORA

def impresora(update,context):
	key=update.callback_query.from_user.id
	global witbox_rota
	global hephestos_rota
	global prusamk_rota
	global ender_rota
	context.chat_data[key]['impresora']=update.callback_query['data']
	#Primero leemos el archivo que para eso esta
	leer_archivo()
	button_list = [
			InlineKeyboardButton("Urgente para Reset", callback_data="Urgente para Reset"),
			InlineKeyboardButton("Proyecto de Reset", callback_data="Proyecto de Reset"),
			InlineKeyboardButton("Trabajo de uni", callback_data="Trabajo de uni"),
			InlineKeyboardButton("Proyecto personal", callback_data="Proyecto personal"),
			InlineKeyboardButton("Servicio de Impresiones", callback_data="Servicio de Impresiones"),
			InlineKeyboardButton("Chorrada", callback_data="Chorrada")
			]
	reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
	update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
											   text="Por último, ¿a qué categoría pertenece tu impresión?",
											   reply_markup=reply_markup)
	return CATEGORIA


def categoria(update,context):
	key=update.callback_query.from_user.id
	context.chat_data[key]['categoria']=update.callback_query['data']

	#Mensaje con la info para el user
	update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
				 	 text="Este es el resumen de lo que voy a apuntar en el calendario:\n"
				 	 "Nombre: "+context.chat_data[key]['nombre']+" ("+context.chat_data[key]['alias']+")"+"\n"
				 	 "Dia: "+str(context.chat_data[key]['dia_impresion'])+"/"+str(context.chat_data[key]['mes_impresion'])+
				 	 " a las "+str(context.chat_data[key]['hora_impresion'])+":"+str(context.chat_data[key]['minuto_impresion'])+"\n"
				 	 "Impresora: "+context.chat_data[key]['impresora']+" durante "+str(context.chat_data[key]['duracion_h_impresion'])+
				 	 " horas y "+str(context.chat_data[key]['duracion_min_impresion'])+" minutos."+"\n"
				 	 "Categoría: "+context.chat_data[key]['categoria']+"\n"
				 	 "Fecha de la reserva: "+str(context.chat_data[key]['fecha_pedido'].day)+"/"+
				 	 str(context.chat_data[key]['fecha_pedido'].month)+" a las "+str(context.chat_data[key]['fecha_pedido'].hour)+
				 	 ":"+str(context.chat_data[key]['fecha_pedido'].minute))

	#Boton de reservar
	button_list = [InlineKeyboardButton("Reservar", callback_data="Reservar")]
	reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))

	#Mensaje para reservar
	update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
					 text="Si todo esta correcto, introduce /reservar para terminar. "
					 "Si hay algo mal, vuelve a empezar poniendo /impresion",
					 reply_markup=reply_markup)

	context.chat_data[key]['reservar']=1
	return RESERVAR


def reservar(update,context):
	key=update.callback_query.from_user.id
	try:
		if context.chat_data[key]['reservar']==1:
			##Aqui va el codigo de mandarlos con la Google Calendar API
			creds = None

			if os.path.exists(path+'/token.pickle'):
				with open(path+'/token.pickle', 'rb') as token:
					creds = pickle.load(token)
			# If there are no (valid) credentials available, let the user log in.
			if not creds or not creds.valid:
				if creds and creds.expired and creds.refresh_token:
					creds.refresh(Request())
				else:
					flow = InstalledAppFlow.from_client_secrets_file(
						path+'/credentials.json', SCOPES)
					creds = flow.run_local_server()
				# Save the credentials for the next run
				with open(path+'/token.pickle', 'wb') as token:
					pickle.dump(creds, token)

			service = build('calendar', 'v3', credentials=creds)


			##############TRATAMIENTO DE LOS DATOS PARA PODER PASARLOS AL CALENDARIO
			#####El nombre del evento sera "IMPRESION DE XXXX"
			summ="Impresión de "+context.chat_data[key]['nombre']+" ("+context.chat_data[key]['alias']+") en la impresora "+context.chat_data[key]['impresora']
			summ=summ+" ["+context.chat_data[key]['categoria']+"]"
			summ=summ+" durante "+str(context.chat_data[key]['duracion_h_impresion'])+" horas y "+str(context.chat_data[key]['duracion_min_impresion'])+" minutos"

			#####En la descripcion irá el dia que se ha reservado por si se prende wey
			descr="Reservado el "+str(context.chat_data[key]['fecha_pedido'].day)+"/"+str(context.chat_data[key]['fecha_pedido'].month)+"/"+str(context.chat_data[key]['fecha_pedido'].year)+" a las "+str(context.chat_data[key]['fecha_pedido'].hour)+":"+str(context.chat_data[key]['fecha_pedido'].minute)
			#####La fecha del inicio de la reserva
			agno=context.chat_data[key]['fecha_pedido'].year
			#Caso de que la fecha de impresion sea anterior a la del pedido (consideramos cambio de año)
			if context.chat_data[key]['mes_impresion'] < context.chat_data[key]['fecha_pedido'].month:
				agno=agno+1
			#IMPORTANTE: definimos el offset respecto al UTC, que en invierno es UTC+1 y en verano UTC+2

			utcoff=int(context.chat_data[key]['fecha_pedido'].utcoffset() / timedelta(hours=1))

			#Le ponemos bonita la fecha de inicio (en el formato que quiere google calendar)
			inicio=str(agno)+"-"+str(context.chat_data[key]['mes_impresion'])+"-"+str(context.chat_data[key]['dia_impresion'])+"T"+str(context.chat_data[key]['hora_impresion'])+":"+str(context.chat_data[key]['minuto_impresion'])+":00+0"+str(utcoff)+":00:00"
			#####La fecha del fin de la reserva (calculitos)
			mes_fin=context.chat_data[key]['mes_impresion']
			dia_fin=context.chat_data[key]['dia_impresion']
			hora_fin=context.chat_data[key]['hora_impresion']+context.chat_data[key]['duracion_h_impresion']
			minuto_fin=context.chat_data[key]['minuto_impresion']+context.chat_data[key]['duracion_min_impresion']

			if minuto_fin>59:
				hora_fin=hora_fin+1
				minuto_fin=minuto_fin-59

			if hora_fin>24:
				dia_fin=dia_fin+1
				hora_fin=hora_fin-24

			if mes_fin==2: ##FEBRERO
				if dia_fin>28:
					if agno%4==0:		##SUpuesto de febrero bisiesto
						dia_fin=dia_fin-29
						mes_fin=mes_fin+1
					else:				##Supuesto de febrero normal
						dia_fin=dia_fin-28
						mes_fin=mes_fin+1
			elif mes_fin==4 or mes_fin==6 or mes_fin==9 or mes_fin==11:
				if dia_fin>30:			##Meses de 30 dias
					dia_fin=dia_fin-30
					mes_fin=mes_fin+1
			elif mes_fin==1 or mes_fin==3 or mes_fin==5 or mes_fin==7 or mes_fin==8 or mes_fin==10:
				if dia_fin>31:			##Meses de 31 dias
					dia_fin=dia_fin-31
					mes_fin=mes_fin+1
			elif mes_fin==12:
				if dia_fin>31:			##Diciembre
					dia_fin=dia_fin-31
					mes_fin=1
					agno=agno+1 ##Ajuste de nuevo año


			##Y ahora construimos el array del fin de impresion
			fin=str(agno)+"-"+str(mes_fin)+"-"+str(dia_fin)+"T"+str(hora_fin)+":"+str(minuto_fin)+":00+0"+str(utcoff)+":00:00"

			#Añadimos el evento al calendario de Reset (3dreset@gmail.com)
			event = {'summary': summ, 'description': descr,'start': {'dateTime': inicio},'end': {'dateTime': fin}}
			event_created=event = service.events().insert(calendarId='primary', body=event).execute()

			#Mandamos mensaje con el id del evento para que luego puedan borrarlo si se equivocan
			emoji=u'\U0001F496'
			update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
												   text="La info se ha mandado al calendario. El id de tu reserva"
												   " en caso de que quieras cancelarla aparece en el siguiente mensaje.\n"
												   "Para volver a empezar pon /start. Gracias por usar el bot "+emoji)
			update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
												   text=event_created['id'])
			print(event_created['id'])

			#Y por ultimo eliminamos la sesion
			del context.chat_data[key]
		else:
			update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
												   text="Ha habido un error. Pon /start para empezar.")

	except:
		update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
											   text="Ha habido un error. Pon /start para empezar.")
		return ConversationHandler.END

	return ConversationHandler.END

## CONVERSACION PARA BORRAR IMPRESIONES (borrar, borrar_id)

def borrar(update,context):
	key=update.message.from_user.id
	context.chat_data[key]=dict(i=0,impresion=0,reservar=0, rota=0, arreglada=0, borrar=1, nombre='',
								alias='',fecha_pedido='',duracion_h_impresion=0,duracion_min_impresion=0,
								dia_impresion=0,mes_impresion=0,hora_impresion=0,minuto_impresion=0,
								impresora='', categoria='')
	context.chat_data[key]['borrar']=1
	update.message.reply_text(text="Para borrar una impresión, dime el id que te di cuando hiciste la reserva")

	return BORRAR_ID


def borrar_id(update,context):
	key=update.message.from_user.id
	#Recogemos el ID
	event_todel=update.message.text

	##Aqui va el codigo de mandarlos con la Google Calendar API
	creds = None
	if os.path.exists(path+'/token.pickle'):
		with open(path+'/token.pickle', 'rb') as token:
			creds = pickle.load(token)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				path+'/credentials.json', SCOPES)
			creds = flow.run_local_server()
		# Save the credentials for the next run
		with open(path+'/token.pickle', 'wb') as token:
			pickle.dump(creds, token)

	service = build('calendar', 'v3', credentials=creds)

	#Borramos el evento del calendario
	success=service.events().delete(calendarId='primary', eventId=event_todel).execute()

	#Mandamos el mensaje
	update.message.reply_text(text="Done. Pulsa /start para volver a empezar.")
	#Quitamos la variable de control
	context.chat_data[key]['borrar']=0

	return ConversationHandler.END

# CONVERSACION PARA NOTIFICAR IMPRESORA ROTA (rota, rota_id)

def rota(update,context):
	global witbox_rota
	global hephestos_rota
	global prusamk_rota
	global ender_rota
	leer_archivo()
	key=update.message.from_user.id
	context.chat_data[key]=dict(i=0,impresion=0,reservar=0, rota=1, arreglada=0, borrar=0, nombre='',
								alias='',fecha_pedido='',duracion_h_impresion=0,duracion_min_impresion=0,
								dia_impresion=0,mes_impresion=0,hora_impresion=0,minuto_impresion=0,
								impresora='', categoria='')

	button_list = []

	if ender_rota == '0':
		button_list.append(InlineKeyboardButton("Ender 3 V3 SE", callback_data="Ender 3 V3 SE"))

	if witbox_rota == '0':
		button_list.append(InlineKeyboardButton("Witbox 2", callback_data="Witbox 2"))

	if prusamk_rota == '0':
		button_list.append(InlineKeyboardButton("Prusa MK3S", callback_data="Prusa MK3S"))

	if hephestos_rota == '0':
		button_list.append(InlineKeyboardButton("Hephestos 2", callback_data="Hephestos 2"))

	if hephestos_rota == '1' and witbox_rota =='1' and ender_rota=='1' and prusamk_rota == '1':
		update.message.reply_text(text="Creo que ya no quedan mas impresoras por romper")

		#button_list = [
		#		InlineKeyboardButton("Prusa MK3S", callback_data="Prusa MK3S"),
		#		InlineKeyboardButton("Hephestos 2", callback_data="Hephestos 2"),
		#		InlineKeyboardButton("Witbox 2", callback_data="Witbox 2"),
		#		InlineKeyboardButton("Ender 3 V3 SE", callback_data="Ender 3 V3 SE")
		#		]
	else:
		reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
		update.message.reply_text(text="Oh diosito, ¿qué impresora se ha roto?", reply_markup=reply_markup)

	return ROTA_ID

def rota_id(update,context):
	key=update.callback_query.from_user.id
	recienrompida=update.callback_query['data']

	global witbox_rota
	global hephestos_rota
	global prusamk_rota
	global ender_rota
	leer_archivo()

	if recienrompida == "Prusa MK3S":
		prusamk_rota = 1
	elif recienrompida == "Hephestos 2":
		hephestos_rota = 1
	elif recienrompida == "Witbox 2":
		witbox_rota = 1
	elif recienrompida == "Ender 3 V3 SE":
		ender_rota = 1

	escribir_archivo()

	update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
										   text="Gracias por informar, esperemos que no sea grave :(")
	context.chat_data[key]['rota']=0

	return ConversationHandler.END

# CONVERSACION PARA NOTIFICAR IMPRESORA ARREGLADA (arreglada, arreglada_id)

def arreglada(update,context):
	global witbox_rota
	global hephestos_rota
	global prusamk_rota
	global ender_rota
	leer_archivo()
	key=update.message.from_user.id
	context.chat_data[key]=dict(i=0,impresion=0,reservar=0, rota=0, arreglada=1, borrar=0, nombre='',
								alias='',fecha_pedido='',duracion_h_impresion=0,duracion_min_impresion=0,
								dia_impresion=0,mes_impresion=0,hora_impresion=0,minuto_impresion=0,
								impresora='', categoria='')

	button_list = []

	if ender_rota == '1' or ender_rota == '2':
		button_list.append(InlineKeyboardButton("Ender 3 V3 SE", callback_data="Ender 3 V3 SE"))

	if witbox_rota == '1' or witbox_rota == '2':
		button_list.append(InlineKeyboardButton("Witbox 2", callback_data="Witbox 2"))

	if prusamk_rota == '1' or prusamk_rota == '2':
		button_list.append(InlineKeyboardButton("Prusa MK3S", callback_data="Prusa MK3S"))

	if hephestos_rota == '1' or hephestos_rota == '2':
		button_list.append(InlineKeyboardButton("Hephestos 2", callback_data="Hephestos 2"))

	if hephestos_rota == '0' and witbox_rota =='0' and ender_rota=='0' and prusamk_rota == '0':
		update.message.reply_text(text="están todas arregladas, YAY")
	else:
		reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
		update.message.reply_text(text="OH YES, ¿qué impresora se ha arreglado?", reply_markup=reply_markup)

	return ARREGLADA_ID

def arreglada_id(update,context):
	key=update.callback_query.from_user.id
	recienarreglada=update.callback_query['data']

	global witbox_rota
	global hephestos_rota
	global prusamk_rota
	global ender_rota
	leer_archivo()

	if recienarreglada == "Prusa MK3S":
		prusamk_rota = 0
	elif recienarreglada == "Hephestos 2":
		hephestos_rota = 0
	elif recienarreglada == "Witbox 2":
		witbox_rota = 0
	elif recienarreglada == "Ender 3 V3 SE":
		ender_rota = 0

	escribir_archivo()

	update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
										   text="¡¡GRACIAS AL CIELO, SE ARREGLÓ!! Y a ti por informar <3")
	context.chat_data[key]['arreglada']=0

	return ConversationHandler.END

def mantenimiento(update,context):
	global witbox_rota
	global hephestos_rota
	global prusamk_rota
	global ender_rota
	leer_archivo()
	key=update.message.from_user.id
	context.chat_data[key]=dict(i=0,impresion=0,reservar=0, rota=0, arreglada=0, borrar=0, nombre='',
								alias='',fecha_pedido='',duracion_h_impresion=0,duracion_min_impresion=0,
								dia_impresion=0,mes_impresion=0,hora_impresion=0,minuto_impresion=0,
								impresora='', categoria='',mantenimiento=1)

	button_list = []

	if ender_rota == '1' or ender_rota == '0':
		button_list.append(InlineKeyboardButton("Ender 3 V3 SE", callback_data="Ender 3 V3 SE"))

	if witbox_rota == '1' or witbox_rota == '0':
		button_list.append(InlineKeyboardButton("Witbox 2", callback_data="Witbox 2"))

	if prusamk_rota == '1' or prusamk_rota == '0':
		button_list.append(InlineKeyboardButton("Prusa MK3S", callback_data="Prusa MK3S"))

	if hephestos_rota == '1' or hephestos_rota == '0':
		button_list.append(InlineKeyboardButton("Hephestos 2", callback_data="Hephestos 2"))

	if hephestos_rota == '2' and witbox_rota =='2' and ender_rota=='2' and prusamk_rota == '2':
		update.message.reply_text(text="están todas arregladas, YAY")
	else:
		reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
		update.message.reply_text(text="Qué impresora está en mantenimiento?", reply_markup=reply_markup)

	return MANTENIMIENTO_ID

def mantenimiento_id(update,context):
	key=update.callback_query.from_user.id
	mantenimiento=update.callback_query['data']

	global witbox_rota
	global hephestos_rota
	global prusamk_rota
	global ender_rota
	leer_archivo()

	if mantenimiento == "Prusa MK3S":
		prusamk_rota = 2
	elif mantenimiento == "Hephestos 2":
		hephestos_rota = 2
	elif mantenimiento == "Witbox 2":
		witbox_rota = 2
	elif mantenimiento == "Ender 3 V3 SE":
		ender_rota = 2

	escribir_archivo()

	update.callback_query.bot.send_message(chat_id=update.callback_query.message.chat.id,
										   text="Impresora en mantenimiento")
	return ConversationHandler.END


# ERROR (fallback de todas las convos: entra aqui cuando mendas un comando que no se espera)

def error(update,context):
	#Borramos la sesion para que tenga que empezar de nuevo
	key=update.message.from_user.id
	del context.chat_data[key]
	#Mensaje informativo
	update.message.reply_text(text="Vaya, no me esperaba eso. El proceso en el que estabas "
								   "se ha cancelado. Manda de nuevo /impresion, /borrar, "
								   "/rota o /arreglada para volver a empezar lo que estabas "
								   "haciendo o /futuras para ver las impresiones programadas. "
								   "Y esta vez haz caso a lo que te pide el bot, please and thank you")
	return ConversationHandler.END



# FUTURAS (comando)

def futuras(update,context):
	##Ejemplo sacado tal cual de la pagina de google
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(path+'/token.pickle'):
        with open(path+'/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                path+'/credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(path+'/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    update.message.reply_text(text="Estos son las 10 impresiones siguientes:")

    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    #En caso de que no haya ningún evento
    if not events:
        update.message.reply_text(text="Parece que no hay impresiones programadas")
        sticker_rainbow_id='CAADAgADlQIAAkcVaAkG5pdrTGfBvAI'
        update.message.reply_sticker(sticker=sticker_rainbow_id)
    #Caso de que si haya eventos
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start=start.split("T")
        fecha=start[0].split("-")
        hora=start[1].split("+")
        hora=hora[0]

        summary=event['summary']

        update.message.reply_text(text=summary+" el día "+fecha[2]+"/"+fecha[1]+" a las "+hora)

def estado(update,context):
	global witbox_rota
	global prusamk_rota
	global hephestos_rota
	global ender_rota
	leer_archivo()
	if hephestos_rota == '0' or ender_rota == '0' or witbox_rota == '0' or prusamk_rota == '0':
		update.message.reply_text(text="Las impresoras operativas son:")
		if hephestos_rota == '0':
			update.message.reply_text(text="Hephestos 2")
		if ender_rota == '0':
			update.message.reply_text(text="Ender 3 V3 SE")
		if witbox_rota == '0':
			update.message.reply_text(text="Witbox 2")
		if prusamk_rota =='0':
			update.message.reply_text(text="Prusa MK3S")

	if hephestos_rota == '1' or ender_rota == '1' or witbox_rota == '1' or prusamk_rota == '1':
		update.message.reply_text(text="Las impresoras rotas son:")
		if hephestos_rota == '1':
			update.message.reply_text(text="Hephestos 2")
		if ender_rota == '1':
			update.message.reply_text(text="Ender 3 V3 SE")
		if witbox_rota == '1':
			update.message.reply_text(text="Witbox 2")
		if prusamk_rota =='1':
			update.message.reply_text(text="Prusa MK3S")

	if hephestos_rota == '2' or ender_rota == '2' or witbox_rota == '2' or prusamk_rota == '2':
		update.message.reply_text(text="En mantenimiento están:")
		if hephestos_rota == '2':
			update.message.reply_text(text="Hephestos 2")
		if ender_rota == '2':
			update.message.reply_text(text="Ender 3 V3 SE")
		if witbox_rota == '2':
			update.message.reply_text(text="Witbox 2")
		if prusamk_rota =='2':
			update.message.reply_text(text="Prusa MK3S")	

def version(update,context):
	update.message.reply_text(text="Bot Impresiones Reset V3.2")

def credits(update,context):
	update.message.reply_text(text="Creado y mantenido para reset por:")
	update.message.reply_text(text="Montse DCD (2020): Versión original del bot")
	update.message.reply_text(text="Miguel Sánchez de León 'Peque' (2020): Conexión del bot al servidor y Mantenimiento general")
	update.message.reply_text(text="Jaime Bravo (2021): Implementación de mejoras de estabilidad")
	update.message.reply_text(text="Álvaro GCP (2023): Desarrollo de la versión 3 del Bot")
	sticker_vocalialogo_id='CAACAgQAAxkBAAEK3lVlaakwJ7CCb42o16oYepAa_spvcQACuBAAArzPUFNaz8KoGb3bhDME'
	sticker_resetlogo_id='CAACAgQAAxkBAAEK3lRlaakvmn7nb_szE7dQYynt2ZDP8gAC_hIAAsKsUFMEo4Bbf2P7zzME'
	update.message.reply_sticker(sticker=sticker_resetlogo_id)
	update.message.reply_sticker(sticker=sticker_vocalialogo_id)


def api(update,context):
	sticker_python_id='CAACAgQAAxkBAAEK3k5laabKW7KzJ2oxsjq6ltbfUr_rkQACXREAAglgUVP0nJuCjbgcnDME'
	update.message.reply_sticker(sticker=sticker_python_id)
	update.message.reply_text(text="Python Telegram Bot API: V12.5.1")
	sticker_google_id='CAACAgQAAxkBAAEK3lBlaabMBPW1dIqZRZEbSempx1GTvgACcBMAAnuQSVPQv3LZo6JNfjME'
	update.message.reply_sticker(sticker=sticker_google_id)
	update.message.reply_text(text="Google API: V1.8.0")
	sticker_oauth_id='CAACAgQAAxkBAAEK3lJlaabPOWQ5cYSlxtA5-9JSmxBWkwAC4RIAAlTYUVP_CGrgEruWAAEzBA'
	update.message.reply_sticker(sticker=sticker_oauth_id)
	update.message.reply_text(text="Google OAuth Library: V0.4.1")
	sticker_dateutil_id='CAACAgQAAxkBAAEK3kxlaabHVYeRE90iKkPkvxXM-kUlaAAC6Q4AAht0UFMpPpZJkm33TzME'
	update.message.reply_sticker(sticker=sticker_dateutil_id)
	update.message.reply_text(text="Dateutil: V2.8.1")
##------------------------------------------------------------------------------------------------------------------##
import requests
import re
def get_url():
    contents = requests.get('https://random.dog/woof.json').json()
    url = contents['url']
    return url

def bop(update,context):
    url = get_url()
    update.message.reply_photo(photo=url)

##------------------------------------------------------------------------------------------------------------------##

def main():
	#Creamos updater y dispatcher ligado a nuestro TOKEN
	# updater = Updater(token='793436996:AAHfjuU7cmOWZru16Rt4jgdJDtWZjq5lq58', use_context=True)	#De mi bot de pruebas
	updater = Updater(token='706610104:AAFCzxCTS7vsgOy-lT6Vqd7jf057vbS_Xyw', use_context=True)	#Del de impresiones
	dispatcher = updater.dispatcher

	#Conversacion principal: handler
	convo_handler = ConversationHandler(
		entry_points=[CommandHandler('impresion',impresion)],

		states={
			DURACION: [CommandHandler('start',start),
					   CommandHandler('impresion',impresion),
					   CommandHandler('futuras',futuras),
					   MessageHandler(Filters.text, duracion)],

			DIA: [CommandHandler('start',start),
				  CommandHandler('impresion',impresion),
				  CommandHandler('futuras',futuras),
				  MessageHandler(Filters.text, dia)],

			HORA: [CommandHandler('start',start),
				   CommandHandler('impresion',impresion),
				   CommandHandler('futuras',futuras),
				   MessageHandler(Filters.text, hora)],

			IMPRESORA: [CommandHandler('start',start),
					    CommandHandler('impresion',impresion),
					    CommandHandler('futuras',futuras),
					    CallbackQueryHandler(impresora)],

			CATEGORIA: [CommandHandler('start',start),
					    CommandHandler('impresion',impresion),
					    CommandHandler('futuras',futuras),
					    CallbackQueryHandler(categoria)],

			RESERVAR: [CommandHandler('start',start),
					   CommandHandler('impresion',impresion),
					   CommandHandler('futuras',futuras),
					   CallbackQueryHandler(reservar)],

			#ERROR:	[CallbackQueryHandler(error)],
		},

		fallbacks=[MessageHandler(Filters.text, error)]
	)
	dispatcher.add_handler(convo_handler)

	#Conversacion para borrar eventos: handler
	borrar_handler = ConversationHandler(
		entry_points=[CommandHandler('borrar',borrar)],

		states={
			BORRAR_ID: [CommandHandler('start',start),
					    CommandHandler('impresion',impresion),
					    CommandHandler('futuras',futuras),
					    MessageHandler(Filters.text, borrar_id)],
		},

		fallbacks=[MessageHandler(Filters.text, error)]
	)
	dispatcher.add_handler(borrar_handler)

	#Conversacion para notificar impresora rota: handler
	rota_handler = ConversationHandler(
		entry_points=[CommandHandler('rota',rota)],

		states={
			ROTA_ID: [CommandHandler('start',start),
					    CommandHandler('impresion',impresion),
					    CommandHandler('futuras',futuras),
					    CallbackQueryHandler(rota_id)],
		},

		fallbacks=[MessageHandler(Filters.text, error)]
	)
	dispatcher.add_handler(rota_handler)

	#Conversacion para notificar impresora rota: handler
	arreglada_handler = ConversationHandler(
		entry_points=[CommandHandler('arreglada',arreglada)],

		states={
			ARREGLADA_ID: [CommandHandler('start',start),
					       CommandHandler('impresion',impresion),
					       CommandHandler('futuras',futuras),
					       CallbackQueryHandler(arreglada_id)],
		},

		fallbacks=[MessageHandler(Filters.text, error)]
	)
	dispatcher.add_handler(arreglada_handler)

	mantenimiento_handler = ConversationHandler(
		entry_points=[CommandHandler('mantenimiento',mantenimiento)],

		states={
			MANTENIMIENTO_ID: [CommandHandler('start',start),
					    CommandHandler('impresion',impresion),
					    CommandHandler('futuras',futuras),
					    CallbackQueryHandler(mantenimiento_id)],
		},

		fallbacks=[MessageHandler(Filters.text, error)]
	)
	dispatcher.add_handler(mantenimiento_handler)

	#Handlers de comandos

	start_handler = CommandHandler('start',start)
	dispatcher.add_handler(start_handler)

	futuras_handler = CommandHandler('futuras',futuras)
	dispatcher.add_handler(futuras_handler)

	estado_handler = CommandHandler('estado',estado)
	dispatcher.add_handler(estado_handler)

	api_handler = CommandHandler('api',api)
	dispatcher.add_handler(api_handler)

	version_handler = CommandHandler('version',version)
	dispatcher.add_handler(version_handler)

	credits_handler = CommandHandler('credits',credits)
	dispatcher.add_handler(credits_handler)

	#Esto es lo de los perretes
	perrete_handler = CommandHandler('bop',bop)
	dispatcher.add_handler(perrete_handler)

	#Updater updating
	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
	main()
