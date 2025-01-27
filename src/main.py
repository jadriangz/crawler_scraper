import asyncio
import os
import pdfkit
import requests
from crawl4ai import AsyncWebCrawler
from argparse import ArgumentParser
from urllib.parse import urljoin

class WebScraper:
    async def scrape(self, url: str) -> str:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown, result.links  # Devuelve el contenido y los enlaces

    async def scrape_recursive(self, base_url: str, max_depth: int = 3) -> dict:
        visited = set()
        to_visit = [(base_url, 0)]  # (url, profundidad)
        all_content = {}

        while to_visit:
            url, depth = to_visit.pop(0)
            if url in visited or depth > max_depth:
                continue

            print(f"Scraping: {url} (Profundidad: {depth})")
            try:
                content, links = await self.scrape(url)
                all_content[url] = content
                visited.add(url)

                # Agregar enlaces a la lista de pendientes
                for link in links:
                    full_url = urljoin(base_url, link)
                    if full_url not in visited:
                        to_visit.append((full_url, depth + 1))
            except Exception as e:
                print(f"Error al scrapear {url}: {str(e)}")

        return all_content

class DeepseekProcessor:
    @staticmethod
    def process_content(content: str, prompt: str, api_key: str) -> str:
        endpoint = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": "deepseekR1",
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"{content}"}
            ]
        }
        try:
            response = requests.post(endpoint, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Deepseek API Error: {str(e)}")

class PDFGenerator:
    @staticmethod
    def generate_pdf(content: str, output_path: str):
        options = {
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'margin-top': '15mm',
            'margin-right': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '15mm',
            'quiet': ''
        }
        try:
            pdfkit.from_string(content, output_path, options=options)
        except Exception as e:
            raise RuntimeError(f"PDF Generation Error: {str(e)}")

async def main(base_url: str, prompt: str, output_path: str, max_depth: int = 3):
    scraper = WebScraper()
    all_content = await scraper.scrape_recursive(base_url, max_depth)

    # Procesar todo el contenido con Deepseek
    processed_content = ""
    for url, content in all_content.items():
        processed_content += f"# Contenido de {url}\n\n"
        processed_content += DeepseekProcessor.process_content(
            content=content,
            prompt=prompt,
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
        processed_content += "\n\n"

    # Generar PDF con todo el contenido
    PDFGenerator.generate_pdf(processed_content, output_path)
    print(f"✓ PDF generado en: {output_path}")

if __name__ == "__main__":
    # Valores por defecto
    DEFAULT_URL = "https://docs.n8n.io"
    DEFAULT_PROMPT = "Analisa todo el contenido de la página web, y genera un documento PDF con estructura jerarquica considerando todos los títulos, subtítulos y subniveles que tenga el sitio web para que sea sencillamente interpretable."
    DEFAULT_OUTPUT = "outputs/n8ndocs.pdf"
    DEFAULT_MAX_DEPTH = 5  # Profundidad máxima por defecto

    # Configuración del parser de argumentos
    parser = ArgumentParser(description="AI Web Scraper - Generador de PDFs")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL a scrapear")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Instrucciones para el LLM")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Ruta de salida del PDF")
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH, help="Profundidad máxima de scraping")
    
    args = parser.parse_args()
    
    # Crear carpeta de salida si no existe
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
    
    # Ejecutar el flujo principal
    asyncio.run(main(args.url, args.prompt, args.output, args.max_depth))