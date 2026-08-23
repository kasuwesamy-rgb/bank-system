import flet as ft
from database import connect_db
from dashboard import dashboard

def login_view(page: ft.Page):

    username = ft.TextField(label="Nom d'utilisateur")
    password = ft.TextField(label="Mot de passe", password=True)

    message = ft.Text()

    def login(e):
        conn = connect_db()
        cursor = conn.cursor()

        sql = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(sql, (username.value, password.value))

        user = cursor.fetchone()

        if user:
            page.clean()              # Efface la page de connexion
            page.add(dashboard(page)) # Affiche le tableau de bord
        else:
            message.value = "Nom d'utilisateur ou mot de passe incorrect"
            message.color = "red"
            page.update()

        cursor.close()
        conn.close()

    return ft.Column(
        [
            ft.Text(
                "BANK SYSTEM",
                size=30,
                weight=ft.FontWeight.BOLD
            ),
            username,
            password,
            ft.ElevatedButton(
                "Se connecter",
                on_click=login
            ),
            message
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )