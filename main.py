import flet as ft
import requests

# Subtitua pela URL do seu backend rodando na nuvem
BACKEND_URL = "https://globalhistoricalsatelitedata.streamlit.app/"

def main(page: ft.Page):
    page.title = "GOES Satélite"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0b0f19"
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # 1. Indicador de Carregamento (Spinner animado)
    loading_spinner = ft.ProgressRing(visible=False, width=50, height=50, color=ft.colors.BLUE_400)
    status_text = ft.Text("Aguardando solicitação...", color=ft.colors.GREY_400, size=14)
    
    # 2. Exibição da Imagem de Satélite
    image_display = ft.Image(visible=False, width=360, height=360, fit=ft.ImageFit.CONTAIN)

    def processar_imagem(e):
        # Exibe o indicador de carregamento animado
        loading_spinner.visible = True
        status_text.value = "⏳ Conectando e processando dados do satélite..."
        status_text.color = ft.colors.BLUE_200
        image_display.visible = False
        btn_gerar.disabled = True
        page.update()

        try:
            # Solicita a imagem gerada pelo backend
            response = requests.get(f"{BACKEND_URL}/goes_result.png", timeout=60)
            
            if response.status_code == 200:
                # Atualiza e mostra a imagem capturada
                image_display.src_base64 = response.content.hex() # Ou passa a URL direta se for link estático
                image_display.src = f"{BACKEND_URL}/goes_result.png"
                image_display.visible = True
                status_text.value = "✅ Imagem de Satélite Atualizada!"
                status_text.color = ft.colors.GREEN_400
            else:
                status_text.value = f"⚠️ Erro ao buscar imagem ({response.status_code})"
                status_text.color = ft.colors.RED_400
        except Exception as err:
            status_text.value = f"❌ Erro de Conexão: {str(err)}"
            status_text.color = ft.colors.RED_400
        finally:
            loading_spinner.visible = False
            btn_gerar.disabled = False
            page.update()

    # Botão com visual moderno
    btn_gerar = ft.ElevatedButton(
        text="🚀 Carregar Satélite",
        on_click=processar_imagem,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.BLUE_600,
            padding=18,
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )

    # Layout nativo da tela
    page.add(
        ft.Text("🛰️ Monitor Satelital GOES", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
        ft.Text("Visualização NAE / GOES-16 e GOES-19", size=12, color=ft.colors.GREY_500),
        ft.Divider(height=25, color=ft.colors.TRANSPARENT),
        btn_gerar,
        ft.Divider(height=20, color=ft.colors.TRANSPARENT),
        loading_spinner,
        ft.Divider(height=10, color=ft.colors.TRANSPARENT),
        status_text,
        ft.Divider(height=20, color=ft.colors.TRANSPARENT),
        image_display
    )

ft.app(target=main)
