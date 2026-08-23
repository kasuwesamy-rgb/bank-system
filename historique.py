import flet as ft
from database import connect_db
from datetime import datetime
import tempfile
import os
import webbrowser
import html


def historique_view(page: ft.Page):

    # =========================================================
    # COMPTE ACTUEL
    # =========================================================

    compte_actuel = {
        "id": None,
        "numero": None,
        "solde": 0.0
    }

    # =========================================================
    # CHAMPS CLIENT
    # =========================================================

    client_dropdown = ft.Dropdown(
        label="Client",
        hint_text="Sélectionner le client",
        width=600,
        options=[]
    )

    # =========================================================
    # CHAMP COMPTE
    # =========================================================

    compte_dropdown = ft.Dropdown(
        label="Compte",
        hint_text="Le compte apparaîtra automatiquement",
        width=600,
        options=[]
    )

    # =========================================================
    # AFFICHAGE COMPTE
    # =========================================================

    numero_compte_text = ft.Text(
        "Numéro de compte : -",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_900
    )

    solde_text = ft.Text(
        "Solde actuel : 0.00 $",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.GREEN_800
    )

    # =========================================================
    # STATISTIQUES
    # =========================================================

    total_depots_text = ft.Text(
        "0.00 $",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    total_retraits_text = ft.Text(
        "0.00 $",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    total_envoyes_text = ft.Text(
        "0.00 $",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    total_recus_text = ft.Text(
        "0.00 $",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    nombre_mouvements_text = ft.Text(
        "0",
        size=18,
        weight=ft.FontWeight.BOLD
    )

    message = ft.Text(
        "",
        size=15
    )

    # =========================================================
    # TABLEAU
    # =========================================================

    tableau = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date")),
            ft.DataColumn(ft.Text("N° opération")),
            ft.DataColumn(ft.Text("Type")),
            ft.DataColumn(ft.Text("Libellé")),
            ft.DataColumn(ft.Text("Débit")),
            ft.DataColumn(ft.Text("Crédit")),
            ft.DataColumn(ft.Text("Solde")),
        ],
        rows=[],
        column_spacing=20
    )

    # =========================================================
    # MESSAGE
    # =========================================================

    def afficher_message(
        texte,
        couleur=ft.Colors.BLACK
    ):
        message.value = texte
        message.color = couleur
        page.update()

    # =========================================================
    # FORMATER DATE
    # =========================================================

    def formater_date(date_operation):

        if date_operation is None:
            return "-"

        if isinstance(date_operation, datetime):
            return date_operation.strftime(
                "%d/%m/%Y %H:%M:%S"
            )

        try:
            return datetime.strptime(
                str(date_operation),
                "%Y-%m-%d %H:%M:%S"
            ).strftime(
                "%d/%m/%Y %H:%M:%S"
            )

        except Exception:
            return str(date_operation)

    # =========================================================
    # VIDER DONNÉES COMPTE
    # =========================================================

    def vider_donnees():

        compte_actuel["id"] = None
        compte_actuel["numero"] = None
        compte_actuel["solde"] = 0.0

        compte_dropdown.options.clear()
        compte_dropdown.value = None

        numero_compte_text.value = (
            "Numéro de compte : -"
        )

        solde_text.value = (
            "Solde actuel : 0.00 $"
        )

        total_depots_text.value = "0.00 $"
        total_retraits_text.value = "0.00 $"
        total_envoyes_text.value = "0.00 $"
        total_recus_text.value = "0.00 $"
        nombre_mouvements_text.value = "0"

        tableau.rows = []

    # =========================================================
    # CHARGER CLIENTS
    # =========================================================

    def charger_clients():

        conn = None
        cursor = None

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

                client_id = int(client[0])

                nom = str(client[1] or "")
                postnom = str(client[2] or "")
                prenom = str(client[3] or "")

                nom_complet = " ".join(
                    x
                    for x in [
                        nom,
                        postnom,
                        prenom
                    ]
                    if x.strip()
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

        except Exception as ex:

            afficher_message(
                f"Erreur chargement clients : {ex}",
                ft.Colors.RED
            )

        finally:

            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        page.update()

    # =========================================================
    # CHARGER COMPTE DU CLIENT AUTOMATIQUEMENT
    #
    # MÊME LOGIQUE QUE VIREMENT
    #
    # CLIENT
    #    ↓
    # RECHERCHE COMPTE
    #    ↓
    # SÉLECTION AUTOMATIQUE
    #    ↓
    # NUMÉRO COMPTE
    #    ↓
    # SOLDE
    #    ↓
    # HISTORIQUE
    # =========================================================

    def charger_compte_client(e=None):

        # -----------------------------------------------------
        # VIDER L'ANCIEN COMPTE
        # -----------------------------------------------------

        vider_donnees()

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
        cursor = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # =================================================
            # RECHERCHER LES COMPTES DU CLIENT
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
            # =================================================

            if not comptes:

                compte_dropdown.options.clear()
                compte_dropdown.value = None

                numero_compte_text.value = (
                    "Numéro de compte : Aucun compte"
                )

                solde_text.value = (
                    "Solde actuel : 0.00 $"
                )

                tableau.rows = []

                afficher_message(
                    "Ce client ne possède aucun compte. "
                    "Veuillez d'abord ouvrir un compte.",
                    ft.Colors.RED
                )

                page.update()
                return

            # =================================================
            # CHARGER LES COMPTES
            # =================================================

            compte_dropdown.options.clear()

            for compte in comptes:

                compte_id = int(
                    compte[0]
                )

                numero = str(
                    compte[1] or "-"
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
            # PREMIER COMPTE AUTOMATIQUE
            #
            # EXACTEMENT COMME VIREMENT
            # =================================================

            premier = comptes[0]

            compte_id = int(
                premier[0]
            )

            numero = str(
                premier[1] or "-"
            )

            solde = float(
                premier[2] or 0
            )

            # -------------------------------------------------
            # ENREGISTRER COMPTE ACTUEL
            # -------------------------------------------------

            compte_actuel["id"] = compte_id
            compte_actuel["numero"] = numero
            compte_actuel["solde"] = solde

            # -------------------------------------------------
            # SÉLECTIONNER AUTOMATIQUEMENT
            # -------------------------------------------------

            compte_dropdown.value = str(
                compte_id
            )

            # -------------------------------------------------
            # AFFICHER NUMÉRO AUTOMATIQUEMENT
            # -------------------------------------------------

            numero_compte_text.value = (
                f"Numéro de compte : {numero}"
            )

            numero_compte_text.color = (
                ft.Colors.BLUE_900
            )

            # -------------------------------------------------
            # AFFICHER SOLDE AUTOMATIQUEMENT
            # -------------------------------------------------

            solde_text.value = (
                f"Solde actuel : "
                f"{solde:,.2f} $"
            )

            solde_text.color = (
                ft.Colors.GREEN_800
            )

            # -------------------------------------------------
            # CHARGER HISTORIQUE AUTOMATIQUEMENT
            # -------------------------------------------------

            charger_historique()

            message.value = (
                f"Compte {numero} "
                f"chargé automatiquement."
            )

            message.color = ft.Colors.GREEN

        except Exception as ex:

            afficher_message(
                f"Erreur chargement compte : {ex}",
                ft.Colors.RED
            )

        finally:

            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        page.update()

    # =========================================================
    # CHANGER DE COMPTE MANUELLEMENT
    # =========================================================

    def changer_compte(e=None):

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
                "Client ou compte invalide.",
                ft.Colors.RED
            )
            return

        conn = None
        cursor = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    numero_compte,
                    solde
                FROM comptes
                WHERE
                    id = %s
                    AND client_id = %s
                LIMIT 1
            """, (
                compte_id,
                client_id
            ))

            compte = cursor.fetchone()

            if not compte:

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
                compte[1] or "-"
            )

            compte_actuel["solde"] = float(
                compte[2] or 0
            )

            numero_compte_text.value = (
                f"Numéro de compte : "
                f"{compte[1] or '-'}"
            )

            solde_text.value = (
                f"Solde actuel : "
                f"{float(compte[2] or 0):,.2f} $"
            )

            # Recharger l'historique
            charger_historique()

            page.update()

        except Exception as ex:

            afficher_message(
                f"Erreur sélection compte : {ex}",
                ft.Colors.RED
            )

        finally:

            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # =========================================================
    # CHARGER HISTORIQUE
    # =========================================================

    def charger_historique(e=None):

        # -----------------------------------------------------
        # SI COMPTE NON ENREGISTRÉ
        # -----------------------------------------------------

        if not compte_actuel["id"]:

            if compte_dropdown.value:

                try:

                    compte_actuel["id"] = int(
                        compte_dropdown.value
                    )

                except Exception:

                    afficher_message(
                        "Compte invalide.",
                        ft.Colors.RED
                    )
                    return

            else:

                afficher_message(
                    "Veuillez sélectionner un client.",
                    ft.Colors.ORANGE
                )
                return

        compte_id = compte_actuel["id"]

        conn = None
        cursor = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # =================================================
            # INFORMATIONS COMPTE
            # =================================================

            cursor.execute("""
                SELECT
                    numero_compte,
                    solde
                FROM comptes
                WHERE id = %s
                LIMIT 1
            """, (
                compte_id,
            ))

            compte = cursor.fetchone()

            if not compte:

                afficher_message(
                    "Compte introuvable.",
                    ft.Colors.RED
                )
                return

            numero_compte = str(
                compte[0] or "-"
            )

            solde_actuel = float(
                compte[1] or 0
            )

            # =================================================
            # IMPORTANT
            # METTRE À JOUR LE COMPTE ACTUEL
            # =================================================

            compte_actuel["numero"] = (
                numero_compte
            )

            compte_actuel["solde"] = (
                solde_actuel
            )

            # =================================================
            # AFFICHER NUMÉRO
            # =================================================

            numero_compte_text.value = (
                f"Numéro de compte : "
                f"{numero_compte}"
            )

            # =================================================
            # AFFICHER SOLDE
            # =================================================

            solde_text.value = (
                f"Solde actuel : "
                f"{solde_actuel:,.2f} $"
            )

            # =================================================
            # LISTE MOUVEMENTS
            # =================================================

            mouvements = []

            # =================================================
            # DÉPÔTS
            # =================================================

            cursor.execute("""
                SELECT
                    id,
                    numero_depot,
                    montant,
                    date_depot
                FROM depots
                WHERE compte_id = %s
                ORDER BY date_depot ASC, id ASC
            """, (
                compte_id,
            ))

            for row in cursor.fetchall():

                mouvements.append({
                    "date": row[3],
                    "numero": row[1],
                    "type": "DÉPÔT",
                    "libelle": "Dépôt d'argent",
                    "debit": 0.0,
                    "credit": float(row[2] or 0)
                })

            # =================================================
            # RETRAITS
            # =================================================

            cursor.execute("""
                SELECT
                    id,
                    numero_retrait,
                    montant,
                    date_retrait
                FROM retraits
                WHERE compte_id = %s
                ORDER BY date_retrait ASC, id ASC
            """, (
                compte_id,
            ))

            for row in cursor.fetchall():

                mouvements.append({
                    "date": row[3],
                    "numero": row[1],
                    "type": "RETRAIT",
                    "libelle": "Retrait d'argent",
                    "debit": float(row[2] or 0),
                    "credit": 0.0
                })

            # =================================================
            # VIREMENTS ENVOYÉS
            # =================================================

            cursor.execute("""
                SELECT
                    v.id,
                    v.numero_virement,
                    v.montant,
                    v.date_virement,
                    c.numero_compte
                FROM virements v
                LEFT JOIN comptes c
                    ON c.id = v.compte_destination_id
                WHERE v.compte_source_id = %s
                ORDER BY
                    v.date_virement ASC,
                    v.id ASC
            """, (
                compte_id,
            ))

            for row in cursor.fetchall():

                destination = str(
                    row[4] or "-"
                )

                mouvements.append({
                    "date": row[3],
                    "numero": row[1],
                    "type": "VIREMENT",
                    "libelle": (
                        f"Virement envoyé vers "
                        f"{destination}"
                    ),
                    "debit": float(row[2] or 0),
                    "credit": 0.0
                })

            # =================================================
            # VIREMENTS REÇUS
            # =================================================

            cursor.execute("""
                SELECT
                    v.id,
                    v.numero_virement,
                    v.montant,
                    v.date_virement,
                    c.numero_compte
                FROM virements v
                LEFT JOIN comptes c
                    ON c.id = v.compte_source_id
                WHERE v.compte_destination_id = %s
                ORDER BY
                    v.date_virement ASC,
                    v.id ASC
            """, (
                compte_id,
            ))

            for row in cursor.fetchall():

                source = str(
                    row[4] or "-"
                )

                mouvements.append({
                    "date": row[3],
                    "numero": row[1],
                    "type": "VIREMENT",
                    "libelle": (
                        f"Virement reçu de "
                        f"{source}"
                    ),
                    "debit": 0.0,
                    "credit": float(row[2] or 0)
                })

            # =================================================
            # TRI
            # =================================================

            def cle_tri(mouvement):

                valeur = mouvement["date"]

                if valeur is None:
                    return datetime.min

                if isinstance(
                    valeur,
                    datetime
                ):
                    return valeur

                try:

                    return datetime.strptime(
                        str(valeur),
                        "%Y-%m-%d %H:%M:%S"
                    )

                except Exception:

                    return datetime.min

            mouvements.sort(
                key=cle_tri
            )

            # =================================================
            # CALCULS
            # =================================================

            total_depots = 0.0
            total_retraits = 0.0
            total_envoyes = 0.0
            total_recus = 0.0

            variation_totale = 0.0

            for mouvement in mouvements:

                debit = mouvement["debit"]
                credit = mouvement["credit"]

                variation_totale += (
                    credit - debit
                )

                if mouvement["type"] == "DÉPÔT":

                    total_depots += credit

                elif mouvement["type"] == "RETRAIT":

                    total_retraits += debit

                elif mouvement["type"] == "VIREMENT":

                    if debit > 0:
                        total_envoyes += debit

                    if credit > 0:
                        total_recus += credit

            # =================================================
            # SOLDE INITIAL
            # =================================================

            solde_initial = (
                solde_actuel
                - variation_totale
            )

            solde_courant = solde_initial

            # =================================================
            # REMPLIR TABLEAU
            # =================================================

            tableau.rows = []

            for mouvement in mouvements:

                debit = mouvement["debit"]
                credit = mouvement["credit"]

                solde_courant += (
                    credit - debit
                )

                # ------------------------------------------------
                # DÉBIT
                # ------------------------------------------------

                if debit > 0:

                    debit_control = ft.Text(
                        f"- {debit:,.2f} $",
                        color=ft.Colors.RED,
                        weight=ft.FontWeight.BOLD
                    )

                else:

                    debit_control = ft.Text("-")

                # ------------------------------------------------
                # CRÉDIT
                # ------------------------------------------------

                if credit > 0:

                    credit_control = ft.Text(
                        f"+ {credit:,.2f} $",
                        color=ft.Colors.GREEN,
                        weight=ft.FontWeight.BOLD
                    )

                else:

                    credit_control = ft.Text("-")

                tableau.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Text(
                                    formater_date(
                                        mouvement["date"]
                                    )
                                )
                            ),

                            ft.DataCell(
                                ft.Text(
                                    str(
                                        mouvement["numero"]
                                    )
                                )
                            ),

                            ft.DataCell(
                                ft.Text(
                                    mouvement["type"],
                                    weight=ft.FontWeight.BOLD
                                )
                            ),

                            ft.DataCell(
                                ft.Text(
                                    mouvement["libelle"]
                                )
                            ),

                            ft.DataCell(
                                debit_control
                            ),

                            ft.DataCell(
                                credit_control
                            ),

                            ft.DataCell(
                                ft.Text(
                                    f"{solde_courant:,.2f} $",
                                    weight=ft.FontWeight.BOLD
                                )
                            )
                        ]
                    )
                )

            # =================================================
            # STATISTIQUES
            # =================================================

            total_depots_text.value = (
                f"{total_depots:,.2f} $"
            )

            total_retraits_text.value = (
                f"{total_retraits:,.2f} $"
            )

            total_envoyes_text.value = (
                f"{total_envoyes:,.2f} $"
            )

            total_recus_text.value = (
                f"{total_recus:,.2f} $"
            )

            nombre_mouvements_text.value = str(
                len(mouvements)
            )

            # =================================================
            # MESSAGE
            # =================================================

            if mouvements:

                message.value = (
                    f"{len(mouvements)} "
                    f"mouvement(s) trouvé(s)."
                )

                message.color = ft.Colors.GREEN

            else:

                message.value = (
                    "Aucun mouvement pour ce compte."
                )

                message.color = ft.Colors.ORANGE

        except Exception as ex:

            message.value = (
                f"Erreur historique : {ex}"
            )

            message.color = ft.Colors.RED

        finally:

            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        page.update()

    # =========================================================
    # IMPRESSION DU RELEVÉ
    # =========================================================

    def imprimer_releve(e=None):

        if not compte_actuel["id"]:

            afficher_message(
                "Veuillez sélectionner un client.",
                ft.Colors.RED
            )
            return

        conn = None
        cursor = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # =================================================
            # CLIENT + COMPTE
            # =================================================

            cursor.execute("""
                SELECT
                    c.nom,
                    c.postnom,
                    c.prenom,
                    co.numero_compte,
                    co.solde
                FROM comptes co
                INNER JOIN clients c
                    ON c.id = co.client_id
                WHERE co.id = %s
                LIMIT 1
            """, (
                compte_actuel["id"],
            ))

            compte = cursor.fetchone()

            if not compte:

                afficher_message(
                    "Informations du compte introuvables.",
                    ft.Colors.RED
                )
                return

            nom_client = " ".join(
                x
                for x in [
                    str(compte[0] or ""),
                    str(compte[1] or ""),
                    str(compte[2] or "")
                ]
                if x.strip()
            )

            if not nom_client:
                nom_client = "Client"

            numero = str(
                compte[3] or "-"
            )

            solde_actuel = float(
                compte[4] or 0
            )

            # =================================================
            # MOUVEMENTS
            # =================================================

            mouvements = []

            # =================================================
            # DÉPÔTS
            # =================================================

            cursor.execute("""
                SELECT
                    id,
                    numero_depot,
                    montant,
                    date_depot
                FROM depots
                WHERE compte_id = %s
                ORDER BY date_depot ASC, id ASC
            """, (
                compte_actuel["id"],
            ))

            for row in cursor.fetchall():

                mouvements.append({
                    "date": row[3],
                    "numero": row[1],
                    "type": "DÉPÔT",
                    "libelle": "Dépôt d'argent",
                    "debit": 0.0,
                    "credit": float(row[2] or 0)
                })

            # =================================================
            # RETRAITS
            # =================================================

            cursor.execute("""
                SELECT
                    id,
                    numero_retrait,
                    montant,
                    date_retrait
                FROM retraits
                WHERE compte_id = %s
                ORDER BY date_retrait ASC, id ASC
            """, (
                compte_actuel["id"],
            ))

            for row in cursor.fetchall():

                mouvements.append({
                    "date": row[3],
                    "numero": row[1],
                    "type": "RETRAIT",
                    "libelle": "Retrait d'argent",
                    "debit": float(row[2] or 0),
                    "credit": 0.0
                })

            # =================================================
            # VIREMENTS ENVOYÉS
            # =================================================

            cursor.execute("""
                SELECT
                    v.id,
                    v.numero_virement,
                    v.montant,
                    v.date_virement,
                    c.numero_compte
                FROM virements v
                LEFT JOIN comptes c
                    ON c.id = v.compte_destination_id
                WHERE v.compte_source_id = %s
                ORDER BY
                    v.date_virement ASC,
                    v.id ASC
            """, (
                compte_actuel["id"],
            ))

            for row in cursor.fetchall():

                mouvements.append({
                    "date": row[3],
                    "numero": row[1],
                    "type": "VIREMENT",
                    "libelle": (
                        f"Virement envoyé vers "
                        f"{row[4] or '-'}"
                    ),
                    "debit": float(row[2] or 0),
                    "credit": 0.0
                })

            # =================================================
            # VIREMENTS REÇUS
            # =================================================

            cursor.execute("""
                SELECT
                    v.id,
                    v.numero_virement,
                    v.montant,
                    v.date_virement,
                    c.numero_compte
                FROM virements v
                LEFT JOIN comptes c
                    ON c.id = v.compte_source_id
                WHERE v.compte_destination_id = %s
                ORDER BY
                    v.date_virement ASC,
                    v.id ASC
            """, (
                compte_actuel["id"],
            ))

            for row in cursor.fetchall():

                mouvements.append({
                    "date": row[3],
                    "numero": row[1],
                    "type": "VIREMENT",
                    "libelle": (
                        f"Virement reçu de "
                        f"{row[4] or '-'}"
                    ),
                    "debit": 0.0,
                    "credit": float(row[2] or 0)
                })

            # =================================================
            # TRI
            # =================================================

            def cle_tri_impression(mouvement):

                valeur = mouvement["date"]

                if isinstance(
                    valeur,
                    datetime
                ):
                    return valeur

                try:

                    return datetime.strptime(
                        str(valeur),
                        "%Y-%m-%d %H:%M:%S"
                    )

                except Exception:

                    return datetime.min

            mouvements.sort(
                key=cle_tri_impression
            )

            # =================================================
            # SOLDE INITIAL
            # =================================================

            variation = sum(
                mouvement["credit"]
                - mouvement["debit"]
                for mouvement in mouvements
            )

            solde_initial = (
                solde_actuel
                - variation
            )

            solde_courant = solde_initial

            total_depots = 0.0
            total_retraits = 0.0
            total_envoyes = 0.0
            total_recus = 0.0

            lignes = ""

            # =================================================
            # LIGNES HTML
            # =================================================

            for mouvement in mouvements:

                debit = mouvement["debit"]
                credit = mouvement["credit"]

                solde_courant += (
                    credit - debit
                )

                if mouvement["type"] == "DÉPÔT":

                    total_depots += credit

                elif mouvement["type"] == "RETRAIT":

                    total_retraits += debit

                elif mouvement["type"] == "VIREMENT":

                    total_envoyes += debit
                    total_recus += credit

                lignes += f"""
                <tr>

                    <td>
                        {html.escape(
                            formater_date(
                                mouvement["date"]
                            )
                        )}
                    </td>

                    <td>
                        {html.escape(
                            str(
                                mouvement["numero"]
                            )
                        )}
                    </td>

                    <td>
                        {html.escape(
                            mouvement["type"]
                        )}
                    </td>

                    <td>
                        {html.escape(
                            mouvement["libelle"]
                        )}
                    </td>

                    <td class="debit">
                        {
                            f"{debit:,.2f} $"
                            if debit > 0
                            else "-"
                        }
                    </td>

                    <td class="credit">
                        {
                            f"{credit:,.2f} $"
                            if credit > 0
                            else "-"
                        }
                    </td>

                    <td>
                        {solde_courant:,.2f} $
                    </td>

                </tr>
                """

            # =================================================
            # DOCUMENT HTML
            # =================================================

            document = f"""
            <!DOCTYPE html>

            <html lang="fr">

            <head>

                <meta charset="UTF-8">

                <title>
                    Relevé de compte {html.escape(numero)}
                </title>

                <style>

                    body {{
                        font-family: Arial, sans-serif;
                        margin: 40px;
                    }}

                    h1, h2 {{
                        text-align: center;
                    }}

                    .entete {{
                        border: 1px solid #333;
                        padding: 20px;
                        margin-bottom: 20px;
                    }}

                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }}

                    th, td {{
                        border: 1px solid #999;
                        padding: 8px;
                        text-align: center;
                    }}

                    th {{
                        background-color: #eeeeee;
                    }}

                    .debit {{
                        color: red;
                        font-weight: bold;
                    }}

                    .credit {{
                        color: green;
                        font-weight: bold;
                    }}

                    .resume {{
                        margin-top: 30px;
                        border: 1px solid #999;
                        padding: 20px;
                    }}

                    .bouton {{
                        padding: 12px 25px;
                        font-size: 16px;
                        cursor: pointer;
                        margin-bottom: 20px;
                    }}

                    .signatures {{
                        display: flex;
                        justify-content: space-between;
                        margin-top: 80px;
                    }}

                    @media print {{
                        .bouton {{
                            display: none;
                        }}
                    }}

                </style>

            </head>

            <body>

                <button
                    class="bouton"
                    onclick="window.print()"
                >
                    🖨 IMPRIMER
                </button>

                <h1>
                    BANK SYSTEM
                </h1>

                <h2>
                    RELEVÉ DE COMPTE
                </h2>

                <div class="entete">

                    <p>
                        <strong>Client :</strong>
                        {html.escape(nom_client)}
                    </p>

                    <p>
                        <strong>Numéro de compte :</strong>
                        {html.escape(numero)}
                    </p>

                    <p>
                        <strong>Solde actuel :</strong>
                        {solde_actuel:,.2f} $
                    </p>

                    <p>
                        <strong>Date d'impression :</strong>
                        {
                            datetime.now().strftime(
                                "%d/%m/%Y %H:%M:%S"
                            )
                        }
                    </p>

                </div>

                <table>

                    <thead>

                        <tr>
                            <th>Date</th>
                            <th>N° opération</th>
                            <th>Type</th>
                            <th>Libellé</th>
                            <th>Débit</th>
                            <th>Crédit</th>
                            <th>Solde</th>
                        </tr>

                    </thead>

                    <tbody>

                        {lignes}

                    </tbody>

                </table>

                <div class="resume">

                    <h2>
                        RÉSUMÉ
                    </h2>

                    <p>
                        <strong>Total dépôts :</strong>
                        {total_depots:,.2f} $
                    </p>

                    <p>
                        <strong>Total retraits :</strong>
                        {total_retraits:,.2f} $
                    </p>

                    <p>
                        <strong>Virements envoyés :</strong>
                        {total_envoyes:,.2f} $
                    </p>

                    <p>
                        <strong>Virements reçus :</strong>
                        {total_recus:,.2f} $
                    </p>

                    <p>
                        <strong>Nombre de mouvements :</strong>
                        {len(mouvements)}
                    </p>

                </div>

                <div class="signatures">

                    <div>
                        <strong>
                            Signature du client
                        </strong>

                        <br><br><br>

                        ______________________
                    </div>

                    <div>
                        <strong>
                            Signature de la banque
                        </strong>

                        <br><br><br>

                        ______________________
                    </div>

                </div>

            </body>

            </html>
            """

            # =================================================
            # CRÉER FICHIER HTML
            # =================================================

            fichier = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".html",
                mode="w",
                encoding="utf-8"
            )

            fichier.write(document)
            fichier.close()

            chemin = os.path.abspath(
                fichier.name
            )

            webbrowser.open(
                "file://" + chemin
            )

            afficher_message(
                "Relevé ouvert pour impression.",
                ft.Colors.GREEN
            )

        except Exception as ex:

            afficher_message(
                f"Erreur impression : {ex}",
                ft.Colors.RED
            )

        finally:

            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # =========================================================
    # ACTUALISER
    # =========================================================

    def actualiser(e=None):

        client_dropdown.value = None

        vider_donnees()

        message.value = ""

        charger_clients()

        page.update()

    # =========================================================
    # BOUTONS
    # =========================================================

    bouton_actualiser = ft.ElevatedButton(
        "Actualiser",
        icon=ft.Icons.REFRESH,
        on_click=actualiser
    )

    bouton_historique = ft.ElevatedButton(
        "Actualiser l'historique",
        icon=ft.Icons.HISTORY,
        on_click=charger_historique
    )

    bouton_imprimer = ft.ElevatedButton(
        "Imprimer le relevé",
        icon=ft.Icons.PRINT,
        on_click=imprimer_releve
    )

    # =========================================================
    # CARTES STATISTIQUES
    # =========================================================

    carte_depots = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "DÉPÔTS",
                    weight=ft.FontWeight.BOLD
                ),
                total_depots_text
            ]
        ),
        padding=15,
        bgcolor=ft.Colors.GREEN_100,
        border_radius=10
    )

    carte_retraits = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "RETRAITS",
                    weight=ft.FontWeight.BOLD
                ),
                total_retraits_text
            ]
        ),
        padding=15,
        bgcolor=ft.Colors.RED_100,
        border_radius=10
    )

    carte_envoyes = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "VIREMENTS ENVOYÉS",
                    weight=ft.FontWeight.BOLD
                ),
                total_envoyes_text
            ]
        ),
        padding=15,
        bgcolor=ft.Colors.ORANGE_100,
        border_radius=10
    )

    carte_recus = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "VIREMENTS REÇUS",
                    weight=ft.FontWeight.BOLD
                ),
                total_recus_text
            ]
        ),
        padding=15,
        bgcolor=ft.Colors.BLUE_100,
        border_radius=10
    )

    carte_mouvements = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "MOUVEMENTS",
                    weight=ft.FontWeight.BOLD
                ),
                nombre_mouvements_text
            ]
        ),
        padding=15,
        bgcolor=ft.Colors.PURPLE_100,
        border_radius=10
    )

    resume = ft.Row(
        controls=[
            carte_depots,
            carte_retraits,
            carte_envoyes,
            carte_recus,
            carte_mouvements
        ],
        wrap=True,
        spacing=10
    )

    # =========================================================
    # ÉVÉNEMENTS
    #
    # IMPORTANT :
    # On utilise ON_SELECT comme dans VIREMENT.
    # =========================================================

    client_dropdown.on_select = (
        charger_compte_client
    )

    compte_dropdown.on_select = (
        changer_compte
    )

    # =========================================================
    # INTERFACE
    # =========================================================

    interface = ft.Column(
        controls=[

            ft.Row(
                controls=[

                    ft.Text(
                        "HISTORIQUE / RELEVÉ DE COMPTE",
                        size=28,
                        weight=ft.FontWeight.BOLD
                    ),

                    ft.Container(
                        expand=True
                    ),

                    bouton_actualiser
                ]
            ),

            ft.Divider(),

            ft.Text(
                "SÉLECTION DU CLIENT",
                size=20,
                weight=ft.FontWeight.BOLD
            ),

            client_dropdown,

            ft.Divider(),

            ft.Text(
                "COMPTE DU CLIENT",
                size=20,
                weight=ft.FontWeight.BOLD
            ),

            compte_dropdown,

            # =================================================
            # NUMÉRO + SOLDE
            # =================================================

            ft.Container(
                content=ft.Column(
                    controls=[
                        numero_compte_text,
                        solde_text
                    ],
                    spacing=10
                ),
                padding=20,
                border=ft.Border.all(
                    1,
                    ft.Colors.BLUE_300
                ),
                border_radius=10,
                bgcolor=ft.Colors.BLUE_50
            ),

            ft.Divider(),

            ft.Text(
                "RÉSUMÉ DES MOUVEMENTS",
                size=20,
                weight=ft.FontWeight.BOLD
            ),

            resume,

            ft.Row(
                controls=[
                    bouton_historique,
                    bouton_imprimer
                ],
                wrap=True
            ),

            message,

            ft.Divider(),

            ft.Text(
                "DÉTAIL DES OPÉRATIONS",
                size=20,
                weight=ft.FontWeight.BOLD
            ),

            ft.Row(
                controls=[
                    tableau
                ],
                scroll=ft.ScrollMode.AUTO
            )

        ],

        spacing=15,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )

    # =========================================================
    # CHARGEMENT INITIAL
    # =========================================================

    charger_clients()

    # =========================================================
    # RETOUR
    # =========================================================

    return ft.Container(
        content=interface,
        padding=20,
        expand=True
    )