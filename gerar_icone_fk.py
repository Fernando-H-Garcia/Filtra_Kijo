# gerar_icone_fk.py — Gera ícone FK em .ico
from PIL import Image, ImageDraw, ImageFont
import os

def criar_icone_fk(caminho_saida):
    """Cria um ícone FK nítido para Explorer + barra de tarefas (evita embaçado)."""
    # Inclui tamanhos que o Windows usa na barra de tarefas / Alt-Tab / DPI alto
    tamanhos = [256, 128, 64, 48, 32, 24, 20, 16]
    imagens = []

    for tam in tamanhos:
        img = Image.new('RGBA', (tam, tam), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Fundo: gradiente suave só para tamanhos maiores; sólido para pequenos (evita ruído)
        if tam >= 48:
            for y in range(tam):
                r = int(18 + (y / tam) * 14)
                g = int(58 + (y / tam) * 38)
                b = int(138 + (y / tam) * 58)
                draw.line([(0, y), (tam - 1, y)], fill=(r, g, b, 255))
        else:
            # Sólido para 16-32: mais nítido em tamanho pequeno
            draw.rectangle([(0, 0), (tam - 1, tam - 1)], fill=(28, 78, 168, 255))

        # Cantos arredondados (máscara)
        raio = max(tam // 6, 2)
        mascara = Image.new('L', (tam, tam), 0)
        draw_mask = ImageDraw.Draw(mascara)
        draw_mask.rounded_rectangle(
            [(0, 0), (tam - 1, tam - 1)],
            radius=raio,
            fill=255
        )
        img.putalpha(mascara)

        # Texto FK: maior e em negrito para nitidez (0.58-0.62)
        if tam >= 64:
            font_size = int(tam * 0.58)
        elif tam >= 32:
            font_size = int(tam * 0.62)
        else:
            font_size = int(tam * 0.60)

        font = None
        for cand in ["C:/Windows/Fonts/arialbd.ttf", "arialbd.ttf", "C:/Windows/Fonts/arial.ttf", "arial.ttf"]:
            try:
                font = ImageFont.truetype(cand, font_size)
                break
            except OSError:
                continue
        if font is None:
            font = ImageFont.load_default()

        texto = "FK"
        # Centralização precisa com bbox
        bbox = draw.textbbox((0, 0), texto, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (tam - tw) // 2 - bbox[0]
        y = (tam - th) // 2 - bbox[1]
        # Ajuste vertical fino para central óptica
        y -= max(1, tam // 32)

        # Sombra: só para tamanhos médios/grandes (em 16-24 a sombra embaça)
        if tam >= 48:
            draw.text((x + 1, y + 1), texto, fill=(0, 0, 0, 90), font=font)
        elif tam >= 32:
            draw.text((x + 1, y + 1), texto, fill=(0, 0, 0, 60), font=font)

        # Texto principal com leve contorno para contraste em DPI alto
        # stroke só em tamanhos grandes para não engrossar demais
        if tam >= 48:
            draw.text((x, y), texto, fill=(255, 255, 255, 255), font=font, stroke_width=max(1, tam // 64), stroke_fill=(255,255,255,255))
        else:
            draw.text((x, y), texto, fill=(255, 255, 255, 255), font=font)

        imagens.append(img)

    # Salva como .ico com múltiplos tamanhos
    imagens[0].save(
        caminho_saida,
        format='ICO',
        sizes=[(t, t) for t in tamanhos],
        append_images=imagens[1:]
    )
    print(f"Icone criado: {caminho_saida}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(script_dir, "fk_icon.ico")
    criar_icone_fk(caminho)
