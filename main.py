import flet as ft
from login import login_view

def main(page: ft.Page):
    page.title = "BANK SYSTEM"
    page.window.width = 500
    page.window.height = 600

    page.add(login_view(page))

ft.app(target=main)