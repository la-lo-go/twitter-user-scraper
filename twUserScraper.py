import tweepy
import time
import datetime
import sqlite3
import os
import fnmatch
from mega import Mega

from apisKeys import *

def iniciar_apis():
    os.system('cls' if os.name == 'nt' else 'clear')
    print ("Iniciando APIs de Twitter y MEGA \nEspere a que este mensaje desaparezca")

    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.secure = True
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        mega = Mega()
        m = mega.login(mega_email, mega_password)
        
        return api, m
    except BaseException as e:
        print(f"EXCEPCION AL INICIAR LA API/MEGA [{e}], reintentado en 5 segundos")
        time.sleep(5)
        iniciar_apis()

def menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"--------   APIs y bot inicados   ---------\n")
    i = 0
    while i == 0:
        print("   1) Sacar los followers")
        print("   2) Sacar los follows")
        print("   3) Sacar los followers y los follows")
        print("   4) Descargar los archivos de un usuario")

        opt = str(input ("\n   Opcion que desea: "))
            
        if opt == "1" or opt == "2" or opt == "3" or opt == "4":
            i = 1
            return opt
        else:
            print(f"\nComando introducido [{opt}] no soportado, vuelva a intentarlo")

def cleanTXT(name):
    open(name, 'w').close()

def idInDatabase (sqliteConnection, id_user):
    try:
        cursor = sqliteConnection.cursor()
        cursor.execute("SELECT rowid FROM usuarios WHERE id = ?", (id_user,))
        data=cursor.fetchall()
        cursor.close
        
        if len(data)==0:
            return False
        else:
            return True

    except sqlite3.Error as error:
        print("Fallo al leer de la base de datos: ", error)
        return False

def createDatabase(con):
    cursorObj = con.cursor()
    cursorObj.execute("CREATE TABLE usuarios(id text PRIMARY KEY, name text, url text)")
    con.commit()

def insertInDatabase (sqliteConnection, entities):
    cursorObj = sqliteConnection.cursor()
    try:
        cursorObj.execute('INSERT INTO usuarios(id, name, url) VALUES(?, ?, ?)', entities)
        sqliteConnection.commit()
    except sqlite3.OperationalError:
        createDatabase(sqliteConnection)
        insertInDatabase (sqliteConnection, entities)

def getDatabaseInfo(sqliteConnection, id):
    try:
        sqliteConnection = sqlite3.connect('IDs_database.db')
        cursor = sqliteConnection.cursor()

        sql_select_query = """SELECT * from usuarios where ID = ?"""
        cursor.execute(sql_select_query, (id,))
        record = cursor.fetchall()

        return [record[0][1], record[0][2]]

    except sqlite3.Error as error:
        print("Fallo al leer de la base de datos: ", error)

def checkUser (name, tries):
    """Checkea si un usuario sigue existiendo en twitter

    Args:
        name (str): nombre del usuario

    Returns:
        ID (str): si el usuario existen
        'protected' (str): si el usuario tiene cuenta privada
        False: El usuario ya no existe
    """
    try: #Para comprobar si el usuario existe o esta protegido y no se sigue
        user = api.get_user(name)._json
        
        if user['protected'] == False or user['following'] == True:
            ID = user['id_str']
            return ID
        else:
            return 'protected'
    except tweepy.TweepError as e:
        if e.api_code == 50 or e.api_code == 63: #User not found-suspended
            return False
        else: #Reintenta 5 veces
            if tries < 5:
                checkUser(name, ++tries)
            else:
                return False

def download_user(id, name):
    """Descarga localmente en una carpeta los archivos que existen de un usuario

    Args:
        id (str): ID del usuario
        name (str): @ del usuario, será la carpeta donde se descarguente

    Returns:
        True/False: Si se ha podido descargar la carpeta
    """
    mega_folder = m.find(id)
    if mega_folder != None:
        files_names = [id+"_Follows.txt", id+"_Followers.txt"]
        try:
            os.mkdir(name)
        except OSError:
            pass
        for file_name in files_names:
            txt_mega = m.find(file_name)
            if txt_mega != None:
                try:
                    m.download(txt_mega, "./"+name)
                except PermissionError: #Bug raro que descarga con exito pero lanza excepcion
                    pass
        return True
    else:
        return False

