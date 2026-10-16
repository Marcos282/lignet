"""RSS endpoints checked on 2026-10-15; availability does not grant reuse rights."""

ASTRONOMY_TERMS = (
    "astronomia,estrela,estrelas,planeta,planetas,exoplaneta,telescópio,universo,"
    "astronomy,star,stars,planet,planets,exoplanet,exoplanets,telescope,telescopes,"
    "universe,galaxy,galaxies,cosmos,nebula,supernova,black hole,solar system,"
    "moon,mars,space,stellar,cosmic"
)

SOURCES = [
    ("NASA", "https://www.nasa.gov/feed/", 10),
    ("Space.com", "https://www.space.com/feeds.xml", 7),
    ("Astronomy Magazine", "https://www.astronomy.com/feed/", 7),
    ("Sky & Telescope", "https://skyandtelescope.org/astronomy-news/feed/", 7),
    ("ESA Space Science", "https://www.esa.int/rssfeed/Science_Exploration/Space_Science", 10),
    ("Universe Today", "https://www.universetoday.com/rss.xml", 7),
    ("NASA Science", "https://science.nasa.gov/feed/", 10),
]

FEED_WARNINGS = {
    "Space.com": "HTTP 403 na leitura direta; mantenha desativada até o editor permitir acesso ao feed.",
    "NASA Science": "XML inválido na leitura direta; mantenha desativada até o editor corrigir o feed.",
}
