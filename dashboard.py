import flet as ft

from database import connect_db
from clients import clients_view
from comptes import comptes_view
from depot import depot_view
from retrait import retrait_view
from virement import virement_view
from historique import historique_view


def dashboard(page: ft.Page):

    page.title = "BANK SYSTEM"

    # =====================================================
    # TITRE
    # =====================================================

    title = ft.Text(
        "BANK SYSTEM",
        size=28,
        weight=ft.FontWeight.BOLD
    )

    # =====================================================
    # STATISTIQUES
    # =====================================================

    nombre_clients = ft.Text(
        "0",
        size=30,
        weight=ft.FontWeight.BOLD
    )

    nombre_comptes = ft.Text(
        "0",
        size=30,
        weight=ft.FontWeight.BOLD
    )

    nombre_transactions = ft.Text(
        "0",
        size=30,
        weight=ft.FontWeight.BOLD
    )

    solde_total = ft.Text(
        "0.00 $",
        size=30,
        weight=ft.FontWeight.BOLD
    )

    # =====================================================
    # CHARGER STATISTIQUES
    # =====================================================

    def charger_statistiques():

        conn = None
        cursor = None

        try:

            conn = connect_db()
            cursor = conn.cursor()

            # =================================================
            # NOMBRE CLIENTS
            # =================================================

            try:

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM clients
                """)

                resultat = cursor.fetchone()

                nombre_clients.value = str(
                    resultat[0]
                    if resultat
                    else 0
                )

            except Exception as erreur:

                print(
                    "Erreur clients :",
                    erreur
                )

                nombre_clients.value = "0"

            # =================================================
            # NOMBRE COMPTES
            # =================================================

            try:

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM comptes
                """)

                resultat = cursor.fetchone()

                nombre_comptes.value = str(
                    resultat[0]
                    if resultat
                    else 0
                )

            except Exception as erreur:

                print(
                    "Erreur comptes :",
                    erreur
                )

                nombre_comptes.value = "0"

            # =================================================
            # NOMBRE DÉPÔTS
            # =================================================

            nombre_depots = 0

            try:

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM depots
                """)

                resultat = cursor.fetchone()

                nombre_depots = (
                    int(resultat[0])
                    if resultat
                    else 0
                )

            except Exception as erreur:

                print(
                    "Erreur dépôts :",
                    erreur
                )

            # =================================================
            # NOMBRE RETRAITS
            # =================================================

            nombre_retraits = 0

            try:

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM retraits
                """)

                resultat = cursor.fetchone()

                nombre_retraits = (
                    int(resultat[0])
                    if resultat
                    else 0
                )

            except Exception as erreur:

                print(
                    "Erreur retraits :",
                    erreur
                )

            # =================================================
            # NOMBRE VIREMENTS
            # =================================================

            nombre_virements = 0

            try:

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM virements
                """)

                resultat = cursor.fetchone()

                nombre_virements = (
                    int(resultat[0])
                    if resultat
                    else 0
                )

            except Exception as erreur:

                print(
                    "Erreur virements :",
                    erreur
                )

            # =================================================
            # TOTAL MOUVEMENTS
            # =================================================

            total_mouvements = (
                nombre_depots
                + nombre_retraits
                + nombre_virements
            )

            nombre_transactions.value = str(
                total_mouvements
            )

            # =================================================
            # SOLDE TOTAL
            # =================================================

            try:

                cursor.execute("""
                    SELECT
                        COALESCE(
                            SUM(solde),
                            0
                        )
                    FROM comptes
                """)

                resultat = cursor.fetchone()

                total = (
                    float(resultat[0])
                    if resultat
                    and resultat[0] is not None
                    else 0
                )

                solde_total.value = (
                    f"{total:,.2f} $"
                )

            except Exception as erreur:

                print(
                    "Erreur solde :",
                    erreur
                )

                solde_total.value = "0.00 $"

        except Exception as erreur:

            print(
                "Erreur connexion Dashboard :",
                erreur
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

    # =====================================================
    # TABLEAU DES 8 NOMS
    # =====================================================

    noms = [
        "DORCAS BALUME",
        "MAOMBI DAWANDE RUTH",
        "MENGI KAPATA BRIGITTE",
        "BUKILI DAMAS BOHULE",
        "KAMBALE KATHENDE ERICK",
        "MUHINDO KAPIMA BERNARD",
        "SILUSAWA KASUWE",
        "ASHIKANI TCHOMBE NATHALIE"
    ]

    # =====================================================
    # CRÉATION DES LIGNES
    # =====================================================

    lignes_noms = []

    for numero, nom in enumerate(noms, start=1):

        lignes_noms.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(
                            str(numero),
                            size=13
                        )
                    ),

                    ft.DataCell(
                        ft.Text(
                            nom,
                            size=13,
                            weight=ft.FontWeight.W_500
                        )
                    )
                ]
            )
        )

    # =====================================================
    # TABLEAU
    # =====================================================

    tableau_noms = ft.DataTable(

        columns=[
            ft.DataColumn(
                ft.Text(
                    "N°",
                    weight=ft.FontWeight.BOLD
                )
            ),

            ft.DataColumn(
                ft.Text(
                    "NOM COMPLET",
                    weight=ft.FontWeight.BOLD
                )
            )
        ],

        rows=lignes_noms,

        column_spacing=30,

        heading_row_height=40,

        data_row_min_height=35,

        data_row_max_height=40
    )

    # =====================================================
    # BLOC DU TABLEAU
    # =====================================================

    bloc_noms = ft.Container(

        content=ft.Column(
            [
                ft.Text(
                    "Membres du groupe",
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),

                ft.Divider(
                    height=1
                ),

                tableau_noms
            ],

            spacing=5
        ),

        padding=10,

        border_radius=10,

        bgcolor=ft.Colors.GREY_100,

        width=470
    )

    # =====================================================
    # CARTE CLIENTS
    # =====================================================

    carte_clients = ft.Container(

        content=ft.Column(
            [
                ft.Text(
                    "Clients",
                    size=18
                ),

                nombre_clients
            ]
        ),

        bgcolor=ft.Colors.BLUE_100,

        padding=20,

        border_radius=10,

        col={
            "sm": 6,
            "md": 3
        }
    )

    # =====================================================
    # CARTE COMPTES
    # =====================================================

    carte_comptes = ft.Container(

        content=ft.Column(
            [
                ft.Text(
                    "Comptes",
                    size=18
                ),

                nombre_comptes
            ]
        ),

        bgcolor=ft.Colors.GREEN_100,

        padding=20,

        border_radius=10,

        col={
            "sm": 6,
            "md": 3
        }
    )

    # =====================================================
    # CARTE MOUVEMENTS
    # =====================================================

    carte_transactions = ft.Container(

        content=ft.Column(
            [
                ft.Text(
                    "Mouvements",
                    size=18
                ),

                nombre_transactions
            ]
        ),

        bgcolor=ft.Colors.ORANGE_100,

        padding=20,

        border_radius=10,

        col={
            "sm": 6,
            "md": 3
        }
    )

    # =====================================================
    # CARTE SOLDE
    # =====================================================

    carte_solde = ft.Container(

        content=ft.Column(
            [
                ft.Text(
                    "Solde total",
                    size=18
                ),

                solde_total
            ]
        ),

        bgcolor=ft.Colors.PURPLE_100,

        padding=20,

        border_radius=10,

        col={
            "sm": 6,
            "md": 3
        }
    )

    # =====================================================
    # CARTES
    # =====================================================

    cards = ft.ResponsiveRow(
        controls=[
            carte_clients,
            carte_comptes,
            carte_transactions,
            carte_solde
        ]
    )

    # =====================================================
    # CONTENU
    # =====================================================

    contenu = ft.Container(
        expand=True,
        padding=20
    )

    # =====================================================
    # ACCUEIL
    # =====================================================

    def accueil():

        charger_statistiques()

        contenu.content = ft.Column(

            [
                title,

                ft.Divider(),

                cards,

                ft.Divider(),

                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    "Bienvenue dans BANK SYSTEM.",
                                    size=20,
                                    weight=ft.FontWeight.BOLD
                                ),

                                ft.Text(
                                    "Gestion des clients, comptes, "
                                    "dépôts, retraits, virements "
                                    "et relevés de comptes.",
                                    size=17
                                )
                            ],

                            expand=True
                        ),

                        # =================================
                        # TABLEAU DES MEMBRES
                        # =================================

                        bloc_noms
                    ],

                    vertical_alignment=ft.CrossAxisAlignment.START,

                    spacing=20
                )
            ],

            scroll=ft.ScrollMode.AUTO,

            expand=True
        )

        page.update()

    # =====================================================
    # DÉCONNEXION
    # =====================================================

    def deconnecter(e):

        page.clean()

        from login import login_view

        page.add(
            login_view(page)
        )

        page.update()

    # =====================================================
    # CHANGEMENT MENU
    # =====================================================

    def changer_menu(e):

        index = menu.selected_index

        # =================================================
        # ACCUEIL
        # =================================================

        if index == 0:

            accueil()

        # =================================================
        # CLIENTS
        # =================================================

        elif index == 1:

            contenu.content = clients_view(page)

            page.update()

        # =================================================
        # COMPTES
        # =================================================

        elif index == 2:

            contenu.content = comptes_view(page)

            page.update()

        # =================================================
        # DÉPÔT
        # =================================================

        elif index == 3:

            contenu.content = depot_view(page)

            page.update()

        # =================================================
        # RETRAIT
        # =================================================

        elif index == 4:

            contenu.content = retrait_view(page)

            page.update()

        # =================================================
        # VIREMENT
        # =================================================

        elif index == 5:

            contenu.content = virement_view(page)

            page.update()

        # =================================================
        # HISTORIQUE
        # =================================================

        elif index == 6:

            contenu.content = historique_view(page)

            page.update()

        # =================================================
        # DÉCONNEXION
        # =================================================

        elif index == 7:

            deconnecter(e)

    # =====================================================
    # MENU
    # =====================================================

    menu = ft.NavigationRail(

        selected_index=0,

        label_type=ft.NavigationRailLabelType.ALL,

        on_change=changer_menu,

        destinations=[

            ft.NavigationRailDestination(
                icon=ft.Icons.HOME,
                label="Accueil"
            ),

            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE,
                label="Clients"
            ),

            ft.NavigationRailDestination(
                icon=ft.Icons.ACCOUNT_BALANCE,
                label="Comptes"
            ),

            ft.NavigationRailDestination(
                icon=ft.Icons.SAVINGS,
                label="Dépôt"
            ),

            ft.NavigationRailDestination(
                icon=ft.Icons.MONEY_OFF,
                label="Retrait"
            ),

            ft.NavigationRailDestination(
                icon=ft.Icons.SWAP_HORIZ,
                label="Virement"
            ),

            ft.NavigationRailDestination(
                icon=ft.Icons.HISTORY,
                label="Historique"
            ),

            ft.NavigationRailDestination(
                icon=ft.Icons.LOGOUT,
                label="Déconnexion"
            )
        ]
    )

    # =====================================================
    # CHARGEMENT INITIAL
    # =====================================================

    accueil()

    # =====================================================
    # AFFICHAGE
    # =====================================================

    return ft.Row(

        controls=[

            menu,

            ft.VerticalDivider(
                width=1
            ),

            contenu
        ],

        expand=True
    )