def compare_files (user_ID, folder, opc_text):
    """Compara los dos ficheros, el nuevo y el antiguo

    Args:
        user_ID (str): ID del usuarios
        folder (str): carpeta del usuarios
        opc_text (str): "Followers"/"Follows"

    Returns:
        list: diference1 (eliminados), diference2 (nuevos)
    """

    diference1 = []
    diference2 = []

    r_old = get_UsersFromFile (folder, "*"+user_ID+"_"+opc_text+".txt")
    file_old = r_old[0]
    names_old = r_old[1][0]
    urls_old = r_old[1][1]

    r_new = get_UsersFromFile (folder, "New")
    file_new = r_new[0]
    names_new = r_new[1][0]
    urls_new = r_new[1][1]

    for url_old in urls_old: #lista de los que ya no están
        if url_old not in urls_new:
            index = urls_old.index(url_old)
            diference1.append(names_old[index])

    for url_new in urls_new: #lista de los nuevos
        if url_new not in urls_old:
            index = urls_new.index(url_new)
            diference2.append(names_new[index])

    renameFile (file_old, file_new, folder)

    return diference1, diference2

def get_UsersFromFile (folder, gen):
    """Separa los datos de los ficheros descargados

    Args:
        folder (str): Direccion del archivo del archivo
        gen (str): nombre del archivo a buscar

    Returns:
        users: lista de los usuarios
    """
    r = []
    users = []
    names = []
    urls = []

    for file in os.listdir(folder):
        if fnmatch.fnmatch(file, "*"+gen+"*"):
            r.append(file) #nombre del archivo
            with open(folder+'/'+file, "r",) as f: 
                for line in f:
                    if not (line == "USER NOT FOUND\n" or line == "USER SUSPENDED\n"):
                        split = line.split("\t")
                        names.append(split[0]) #nombre de usuario
                        urls.append(split[1]) #url
                        
                users.append(names) #merge los nombres
                users.append(urls) #merge las urls
    
    r.append(users)
    return r

def renameFile (old, new, folder):
    os.chdir(folder)
    os.rename(old, "old.txt")
    os.remove("old.txt")
    os.rename(new, old)
    os.chdir("..")

def extractID (string):
    return string.split("\t")[1].split("=")[1].split("\n")[0]

def uploadAndDelete (m_folder, m_file, file_name):
    """Sube el nuevo archivo a la nube y borra el anterior del archivo

    Args:
        m_folder (tuple): referencia a la carpeta de MEGA
        m_file (tuple): fichero del archivo en MEGA
        file_name (str): nombre del archivo
    """
    print (">>>> Subiendo fichero a MEGA ")
    server_filePath = "./temp/"+file_name

    m.rename(m_file, "temp.txt")
    m.upload(server_filePath, m_folder[0])
    print (">>>> Fichero subido", end="")

    os.remove(server_filePath)
    m.delete(m_file[0])
    print (" y ficheros temporales borrados")

def get_resume(name, resume_list):
    """Crea el resumen final de cada usuario_name

    Args:
        name (str): nombre del usuario_name
        resume_list (list): lista de elementos
                            [0] [3] (str): "Followers" or "Follows"
                            [1] [4] (list [str]): unfollowers or unfollows
                            [2] [5] (list [str]): new followers or new follows

    Returns:
        user_resume (str): resumen formeteado de todos datos
    """
    user_resume = "\n@"+name+":" # Añade el nombre al resumen
    
    if len(resume_list) == 6:
        eliminated_followers = resume_list[1]
        eliminated_follows = resume_list[4]
        soft_or_bans = []
        
        # Mira los mutuals que han sido eliminados
        for e_ers in eliminated_followers:
            for e_ows in eliminated_follows:
                if e_ers == e_ows:
                    soft_or_bans.append(e_ers)
                    
        if len(soft_or_bans) > 0:
            user_resume += f"\n>>>> Softblocks o cuentas de mutuals eliminadas: {len(soft_or_bans)}"
            for user in soft_or_bans:
                resume_list[1].remove(user)
                resume_list[4].remove(user)
                user_resume += "\n     -> "+user
                if checkUser(user, 0) != False:
                    user_resume += " [Softblock]"
                else:
                    user_resume += " [Eliminada]"
        else:
            user_resume += "\n>>>> No hay ningún softblock o cuenta eliminada"
    
    i = 0
    while i < len(resume_list):
        if resume_list[i] == "Followers":
            eliminados_lenght = len(resume_list[i+1]) #Los que le han dejado de seguir
            if eliminados_lenght > 0:
                user_resume += f"\n>>>> Le han dejado de seguir: {eliminados_lenght}"
                for user in resume_list[i+1]: 
                    user_resume += "\n     -> "+user
                    if checkUser(user, 0) == False:
                        user_resume += " [Eliminada]"
            else:
                user_resume += "\n>>>> No le ha dejado de seguir nadie"

            nuevos_lenght = len(resume_list[i+2]) #Los que le han empezado a seguir
            if nuevos_lenght > 0:
                user_resume += f"\n>>>> Le han empezado a seguir: {nuevos_lenght}"
                for user in resume_list[i+2]: 
                    user_resume += "\n     -> "+user
            else:
                user_resume += "\n>>>> No le ha empezado a seguir a nadie"

        if resume_list[i] == "Follows":
            eliminados_lenght = len(resume_list[i+1]) #Los que ha dejado de seguir
            if eliminados_lenght > 0:
                user_resume += f"\n>>>> Ha dejado de seguir a: {eliminados_lenght}"
                for user in resume_list[i+1]: 
                    user_resume += "\n     -> "+user
                    if checkUser(user, 0) == False:
                        user_resume += " [Eliminada]"
            else:
                user_resume += "\n>>>> No ha dejado de seguir a nadie"

            nuevos_lenght = len(resume_list[i+2]) #Los que ha empezado a seguir
            if nuevos_lenght > 0:
                user_resume += f"\n>>>> Ha empezado a seguir a: {nuevos_lenght}"
                for user in resume_list[i+2]: 
                    user_resume += "\n     -> "+user
            else:
                user_resume += "\n>>>> No ha empezado a seguir a nadie"
        i += 3
    return user_resume

