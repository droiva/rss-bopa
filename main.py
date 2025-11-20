import sys
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom

# URL OBJETIVO
URL = "https://miprincipado.asturias.es/bopa/ultimos-boletines?p_r_p_summaryLastBopa=true"

def generar_rss():
    print("Iniciando descarga con requests...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text
        print("Página cargada. Longitud del contenido:", len(content))
    except Exception as e:
        print(f"Error crítico cargando la página: {e}")
        sys.exit(1)
    
    # Analizamos el HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # Buscamos disposiciones
    # La estructura parece ser: <dt>Título [Cód. ...]</dt> <dd>... <a href="...pdf">PDF</a> ...</dd>
    enlaces_bopa = []
    
    # Buscamos todos los dt que podrían contener títulos de disposiciones
    # O buscamos pares dt/dd
    
    # Encontramos el contenedor principal si es posible, o iteramos sobre todos los dt
    # Basado en el HTML visto: <div id="bopa-boletin"> contiene las secciones
    
    contenedor_boletin = soup.find(id="bopa-boletin")
    
    if contenedor_boletin:
        print("Contenedor 'bopa-boletin' encontrado.")
        dts = contenedor_boletin.find_all("dt")
        print(f"Encontrados {len(dts)} elementos dt.")
        
        for dt in dts:
            titulo = dt.get_text(strip=True)
            # El siguiente hermano debería ser dd
            dd = dt.find_next_sibling("dd")
            if dd:
                # Buscar enlace al PDF
                pdf_link = dd.find("a", href=lambda x: x and x.endswith(".pdf"))
                if pdf_link:
                    href = pdf_link.get("href")
                    enlaces_bopa.append((titulo, href))
                else:
                    # Intentar buscar enlace al texto si no hay PDF directo (raro pero posible)
                    text_link = dd.find("a", string="Texto de la disposición")
                    if text_link:
                        href = text_link.get("href")
                        enlaces_bopa.append((titulo, href))
    else:
        print("No se encontró el contenedor 'bopa-boletin'. Intentando búsqueda genérica.")
        # Fallback: buscar enlaces PDF directamente
        pdf_links = soup.find_all("a", href=lambda x: x and x.endswith(".pdf") and "/bopa/" in x)
        for a in pdf_links:
            href = a.get("href")
            # Intentar encontrar un título cercano
            # Esto es menos preciso
            titulo = a.get_text(strip=True) or "Disposición BOPA"
            enlaces_bopa.append((titulo, href))

    # Eliminar duplicados manteniendo el orden
    enlaces_bopa = list(dict.fromkeys(enlaces_bopa))
    
    print(f"✅ Filtrados: Se encontraron {len(enlaces_bopa)} disposiciones válidas.")

    # --- CREACIÓN DEL XML ---
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "BOPA Asturias - Feed"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = "Feed generado automáticamente de las disposiciones del BOPA"
    
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
