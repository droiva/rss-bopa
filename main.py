import time
import sys
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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # MÁSCARA IMPORTANTE: Fingimos ser un navegador Chrome normal
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def generar_rss():
    print("Iniciando navegador virtual con máscara...")
    driver = setup_driver()
    
    try:
        driver.get(URL)
        # Esperamos 15 segundos esta vez
        time.sleep(15)
        content = driver.page_source
        print("Página cargada. Longitud del contenido:", len(content))
    except Exception as e:
        print(f"Error crítico cargando la página: {e}")
        driver.quit()
        sys.exit(1) # Forzamos error si no carga
    
    driver.quit()
    
    # Analizamos el HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # Buscamos enlaces - Estrategia combinada
    enlaces_bopa = []
    todos_enlaces = soup.find_all('a')
    
    print(f"Analizando {len(todos_enlaces)} enlaces encontrados en el HTML...")

    for a in todos_enlaces:
        texto = a.get_text(strip=True)
        href = a.get('href')
        
        # Criterios para detectar si es un boletín
        if href and texto:
            # Buscamos que tenga "Boletín" O que parezca una fecha y tenga enlace de descarga
            if ("Boletín" in texto and "Nº" in texto) or ("sede.asturias.es" in href and "bopa" in href):
                enlaces_bopa.append((texto, href))

    # Eliminar duplicados manteniendo el orden
    enlaces_bopa = list(dict.fromkeys(enlaces_bopa))
    
    print(f"✅ Filtrados: Se encontraron {len(enlaces_bopa)} boletines válidos.")

    # --- CREACIÓN DEL XML (SIEMPRE SE CREA PARA EVITAR ERROR DE GIT) ---
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "BOPA Asturias - Feed"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = "Feed generado automáticamente"
    
    if enlaces_bopa:
        for titulo, url in enlaces_bopa:
            if url.startswith("/"):
                url = f"https://miprincipado.asturias.es{url}"
            
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = titulo
            ET.SubElement(item, "link").text = url
            ET.SubElement(item, "guid").text = url
    else:
        print("⚠️ ADVERTENCIA: No se encontraron datos, se generará un XML vacío pero válido.")
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = "Sin novedades o error de lectura"
        ET.SubElement(item, "description").text = "El script no pudo recuperar los boletines hoy. Revisa los logs."

    # Guardar archivo
    xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent="   ")
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)
    print("Archivo feed.xml guardado exitosamente.")

if __name__ == "__main__":
    generar_rss()