def twitter_scraper (usuario_name, user_ID, option, user_number):
    folder_exist = False #El fichero y carpeta NO existen por defecto
    file_exists = False 
    temp_folder = "./temp"
    mega_folder_name = user_ID
    resume_list = []

    if option == "1":
        opc = ["Followers"]
    elif option == "2":
        opc = ["Follows"]
    elif option == "3":
        opc = ["Followers", "Follows"]
        
    #Borra archivos del disco que hayan quedado de ejecuciones a medias
    for file in os.listdir(temp_folder):
        if (file, "*"+user_ID+"*"):
            os.remove(temp_folder+"/"+file)

    for opc_text in opc:
        file_name = user_ID+"_"+opc_text+".txt"

        #Si ya existe el fichero de ese usuario se descarga, se crea uno temporal para despues comparar 
        mega_folder = m.find(mega_folder_name)
        if mega_folder != None:
            folder_exist = True
            txt_mega = m.find(user_ID+"/"+file_name)
            if txt_mega != None:
                file_exists = True
                file_name = user_ID+"_"+opc_text+"_New.txt"
                try:
                    m.download(txt_mega, temp_folder)
                except PermissionError: #Bug raro que descarga con exito pero lanza excepcion
                    pass

        file_path = temp_folder+"/"+file_name  

        if folder_exist == False:
            m.create_folder(mega_folder_name)
            mega_folder = m.find(mega_folder_name)
            print("\nEl directorio de este usuario no existía")

        if file_exists == 1:
            print (f"\nFichero de los {opc_text.lower()} de @{usuario_name} existente y descargado")
        else:
            print (f"\nFichero de los {opc_text.lower()} de @{usuario_name} NO existente")

        i = 0   
        while i == 0:
            try:
                if opc_text == "Follows":
                    n = str(api.get_user(user_ID).friends_count+1)
                    print (f"\nRecogiendo los IDs de los {n} follows de @{usuario_name}\n")
                    ids = list(tweepy.Cursor(api.friends_ids, screen_name=usuario_name).items())
                    i = 1
                else:
                    n = str(api.get_user(user_ID).followers_count)
                    print (f"\nRecogiendo los IDs de los {n} followers de @{usuario_name}\n")
                    ids = list(tweepy.Cursor(api.followers_ids, screen_name=usuario_name).items())
                    i = 1
            except BaseException as e:
                print("EXCEPCION CONSIGUIENDO LOS IDs: ", e)

        maximo = len(ids)
        users_NotFounds = 0
        users_In = 0

        try:
            sqliteConnection = sqlite3.connect('IDs_database.db')
        except sqlite3.Error as error:
            print("Fallo al conectarse a la base de datos: ", error)  

        with open(file_path, "a", encoding="utf-8") as f:
            i = 0
            users_Out = 900 - api.rate_limit_status()['resources']['users']['/users/:id']['remaining']
            while i < maximo:
                try:
                    if not idInDatabase(sqliteConnection, ids[i]):
                        if users_Out >= 897:
                            users_Out = 900 - api.rate_limit_status()['resources']['users']['/users/:id']['remaining']
                        user=api.get_user(ids[i])
                        screenName=user.screen_name
                        url=f'https://twitter.com/intent/user?user_id={ids[i]}'
                        entities = (str(ids[i]), screenName, url)
                        insertInDatabase (sqliteConnection, entities)
                        f.write("@"+screenName+"\t"+url+"\n")
                        users_Out += 1
                        print(str(user_number)+"/"+usuarios_size+">"+usuario_name+">"+opc_text+">"+str(i+1)+"/"+str(maximo)+") "
                            +screenName+datetime.datetime.now().strftime(" [%H:%M:%S")+", NOT in database, "+str(round((users_Out/900)*100, 1))+"%]")
                    else:
                        entities = getDatabaseInfo(sqliteConnection, ids[i])
                        f.write("@"+entities[0]+"\t"+entities[1]+"\n")
                        print(str(user_number)+"/"+usuarios_size+">"+usuario_name+">"+opc_text+">"+str(i+1)+"/"+str(maximo)+") "
                            +entities[0]+datetime.datetime.now().strftime(" [%H:%M:%S")+", IN database]")
                        users_In += 1
                except tweepy.TweepError as e:
                    if e.api_code == 50: #User not found
                        f.write("USER NOT FOUND\n")
                        print("------------- EXCEPCION: USER NOT FOUND "
                            +datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")+" -------------")
                        users_NotFounds += 1
                    elif e.api_code == 63: #User has been suspended
                        f.write("USER SUSPENDED\n")
                        print("------------- EXCEPCION: USER SUSPENDED "
                            +datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")+" -------------")
                        users_NotFounds += 1
                    else:
                        print("-------------------- EXCEPCION "+datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")+
                            " --------------------")
                        i -= 1
                i += 1

        user_number += 1
        if sqliteConnection:
            sqliteConnection.close()            

        percentages.append(str(round((users_In/maximo)*100))+"%")
        file_name = user_ID+"_"+opc_text+".txt"

        print (f"\n\n>>>> Users not found/suspended: {users_NotFounds}")
        print (f">>>> Users IN database: {percentages[user_number-2]}")

        if file_exists == True:
            eliminados, nuevos = compare_files (user_ID, temp_folder, opc_text) #Saca la diferencia con la anterior copia
            
            resume_list.extend((opc_text, eliminados, nuevos))

            if len(eliminados) > 0 or len(nuevos) > 0: #Si hay cambios se sube
                uploadAndDelete (mega_folder, txt_mega, file_name)
            else:
                print(">>>> No hay cambios con la anterior copia")

        else: #Sube el nuevo archivo al MEGA
            m.upload(file_path, mega_folder[0])

            print (">>>> Fichero subido a MEGA ", end="")
            os.remove(temp_folder+"/"+file_name)
            print("y fichero temporal borrado")
    
    if folder_exist == True:
        return get_resume(usuario_name, resume_list)
    else:
        return f"@{usuario_name} es un nuevo usuario!"
    
#############################################################

if __name__ == '__main__':
    bucle = 0
    while bucle == 0:

        api, m = iniciar_apis()

        option = menu()

        if option == "1":
            usuarios_names = input("\nEscriba los @ de los usuarios de los que quiere sacar sus followers"
                                    " [separados por espacios]:\n-> ").split(" ")
            usuarios_size = str(len(usuarios_names))

        if option == "2":
            usuarios_names = input("\nEscriba los @ de los usuarios de los que quiere sacar sus follows"
                                    " [separados por espacios]:\n-> ").split(" ")
            usuarios_size = str(len(usuarios_names))

        if option == "3":
            usuarios_names = input("\nEscriba los @ de los usuarios de los que quiere sacar sus followers y follows"+
                                    " [separados por espacios]:\n-> ").split(" ")
            usuarios_size = str(len(usuarios_names)*2)

        if option == "4":
            usuarios_names = input("\nEscriba los @ de los usuarios de los que quiere descargar archivos"+
                                    " [separados por espacios]:\n-> ").split(" ")

        user_number = 1
        users_Out = 0
        percentages = []
        resume = []

        for usuario_name in usuarios_names:

            if usuario_name == "": #Comprueba que no se han introducido dos espacios
                user_number += 1
                continue
            
            #Comprueba si el usuario existe o está protegido (con candado)
            check = checkUser(usuario_name, 0)
            if check == False:
                print (f"\n>>>> El usuario @{usuario_name} no existe")
                user_number += 1
                continue
            elif check == 'protected':
                user_number += 1
                continue
            else:
                user_ID = check
            
            if option != "4":
                user_resume = twitter_scraper (usuario_name, user_ID, option, user_number)
                resume.append(user_resume)
                user_number += 1
            else:
                if download_user(user_ID, usuario_name):
                    print(f"\nArchivos de @{usuario_name} descargados")
                else:
                    print(f"\nNo existen archivos de @{usuario_name}")

        if len(percentages) > 1:
            i = 0
            print ("\n\nUsers IN database resume: ")
            while i < len(usuarios_names):
                print (f"   -> {usuarios_names[i]}: {percentages[i]}")
                i += 1

            for r in resume:
                if len(r) > 18:
                    print(r)

        string = input ("\n¿Quiere ejecutar de nuevo el programa? [y/cualquier cosa] ").lower()
        if string == "y":
            os.system('cls' if os.name == 'nt' else 'clear')
        else:
            bucle = 1

    print("\n\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("++++++++++++++++++++++++++++++++   ACABADO   +++++++++++++++++++++++++++++++++")
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n")
