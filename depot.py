import flet as ft
from database import connect_db
from datetime import datetime
import tempfile
import os
import webbrowser


def depot_view(page: ft.Page):

    # =========================================================
    # CHAMPS
    # =========================================================

    client_dropdown = ft.Dropdown(
        label="Client",
        hint_text="Sélectionner un client",
        width=600,
        options=[]
    )

    compte_dropdown = ft.Dropdown(
        label="Compte",
        hint_text="Le compte du client apparaîtra ici",
        width=600,
        options=[]
    )

    montant = ft.TextField(
        label="Montant du dépôt",
        hint_text="Exemple : 100",
        width=600,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    numero_compte_text = ft.Text(
        "Numéro de compte : -",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    solde_actuel = ft.Text(
        "Solde actuel : 0.00 $",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    nouveau_solde = ft.Text(
        "",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    numero_depot = ft.Text(
        "",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    message = ft.Text(
        "",
        size=16
    )

    dernier_depot = {
        "numero": None
    }

    # =========================================================
    # MESSAGE
    # =========================================================

    def afficher_message(texte, couleur):

        message.value = texte
        message.color = couleur
        page.update()

    # =========================================================
    # GÉNÉRER NUMÉRO COMPTE
    # =========================================================

    def generer_numero_compte(cursor):

        annee = datetime.now().year

        cursor.execute("""
            SELECT numero_compte
            FROM comptes
            ORDER BY id DESC
            LIMIT 1
        """)

        dernier = cursor.fetchone()

        if not dernier or not dernier[0]:

            return f"CPT-{annee}-000001"

        try:

            ancien = str(dernier[0])

            dernier_numero = int(
                ancien.split("-")[-1]
            )

            return (
                f"CPT-{annee}-"
                f"{dernier_numero + 1:06d}"
            )

        except Exception:

            return f"CPT-{annee}-000001"

    # =========================================================
    # GÉNÉRER NUMÉRO DÉPÔT
    # =========================================================

    def generer_numero_depot(cursor):

        annee = datetime.now().year

        cursor.execute("""
            SELECT numero_depot
            FROM depots
            ORDER BY id DESC
            LIMIT 1
        """)

        dernier = cursor.fetchone()

        if not dernier or not dernier[0]:

            return f"DEP-{annee}-000001"

        try:

            ancien = str(
                dernier[0]
            )

            dernier_numero = int(
                ancien.split("-")[-1]
            )

            return (
                f"DEP-{annee}-"
                f"{dernier_numero + 1:06d}"
            )

        except Exception:

            return f"DEP-{annee}-000001"

    # =========================================================
    # CHARGER CLIENTS
    # =========================================================

    def charger_clients():

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
                ORDER BY nom, postnom, prenom
            """)

            clients = cursor.fetchall()

            client_dropdown.options.clear()

            for client in clients:

                client_id = client[0]

                nom = client[1] or ""
                postnom = client[2] or ""
                prenom = client[3] or ""

                nom_complet = " ".join(
                    x for x in [
                        nom,
                        postnom,
                        prenom
                    ]
                    if x
                )

                if not nom_complet:

                    nom_complet = (
                        f"Client #{client_id}"
                    )

                client_dropdown.options.append(
                    ft.DropdownOption(
                        key=str(client_id),
                        text=nom_complet
                    )
                )

            client_dropdown.value = None

        except Exception as ex:

            afficher_message(
                f"Erreur clients : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:
                conn.close()

        page.update()

    # =========================================================
    # RÉINITIALISER COMPTE
    # =========================================================

    def vider_compte():

        compte_dropdown.options.clear()

        compte_dropdown.value = None

        numero_compte_text.value = (
            "Numéro de compte : -"
        )

        solde_actuel.value = (
            "Solde actuel : 0.00 $"
        )

        nouveau_solde.value = ""

        page.update()

    # =========================================================
    # CRÉER COMPTE AUTOMATIQUEMENT
    # =========================================================

    def creer_compte(client_id):

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            conn.start_transaction()

            # Vérifier d'abord si le client possède
            # déjà un compte

            cursor.execute("""
                SELECT
                    id,
                    numero_compte,
                    solde
                FROM comptes
                WHERE client_id = %s
                ORDER BY id DESC
                LIMIT 1
            """, (
                client_id,
            ))

            compte = cursor.fetchone()

            if compte:

                conn.commit()

                return {
                    "id": int(compte[0]),
                    "numero": compte[1],
                    "solde": float(
                        compte[2] or 0
                    ),
                    "nouveau": False
                }

            # -------------------------------------------------
            # CRÉER LE COMPTE
            # -------------------------------------------------

            numero = generer_numero_compte(
                cursor
            )

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
                numero,
                client_id,
                0
            ))

            compte_id = cursor.lastrowid

            conn.commit()

            return {
                "id": int(compte_id),
                "numero": numero,
                "solde": 0.0,
                "nouveau": True
            }

        except Exception as ex:

            if conn:

                try:
                    conn.rollback()
                except Exception:
                    pass

            afficher_message(
                f"Erreur création compte : {ex}",
                ft.Colors.RED
            )

            return None

        finally:

            if conn:
                conn.close()

    # =========================================================
    # CHARGER LE COMPTE DU CLIENT
    # =========================================================

    def charger_compte_client(e=None):

        # -----------------------------------------------------
        # TOUJOURS VIDER L'ANCIEN COMPTE
        # -----------------------------------------------------

        compte_dropdown.options.clear()

        compte_dropdown.value = None

        numero_compte_text.value = (
            "Numéro de compte : -"
        )

        solde_actuel.value = (
            "Solde actuel : 0.00 $"
        )

        nouveau_solde.value = ""

        numero_depot.value = ""

        # -----------------------------------------------------
        # VÉRIFIER CLIENT
        # -----------------------------------------------------

        if not client_dropdown.value:

            page.update()

            return

        try:

            client_id = int(
                client_dropdown.value
            )

        except Exception:

            afficher_message(
                "ID du client invalide.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # =================================================
            # RECHERCHE DIRECTE PAR client_id
            # =================================================

            cursor.execute("""
                SELECT
                    id,
                    numero_compte,
                    solde
                FROM comptes
                WHERE client_id = %s
                ORDER BY id DESC
            """, (
                client_id,
            ))

            comptes = cursor.fetchall()

            # =================================================
            # SI LE CLIENT N'A PAS DE COMPTE
            # =================================================

            if not comptes:

                conn.close()
                conn = None

                compte = creer_compte(
                    client_id
                )

                if not compte:

                    return

                compte_id = compte["id"]
                numero = compte["numero"]
                solde = compte["solde"]

                compte_dropdown.options.append(
                    ft.DropdownOption(
                        key=str(compte_id),
                        text=(
                            f"{numero} | "
                            f"Solde : "
                            f"{solde:,.2f} $"
                        )
                    )
                )

                compte_dropdown.value = str(
                    compte_id
                )

                numero_compte_text.value = (
                    f"Numéro de compte : {numero}"
                )

                numero_compte_text.color = (
                    ft.Colors.GREEN
                )

                solde_actuel.value = (
                    f"Solde actuel : "
                    f"{solde:,.2f} $"
                )

                solde_actuel.color = (
                    ft.Colors.BLUE
                )

                message.value = (
                    f"Compte créé automatiquement : "
                    f"{numero}"
                )

                message.color = (
                    ft.Colors.GREEN
                )

                page.update()

                return

            # =================================================
            # AFFICHER LES COMPTES
            # =================================================

            for compte in comptes:

                compte_id = int(
                    compte[0]
                )

                numero = compte[1]

                solde = float(
                    compte[2] or 0
                )

                compte_dropdown.options.append(
                    ft.DropdownOption(
                        key=str(compte_id),
                        text=(
                            f"{numero} | "
                            f"Solde : "
                            f"{solde:,.2f} $"
                        )
                    )
                )

            # =================================================
            # SÉLECTION AUTOMATIQUE DU PREMIER COMPTE
            # =================================================

            compte_id = int(
                comptes[0][0]
            )

            compte_dropdown.value = str(
                compte_id
            )

            # =================================================
            # AFFICHER IMMÉDIATEMENT
            # =================================================

            numero = comptes[0][1]

            solde = float(
                comptes[0][2] or 0
            )

            numero_compte_text.value = (
                f"Numéro de compte : {numero}"
            )

            numero_compte_text.color = (
                ft.Colors.BLUE
            )

            solde_actuel.value = (
                f"Solde actuel : "
                f"{solde:,.2f} $"
            )

            solde_actuel.color = (
                ft.Colors.BLUE
            )

            message.value = (
                "Compte du client chargé automatiquement."
            )

            message.color = (
                ft.Colors.GREEN
            )

        except Exception as ex:

            afficher_message(
                f"Erreur recherche compte : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:

                try:
                    conn.close()
                except Exception:
                    pass

        page.update()

    # =========================================================
    # CHANGEMENT DE COMPTE
    # =========================================================

    def afficher_compte(e=None):

        if not compte_dropdown.value:

            return

        try:

            compte_id = int(
                compte_dropdown.value
            )

            client_id = int(
                client_dropdown.value
            )

        except Exception:

            afficher_message(
                "Compte ou client invalide.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # -------------------------------------------------
            # LE COMPTE DOIT APPARTENIR AU CLIENT
            # -------------------------------------------------

            cursor.execute("""
                SELECT
                    id,
                    numero_compte,
                    solde,
                    client_id
                FROM comptes
                WHERE
                    id = %s
                    AND client_id = %s
            """, (
                compte_id,
                client_id
            ))

            compte = cursor.fetchone()

            if not compte:

                compte_dropdown.value = None

                numero_compte_text.value = (
                    "Numéro de compte : -"
                )

                solde_actuel.value = (
                    "Solde actuel : 0.00 $"
                )

                afficher_message(
                    "Ce compte n'appartient pas "
                    "au client sélectionné.",
                    ft.Colors.RED
                )

                return

            numero = compte[1]

            solde = float(
                compte[2] or 0
            )

            numero_compte_text.value = (
                f"Numéro de compte : {numero}"
            )

            solde_actuel.value = (
                f"Solde actuel : "
                f"{solde:,.2f} $"
            )

            message.value = (
                "Compte prêt pour le dépôt."
            )

            message.color = (
                ft.Colors.GREEN
            )

        except Exception as ex:

            afficher_message(
                f"Erreur compte : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:
                conn.close()

        page.update()

    # =========================================================
    # ENREGISTRER DÉPÔT
    # =========================================================

    def enregistrer_depot(e):

        # -----------------------------------------------------
        # CLIENT
        # -----------------------------------------------------

        if not client_dropdown.value:

            afficher_message(
                "Veuillez sélectionner un client.",
                ft.Colors.RED
            )

            return

        # -----------------------------------------------------
        # COMPTE
        # -----------------------------------------------------

        if not compte_dropdown.value:

            afficher_message(
                "Aucun compte disponible pour ce client.",
                ft.Colors.RED
            )

            return

        # -----------------------------------------------------
        # MONTANT
        # -----------------------------------------------------

        valeur = (
            montant.value or ""
        ).strip()

        if not valeur:

            afficher_message(
                "Veuillez saisir le montant du dépôt.",
                ft.Colors.RED
            )

            return

        try:

            montant_depot = float(
                valeur.replace(",", ".")
            )

        except ValueError:

            afficher_message(
                "Montant invalide.",
                ft.Colors.RED
            )

            return

        if montant_depot <= 0:

            afficher_message(
                "Le montant doit être supérieur à 0.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            client_id = int(
                client_dropdown.value
            )

            compte_id = int(
                compte_dropdown.value
            )

            conn = connect_db()
            cursor = conn.cursor()

            conn.start_transaction()

            # =================================================
            # RÉCUPÉRER LE COMPTE
            # =================================================

            cursor.execute("""
                SELECT
                    c.id,
                    c.numero_compte,
                    c.solde,
                    c.client_id,
                    cl.nom,
                    cl.postnom,
                    cl.prenom
                FROM comptes c

                INNER JOIN clients cl
                    ON cl.id = c.client_id

                WHERE
                    c.id = %s
                    AND c.client_id = %s

                FOR UPDATE
            """, (
                compte_id,
                client_id
            ))

            compte = cursor.fetchone()

            if not compte:

                conn.rollback()

                afficher_message(
                    "Le compte sélectionné n'appartient "
                    "pas au client.",
                    ft.Colors.RED
                )

                return

            # =================================================
            # INFORMATIONS
            # =================================================

            numero_compte = compte[1]

            ancien_solde = float(
                compte[2] or 0
            )

            client_nom = " ".join(
                x for x in [
                    compte[4] or "",
                    compte[5] or "",
                    compte[6] or ""
                ]
                if x
            )

            # =================================================
            # NOUVEAU SOLDE
            # =================================================

            nouveau_solde_value = (
                ancien_solde +
                montant_depot
            )

            # =================================================
            # NUMÉRO DÉPÔT
            # =================================================

            numero = generer_numero_depot(
                cursor
            )

            # =================================================
            # INSERTION DÉPÔT
            # =================================================

            cursor.execute("""
                INSERT INTO depots
                (
                    numero_depot,
                    compte_id,
                    client_id,
                    montant,
                    date_depot
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                numero,
                compte_id,
                client_id,
                montant_depot,
                datetime.now()
            ))

            # =================================================
            # AUGMENTER SOLDE
            # =================================================

            cursor.execute("""
                UPDATE comptes
                SET solde = solde + %s
                WHERE
                    id = %s
                    AND client_id = %s
            """, (
                montant_depot,
                compte_id,
                client_id
            ))

            # =================================================
            # VALIDATION
            # =================================================

            conn.commit()

            dernier_depot["numero"] = numero

            # =================================================
            # AFFICHAGE
            # =================================================

            numero_depot.value = (
                f"N° Dépôt : {numero}"
            )

            numero_depot.color = (
                ft.Colors.GREEN
            )

            nouveau_solde.value = (
                f"Nouveau solde : "
                f"{nouveau_solde_value:,.2f} $"
            )

            nouveau_solde.color = (
                ft.Colors.GREEN
            )

            solde_actuel.value = (
                f"Solde actuel : "
                f"{nouveau_solde_value:,.2f} $"
            )

            solde_actuel.color = (
                ft.Colors.GREEN
            )

            message.value = (
                "Dépôt enregistré avec succès."
            )

            message.color = (
                ft.Colors.GREEN
            )

            montant.value = ""

            page.update()

            # =================================================
            # IMPRIMER
            # =================================================

            imprimer_bordereau(
                numero,
                numero_compte,
                client_nom,
                montant_depot,
                ancien_solde,
                nouveau_solde_value
            )

        except Exception as ex:

            if conn:

                try:
                    conn.rollback()
                except Exception:
                    pass

            afficher_message(
                f"Erreur dépôt : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:

                try:
                    conn.close()
                except Exception:
                    pass

    # =========================================================
    # BORDEREAU
    # =========================================================

    def imprimer_bordereau(
        numero,
        numero_compte,
        client_nom,
        montant_depot,
        ancien_solde,
        nouveau_solde_value
    ):

        date_operation = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        html = f"""
<!DOCTYPE html>

<html lang="fr">

<head>

<meta charset="UTF-8">

<title>Bordereau {numero}</title>

<style>

body {{
    font-family: Arial, sans-serif;
    background: #eeeeee;
    padding: 30px;
}}

.bordereau {{
    width: 700px;
    max-width: 90%;
    margin: auto;
    background: white;
    padding: 40px;
    border: 2px solid black;
}}

h1,
h2 {{
    text-align: center;
}}

.numero {{
    text-align: center;
    font-size: 22px;
    font-weight: bold;
    margin: 25px;
}}

.ligne {{
    margin: 15px 0;
    font-size: 18px;
}}

.montant {{
    border: 2px solid black;
    padding: 20px;
    text-align: center;
    font-size: 25px;
    font-weight: bold;
    margin: 30px 0;
}}

.signatures {{
    display: flex;
    justify-content: space-between;
    margin-top: 80px;
}}

.signature {{
    text-align: center;
}}

.imprimer {{
    text-align: center;
    margin-top: 30px;
}}

button {{
    padding: 12px 30px;
    font-size: 17px;
    cursor: pointer;
}}

@media print {{

    body {{
        background: white;
        padding: 0;
    }}

    .imprimer {{
        display: none;
    }}

}}

</style>

</head>

<body>

<div class="bordereau">

<h1>BANK SYSTEM</h1>

<h2>BORDEREAU DE DÉPÔT</h2>

<hr>

<div class="numero">
N° DÉPÔT : {numero}
</div>

<hr>

<div class="ligne">
<strong>Client :</strong> {client_nom}
</div>

<div class="ligne">
<strong>Numéro de compte :</strong>
{numero_compte}
</div>

<div class="ligne">
<strong>Date :</strong>
{date_operation}
</div>

<div class="montant">

MONTANT DU DÉPÔT

<br><br>

{montant_depot:,.2f} $

</div>

<div class="ligne">
<strong>Ancien solde :</strong>
{ancien_solde:,.2f} $
</div>

<div class="ligne">
<strong>Nouveau solde :</strong>
{nouveau_solde_value:,.2f} $
</div>

<div class="ligne">
<strong>Opération :</strong> DÉPÔT
</div>

<hr>

<div class="signatures">

<div class="signature">
<strong>Client</strong>
<br><br><br>
____________________
</div>

<div class="signature">
<strong>Caissier</strong>
<br><br><br>
____________________
</div>

</div>

<div class="imprimer">

<button onclick="window.print()">
🖨 IMPRIMER
</button>

</div>

</div>

</body>

</html>
"""

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

            webbrowser.open(
                "file://" + chemin
            )

        except Exception as ex:

            afficher_message(
                f"Erreur impression : {ex}",
                ft.Colors.RED
            )

    # =========================================================
    # IMPRIMER DERNIER DÉPÔT
    # =========================================================

    def imprimer_dernier_depot(e):

        numero = dernier_depot["numero"]

        if not numero:

            afficher_message(
                "Aucun dépôt enregistré.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    d.numero_depot,
                    c.numero_compte,
                    cl.nom,
                    cl.postnom,
                    cl.prenom,
                    d.montant,
                    c.solde
                FROM depots d

                INNER JOIN comptes c
                    ON c.id = d.compte_id

                INNER JOIN clients cl
                    ON cl.id = d.client_id

                WHERE d.numero_depot = %s
            """, (
                numero,
            ))

            depot = cursor.fetchone()

            if not depot:

                afficher_message(
                    "Dépôt introuvable.",
                    ft.Colors.RED
                )

                return

            nouveau = float(
                depot[6] or 0
            )

            montant_depot = float(
                depot[5] or 0
            )

            ancien = (
                nouveau -
                montant_depot
            )

            client_nom = " ".join(
                x for x in [
                    depot[2] or "",
                    depot[3] or "",
                    depot[4] or ""
                ]
                if x
            )

            imprimer_bordereau(
                depot[0],
                depot[1],
                client_nom,
                montant_depot,
                ancien,
                nouveau
            )

        except Exception as ex:

            afficher_message(
                f"Erreur impression : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:
                conn.close()

    # =========================================================
    # ACTUALISER
    # =========================================================

    def actualiser(e):

        client_dropdown.value = None

        vider_compte()

        numero_depot.value = ""

        montant.value = ""

        message.value = ""

        dernier_depot["numero"] = None

        charger_clients()

    # =========================================================
    # ÉVÉNEMENTS
    # =========================================================

    # IMPORTANT :
    # on_select est utilisé pour la sélection du client

    client_dropdown.on_select = charger_compte_client

    compte_dropdown.on_select = afficher_compte

    # =========================================================
    # BOUTONS
    # =========================================================

    bouton_enregistrer = ft.ElevatedButton(
        "Enregistrer le dépôt",
        icon=ft.Icons.SAVE,
        on_click=enregistrer_depot
    )

    bouton_imprimer = ft.ElevatedButton(
        "Imprimer le bordereau",
        icon=ft.Icons.PRINT,
        on_click=imprimer_dernier_depot
    )

    bouton_actualiser = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Actualiser",
        on_click=actualiser
    )

    # =========================================================
    # CHARGEMENT INITIAL
    # =========================================================

    charger_clients()

    # =========================================================
    # INTERFACE
    # =========================================================

    return ft.Container(

        padding=20,

        content=ft.Column(

            controls=[

                ft.Row(
                    controls=[

                        ft.Text(
                            "GESTION DES DÉPÔTS",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            expand=True
                        ),

                        bouton_actualiser

                    ]
                ),

                ft.Divider(),

                ft.Card(

                    content=ft.Container(

                        padding=25,

                        content=ft.Column(

                            controls=[

                                ft.Text(
                                    "Nouveau dépôt",
                                    size=22,
                                    weight=ft.FontWeight.BOLD
                                ),

                                # -------------------------
                                # CLIENT
                                # -------------------------

                                client_dropdown,

                                # -------------------------
                                # COMPTE AUTOMATIQUE
                                # -------------------------

                                compte_dropdown,

                                numero_compte_text,

                                solde_actuel,

                                # -------------------------
                                # MONTANT
                                # -------------------------

                                montant,

                                # -------------------------
                                # BOUTONS
                                # -------------------------

                                ft.Row(
                                    controls=[
                                        bouton_enregistrer,
                                        bouton_imprimer
                                    ],
                                    wrap=True
                                ),

                                numero_depot,

                                nouveau_solde,

                                message

                            ],

                            spacing=15

                        )

                    )

                )

            ],

            scroll=ft.ScrollMode.AUTO

        )

    )