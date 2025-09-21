import requests

username = "juniorsatanas"

archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
archives = requests.get(archives_url, headers={"User-Agent": "Mozilla/5.0"}).json()["archives"]

with open("todas_partidas.pgn", "w", encoding="utf-8") as f:
    for url in archives:
        pgn_url = url + "/pgn"
        r = requests.get(pgn_url, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and r.text.strip():
            f.write(r.text + "\n")
            print(f"✅ Baixado: {pgn_url}")
        else:
            print(f"⚠️ Erro ou vazio: {pgn_url}")

print("🎉 Arquivo final: todas_partidas.pgn")
