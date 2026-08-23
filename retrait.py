import flet as ft
from database import connect_db
from datetime import datetime
import tempfile
import os
import webbrowser
import html


def retrait_view(page: ft.Page):

    # =========================================================
    # VARIABLES
    # =========================================================

    compte_actuel = {
        "id": None,
        "numero": None
    }

    dernier_retrait = {
        "numero": None
    }

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

    numero_compte_text = ft.Text(
        "Numéro de compte : -",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    solde_text = ft.Text(
        "Solde actuel : 0.00 $",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    montant = ft.TextField(
        label="Montant du retrait",
        hint_text="Exemple : 50",
        width=600,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    numero_retrait_text = ft.Text(
        "",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    nouveau_solde_text = ft.Text(
        "",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    message = ft.Text(
        "",
        size=16
    )

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

            ancien = str(
                dernier[0]
            )

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
    # GÉNÉRER NUMÉRO RETRAIT
    # =========================================================

    def generer_numero_retrait(cursor):

        annee = datetime.now().year

        cursor.execute("""
            SELECT numero_retrait
            FROM retraits
            ORDER BY id DESC
            LIMIT 1
        """)

        dernier = cursor.fetchone()

        if not dernier or not dernier[0]:

            return f"RET-{annee}-000001"

        try:

            ancien = str(
                dernier[0]
            )

            dernier_numero = int(
                ancien.split("-")[-1]
            )

            return (
                f"RET-{annee}-"
                f"{dernier_numero + 1:06d}"
            )

        except Exception:

            return f"RET-{annee}-000001"

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
    # VIDER COMPTE
    # =========================================================

    def vider_compte():

        compte_actuel["id"] = None
        compte_actuel["numero"] = None

        compte_dropdown.options.clear()

        compte_dropdown.value = None

        numero_compte_text.value = (
            "Numéro de compte : -"
        )

        solde_text.value = (
            "Solde actuel : 0.00 $"
        )

        numero_retrait_text.value = ""

        nouveau_solde_text.value = ""

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

            # -------------------------------------------------
            # VÉRIFIER SI LE CLIENT POSSÈDE DÉJÀ UN COMPTE
            # -------------------------------------------------

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
                    "solde": float(compte[2] or 0),
                    "nouveau": False
                }

            # -------------------------------------------------
            # GÉNÉRER NUMÉRO COMPTE
            # -------------------------------------------------

            numero = generer_numero_compte(
                cursor
            )

            # -------------------------------------------------
            # CRÉER LE COMPTE
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
    # CHARGER AUTOMATIQUEMENT LE COMPTE DU CLIENT
    # =========================================================

    def charger_compte_client(e=None):

        # -----------------------------------------------------
        # VIDER L'ANCIEN COMPTE
        # -----------------------------------------------------

        compte_dropdown.options.clear()

        compte_dropdown.value = None

        compte_actuel["id"] = None
        compte_actuel["numero"] = None

        numero_compte_text.value = (
            "Numéro de compte : -"
        )

        solde_text.value = (
            "Solde actuel : 0.00 $"
        )

        numero_retrait_text.value = ""

        nouveau_solde_text.value = ""

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
            # RECHERCHER LE COMPTE
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
            # SI AUCUN COMPTE
            # CRÉATION AUTOMATIQUE
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

                compte_actuel["id"] = (
                    compte_id
                )

                compte_actuel["numero"] = (
                    numero
                )

                numero_compte_text.value = (
                    f"Numéro de compte : "
                    f"{numero}"
                )

                numero_compte_text.color = (
                    ft.Colors.GREEN
                )

                solde_text.value = (
                    f"Solde actuel : "
                    f"{solde:,.2f} $"
                )

                solde_text.color = (
                    ft.Colors.BLUE
                )

                message.value = (
                    f"Compte créé automatiquement : "
                    f"{numero}. "
                    f"Le solde est de 0.00 $."
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

                numero = str(
                    compte[1]
                )

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
            # SÉLECTION AUTOMATIQUE
            # =================================================

            compte_id = int(
                comptes[0][0]
            )

            numero = str(
                comptes[0][1]
            )

            solde = float(
                comptes[0][2] or 0
            )

            compte_dropdown.value = str(
                compte_id
            )

            compte_actuel["id"] = (
                compte_id
            )

            compte_actuel["numero"] = (
                numero
            )

            # =================================================
            # AFFICHAGE
            # =================================================

            numero_compte_text.value = (
                f"Numéro de compte : "
                f"{numero}"
            )

            numero_compte_text.color = (
                ft.Colors.BLUE
            )

            solde_text.value = (
                f"Solde actuel : "
                f"{solde:,.2f} $"
            )

            solde_text.color = (
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

        if not client_dropdown.value:

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

                vider_compte()

                afficher_message(
                    "Ce compte n'appartient pas "
                    "au client sélectionné.",
                    ft.Colors.RED
                )

                return

            compte_actuel["id"] = int(
                compte[0]
            )

            compte_actuel["numero"] = str(
                compte[1]
            )

            solde = float(
                compte[2] or 0
            )

            numero_compte_text.value = (
                f"Numéro de compte : "
                f"{compte[1]}"
            )

            solde_text.value = (
                f"Solde actuel : "
                f"{solde:,.2f} $"
            )

            numero_compte_text.color = (
                ft.Colors.BLUE
            )

            solde_text.color = (
                ft.Colors.BLUE
            )

            message.value = (
                "Compte prêt pour le retrait."
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
    # ENREGISTRER RETRAIT
    # =========================================================

    def enregistrer_retrait(e):

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
                "Veuillez saisir le montant du retrait.",
                ft.Colors.RED
            )

            return

        try:

            montant_retrait = float(
                valeur.replace(",", ".")
            )

        except ValueError:

            afficher_message(
                "Montant invalide.",
                ft.Colors.RED
            )

            return

        if montant_retrait <= 0:

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
                    "Le compte sélectionné "
                    "n'appartient pas au client.",
                    ft.Colors.RED
                )

                return

            # =================================================
            # INFORMATIONS
            # =================================================

            numero_compte = str(
                compte[1]
            )

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
            # VÉRIFIER LE SOLDE
            # =================================================

            if montant_retrait > ancien_solde:

                conn.rollback()

                afficher_message(
                    f"Solde insuffisant. "
                    f"Solde disponible : "
                    f"{ancien_solde:,.2f} $",
                    ft.Colors.RED
                )

                return

            # =================================================
            # CALCUL NOUVEAU SOLDE
            # =================================================

            nouveau_solde = (
                ancien_solde -
                montant_retrait
            )

            # =================================================
            # NUMÉRO RETRAIT
            # =================================================

            numero_ret = generer_numero_retrait(
                cursor
            )

            # =================================================
            # INSERTION RETRAIT
            # =================================================

            cursor.execute("""
                INSERT INTO retraits
                (
                    numero_retrait,
                    compte_id,
                    client_id,
                    montant,
                    date_retrait
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
                numero_ret,
                compte_id,
                client_id,
                montant_retrait,
                datetime.now()
            ))

            # =================================================
            # DIMINUER SOLDE
            # =================================================

            cursor.execute("""
                UPDATE comptes
                SET solde = solde - %s
                WHERE
                    id = %s
                    AND client_id = %s
            """, (
                montant_retrait,
                compte_id,
                client_id
            ))

            if cursor.rowcount != 1:

                conn.rollback()

                afficher_message(
                    "Erreur lors de la mise à jour "
                    "du solde.",
                    ft.Colors.RED
                )

                return

            # =================================================
            # VALIDATION
            # =================================================

            conn.commit()

            dernier_retrait["numero"] = (
                numero_ret
            )

            # =================================================
            # AFFICHAGE
            # =================================================

            numero_retrait_text.value = (
                f"N° Retrait : {numero_ret}"
            )

            numero_retrait_text.color = (
                ft.Colors.GREEN
            )

            nouveau_solde_text.value = (
                f"Nouveau solde : "
                f"{nouveau_solde:,.2f} $"
            )

            nouveau_solde_text.color = (
                ft.Colors.GREEN
            )

            solde_text.value = (
                f"Solde actuel : "
                f"{nouveau_solde:,.2f} $"
            )

            solde_text.color = (
                ft.Colors.GREEN
            )

            message.value = (
                "Retrait enregistré avec succès. "
                "Le solde a été diminué automatiquement."
            )

            message.color = (
                ft.Colors.GREEN
            )

            montant.value = ""

            page.update()

            # =================================================
            # IMPRIMER AUTOMATIQUEMENT
            # =================================================

            ouvrir_bordereau(
                numero_ret,
                numero_compte,
                client_nom,
                montant_retrait,
                ancien_solde,
                nouveau_solde,
                datetime.now()
            )

        except Exception as ex:

            if conn:

                try:
                    conn.rollback()
                except Exception:
                    pass

            afficher_message(
                f"Erreur retrait : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:

                conn.close()

    # =========================================================
    # BORDEREAU DE RETRAIT
    # =========================================================

    def ouvrir_bordereau(
        numero_ret,
        numero_compte,
        client_nom,
        montant_ret,
        ancien_solde,
        nouveau_solde,
        date_operation
    ):

        numero_ret = html.escape(
            str(numero_ret)
        )

        numero_compte = html.escape(
            str(numero_compte)
        )

        client_nom = html.escape(
            str(client_nom)
        )

        date_text = date_operation.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        contenu = f"""
<!DOCTYPE html>

<html lang="fr">

<head>

<meta charset="UTF-8">

<title>Bordereau {numero_ret}</title>

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
    font-size: 26px;
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

    .bordereau {{
        width: auto;
        max-width: none;
        border: none;
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

<h2>BORDEREAU DE RETRAIT</h2>

<hr>

<div class="numero">

N° RETRAIT : {numero_ret}

</div>

<hr>

<div class="ligne">

<strong>Client :</strong>
{client_nom}

</div>

<div class="ligne">

<strong>Numéro de compte :</strong>
{numero_compte}

</div>

<div class="ligne">

<strong>Date :</strong>
{date_text}

</div>

<div class="montant">

MONTANT DU RETRAIT

<br><br>

{montant_ret:,.2f} $

</div>

<div class="ligne">

<strong>Ancien solde :</strong>
{ancien_solde:,.2f} $

</div>

<div class="ligne">

<strong>Montant retiré :</strong>
{montant_ret:,.2f} $

</div>

<div class="ligne">

<strong>Nouveau solde :</strong>
{nouveau_solde:,.2f} $

</div>

<div class="ligne">

<strong>Opération :</strong>
RETRAIT

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

🖨 IMPRIMER LE BORDEREAU

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

            fichier.write(contenu)

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
    # IMPRIMER DERNIER RETRAIT
    # =========================================================

    def imprimer_dernier(e):

        numero_ret = (
            dernier_retrait["numero"]
        )

        if not numero_ret:

            afficher_message(
                "Aucun retrait enregistré.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    r.numero_retrait,
                    r.montant,
                    r.date_retrait,
                    c.numero_compte,
                    c.solde,
                    cl.nom,
                    cl.postnom,
                    cl.prenom
                FROM retraits r

                INNER JOIN comptes c
                    ON c.id = r.compte_id

                INNER JOIN clients cl
                    ON cl.id = r.client_id

                WHERE r.numero_retrait = %s
            """, (
                numero_ret,
            ))

            retrait = cursor.fetchone()

            if not retrait:

                afficher_message(
                    "Retrait introuvable.",
                    ft.Colors.RED
                )

                return

            montant_ret = float(
                retrait[1] or 0
            )

            solde_apres = float(
                retrait[4] or 0
            )

            ancien_solde = (
                solde_apres +
                montant_ret
            )

            client_nom = " ".join(
                x for x in [
                    retrait[5] or "",
                    retrait[6] or "",
                    retrait[7] or ""
                ]
                if x
            )

            ouvrir_bordereau(
                retrait[0],
                retrait[3],
                client_nom,
                montant_ret,
                ancien_solde,
                solde_apres,
                retrait[2]
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

        montant.value = ""

        numero_retrait_text.value = ""

        nouveau_solde_text.value = ""

        message.value = ""

        dernier_retrait["numero"] = None

        charger_clients()

        page.update()

    # =========================================================
    # ÉVÉNEMENTS
    # =========================================================

    client_dropdown.on_select = (
        charger_compte_client
    )

    compte_dropdown.on_select = (
        afficher_compte
    )

    # =========================================================
    # BOUTONS
    # =========================================================

    bouton_enregistrer = ft.ElevatedButton(
        "Enregistrer le retrait",
        icon=ft.Icons.SAVE,
        on_click=enregistrer_retrait
    )

    bouton_imprimer = ft.ElevatedButton(
        "Imprimer le bordereau",
        icon=ft.Icons.PRINT,
        on_click=imprimer_dernier
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
                            "GESTION DES RETRAITS",
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
                                    "Nouveau retrait",
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

                                solde_text,

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

                                numero_retrait_text,

                                nouveau_solde_text,

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