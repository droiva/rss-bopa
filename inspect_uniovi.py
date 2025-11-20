import requests
from bs4 import BeautifulSoup

URL = "https://www.uniovi.es/en/investiga/ayudas/convocatorias/todas"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Based on the markdown, we are looking for links with specific text or structure.
# Let's try to find the container. The markdown showed "Related" header, but that might be misleading.
# Let's look for one of the known titles.
known_title = "Convocatoria de Contratos Predoctorales para personal investigador en formación de la Universidad de Oviedo"
link = soup.find("a", string=lambda x: x and known_title in x)

if link:
    print("Found link:", link)
    # Print parent hierarchy to find the container
    parent = link.parent
    for i in range(5):
        print(f"Parent {i}: {parent.name} {parent.attrs}")
        parent = parent.parent
        if parent is None:
            break
            
    # Print the container's html (truncated)
    container = link.find_parent("div", class_="asset-content") # Guessing class name, but parent loop will reveal true container
    if not container:
        container = link.find_parent("ul")
    
    if container:
        print("\nContainer HTML snippet:")
        print(container.prettify()[:500])
else:
    print("Link not found.")
