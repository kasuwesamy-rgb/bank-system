import flet as ft
from database import connect_db
from datetime import datetime
import webbrowser
import tempfile
import os


def comptes_view(page: ft.Page):

    # =========================================================
    # CHAMPS
    # =========================================================

    client_dropdown = ft.Dropdown(
        label="Sélectionner le client",
        hint_text="Choisir un client",
        width=450,
        options=[]
    )

    type_compte = ft.Dropdown(
        label="Type de compte",
        width=450,
        value="Épargne",
        options=[
            ft.dropdown.Option("Épargne"),
            ft.dropdown.Option("Courant")
        ]
    )

    solde_initial = ft.TextField(
        label="Solde initial",
        hint_text="Exemple : 100",
        width=450,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    numero_compte = ft.Text(
        "",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    message = ft.Text(
        "",
        size=14
    )

    comptes_table = ft.Column(
        spacing=0,
        scroll=ft.ScrollMode.AUTO
    )

    # =========================================================
    # DERNIER COMPTE CRÉÉ / SÉLECTIONNÉ
    # =========================================================

    dernier_compte_id = {
        "id": None
    }

    # =========================================================
    # GÉNÉRER AUTOMATIQUEMENT LE NUMÉRO DE COMPTE
    # =========================================================

    def generer_numero_compte():

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT numero_compte
                FROM comptes
                ORDER BY id DESC
                LIMIT 1
            """)

            dernier = cursor.fetchone()

            annee = datetime.now().year

            if dernier is None:

                nouveau_numero = f"CPT-{annee}-000001"

            else:

                ancien_numero = dernier[0]

                try:

                    dernier_numero = int(
                        ancien_numero.split("-")[-1]
                    )

                    nouveau_numero = (
                        f"CPT-{annee}-{dernier_numero + 1:06d}"
                    )

                except Exception:

                    nouveau_numero = (
                        f"CPT-{annee}-000001"
                    )

            cursor.close()

            return nouveau_numero

        except Exception as e:

            print(
                "Erreur génération numéro :",
                e
            )

            return None

        finally:

            if conn:
                conn.close()

    # =========================================================
    # CHARGER LES CLIENTS
    # =========================================================

    def charger_clients():

        client_dropdown.options.clear()

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    nom,
                    postnom,
                    prenom
                FROM clients
                ORDER BY nom ASC, prenom ASC
            """)

            clients = cursor.fetchall()

            for client in clients:

                client_id = client[0]
                nom = client[1]
                postnom = client[2]
                prenom = client[3]

                nom_complet = " ".join(
                    x
                    for x in [
                        nom,
                        postnom,
                        prenom
                    ]
                    if x
                )

                client_dropdown.options.append(
                    ft.dropdown.Option(
                        key=str(client_id),
                        text=f"{client_id} - {nom_complet}"
                    )
                )

            cursor.close()

        except Exception as e:

            message.value = (
                f"Erreur chargement clients : {e}"
            )

            message.color = ft.Colors.RED

        finally:

            if conn:
                conn.close()

        page.update()

    # =========================================================
    # OUVRIR UN COMPTE
    # =========================================================

    def ouvrir_compte(e):

        message.value = ""
        numero_compte.value = ""

        # -----------------------------------------------------
        # CLIENT
        # -----------------------------------------------------

        if not client_dropdown.value:

            message.value = (
                "Veuillez sélectionner un client."
            )

            message.color = ft.Colors.RED

            page.update()

            return

        # -----------------------------------------------------
        # TYPE DE COMPTE
        # -----------------------------------------------------

        if not type_compte.value:

            message.value = (
                "Veuillez sélectionner le type de compte."
            )

            message.color = ft.Colors.RED

            page.update()

            return

        # -----------------------------------------------------
        # SOLDE
        # -----------------------------------------------------

        if solde_initial.value.strip() == "":

            solde = 0

        else:

            try:

                solde = float(
                    solde_initial.value.replace(
                        ",",
                        "."
                    )
                )

            except ValueError:

                message.value = (
                    "Le solde initial est invalide."
                )

                message.color = ft.Colors.RED

                page.update()

                return

        if solde < 0:

            message.value = (
                "Le solde initial ne peut pas être négatif."
            )

            message.color = ft.Colors.RED

            page.update()

            return

        # -----------------------------------------------------
        # NUMÉRO AUTOMATIQUE
        # -----------------------------------------------------

        nouveau_numero = generer_numero_compte()

        if not nouveau_numero:

            message.value = (
                "Impossible de générer le numéro de compte."
            )

            message.color = ft.Colors.RED

            page.update()

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            client_id = int(
                client_dropdown.value
            )

            # -------------------------------------------------
            # VÉRIFIER CLIENT
            # -------------------------------------------------

            cursor.execute("""
                SELECT id
                FROM clients
                WHERE id = %s
            """, (
                client_id,
            ))

            client = cursor.fetchone()

            if not client:

                message.value = (
                    "Client introuvable."
                )

                message.color = ft.Colors.RED

                cursor.close()

                page.update()

                return

            # -------------------------------------------------
            # VÉRIFIER NUMÉRO
            # -------------------------------------------------

            cursor.execute("""
                SELECT id
                FROM comptes
                WHERE numero_compte = %s
            """, (
                nouveau_numero,
            ))

            existe = cursor.fetchone()

            if existe:

                message.value = (
                    "Ce numéro de compte existe déjà."
                )

                message.color = ft.Colors.RED

                cursor.close()

                page.update()

                return

            # -------------------------------------------------
            # INSERTION COMPTE
            # -------------------------------------------------

            cursor.execute("""
                INSERT INTO comptes
                (
                    numero_compte,
                    client_id,
                    solde
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
            """, (
                nouveau_numero,
                client_id,
                solde
            ))

            conn.commit()

            compte_id = cursor.lastrowid

            dernier_compte_id["id"] = compte_id

            cursor.close()

            # -------------------------------------------------
            # AFFICHER LE NUMÉRO
            # -------------------------------------------------

            numero_compte.value = (
                f"Numéro de compte : {nouveau_numero}"
            )

            numero_compte.color = ft.Colors.GREEN

            message.value = (
                f"Compte ouvert avec succès ! "
                f"Numéro : {nouveau_numero}"
            )

            message.color = ft.Colors.GREEN

            # -------------------------------------------------
            # NETTOYER
            # -------------------------------------------------

            solde_initial.value = ""

            # -------------------------------------------------
            # ACTUALISER LA LISTE
            # -------------------------------------------------

            charger_comptes()

            page.update()

        except Exception as ex:

            if conn:

                conn.rollback()

            message.value = (
                f"Erreur ouverture compte : {ex}"
            )

            message.color = ft.Colors.RED

            page.update()

        finally:

            if conn:
                conn.close()

    # =========================================================
    # IMPRIMER LE REÇU
    # =========================================================

    def imprimer_recu(e):

        # -----------------------------------------------------
        # VÉRIFIER COMPTE
        # -----------------------------------------------------

        if not dernier_compte_id["id"]:

            message.value = (
                "Veuillez d'abord ouvrir ou sélectionner un compte."
            )

            message.color = ft.Colors.RED

            page.update()

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # -------------------------------------------------
            # RÉCUPÉRER LE COMPTE ET LE CLIENT
            # -------------------------------------------------

            cursor.execute("""
                SELECT
                    c.numero_compte,
                    c.solde,
                    cl.nom,
                    cl.postnom,
                    cl.prenom
                FROM comptes c
                INNER JOIN clients cl
                    ON c.client_id = cl.id
                WHERE c.id = %s
            """, (
                dernier_compte_id["id"],
            ))

            compte = cursor.fetchone()

            cursor.close()

            if not compte:

                message.value = (
                    "Compte introuvable."
                )

                message.color = ft.Colors.RED

                page.update()

                return

            # -------------------------------------------------
            # DONNÉES
            # -------------------------------------------------

            numero = compte[0]
            solde = compte[1]

            nom = compte[2]
            postnom = compte[3]
            prenom = compte[4]

            client_nom = " ".join(
                x
                for x in [
                    nom,
                    postnom,
                    prenom
                ]
                if x
            )

            # -------------------------------------------------
            # GÉNÉRER LE REÇU
            # -------------------------------------------------

            imprimer_html(
                numero=numero,
                client_nom=client_nom,
                type_cpt=type_compte.value,
                solde=solde
            )

            message.value = (
                "Reçu ouvert avec succès. "
                "Vous pouvez maintenant l'imprimer."
            )

            message.color = ft.Colors.GREEN

            page.update()

        except Exception as ex:

            message.value = (
                f"Erreur impression : {ex}"
            )

            message.color = ft.Colors.RED

            page.update()

        finally:

            if conn:
                conn.close()

    # =========================================================
    # CRÉER LE REÇU HTML
    # =========================================================

    def imprimer_html(
        numero,
        client_nom,
        type_cpt,
        solde
    ):

        date_actuelle = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        # -----------------------------------------------------
        # CONTENU DU REÇU
        # -----------------------------------------------------

        html = f"""
<!DOCTYPE html>

<html lang="fr">

<head>

<meta charset="UTF-8">

<title>
Reçu ouverture compte - {numero}
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #f2f2f2;

    margin: 0;

    padding: 30px;

}}

.recu {{

    width: 750px;

    max-width: 100%;

    margin: auto;

    background: white;

    border: 2px solid #222;

    padding: 40px;

}}

.entete {{

    text-align: center;

}}

.entete h1 {{

    font-size: 30px;

    margin: 0;

}}

.entete h2 {{

    font-size: 21px;

    margin-top: 10px;

}}

hr {{

    border: none;

    border-top: 1px solid #333;

    margin: 25px 0;

}}

.numero {{

    text-align: center;

    font-size: 25px;

    font-weight: bold;

    margin: 25px 0;

}}

.ligne {{

    font-size: 18px;

    margin: 16px 0;

}}

.signatures {{

    display: flex;

    justify-content: space-between;

    margin-top: 90px;

}}

.signature {{

    width: 40%;

    text-align: center;

}}

.footer {{

    text-align: center;

    margin-top: 45px;

}}

.boutons {{

    text-align: center;

    margin-top: 25px;

}}

button {{

    background: #1769aa;

    color: white;

    border: none;

    padding: 12px 35px;

    font-size: 17px;

    border-radius: 5px;

    cursor: pointer;

}}

button:hover {{

    background: #0d4f83;

}}

@media print {{

    body {{

        background: white;

        padding: 0;

    }}

    .recu {{

        width: 100%;

        border: 2px solid #000;

    }}

    .boutons {{

        display: none;

    }}

}}

</style>

</head>

<body>

<div class="recu">

    <div class="entete">

        <h1>BANK SYSTEM</h1>

        <h2>
            REÇU D'OUVERTURE DE COMPTE
        </h2>

    </div>

    <hr>

    <div class="numero">

        N° COMPTE : {numero}

    </div>

    <hr>

    <div class="ligne">

        <strong>Client :</strong>
        {client_nom}

    </div>

    <div class="ligne">

        <strong>Type de compte :</strong>
        {type_cpt}

    </div>

    <div class="ligne">

        <strong>Solde initial :</strong>
        {float(solde):,.2f} $

    </div>

    <div class="ligne">

        <strong>Date d'ouverture :</strong>
        {date_actuelle}

    </div>

    <div class="ligne">

        <strong>Statut :</strong>
        Actif

    </div>

    <hr>

    <div class="signatures">

        <div class="signature">

            <strong>
                Signature du client
            </strong>

            <br><br><br>

            ________________________

        </div>

        <div class="signature">

            <strong>
                Signature de l'agent
            </strong>

            <br><br><br>

            ________________________

        </div>

    </div>

    <div class="footer">

        <p>
            Merci de votre confiance.
        </p>

        <div class="boutons">

            <button
                onclick="window.print()"
            >
                🖨 IMPRIMER LE REÇU
            </button>

        </div>

    </div>

</div>

</body>

</html>
"""

        # -----------------------------------------------------
        # CRÉER FICHIER TEMPORAIRE
        # -----------------------------------------------------

        try:

            fichier = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".html",
                delete=False,
                encoding="utf-8"
            )

            fichier.write(html)

            fichier.close()

            chemin = os.path.abspath(
                fichier.name
            )

            # -------------------------------------------------
            # WINDOWS
            # -------------------------------------------------

            if os.name == "nt":

                os.startfile(chemin)

            # -------------------------------------------------
            # AUTRES SYSTÈMES
            # -------------------------------------------------

            else:

                webbrowser.open_new_tab(
                    "file://" + chemin
                )

        except Exception as ex:

            message.value = (
                f"Erreur création reçu : {ex}"
            )

            message.color = ft.Colors.RED

            page.update()

    # =========================================================
    # IMPRIMER UN COMPTE DEPUIS LA LISTE
    # =========================================================

    def imprimer_compte_ligne(
        e,
        compte_id
    ):

        dernier_compte_id["id"] = compte_id

        imprimer_recu(e)

    # =========================================================
    # CHARGER LES COMPTES
    # =========================================================

    def charger_comptes():

        comptes_table.controls.clear()

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    c.id,
                    c.numero_compte,
                    c.client_id,
                    c.solde,
                    cl.nom,
                    cl.postnom,
                    cl.prenom
                FROM comptes c
                INNER JOIN clients cl
                    ON c.client_id = cl.id
                ORDER BY c.id DESC
            """)

            comptes = cursor.fetchall()

            cursor.close()

            # -------------------------------------------------
            # EN-TÊTE
            # -------------------------------------------------

            comptes_table.controls.append(

                ft.Container(

                    padding=10,

                    bgcolor=ft.Colors.BLUE_50,

                    content=ft.Row(

                        controls=[

                            ft.Text(
                                "N°",
                                width=50,
                                weight=ft.FontWeight.BOLD
                            ),

                            ft.Text(
                                "Numéro de compte",
                                width=180,
                                weight=ft.FontWeight.BOLD
                            ),

                            ft.Text(
                                "Client",
                                width=200,
                                weight=ft.FontWeight.BOLD
                            ),

                            ft.Text(
                                "Solde",
                                width=120,
                                weight=ft.FontWeight.BOLD
                            ),

                            ft.Text(
                                "Action",
                                width=100,
                                weight=ft.FontWeight.BOLD
                            )

                        ]

                    )

                )

            )

            # -------------------------------------------------
            # COMPTES
            # -------------------------------------------------

            for compte in comptes:

                id_compte = compte[0]

                numero = compte[1]

                solde = compte[3]

                nom = compte[4]

                postnom = compte[5]

                prenom = compte[6]

                client_nom = " ".join(
                    x
                    for x in [
                        nom,
                        postnom,
                        prenom
                    ]
                    if x
                )

                # -------------------------------------------------
                # BOUTON IMPRESSION
                # -------------------------------------------------

                bouton_print = ft.IconButton(

                    icon=ft.Icons.PRINT,

                    tooltip="Imprimer le reçu",

                    on_click=lambda e,
                    cid=id_compte:
                    imprimer_compte_ligne(
                        e,
                        cid
                    )
                )

                comptes_table.controls.append(

                    ft.Container(

                        padding=10,

                        border=ft.Border(

                            bottom=ft.BorderSide(
                                1,
                                ft.Colors.GREY_300
                            )

                        ),

                        content=ft.Row(

                            controls=[

                                ft.Text(
                                    str(id_compte),
                                    width=50
                                ),

                                ft.Text(
                                    numero,
                                    width=180,
                                    weight=ft.FontWeight.BOLD
                                ),

                                ft.Text(
                                    client_nom,
                                    width=200
                                ),

                                ft.Text(
                                    f"{float(solde):,.2f} $",
                                    width=120
                                ),

                                bouton_print

                            ]

                        )

                    )

                )

            page.update()

        except Exception as ex:

            comptes_table.controls.append(

                ft.Text(
                    f"Erreur : {ex}",
                    color=ft.Colors.RED
                )

            )

            page.update()

        finally:

            if conn:
                conn.close()

    # =========================================================
    # BOUTON OUVRIR
    # =========================================================

    bouton_ouvrir = ft.ElevatedButton(

        "Ouvrir le compte",

        icon=ft.Icons.ACCOUNT_BALANCE,

        on_click=ouvrir_compte

    )

    # =========================================================
    # BOUTON IMPRIMER
    # =========================================================

    bouton_imprimer = ft.ElevatedButton(

        "Imprimer le reçu",

        icon=ft.Icons.PRINT,

        on_click=imprimer_recu

    )

    # =========================================================
    # ACTUALISER
    # =========================================================

    bouton_actualiser = ft.IconButton(

        icon=ft.Icons.REFRESH,

        tooltip="Actualiser",

        on_click=lambda e: (
            charger_clients(),
            charger_comptes()
        )

    )

    # =========================================================
    # CHARGEMENT INITIAL
    # =========================================================

    charger_clients()

    charger_comptes()

    # =========================================================
    # INTERFACE
    # =========================================================

    return ft.Container(

        padding=20,

        content=ft.Column(

            controls=[

                # -------------------------------------------------
                # TITRE
                # -------------------------------------------------

                ft.Row(

                    controls=[

                        ft.Text(

                            "Gestion des comptes",

                            size=28,

                            weight=ft.FontWeight.BOLD,

                            expand=True

                        ),

                        bouton_actualiser

                    ]

                ),

                ft.Divider(),

                # -------------------------------------------------
                # OUVERTURE COMPTE
                # -------------------------------------------------

                ft.Card(

                    content=ft.Container(

                        padding=20,

                        content=ft.Column(

                            controls=[

                                ft.Text(

                                    "Ouverture d'un compte",

                                    size=22,

                                    weight=ft.FontWeight.BOLD

                                ),

                                client_dropdown,

                                type_compte,

                                solde_initial,

                                ft.Row(

                                    controls=[

                                        bouton_ouvrir,

                                        bouton_imprimer

                                    ]

                                ),

                                numero_compte,

                                message

                            ],

                            spacing=15

                        )

                    )

                ),

                ft.Divider(),

                # -------------------------------------------------
                # LISTE
                # -------------------------------------------------

                ft.Text(

                    "Comptes ouverts",

                    size=22,

                    weight=ft.FontWeight.BOLD

                ),

                ft.Container(

                    height=400,

                    content=ft.Column(

                        controls=[

                            comptes_table

                        ],

                        scroll=ft.ScrollMode.AUTO

                    )

                )

            ],

            scroll=ft.ScrollMode.AUTO

        )

    )