import asyncio
import os
import pdfkit
import requests
from crawl4ai import AsyncWebCrawler
from argparse import ArgumentParser

class WebScraper:
    async def scrape(self, url: str) -> str:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown

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

async def main(url: str, prompt: str, output_path: str):
    scraper = WebScraper()
    markdown = await scraper.scrape(url)
    processed_content = DeepseekProcessor.process_content(markdown, prompt, os.getenv("DEEPSEEK_API_KEY"))
    PDFGenerator.generate_pdf(processed_content, output_path)
    print(f"✓ PDF generado en: {output_path}")

if __name__ == "__main__":
    parser = ArgumentParser(description="AI Web Scraper - Generador de PDFs")
    parser.add_argument("--url", required=True, help="URL a scrapear")
    parser.add_argument("--prompt", required=True, help="Instrucciones para el LLM")
    parser.add_argument("--output", default="outputs/documento.pdf", help="Ruta de salida del PDF")
    args = parser.parse_args()
    
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
    
    asyncio.run(main(args.url, args.prompt, args.output))