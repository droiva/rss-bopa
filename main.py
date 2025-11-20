import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom

# URL OBJETIVO
URL = "https://miprincipado.asturias.es/bopa/ultimos-boletines?p_r_p_summaryLastBopa=true"

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Sin interfaz gráfica
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Configuración para entornos de servidor (GitHub Actions)
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def generar_rss():
    print("Iniciando navegador virtual...")
    driver = setup_driver()
    
    try:
        driver.get(URL)
        # Esperamos 10 segundos para asegurar que el JS del Principado cargue
        time.sleep(10)
        content = driver.page_source
    except Exception as e:
        print(f"Error cargando la página: {e}")
        driver.quit()
        return
    
    driver.quit()
    
    # Analizamos el HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # BUSQUEDA INTELIGENTE:
    # Buscamos todos los enlaces que contengan el texto "Boletín"
    # Esto evita tener que buscar la clase CSS exacta.
    todos_enlaces = soup.find_all('a')
    enlaces_bopa = []
    
    for a in todos_enlaces:
        texto = a.get_text(strip=True)
        href = a.get('href')
        if href and "Boletín" in texto and "Nº" in texto:
            enlaces_bopa.append((texto, href))

    print(f"Encontrados {len(enlaces_bopa)} boletines.")

    if not enlaces_bopa:
        print("No se encontraron enlaces. Revisa si la web ha cambiado drásticamente.")
        return

    # Crear estructura RSS
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "BOPA Asturias - No Oficial"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = "Feed generado via GitHub Actions"
    
    for titulo, url in enlaces_bopa:
        # Arreglar URL si es relativa
        if url.startswith("/"):
            url = f"https://miprincipado.asturias.es{url}"
            
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = titulo
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "guid").text = url

    # Guardar archivo
    xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent="   ")
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)
    print("RSS generado exitosamente.")

if __name__ == "__main__":
    generar_rss()
