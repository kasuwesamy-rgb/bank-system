import flet as ft
from database import connect_db


def clients_view(page: ft.Page):

    # ==============================
    # CHAMPS DU FORMULAIRE
    # ==============================

    id_client = ft.TextField(
        label="ID du client",
        width=400,
        visible=False
    )

    nom = ft.TextField(
        label="Nom",
        width=400
    )

    postnom = ft.TextField(
        label="Postnom",
        width=400
    )

    prenom = ft.TextField(
        label="Prénom",
        width=400
    )

    telephone = ft.TextField(
        label="Téléphone",
        width=400
    )

    adresse = ft.TextField(
        label="Adresse",
        width=400
    )

    message = ft.Text("")

    # ==============================
    # TABLEAU DES CLIENTS
    # ==============================

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nom")),
            ft.DataColumn(ft.Text("Postnom")),
            ft.DataColumn(ft.Text("Prénom")),
            ft.DataColumn(ft.Text("Téléphone")),
            ft.DataColumn(ft.Text("Adresse")),
            ft.DataColumn(ft.Text("Actions")),
        ],
        rows=[]
    )

    # ==============================
    # VIDER LES CHAMPS
    # ==============================

    def vider_champs():
        id_client.value = ""
        nom.value = ""
        postnom.value = ""
        prenom.value = ""
        telephone.value = ""
        adresse.value = ""

    # ==============================
    # CHARGER LES CLIENTS
    # ==============================

    def charger_clients():

        table.rows.clear()

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    nom,
                    postnom,
                    prenom,
                    telephone,
                    adresse
                FROM clients
                ORDER BY id DESC
            """)

            clients = cursor.fetchall()

            for client in clients:

                client_id = client[0]
                nom_client = client[1] or ""
                postnom_client = client[2] or ""
                prenom_client = client[3] or ""
                telephone_client = client[4] or ""
                adresse_client = client[5] or ""

                # Bouton modifier
                bouton_modifier = ft.ElevatedButton(
                    "Modifier",
                    on_click=lambda e, c=client: remplir_formulaire(c)
                )

                # Bouton supprimer
                bouton_supprimer = ft.ElevatedButton(
                    "Supprimer",
                    on_click=lambda e, cid=client_id: supprimer_client(cid)
                )

                actions = ft.Row(
                    [
                        bouton_modifier,
                        bouton_supprimer
                    ],
                    spacing=5
                )

                table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Text(str(client_id))
                            ),

                            ft.DataCell(
                                ft.Text(nom_client)
                            ),

                            ft.DataCell(
                                ft.Text(postnom_client)
                            ),

                            ft.DataCell(
                                ft.Text(prenom_client)
                            ),

                            ft.DataCell(
                                ft.Text(telephone_client)
                            ),

                            ft.DataCell(
                                ft.Text(adresse_client)
                            ),

                            ft.DataCell(
                                actions
                            ),
                        ]
                    )
                )

            cursor.close()
            conn.close()

            page.update()

        except Exception as erreur:

            message.value = f"Erreur : {erreur}"
            page.update()

    # ==============================
    # REMPLIR LE FORMULAIRE
    # ==============================

    def remplir_formulaire(client):

        id_client.value = str(client[0])
        nom.value = client[1] or ""
        postnom.value = client[2] or ""
        prenom.value = client[3] or ""
        telephone.value = client[4] or ""
        adresse.value = client[5] or ""

        message.value = "Client sélectionné pour modification."
        message.color = ft.Colors.BLUE

        page.update()

    # ==============================
    # ENREGISTRER CLIENT
    # ==============================

    def enregistrer_client(e):

        if nom.value.strip() == "":
            message.value = "Veuillez saisir le nom du client."
            message.color = ft.Colors.RED
            page.update()
            return

        try:

            conn = connect_db()
            cursor = conn.cursor()

            sql = """
                INSERT INTO clients
                (
                    nom,
                    postnom,
                    prenom,
                    telephone,
                    adresse
                )
                VALUES (%s, %s, %s, %s, %s)
            """

            valeurs = (
                nom.value.strip(),
                postnom.value.strip(),
                prenom.value.strip(),
                telephone.value.strip(),
                adresse.value.strip()
            )

            cursor.execute(sql, valeurs)

            conn.commit()

            cursor.close()
            conn.close()

            vider_champs()

            message.value = "Client enregistré avec succès."
            message.color = ft.Colors.GREEN

            charger_clients()

        except Exception as erreur:

            message.value = f"Erreur lors de l'enregistrement : {erreur}"
            message.color = ft.Colors.RED

            page.update()

    # ==============================
    # MODIFIER CLIENT
    # ==============================

    def modifier_client(e):

        if id_client.value.strip() == "":
            message.value = "Sélectionnez d'abord un client."
            message.color = ft.Colors.RED
            page.update()
            return

        if nom.value.strip() == "":
            message.value = "Veuillez saisir le nom."
            message.color = ft.Colors.RED
            page.update()
            return

        try:

            conn = connect_db()
            cursor = conn.cursor()

            sql = """
                UPDATE clients
                SET
                    nom = %s,
                    postnom = %s,
                    prenom = %s,
                    telephone = %s,
                    adresse = %s
                WHERE id = %s
            """

            valeurs = (
                nom.value.strip(),
                postnom.value.strip(),
                prenom.value.strip(),
                telephone.value.strip(),
                adresse.value.strip(),
                int(id_client.value)
            )

            cursor.execute(sql, valeurs)

            conn.commit()

            cursor.close()
            conn.close()

            vider_champs()

            message.value = "Client modifié avec succès."
            message.color = ft.Colors.GREEN

            charger_clients()

        except Exception as erreur:

            message.value = f"Erreur lors de la modification : {erreur}"
            message.color = ft.Colors.RED

            page.update()

    # ==============================
    # SUPPRIMER CLIENT
    # ==============================

    def supprimer_client(client_id):

        try:

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM clients WHERE id = %s",
                (client_id,)
            )

            conn.commit()

            cursor.close()
            conn.close()

            message.value = "Client supprimé avec succès."
            message.color = ft.Colors.GREEN

            charger_clients()

        except Exception as erreur:

            message.value = (
                f"Impossible de supprimer le client : {erreur}"
            )

            message.color = ft.Colors.RED

            page.update()

    # ==============================
    # BOUTONS
    # ==============================

    bouton_enregistrer = ft.ElevatedButton(
        "Enregistrer",
        on_click=enregistrer_client
    )

    bouton_modifier = ft.ElevatedButton(
        "Modifier",
        on_click=modifier_client
    )

    bouton_actualiser = ft.ElevatedButton(
        "Actualiser",
        on_click=lambda e: charger_clients()
    )

    bouton_nouveau = ft.ElevatedButton(
        "Nouveau",
        on_click=lambda e: (
            vider_champs(),
            page.update()
        )
    )

    # ==============================
    # FORMULAIRE
    # ==============================

    formulaire = ft.Column(
        [
            ft.Text(
                "INFORMATIONS DU CLIENT",
                size=20,
                weight=ft.FontWeight.BOLD
            ),

            id_client,
            nom,
            postnom,
            prenom,
            telephone,
            adresse,

            ft.Row(
                [
                    bouton_enregistrer,
                    bouton_modifier,
                    bouton_nouveau,
                    bouton_actualiser
                ],
                spacing=10
            ),

            message
        ],
        spacing=10
    )

    # ==============================
    # AFFICHAGE FINAL
    # ==============================

    page_clients = ft.Column(
        [
            ft.Text(
                "GESTION DES CLIENTS",
                size=28,
                weight=ft.FontWeight.BOLD
            ),

            ft.Divider(),

            formulaire,

            ft.Divider(),

            ft.Text(
                "LISTE DES CLIENTS",
                size=20,
                weight=ft.FontWeight.BOLD
            ),

            ft.Row(
                [
                    table
                ],
                scroll=ft.ScrollMode.AUTO
            )
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )

    # Charger les clients au démarrage
    charger_clients()

    return page_clients