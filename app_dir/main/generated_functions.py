from __future__ import print_function

import json
from django.http import HttpResponse, JsonResponse, request
from googleapiclient import errors
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from app_dir.main.models import MailBox

import requests
import pickle
import os.path
import httplib2
import os
import base64
import mimetypes

try:
    import argparse

    flags = tools.argparser.parse_args([])
except ImportError:
    flags = None

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def Read(param, param2):
    creds = None
    if os.path.exists('token' + param + '.pickle'):
        with open('token' + param + '.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'media/mailbox/' + param, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token' + param + '.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=[param2]).execute()
    messages = results.get('messages', [])
    if not messages:
        print("No messages found.")
    else:
        list = []
        print("Message snippets:")
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            print(msg['snippet'])
            list.append(msg['snippet'])

        return list


def Search(param, param2, param3):
    creds = None
    if os.path.exists('token' + param + '.pickle'):
        with open('token' + param + '.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'media/mailbox/' + param, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token' + param + '.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=[param2], q=param3).execute()
    messages = results.get('messages', [])
    if not messages:
        print("No messages found.")
    else:
        print("Message snippets:")
        list = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            print(msg['snippet'])
            list.append(msg['snippet'])
        return list


def Label(param):
    creds = None
    if os.path.exists('token' + param + '.pickle'):
        with open('token' + param + '.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'media/mailbox/' + param, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token' + param + '.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    list = []
    for label in labels:
        list.append(label['name'])
        # list.append('\\n\\n')
    print(list)
    return list


class auth:
    def __init__(self, SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME):
        self.SCOPES = SCOPES
        self.CLIENT_SECRET_FILE = CLIENT_SECRET_FILE
        self.APPLICATION_NAME = APPLICATION_NAME

    def get_credentials(self):
        cwd_dir = os.getcwd()
        credential_dir = os.path.join(cwd_dir, '.media/mailbox/' + self.CLIENT_SECRET_FILE)
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'credentials.json')
        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials


class SendEMail:
    def __init__(self, service):
        self.service = service

    def create_message(self, sender, to, subject, message_text):
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def create_message_with_attachment(self,
                                       sender, to, subject, message_text, file):
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        msg = MIMEText(message_text)
        message.attach(msg)
        content_type, encoding = mimetypes.guess_type(file)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(file, 'rb')
            msg = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(file, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(file, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(file, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(file)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self, user_id, message):
        try:
            message = (self.service.users().messages().send(userId=user_id, body=message).execute())
            list = 'Message Successfully Sent!\nMessage Id: %s' % message['id']
            print(list)
            return list
        except errors.HttpError as error:
            print('An error occurred: %s' % error)


def Send(param, param2, param3, param4, param5):
    SCOPES = 'https://mail.google.com/'
    CLIENT_SECRET_FILE = 'media/mailbox/' + param
    APPLICATION_NAME = 'Gmail API Python Quickstart'
    authInst = auth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
    credentials = authInst.get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    sendInst = SendEMail(service)
    message = sendInst.create_message(param2, param3, param4, param5)
    list = sendInst.send_message('me', message)
    return list


def weather_info(city):
    api_key = "bd27419d66c8678613e978ca561ad3f7"
    url = "http://api.openweathermap.org/data/2.5/forecast?APPID={}".format(api_key) + "&q=" + city
    data = requests.get(url).json()
    print(data)
    # data = (data['list'][0]['main']['temp'])
    data = data['list'][0]['weather'][0]['main']
    return data


def action_motor(motor_status):
    url = 'http://127.0.0.1:8000/api/actuators/9/'

    data = {

        "topic": "mc101",
        "value": motor_status,
        "time": "2019-01-24T13:35:24.246226Z",
        "name": "1"
    }
    response = requests.put(url, data=data)
    print(response.text)


def get_lowersensor():
    empty_list = []
    sensor_tag = 'soil_moisture_sensor::2.33::21.22::sayeed'
    data = requests.get("http://127.0.0.1:8000/api/lowersensors/").json()
    for i in data:
        if i['topic'] == sensor_tag:
            empty_list.append(i)

    data = empty_list[-1]
    print(data)

    data = int(data['value'])
    return data


def value_to_print(text):
    print(text + " pass function")
    return text


def print_content(what_to_print):
    result = what_to_print
    print(result)
    return result


import ast
import copy


def convertExpr2Expression(Expr):
    Expr.lineno = 0
    Expr.col_offset = 0
    result = ast.Expression(Expr.value, lineno=0, col_offset=0)

    return result


def exec_with_return(code):
    code_ast = ast.parse(code)

    init_ast = copy.deepcopy(code_ast)
    init_ast.body = code_ast.body[:-1]

    last_ast = copy.deepcopy(code_ast)
    last_ast.body = code_ast.body[-1:]

    exec(compile(init_ast, "<ast>", "exec"), globals())
    if type(last_ast.body[0]) == ast.Expr:
        return eval(compile(convertExpr2Expression(last_ast.body[0]), "<ast>", "eval"), globals())
    else:
        exec(compile(last_ast, "<ast>", "exec"), globals())


def custom_if(param0, param1):
    if param0 is True:
        result = param1
        return result


def custom_if_else(param0, param1, param2):
    if param0 is True:
        result = param1
        return result
    else:
        return param2


def api_creator(param0, param1, param2, param3):
    url = 'http://127.0.0.1:8000/api/api/'
    second_url = 'http://127.0.0.1:8000/api/service_registry/'
    data = {
        "name": param0,
        "api": param1,
        "fields": param2,
        "connection": param3
    }
    data2 = {
        "name": param0,
        "service_type": 'api'
    }
    requests.post(url, data=data)
    requests.post(second_url, data=data2)

    return "API Created Successfully!"
    # print(response.text)


def interactive_creator(param0, param1):
    url = 'http://127.0.0.1:8000/api/interactive/'
    second_url = 'http://127.0.0.1:8000/api/service_registry/'

    data = {
        "name": param0,
        "fields": param1,
    }
    data2 = {
        "name": param0,
        "service_type": 'interactive'
    }
    requests.post(url, data=data)
    requests.post(second_url, data=data2)
    return "Interactive Block Created Successfully!"
def newspaper_headlines(param0,param1,param2):
    data = requests.get(" https://newsapi.org/v2/top-headlines?q=" + param0 + "&from=" + param1 + "&sortBy=" + param2 + "&apiKey=0bd59e0fc1474b5caf16c806d5dffc9c ").json()
    print(data)
    return data

def recipe_puppy(param0,param1,param2):
    data = requests.get(" http://www.recipepuppy.com/api/?i=" + param0 + "&q=" + param1 + "&p=" + param2 + " ").json()
    print(data)
    return data

def cricket(param0,param1,param2):
    data = requests.get(" https://dev132-cricket-live-scores-v1.p.rapidapi.com/matches.php?completedlimit=" + param0 + "&inprogresslimit=" + param1 + "&upcomingLimit=" + param2 + "&appid=dc0613934dmsh24f397f54e7f03bp19870ejsncb99ec04982d ").json()
    print(data)
    return data

def doctor(param0,param1,param2):
    data = requests.get(" https://api.betterdoctor.com/2016-03-01/doctors?location=" + param0 + "&skip=" + param1 + "&limit=" + param2 + "&user_key='CODE_SAMPLES_KEY_9d3608187' ").json()
    print(data)
    return data


def rajon():
    path = 'mailbox/credentials.json'
    result = path.split('/')
    print(result)
    return result[1]

def news(param0,param1,param2):
    data = requests.get(" https://newsapi.org/v2/top-headlines?q=" + param0 + "&from=" + param1 + "&sortBy=" + param2 + "&apiKey=0bd59e0fc1474b5caf16c806d5dffc9c ").json()
    print(data)
    return data
