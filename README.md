# Python Music Player

Aplicativo Python/Kivy para tocar músicas salvas no Android.

## Arquivos principais

- `main.py`: código do aplicativo.
- `buildozer.spec`: configuração para gerar APK Android.
- `requirements.txt`: dependências para testar no computador.
- `.github/workflows/build-apk.yml`: automação do GitHub Actions para gerar o APK na nuvem.

## Como gerar o APK pelo GitHub

1. Crie um repositório no GitHub.
2. Envie estes arquivos para o repositório.
3. Abra a aba Actions.
4. Rode o workflow `Build Android APK`.
5. Baixe o artifact `music-player-apk`.
6. Extraia o ZIP baixado.
7. Instale o APK no Android.
