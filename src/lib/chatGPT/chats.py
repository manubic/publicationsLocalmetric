from openai import OpenAI
import json
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from io import BytesIO


class Chat:
    def __init__(self, openai_client: OpenAI, *prompts: list[str]) -> None:
        self.openai_client: OpenAI = openai_client
        self.messages: list[dict] = []
        for prompt in prompts:
            self.messages.append({"role": "user", "content": prompt})
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=self.messages,
        )
        self.messages.append(
            {"role": "system", "content": response.choices[0].message.content}
        )

    def query(self, query: str) -> str:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=self.messages + [{"role": "user", "content": query}],
        )
        return json.loads(response.choices[0].message.content)


class MenuModel(Chat):
    def __init__(self, openai_client: OpenAI) -> None:
        first_query: str = """
            Tu objetivo es leer el menu de un restaurante.
            El menu te puede llegar de dos maneras distintas y lo devolveras en formato json: 
                - Puesto en una imagen: devuelve el menu de manera literal sin interpretaciones y en formato json.
                - Puesto en un texto: devuelve el menu de manera literal sin interpretaciones y en formato json.
        """
        self.query: str = """
            Escribeme el titulo y una pequeña descripcion de cada producto de este menu en formato json:
                - Si es un restaurante sacame solamente el producto con su descripcion por cada plato o bebida.
                - Si no es un restaurante sacame solamente el servicio con su descripcion por cada servicio.
            Hazlo con este formato: {Items: [[Titulo comida o servivio, descripcion de la comida o servivio], [Titulo comida o servivio, descripcion de la comida o servivio], etc...]}.
            No saques los precios de los productos. Y descripción si en el texto viene el producto y su descripcion.
        """
        super().__init__(openai_client, first_query)

    def get_menu_from_text(self, list_texts: list[str]):
        query: str = (
            ("\n".join([content[0] for content in list_texts[1:]])) + ". " + self.query
        )
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=self.messages + [{"role": "system", "content": query}],
        )
        parsed_content: str = (
            "{"
            + response.choices[0]
            .message.content.replace("  ", "")
            .replace("\n", "")
            .split("{")[1]
            .split("}")[0]
            + "}"
        )
        return json.loads(parsed_content)

    def get_menu_or_services_from_html(
        self, urls_or_texts: list[str]
    ) -> dict[str, list[list[str]]]:
        if urls_or_texts[0][0] == "codigo":
            return self.get_menu_from_text(urls_or_texts)
        try:
            html_list: list[str] = [
                BeautifulSoup(requests.get(url[0]).text, "html.parser").get_text()
                for url in urls_or_texts
            ]
        except Exception:
            return False
        result: list[str] = []
        for html in html_list:
            if "403" in html:
                return False
            query: str = (html + ". " + self.query).replace("\n", "").replace("  ", "")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=self.messages + [{"role": "system", "content": query}],
            )
            if "Items" not in json.loads(response.choices[0].message.content):
                return False
            result += json.loads(response.choices[0].message.content)["Items"]
        return {"Items": result}

    def get_menu_from_file(self, urls_files: list[str]) -> dict[str, list[list[str]]]:
        if urls_files[0][0].split("?")[0].split(".")[-1] == "pdf":
            return self.get_menu_from_pdf(urls_files)

        result: list[list[str]] = []
        for url in urls_files:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.query},
                            {"type": "image_url", "image_url": {"url": url[0]}},
                        ],
                    }
                ],
                max_tokens=4096,
            )
            parsed_content: str = (
                "{"
                + response.choices[0]
                .message.content.replace("  ", "")
                .replace("\n", "")
                .split("{")[1]
                .split("}")[0]
                + "}"
            )
            result += json.loads(parsed_content)["Items"]
        return {"Items": result}

    def get_menu_from_pdf(self, urls_pdf: list[str]):
        urls_pdf_content: list[str] = []
        for url in urls_pdf:
            pdf = PdfReader(BytesIO(requests.get(url[0]).content))
            urls_pdf_content.append(
                "".join([pdf.pages[i].extract_text() for i in range(len(pdf.pages))])
            )

        result: list[list[str]] = []
        for text in urls_pdf_content:
            query: str = (text + self.query).replace("\n", "").replace("  ", "")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=self.messages + [{"role": "system", "content": query}],
            )
            parsed_content: str = (
                "{"
                + response.choices[0]
                .message.content.replace("  ", "")
                .replace("\n", "")
                .split("{")[1]
                .split("}")[0]
                + "}"
            )
            result += json.loads(parsed_content)["Items"]
        return {"Items": result}


class PublicationsModel(Chat):
    def __init__(self, openai_client: OpenAI) -> None:
        query: str = """
            Eres un experto en generar publicaciones de Google Maps. Tu objetivo es siempre crear publicaciones atractivas que generen alegría y hagan que los clientes quieran venir al local
            Me devolveras las publicaciones en formato json, hazlo con este formato: {publications: [texto publicacion 1, texto publicacion 2, etc...]}.
        """
        super().__init__(openai_client, query)

    def create_publications(
        self,
        items: list[list[str]],
        examples: list[str],
        client_name: str,
        images: list[dict[str, str]],
    ) -> list[str]:
        parsed_items: str = "".join(
            [
                f"- {item[0]}: {item[1]}\n" if len(item) > 1 else f"- {item[0]}"
                for item in items
            ]
        )
        query: str = (
            """
            En base a este menu de productos / servicios:
                ITEMS
            Y en base a estas publicaciones que te daran un ejemplo y el nombre de la ciudad donde se encuentra el local:
                EXAMPLES
            Crea solamente publicaciones de productos que esten entre estas imagenes disponibles:
                IMAGES
            Creame 3 nuevas publicaciones con productos / servicios del menu y una publicacion referenciando el tipo de comida / servicio y la cultura para que el local resulte atractivo.
            Las publicaciones no deben tener hashtags. El nombre del local es CLIENTNAME.
            Usa un lenguaje simple, de sexto grado como mucho y escribe las publicaciones en el mismo idioma de las publicaciones de ejemplo, por ejemplo, si las publicaciones estan en italiano escribe en italiano
            si son en español escribe en español de España.
            Trata de poner emojis y separar cada frase con saltos de linea.
            Devuelveme las publicaciones en formato json, hazlo con este formato: {
                "publications": [
                    {"text": texto publicacion 1, "product": nombre exacto del producto escogido para la publicacion 1}, 
                    {"text": texto publicacion 2, "product": nombre exacto del producto escogido para la publicacion 2},
                    etc...
                ]
            }.
        """.replace("ITEMS", parsed_items)
            .replace("EXAMPLES", "\n".join(examples))
            .replace("CLIENTNAME", client_name)
            .replace("IMAGES", "\n".join([f"- {image['name']}" for image in images]))
        )

        self.messages.append({"role": "user", "content": query})
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=self.messages,
        )
        self.messages.append(
            {"role": "system", "content": response.choices[0].message.content}
        )
        return json.loads(response.choices[0].message.content)
