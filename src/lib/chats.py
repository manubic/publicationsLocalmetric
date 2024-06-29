from openai import OpenAI
import json, requests
from bs4 import BeautifulSoup

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



class MenuChat(Chat):
    def __init__(self, OpenAIclient: OpenAI) -> None:
        firstQuery: str = '''
            Tu objetivo es leer el menu de un restaurante.
            El menu te puede llegar de dos maneras distintas y lo devolveras en formato json: 
                - Puesto en una imagen: devuelve el menu de manera literal sin interpretaciones y en formato json.
                - Puesto en un texto: devuelve el menu de manera literal sin interpretaciones y en formato json.
        '''
        super().__init__(OpenAIclient, firstQuery)

    def getMenuOrServicesFromHTML(self, urls: list[str]) -> dict[str, str]:
        HTML: str = ''.join([BeautifulSoup(requests.get(url[0]).content, 'html.parser').get_text() for url in urls])
        query: str = HTML + '''
            Escribeme el titulo y una pequeña descripcion de cada producto de este menu en formato json:
                - Si es un restaurante sacame solamente el producto con su descripcion por cada plato o bebida.
                - Si no es un restaurante sacame solamente el servicio con su descripcion por cada servicio.
            Hazlo con este formato: {Items: [[Titulo comida o servivio, descripcion de la comida o servivio], [Titulo comida o servivio, descripcion de la comida o servivio], etc...]}.
            No saques los precios de los productos. Y descripción si en el texto viene el producto y su descripcion.
        '''
        print(query)

        self.messages.append({"role": "user", "content": query.replace("\n", "").replace('  ', '')})
        response = self.OpenAIclient.chat.completions.create(
            model = "gpt-4o",
            response_format = {"type": "json_object"},
            messages = self.messages,
        )
        self.messages.append({"role": "system", "content": response.choices[0].message.content})
        return json.loads(response.choices[0].message.content)
    
    def getMenuFromIMG(self, urlsIMG: list[str]) -> dict[str, list[list[str]]]:
        query: str = '''
            Escribeme el titulo y una pequeña descripcion de cada producto de este menu en formato json:
                - Si es un restaurante sacame solamente el producto con su descripcion por cada plato o bebida.
                - Si no es un restaurante sacame solamente el servicio con su descripcion por cada servicio.
            Hazlo con este formato: {Items: [[Titulo comida o servivio, descripcion de la comida o servivio], [Titulo comida o servivio, descripcion de la comida o servivio], etc...]}.
            No saques los precios de los productos. Y descripción si en el texto viene el producto y su descripcion.
        '''
        result = []
        
        for url in urlsIMG:
            response = self.OpenAIclient.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
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



class PublicationsChat(Chat):
    def __init__(self, OpenAIclient: OpenAI) -> None:
        query: str = '''
            Eres un experto en creacion de contenido para redes sociales tu objetivo es siempre crear el contenido que mas genera interacciones, curiosidad y es relevante para el usuario.
            Me devolveras las publicaciones en formato json, hazlo con este formato: {publications: [texto publicacion 1, texto publicacion 2, etc...]}.
        '''
        super().__init__(OpenAIclient, query)

    def createPublications(self, items: list[list[str]], examples: list[str], clientName: str) -> list[str]:
        parsedItems = ''.join([f'- {item[0]}: {item[1]}\n' if len(item) > 1 else f'- {item[0]}' for item in items])
        query: str = '''
            En base a este menu:
                ITEMS
            Y en base a estas publicaciones que te daran un ejemplo y el nombre de la ciudad donde se encuentra el restaurante:
                EXAMPLES
            Creame 3 nuevas publicaciones con productos del menu y una publicacion referenciando el tipo de comida y la cultura para que el local resulte atractivo.
            Las publicaciones no deben tener hashtags y al final debes añadir esta frase: (salto de linea) (emoji location)Si estas buscando un restaurante en (aqui el nombre de la ciudad), ¡En CLIENTNAME te esperamos!.
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