from openai import OpenAI
import json, requests, time
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from io import BytesIO

class Chat:
    def __init__(self, OpenAIclient: OpenAI, *prompts: list[str]) -> None:
        self.OpenAIclient: OpenAI = OpenAIclient
        self.messages: list[dict] = []
        for prompt in prompts:
            self.messages.append({"role": "user", "content": prompt})
        response = self.OpenAIclient.chat.completions.create(
            model = "gpt-4o",
            response_format = {"type": "json_object"},
            messages = self.messages,
        )
        self.messages.append({"role": "system", "content": response.choices[0].message.content})



class MenuModel(Chat):
    def __init__(self, OpenAIclient: OpenAI) -> None:
        firstQuery: str = '''
            Tu objetivo es leer el menu de un restaurante.
            El menu te puede llegar de dos maneras distintas y lo devolveras en formato json: 
                - Puesto en una imagen: devuelve el menu de manera literal sin interpretaciones y en formato json.
                - Puesto en un texto: devuelve el menu de manera literal sin interpretaciones y en formato json.
        '''
        self.query: str = '''
            Escribeme el titulo y una pequeña descripcion de cada producto de este menu en formato json:
                - Si es un restaurante sacame solamente el producto con su descripcion por cada plato o bebida.
                - Si no es un restaurante sacame solamente el servicio con su descripcion por cada servicio.
            Hazlo con este formato y solamente este formato sin inventarte ningun otro tipo de formato: {Items: [[Titulo comida o servivio, descripcion de la comida o servivio], [Titulo comida o servivio, descripcion de la comida o servivio], etc...]}.
            No saques los precios de los productos. Y descripción si en el texto viene el producto y su descripcion.
        '''
        super().__init__(OpenAIclient, firstQuery)

    def getMenuOrServicesFromHTML(self, urls: list[str]) -> dict[str, list[list[str]]]:
        HTMLList: list[str] = [BeautifulSoup(requests.get(url[0]).content, 'html.parser').get_text() for url in urls]
        result: list[str] = []
        for html in HTMLList:
            if html.split(' ')[0] == '403': return False
            query: str = (html + '. ' + self.query).replace('\n', '').replace('  ', '')
            response = self.OpenAIclient.chat.completions.create(
                model = "gpt-4o",
                response_format = {"type": "json_object"},
                messages = self.messages + [{"role": "system", "content": query}],
            )
            result += json.loads(response.choices[0].message.content)['Items']
        return {'Items': result}

    def getMenuFromFile(self, urlsFiles: list[str]) -> dict[str, list[list[str]]]:
        if urlsFiles[0][0].split('?')[0].split('.')[-1] == 'pdf':
            return self.getMenuFromPDF(urlsFiles)

        result = []
        for url in urlsFiles:
            response = self.OpenAIclient.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.query},
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": url[0]
                        },
                        },
                    ],
                    }
                ],
                max_tokens=1000,
            )
            splitted_content: list[str] = (response.choices[0].message.content.replace('  ', '')).split('\n')[1::]
            result += json.loads(''.join(splitted_content[:len(splitted_content)-1:]))['Items']
        return {'Items': result}
    
    def getMenuFromPDF(self, urlsPDF: list[str]):
        urlsPDFcontent: list[str] = []
        for url in urlsPDF:
            pdf = PdfReader(BytesIO(requests.get(url[0]).content))
            urlsPDFcontent.append(''.join([pdf.pages[i].extract_text() for i in range(len(pdf.pages))]))

        result = []
        for text in urlsPDFcontent:
            query: str = (text + self.query).replace('\n', '').replace('  ', '')
            response = self.OpenAIclient.chat.completions.create(
                model = "gpt-4o",
                response_format = {"type": "json_object"},
                messages = self.messages + [{"role": "system", "content": query}],
            )
            result += json.loads(response.choices[0].message.content)['Items']
        return {'Items': result}



class PublicationsModel(Chat):
    def __init__(self, OpenAIclient: OpenAI) -> None:
        query: str = '''
            Eres un experto en generar publicaciones de Google Maps. Tu objetivo es siempre crear publicaciones atractivas que generen alegría y hagan que los clientes quieran venir al local
            Me devolveras las publicaciones en formato json, hazlo con este formato: {publications: [texto publicacion 1, texto publicacion 2, etc...]}.
        '''
        super().__init__(OpenAIclient, query)

    def createPublications(self, items: list[list[str]], examples: list[str], clientName: str) -> list[str]:
        parsedItems: str = ''.join([f'- {item[0]}: {item[1]}\n' if len(item) > 1 else f'- {item[0]}' for item in items])
        query: str = '''
            En base a este menu de productos / servicios:
                ITEMS
            Y en base a estas publicaciones que te daran un ejemplo y el nombre de la ciudad donde se encuentra el local:
                EXAMPLES
            Creame 3 nuevas publicaciones con productos / servicios del menu y una publicacion referenciando el tipo de comida / servicio y la cultura para que el local resulte atractivo.
            Las publicaciones no deben tener hashtags.
            Usa un lenguaje simple, de sexto grado como mucho y escribe las publicaciones en el mismo idioma que los ejemplos, si son en español escribe en español de España.
            Trata de poner emojis y separar cada frase con saltos de linea.
            Devuelveme las publicaciones en formato json, hazlo con este formato: {publications: [texto publicacion 1, texto publicacion 2, etc...]}.
        '''.replace("ITEMS", parsedItems).replace("EXAMPLES", '\n'.join(examples)).replace("CLIENTNAME", clientName)

        self.messages.append({"role": "user", "content": query})
        response = self.OpenAIclient.chat.completions.create(
            model = "gpt-4o",
            response_format = {"type": "json_object"},
            messages = self.messages,
        )
        self.messages.append({"role": "system", "content": response.choices[0].message.content})
        return json.loads(response.choices[0].message.content)