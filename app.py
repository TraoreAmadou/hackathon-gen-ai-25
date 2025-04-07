from flask import Flask, render_template_string
import requests
import pandas as pd

app = Flask(__name__)

API_TOKEN = "GxVU3F0PVtasjhz4igAtgOMqHjRvu5Aj"
URL = "https://prim.iledefrance-mobilites.fr/marketplace/ilico/getData?method=getlc&format=json&status=available"
HEADERS = {"Accept": "application/json", "apikey": API_TOKEN}

@app.route('/')
def index():
    # Appel API
    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        return f"Erreur API : {response.status_code} - {response.text}"
    
    data = response.json()
    frames = data['dataObjects']['CompositeFrame']['frames']['GeneralFrame']
    
    operators = []
    schematic_maps = []
    lignes = []

    for frame in frames:
        ref = frame['TypeOfFrameRef']['ref']
        if ref == 'FR1:TypeOfFrame:NETEX_COMMUN:':
            operators = frame['members'].get('Operator', [])
            schematic_maps = frame['members'].get('SchematicMap', [])
        elif ref == 'FR1:TypeOfFrame:NETEX_LIGNE:':
            lignes = frame['members'].get('Line', [])

    operator_dict = {op['id']: op.get('Name', '') for op in operators}
    map_dict = {
        smap.get("DepictedObjectRef", {}).get("ref"): smap.get("ImageUri")
        for smap in schematic_maps
    }

    extracted = []
    for ligne in lignes:
        op_ref = ligne.get("OperatorRef", {}).get("ref")
        operator_name = operator_dict.get(op_ref, "Inconnu")
        plan_url = map_dict.get(ligne.get("id"))

        access = ligne.get("AccessibilityAssessment", {})
        mobility = access.get("MobilityImpairedAccess")
        limitations = access.get("limitations", {}).get("AccessibilityLimitation", {})
        
        extracted.append({
            "Nom": ligne.get("Name"),
            "Code Public": ligne.get("PublicCode"),
            "Mode": ligne.get("TransportMode"),
            "Sous-mode": ligne.get("TransportSubmode", {}).get("BusSubmode") or ligne.get("TransportSubmode", {}).get("RailSubmode"),
            "Statut": ligne.get("status"),
            "Opérateur": operator_name,
            "Plan": plan_url or "",
            "Accessibilité": mobility,
            "UFR": limitations.get("WheelchairAccessAccessibility"),
            "Audio": limitations.get("AudibleSignsAvailable"),
            "Visuel": limitations.get("VisualSignsAvailable")
        })

    df = pd.DataFrame(extracted)
    html_table = df.to_html(classes="table table-bordered table-striped", index=False, escape=False)

    return render_template_string(f"""
    <html>
    <head>
        <title>Lignes IDF Mobilités</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    </head>
    <body class="p-4">
        <h1 class="mb-4">📊 Lignes Commerciales - Île-de-France Mobilités</h1>
        {html_table}
    </body>
    </html>
    """)

if __name__ == '__main__':
    app.run(debug=True)
