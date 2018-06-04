import time
import datetime
import requests
import urllib
from sys import stdout
import mechanicalsoup
import argparse
from credential import TOKEN, ID


URLTEL = "https://api.telegram.org/bot{}/".format(TOKEN)
nic_base = "http://www.nic.cl/registry/Whois.do?d="

# TODO: cambiar estos parámetros para que no sean variables globales
initial_politeness = 30
politeness = initial_politeness
politeness_tel = initial_politeness

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URLTEL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)

def unconditional(message, chat_id):
    global politeness_tel
    try:
        send_message(message, chat_id)
        politeness_tel = initial_politeness
    except Exception as e:
        print('Exception telegram! waiting ' + str(politeness_tel) + 's')
        time.sleep(politeness_tel)
        politeness_tel = 1.2 * politeness_tel

def is_free(url):
    global politeness
    try:
        browser = mechanicalsoup.StatefulBrowser()
        url = nic_base + url
        o = browser.open(url)
        page = browser.get_current_page()
        first_button = page.find_all('button')[0]
        politeness = initial_politeness
        if first_button.text.startswith('Inscribir'):
            return True
        elif first_button.text.startswith('Restaurar'):
            return False
    except Exception as e:
        print('Exception en nic! waiting ' + str(politeness) + 's')
        time.sleep(politeness)
        politeness = 1.2 * politeness
        return False
    return False
    
def main():
    global initial_politeness
    parser = argparse.ArgumentParser(description='Robot para avisar si un dominio de NIC Chile se ha liberado.')
    parser.add_argument('url', metavar='URL', type=str,
                        help='Url a consultar')
    parser.add_argument('-nv', '--notVerbose', default=False, action='store_true',
                        help='Muestra 0 información del funcionamiento.')
    parser.add_argument('-e', '--every', type=int, default=720, metavar='N', help='Minutos cada cuanto se reporta (independiente del resultado).')
    parser.add_argument('-s', '--segundos', type=int, default=5, metavar='S', help='Segundos cada cuanto se consulta el servicio de NIC Chile.')
    parser.add_argument('-m', '--multiplicador', type=float, default=2.0, metavar='M', help='Base de delay exponencial de espera para alertar cuando ya se ha liberado el dominio.')
    parser.add_argument('-M', '--maxRequests', type=int, default=25000, metavar='R', help='Número máximo de requests totales.')

    args = parser.parse_args()
    verbose = not args.notVerbose
    every_minutes = args.every
    segundos = args.segundos
    url = args.url
    mult = args.multiplicador
    maxRequests = args.maxRequests
    reportAt = 11

    initial_politeness += segundos

    if verbose:
        print("comenzando!")

    report_anyway = False
    was_free = False
    report_time = False
    already_reported_time = False

    i = 0
    t = segundos
    every = int((60 * every_minutes) / t)
    add_delay = 1
        
    free_message = '****** ' + url + ' ESTA LIBRE!!!! ******\n\n PARA INSCRIBIR, IR AHORA A\n\n' + nic_base + url 
    while True:
        if i == maxRequests:
            print()
            print('Terminando esta ejecución... bye')
            break
        if i % every == every - 1:
            report_anyway = True

        ahora = datetime.datetime.now()
        hora = ahora.hour
        minuto = ahora.minute

        if (hora == reportAt or hora == 12 + reportAt) and minuto == 0:
            if already_reported_time:
                report_time = False
            else:
                report_time = True
        elif (hora == reportAt or hora == 12 + reportAt) and minuto > 0:
            already_reported_time = False

        if verbose:
            stdout.write('\r' + str(i) + ' requests enviadas a ' + str(nic_base) + url)

        go = is_free(url)
        if not go and was_free:
            if verbose:
                print('\n:( TOO LATE')
            too_late_message = 'DEMASIADO TARDE!!!!\n\nDOMINIO YA FUE TOMADO!!!!\n\n:('
            unconditional(too_late_message, ID)
            unconditional('terminando', ID)
            break


        if go or report_anyway or report_time:
            if verbose:
                print('\nreportando...')
            if go:
                unconditional(free_message, ID)
                add_delay *= mult
                t += add_delay
                unconditional('(siguiente alerta en ' + str(int(t)) + 's)', ID)
                was_free = True
            elif report_anyway:
                message = 'Dominio ' + url + ' sigue sin liberarse'
                unconditional(message, ID)
                report_anyway = False
            elif report_time:
                message = 'Dominio ' + url + ' sigue sin liberarse'
                unconditional(message, ID)
                already_reported_time = True

        i += 1
        time.sleep(t)

if __name__ == '__main__':
    main()





