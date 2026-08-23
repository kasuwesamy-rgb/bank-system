import flet as ft
from database import connect_db
from datetime import datetime
import tempfile
import os
import webbrowser
import html


def virement_view(page: ft.Page):

    # =========================================================
    # VARIABLES
    # =========================================================

    dernier_virement = {
        "numero": None
    }

    compte_source_actuel = {
        "id": None,
        "numero": None,
        "solde": 0.0
    }

    compte_destination_actuel = {
        "id": None,
        "numero": None,
        "solde": 0.0
    }

    # =========================================================
    # CHAMPS SOURCE
    # =========================================================

    client_source_dropdown = ft.Dropdown(
        label="Client source",
        hint_text="Sélectionner le client qui envoie",
        width=600,
        options=[]
    )

    compte_source_dropdown = ft.Dropdown(
        label="Compte source",
        hint_text="Le compte apparaîtra automatiquement",
        width=600,
        options=[]
    )

    numero_compte_source = ft.Text(
        "Numéro compte source : -",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    solde_source = ft.Text(
        "Solde source : 0.00 $",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    # =========================================================
    # CHAMPS DESTINATION
    # =========================================================

    client_destination_dropdown = ft.Dropdown(
        label="Client destination",
        hint_text="Sélectionner le client qui reçoit",
        width=600,
        options=[]
    )

    compte_destination_dropdown = ft.Dropdown(
        label="Compte destination",
        hint_text="Le compte apparaîtra automatiquement",
        width=600,
        options=[]
    )

    numero_compte_destination = ft.Text(
        "Numéro compte destination : -",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    solde_destination = ft.Text(
        "Solde destination : 0.00 $",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    # =========================================================
    # MONTANT
    # =========================================================

    montant = ft.TextField(
        label="Montant du virement",
        hint_text="Exemple : 100",
        width=600,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    # =========================================================
    # RÉSULTATS
    # =========================================================

    numero_virement_text = ft.Text(
        "",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    nouveau_solde_source = ft.Text(
        "",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    nouveau_solde_destination = ft.Text(
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

    def afficher_message(texte, couleur=ft.Colors.BLACK):

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
    # GÉNÉRER NUMÉRO VIREMENT
    # =========================================================

    def generer_numero_virement(cursor):

        annee = datetime.now().year

        cursor.execute("""
            SELECT numero_virement
            FROM virements
            ORDER BY id DESC
            LIMIT 1
        """)

        dernier = cursor.fetchone()

        if not dernier or not dernier[0]:

            return f"VIR-{annee}-000001"

        try:

            ancien = str(
                dernier[0]
            )

            dernier_numero = int(
                ancien.split("-")[-1]
            )

            return (
                f"VIR-{annee}-"
                f"{dernier_numero + 1:06d}"
            )

        except Exception:

            return f"VIR-{annee}-000001"

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

            client_source_dropdown.options.clear()
            client_destination_dropdown.options.clear()

            for client in clients:

                client_id = int(
                    client[0]
                )

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

                option = ft.DropdownOption(
                    key=str(client_id),
                    text=nom_complet
                )

                client_source_dropdown.options.append(
                    option
                )

                client_destination_dropdown.options.append(
                    ft.DropdownOption(
                        key=str(client_id),
                        text=nom_complet
                    )
                )

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
    # RÉINITIALISER SOURCE
    # =========================================================

    def reset_compte_source():

        compte_source_actuel["id"] = None
        compte_source_actuel["numero"] = None
        compte_source_actuel["solde"] = 0.0

        compte_source_dropdown.options.clear()

        compte_source_dropdown.value = None

        numero_compte_source.value = (
            "Numéro compte source : -"
        )

        solde_source.value = (
            "Solde source : 0.00 $"
        )

        numero_compte_source.color = (
            ft.Colors.BLACK
        )

        solde_source.color = (
            ft.Colors.BLACK
        )

    # =========================================================
    # RÉINITIALISER DESTINATION
    # =========================================================

    def reset_compte_destination():

        compte_destination_actuel["id"] = None
        compte_destination_actuel["numero"] = None
        compte_destination_actuel["solde"] = 0.0

        compte_destination_dropdown.options.clear()

        compte_destination_dropdown.value = None

        numero_compte_destination.value = (
            "Numéro compte destination : -"
        )

        solde_destination.value = (
            "Solde destination : 0.00 $"
        )

        numero_compte_destination.color = (
            ft.Colors.BLACK
        )

        solde_destination.color = (
            ft.Colors.BLACK
        )

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
                    "numero": str(compte[1]),
                    "solde": float(compte[2] or 0)
                }

            # -------------------------------------------------
            # GÉNÉRER NUMÉRO
            # -------------------------------------------------

            numero = generer_numero_compte(
                cursor
            )

            # -------------------------------------------------
            # CRÉER COMPTE
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
                "solde": 0.0
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
    # CHARGER COMPTE SOURCE AUTOMATIQUEMENT
    # =========================================================

    def charger_compte_source(e=None):

        # -----------------------------------------------------
        # VIDER ANCIEN COMPTE
        # -----------------------------------------------------

        reset_compte_source()

        # -----------------------------------------------------
        # VÉRIFIER CLIENT
        # -----------------------------------------------------

        if not client_source_dropdown.value:

            page.update()

            return

        try:

            client_id = int(
                client_source_dropdown.value
            )

        except Exception:

            afficher_message(
                "ID client source invalide.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # =================================================
            # RECHERCHER COMPTE
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

                compte_source_dropdown.options.append(
                    ft.DropdownOption(
                        key=str(compte_id),
                        text=(
                            f"{numero} | "
                            f"Solde : "
                            f"{solde:,.2f} $"
                        )
                    )
                )

                compte_source_dropdown.value = (
                    str(compte_id)
                )

                compte_source_actuel["id"] = (
                    compte_id
                )

                compte_source_actuel["numero"] = (
                    numero
                )

                compte_source_actuel["solde"] = (
                    solde
                )

                numero_compte_source.value = (
                    f"Numéro compte source : "
                    f"{numero}"
                )

                numero_compte_source.color = (
                    ft.Colors.BLUE
                )

                solde_source.value = (
                    f"Solde source : "
                    f"{solde:,.2f} $"
                )

                solde_source.color = (
                    ft.Colors.BLUE
                )

                message.value = (
                    f"Compte source créé automatiquement : "
                    f"{numero}."
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

                compte_source_dropdown.options.append(
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

            premier = comptes[0]

            compte_id = int(
                premier[0]
            )

            numero = str(
                premier[1]
            )

            solde = float(
                premier[2] or 0
            )

            compte_source_dropdown.value = (
                str(compte_id)
            )

            compte_source_actuel["id"] = (
                compte_id
            )

            compte_source_actuel["numero"] = (
                numero
            )

            compte_source_actuel["solde"] = (
                solde
            )

            # =================================================
            # AFFICHAGE
            # =================================================

            numero_compte_source.value = (
                f"Numéro compte source : "
                f"{numero}"
            )

            numero_compte_source.color = (
                ft.Colors.BLUE
            )

            solde_source.value = (
                f"Solde source : "
                f"{solde:,.2f} $"
            )

            solde_source.color = (
                ft.Colors.BLUE
            )

            message.value = (
                "Compte source chargé automatiquement."
            )

            message.color = (
                ft.Colors.GREEN
            )

        except Exception as ex:

            afficher_message(
                f"Erreur compte source : {ex}",
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
    # AFFICHER COMPTE SOURCE
    # =========================================================

    def afficher_compte_source(e=None):

        if not client_source_dropdown.value:

            return

        if not compte_source_dropdown.value:

            return

        try:

            client_id = int(
                client_source_dropdown.value
            )

            compte_id = int(
                compte_source_dropdown.value
            )

        except Exception:

            afficher_message(
                "Client ou compte source invalide.",
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

                reset_compte_source()

                afficher_message(
                    "Ce compte source n'appartient "
                    "pas au client sélectionné.",
                    ft.Colors.RED
                )

                return

            compte_source_actuel["id"] = int(
                compte[0]
            )

            compte_source_actuel["numero"] = str(
                compte[1]
            )

            compte_source_actuel["solde"] = float(
                compte[2] or 0
            )

            numero_compte_source.value = (
                f"Numéro compte source : "
                f"{compte[1]}"
            )

            solde_source.value = (
                f"Solde source : "
                f"{float(compte[2] or 0):,.2f} $"
            )

            numero_compte_source.color = (
                ft.Colors.BLUE
            )

            solde_source.color = (
                ft.Colors.BLUE
            )

        except Exception as ex:

            afficher_message(
                f"Erreur compte source : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:

                conn.close()

        page.update()

    # =========================================================
    # CHARGER COMPTE DESTINATION AUTOMATIQUEMENT
    # =========================================================

    def charger_compte_destination(e=None):

        reset_compte_destination()

        if not client_destination_dropdown.value:

            page.update()

            return

        try:

            client_id = int(
                client_destination_dropdown.value
            )

        except Exception:

            afficher_message(
                "ID client destination invalide.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # =================================================
            # RECHERCHER COMPTE
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
            # AUCUN COMPTE
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

                compte_destination_dropdown.options.append(
                    ft.DropdownOption(
                        key=str(compte_id),
                        text=(
                            f"{numero} | "
                            f"Solde : "
                            f"{solde:,.2f} $"
                        )
                    )
                )

                compte_destination_dropdown.value = (
                    str(compte_id)
                )

                compte_destination_actuel["id"] = (
                    compte_id
                )

                compte_destination_actuel["numero"] = (
                    numero
                )

                compte_destination_actuel["solde"] = (
                    solde
                )

                numero_compte_destination.value = (
                    f"Numéro compte destination : "
                    f"{numero}"
                )

                numero_compte_destination.color = (
                    ft.Colors.GREEN
                )

                solde_destination.value = (
                    f"Solde destination : "
                    f"{solde:,.2f} $"
                )

                solde_destination.color = (
                    ft.Colors.GREEN
                )

                message.value = (
                    f"Compte destination créé automatiquement : "
                    f"{numero}."
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

                compte_destination_dropdown.options.append(
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

            premier = comptes[0]

            compte_id = int(
                premier[0]
            )

            numero = str(
                premier[1]
            )

            solde = float(
                premier[2] or 0
            )

            compte_destination_dropdown.value = (
                str(compte_id)
            )

            compte_destination_actuel["id"] = (
                compte_id
            )

            compte_destination_actuel["numero"] = (
                numero
            )

            compte_destination_actuel["solde"] = (
                solde
            )

            # =================================================
            # AFFICHAGE
            # =================================================

            numero_compte_destination.value = (
                f"Numéro compte destination : "
                f"{numero}"
            )

            numero_compte_destination.color = (
                ft.Colors.GREEN
            )

            solde_destination.value = (
                f"Solde destination : "
                f"{solde:,.2f} $"
            )

            solde_destination.color = (
                ft.Colors.GREEN
            )

            message.value = (
                "Compte destination chargé automatiquement."
            )

            message.color = (
                ft.Colors.GREEN
            )

        except Exception as ex:

            afficher_message(
                f"Erreur compte destination : {ex}",
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
    # AFFICHER COMPTE DESTINATION
    # =========================================================

    def afficher_compte_destination(e=None):

        if not client_destination_dropdown.value:

            return

        if not compte_destination_dropdown.value:

            return

        try:

            client_id = int(
                client_destination_dropdown.value
            )

            compte_id = int(
                compte_destination_dropdown.value
            )

        except Exception:

            afficher_message(
                "Client ou compte destination invalide.",
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

                reset_compte_destination()

                afficher_message(
                    "Ce compte destination n'appartient "
                    "pas au client sélectionné.",
                    ft.Colors.RED
                )

                return

            compte_destination_actuel["id"] = int(
                compte[0]
            )

            compte_destination_actuel["numero"] = str(
                compte[1]
            )

            compte_destination_actuel["solde"] = float(
                compte[2] or 0
            )

            numero_compte_destination.value = (
                f"Numéro compte destination : "
                f"{compte[1]}"
            )

            solde_destination.value = (
                f"Solde destination : "
                f"{float(compte[2] or 0):,.2f} $"
            )

            numero_compte_destination.color = (
                ft.Colors.GREEN
            )

            solde_destination.color = (
                ft.Colors.GREEN
            )

        except Exception as ex:

            afficher_message(
                f"Erreur compte destination : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:

                conn.close()

        page.update()

    # =========================================================
    # ENREGISTRER VIREMENT
    # =========================================================

    def enregistrer_virement(e):

        # -----------------------------------------------------
        # CLIENT SOURCE
        # -----------------------------------------------------

        if not client_source_dropdown.value:

            afficher_message(
                "Veuillez sélectionner le client source.",
                ft.Colors.RED
            )

            return

        # -----------------------------------------------------
        # COMPTE SOURCE
        # -----------------------------------------------------

        if not compte_source_dropdown.value:

            afficher_message(
                "Aucun compte source disponible.",
                ft.Colors.RED
            )

            return

        # -----------------------------------------------------
        # CLIENT DESTINATION
        # -----------------------------------------------------

        if not client_destination_dropdown.value:

            afficher_message(
                "Veuillez sélectionner le client destination.",
                ft.Colors.RED
            )

            return

        # -----------------------------------------------------
        # COMPTE DESTINATION
        # -----------------------------------------------------

        if not compte_destination_dropdown.value:

            afficher_message(
                "Aucun compte destination disponible.",
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
                "Veuillez saisir le montant du virement.",
                ft.Colors.RED
            )

            return

        try:

            montant_virement = float(
                valeur.replace(",", ".")
            )

        except ValueError:

            afficher_message(
                "Montant invalide.",
                ft.Colors.RED
            )

            return

        if montant_virement <= 0:

            afficher_message(
                "Le montant doit être supérieur à zéro.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            client_source_id = int(
                client_source_dropdown.value
            )

            client_destination_id = int(
                client_destination_dropdown.value
            )

            compte_source_id = int(
                compte_source_dropdown.value
            )

            compte_destination_id = int(
                compte_destination_dropdown.value
            )

            # -------------------------------------------------
            # MÊME COMPTE
            # -------------------------------------------------

            if compte_source_id == compte_destination_id:

                afficher_message(
                    "Le compte source et le compte destination "
                    "ne peuvent pas être identiques.",
                    ft.Colors.RED
                )

                return

            conn = connect_db()
            cursor = conn.cursor()

            conn.start_transaction()

            # =================================================
            # COMPTE SOURCE
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
                compte_source_id,
                client_source_id
            ))

            source = cursor.fetchone()

            if not source:

                conn.rollback()

                afficher_message(
                    "Le compte source n'appartient "
                    "pas au client source.",
                    ft.Colors.RED
                )

                return

            # =================================================
            # COMPTE DESTINATION
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
                compte_destination_id,
                client_destination_id
            ))

            destination = cursor.fetchone()

            if not destination:

                conn.rollback()

                afficher_message(
                    "Le compte destination n'appartient "
                    "pas au client destination.",
                    ft.Colors.RED
                )

                return

            # =================================================
            # INFORMATIONS SOURCE
            # =================================================

            numero_source = str(
                source[1]
            )

            ancien_solde_source = float(
                source[2] or 0
            )

            client_source_nom = " ".join(
                str(x)
                for x in [
                    source[4] or "",
                    source[5] or "",
                    source[6] or ""
                ]
                if x
            )

            # =================================================
            # INFORMATIONS DESTINATION
            # =================================================

            numero_destination = str(
                destination[1]
            )

            ancien_solde_destination = float(
                destination[2] or 0
            )

            client_destination_nom = " ".join(
                str(x)
                for x in [
                    destination[4] or "",
                    destination[5] or "",
                    destination[6] or ""
                ]
                if x
            )

            # =================================================
            # VÉRIFIER SOLDE
            # =================================================

            if montant_virement > ancien_solde_source:

                conn.rollback()

                afficher_message(
                    f"Solde insuffisant. "
                    f"Solde disponible : "
                    f"{ancien_solde_source:,.2f} $",
                    ft.Colors.RED
                )

                return

            # =================================================
            # NOUVEAUX SOLDES
            # =================================================

            nouveau_solde_source = (
                ancien_solde_source
                - montant_virement
            )

            nouveau_solde_destination = (
                ancien_solde_destination
                + montant_virement
            )

            # =================================================
            # NUMÉRO VIREMENT
            # =================================================

            numero_virement = (
                generer_numero_virement(
                    cursor
                )
            )

            date_virement = datetime.now()

            # =================================================
            # INSERTION VIREMENT
            # =================================================

            cursor.execute("""
                INSERT INTO virements
                (
                    numero_virement,
                    compte_source_id,
                    client_source_id,
                    compte_destination_id,
                    client_destination_id,
                    montant,
                    date_virement
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                numero_virement,
                compte_source_id,
                client_source_id,
                compte_destination_id,
                client_destination_id,
                montant_virement,
                date_virement
            ))

            # =================================================
            # DÉBIT SOURCE
            # =================================================

            cursor.execute("""
                UPDATE comptes

                SET solde = solde - %s

                WHERE
                    id = %s
                    AND client_id = %s
            """, (
                montant_virement,
                compte_source_id,
                client_source_id
            ))

            if cursor.rowcount != 1:

                conn.rollback()

                afficher_message(
                    "Erreur lors du débit du compte source.",
                    ft.Colors.RED
                )

                return

            # =================================================
            # CRÉDIT DESTINATION
            # =================================================

            cursor.execute("""
                UPDATE comptes

                SET solde = solde + %s

                WHERE
                    id = %s
                    AND client_id = %s
            """, (
                montant_virement,
                compte_destination_id,
                client_destination_id
            ))

            if cursor.rowcount != 1:

                conn.rollback()

                afficher_message(
                    "Erreur lors du crédit du compte destination.",
                    ft.Colors.RED
                )

                return

            # =================================================
            # COMMIT
            # =================================================

            conn.commit()

            dernier_virement["numero"] = (
                numero_virement
            )

            # =================================================
            # AFFICHAGE
            # =================================================

            numero_virement_text.value = (
                f"N° Virement : {numero_virement}"
            )

            numero_virement_text.color = (
                ft.Colors.GREEN
            )

            nouveau_solde_source.value = (
                f"Nouveau solde source : "
                f"{nouveau_solde_source:,.2f} $"
            )

            nouveau_solde_source.color = (
                ft.Colors.GREEN
            )

            nouveau_solde_destination.value = (
                f"Nouveau solde destination : "
                f"{nouveau_solde_destination:,.2f} $"
            )

            nouveau_solde_destination.color = (
                ft.Colors.GREEN
            )

            solde_source.value = (
                f"Solde source : "
                f"{nouveau_solde_source:,.2f} $"
            )

            solde_source.color = (
                ft.Colors.GREEN
            )

            solde_destination.value = (
                f"Solde destination : "
                f"{nouveau_solde_destination:,.2f} $"
            )

            solde_destination.color = (
                ft.Colors.GREEN
            )

            compte_source_actuel["solde"] = (
                nouveau_solde_source
            )

            compte_destination_actuel["solde"] = (
                nouveau_solde_destination
            )

            montant.value = ""

            message.value = (
                "Virement enregistré avec succès. "
                "Le compte source a été débité et "
                "le compte destination a été crédité."
            )

            message.color = (
                ft.Colors.GREEN
            )

            page.update()

            # =================================================
            # IMPRESSION AUTOMATIQUE
            # =================================================

            ouvrir_bordereau(
                numero_virement,
                client_source_nom,
                numero_source,
                client_destination_nom,
                numero_destination,
                montant_virement,
                ancien_solde_source,
                nouveau_solde_source,
                ancien_solde_destination,
                nouveau_solde_destination,
                date_virement
            )

        except Exception as ex:

            if conn:

                try:
                    conn.rollback()
                except Exception:
                    pass

            afficher_message(
                f"Erreur virement : {ex}",
                ft.Colors.RED
            )

        finally:

            if conn:

                conn.close()

    # =========================================================
    # BORDEREAU
    # =========================================================

    def ouvrir_bordereau(
        numero,
        client_source,
        compte_source,
        client_destination,
        compte_destination,
        montant_virement,
        ancien_source,
        nouveau_source,
        ancien_destination,
        nouveau_destination,
        date_operation
    ):

        numero = html.escape(
            str(numero)
        )

        client_source = html.escape(
            str(client_source)
        )

        compte_source = html.escape(
            str(compte_source)
        )

        client_destination = html.escape(
            str(client_destination)
        )

        compte_destination = html.escape(
            str(compte_destination)
        )

        date_text = date_operation.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        contenu = f"""
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
    width: 750px;
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

.section {{
    border: 1px solid #999;
    padding: 20px;
    margin: 20px 0;
}}

.ligne {{
    font-size: 18px;
    margin: 12px 0;
}}

.montant {{
    border: 2px solid black;
    padding: 25px;
    text-align: center;
    font-size: 28px;
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
    margin-top: 40px;
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

<h2>BORDEREAU DE VIREMENT</h2>

<hr>

<div class="numero">

N° VIREMENT : {numero}

</div>

<hr>

<div class="section">

<h3>COMPTE SOURCE</h3>

<div class="ligne">
<strong>Client :</strong>
{client_source}
</div>

<div class="ligne">
<strong>Numéro de compte :</strong>
{compte_source}
</div>

<div class="ligne">
<strong>Ancien solde :</strong>
{ancien_source:,.2f} $
</div>

<div class="ligne">
<strong>Nouveau solde :</strong>
{nouveau_source:,.2f} $
</div>

</div>

<div class="section">

<h3>COMPTE DESTINATION</h3>

<div class="ligne">
<strong>Client :</strong>
{client_destination}
</div>

<div class="ligne">
<strong>Numéro de compte :</strong>
{compte_destination}
</div>

<div class="ligne">
<strong>Ancien solde :</strong>
{ancien_destination:,.2f} $
</div>

<div class="ligne">
<strong>Nouveau solde :</strong>
{nouveau_destination:,.2f} $
</div>

</div>

<div class="ligne">

<strong>Date :</strong>
{date_text}

</div>

<div class="montant">

MONTANT DU VIREMENT

<br><br>

{montant_virement:,.2f} $

</div>

<div class="ligne">

<strong>Opération :</strong>
VIREMENT

</div>

<hr>

<div class="signatures">

<div class="signature">

<strong>Client source</strong>

<br><br><br>

____________________

</div>

<div class="signature">

<strong>Caissier</strong>

<br><br><br>

____________________

</div>

<div class="signature">

<strong>Client destination</strong>

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
    # IMPRIMER DERNIER VIREMENT
    # =========================================================

    def imprimer_dernier_virement(e):

        numero = dernier_virement["numero"]

        if not numero:

            afficher_message(
                "Aucun virement à imprimer.",
                ft.Colors.RED
            )

            return

        conn = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    v.numero_virement,
                    v.montant,
                    v.date_virement,

                    cs.numero_compte,
                    cs.solde,

                    cd.numero_compte,
                    cd.solde,

                    cls.nom,
                    cls.postnom,
                    cls.prenom,

                    cld.nom,
                    cld.postnom,
                    cld.prenom

                FROM virements v

                INNER JOIN comptes cs
                    ON cs.id = v.compte_source_id

                INNER JOIN comptes cd
                    ON cd.id = v.compte_destination_id

                INNER JOIN clients cls
                    ON cls.id = v.client_source_id

                INNER JOIN clients cld
                    ON cld.id = v.client_destination_id

                WHERE v.numero_virement = %s

                LIMIT 1
            """, (
                numero,
            ))

            virement = cursor.fetchone()

            if not virement:

                afficher_message(
                    "Virement introuvable.",
                    ft.Colors.RED
                )

                return

            montant_virement = float(
                virement[1] or 0
            )

            solde_source_apres = float(
                virement[4] or 0
            )

            solde_destination_apres = float(
                virement[6] or 0
            )

            ancien_source = (
                solde_source_apres
                + montant_virement
            )

            ancien_destination = (
                solde_destination_apres
                - montant_virement
            )

            client_source = " ".join(
                str(x)
                for x in [
                    virement[7] or "",
                    virement[8] or "",
                    virement[9] or ""
                ]
                if x
            )

            client_destination = " ".join(
                str(x)
                for x in [
                    virement[10] or "",
                    virement[11] or "",
                    virement[12] or ""
                ]
                if x
            )

            ouvrir_bordereau(
                virement[0],
                client_source,
                virement[3],
                client_destination,
                virement[5],
                montant_virement,
                ancien_source,
                solde_source_apres,
                ancien_destination,
                solde_destination_apres,
                virement[2]
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

        client_source_dropdown.value = None
        client_destination_dropdown.value = None

        reset_compte_source()
        reset_compte_destination()

        montant.value = ""

        numero_virement_text.value = ""

        nouveau_solde_source.value = ""

        nouveau_solde_destination.value = ""

        message.value = ""

        dernier_virement["numero"] = None

        charger_clients()

        page.update()

    # =========================================================
    # ÉVÉNEMENTS
    # =========================================================

    # IMPORTANT :
    # Même fonctionnement que ton retrait

    client_source_dropdown.on_select = (
        charger_compte_source
    )

    client_destination_dropdown.on_select = (
        charger_compte_destination
    )

    compte_source_dropdown.on_select = (
        afficher_compte_source
    )

    compte_destination_dropdown.on_select = (
        afficher_compte_destination
    )

    # =========================================================
    # BOUTONS
    # =========================================================

    bouton_enregistrer = ft.ElevatedButton(
        "Enregistrer le virement",
        icon=ft.Icons.SEND,
        on_click=enregistrer_virement
    )

    bouton_imprimer = ft.ElevatedButton(
        "Imprimer le bordereau",
        icon=ft.Icons.PRINT,
        on_click=imprimer_dernier_virement
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
                            "GESTION DES VIREMENTS",
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
                                    "Nouveau virement",
                                    size=22,
                                    weight=ft.FontWeight.BOLD
                                ),

                                # =================================================
                                # SOURCE
                                # =================================================

                                ft.Text(
                                    "COMPTE SOURCE",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE
                                ),

                                client_source_dropdown,

                                compte_source_dropdown,

                                numero_compte_source,

                                solde_source,

                                ft.Divider(),

                                # =================================================
                                # DESTINATION
                                # =================================================

                                ft.Text(
                                    "COMPTE DESTINATION",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN
                                ),

                                client_destination_dropdown,

                                compte_destination_dropdown,

                                numero_compte_destination,

                                solde_destination,

                                ft.Divider(),

                                # =================================================
                                # MONTANT
                                # =================================================

                                montant,

                                # =================================================
                                # BOUTONS
                                # =================================================

                                ft.Row(
                                    controls=[
                                        bouton_enregistrer,
                                        bouton_imprimer
                                    ],
                                    wrap=True
                                ),

                                numero_virement_text,

                                nouveau_solde_source,

                                nouveau_solde_destination,

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