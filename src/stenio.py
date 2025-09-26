import re
import chess.pgn
from collections import Counter, defaultdict
import io
import requests
import time
from datetime import datetime, timedelta
import json


class ChessComDownloader:
    def __init__(self, username):
        self.username = username.lower()
        self.base_url = "https://api.chess.com/pub/player"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
        }

    def get_available_archives(self):
        """Obtém lista de arquivos mensais disponíveis"""
        url = f"{self.base_url}/{self.username}/games/archives"
        try:
            print(f"🔗 Tentando acessar: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            print(f"📡 Status da resposta: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                archives = data.get('archives', [])
                print(f"✅ Encontrados {len(archives)} arquivos mensais")
                return archives
            elif response.status_code == 403:
                print("❌ Acesso negado (403) - A API pode estar bloqueando requisições")
                print("💡 SOLUÇÃO ALTERNATIVA:")
                print("   1. Acesse: https://www.chess.com/member/steniosousa")
                print("   2. Vá para a aba 'Games'")
                print("   3. Clique em 'Download' e baixe o arquivo PGN")
                print("   4. Use o método: analyze_from_pgn_file('arquivo.pgn', 'steniosousa')")
                return []
            elif response.status_code == 404:
                print("❌ Usuário não encontrado (404)")
                print("💡 Verifique se o nome do usuário está correto")
                return []
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return []
        except requests.exceptions.Timeout:
            print("❌ Timeout na conexão - tente novamente")
            return []
        except requests.exceptions.ConnectionError:
            print("❌ Erro de conexão - verifique sua internet")
            return []
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return []

    def download_month_games(self, archive_url):
        """Baixa jogos de um mês específico"""
        try:
            print(f"📥 Baixando: {archive_url}")
            response = requests.get(archive_url, headers=self.headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                games = data.get('games', [])
                print(f"✅ {len(games)} jogos baixados")
                return games
            else:
                print(f"❌ Erro ao baixar jogos: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Erro ao baixar: {e}")
            return []

    def download_recent_games(self, months=6):
        """Baixa jogos dos últimos N meses"""
        print(f"🔄 Baixando jogos dos últimos {months} meses para {self.username}...")

        archives = self.get_available_archives()
        if not archives:
            print("\n" + "=" * 60)
            print("📋 INSTRUÇÕES PARA DOWNLOAD MANUAL:")
            print("=" * 60)
            print(f"1. Acesse: https://www.chess.com/member/{self.username}")
            print("2. Clique na aba 'Games' ou 'Partidas'")
            print("3. Clique no botão 'Download' (ícone de seta para baixo)")
            print("4. Baixe o arquivo .pgn")
            print("5. Execute: analyze_from_pgn_file('arquivo.pgn', 'steniosousa')")
            print("=" * 60)
            return []

        # Pegar apenas os últimos N meses
        recent_archives = archives[-months:] if len(archives) > months else archives
        print(f"📂 Processando {len(recent_archives)} arquivos mensais...")

        all_games = []
        for i, archive in enumerate(recent_archives, 1):
            print(f"📥 Baixando arquivo {i}/{len(recent_archives)}...")
            games = self.download_month_games(archive)
            all_games.extend(games)
            time.sleep(0.5)  # Rate limiting mais conservador

        print(f"✅ Total de jogos baixados: {len(all_games)}")
        return all_games

    def convert_to_pgn(self, games):
        """Converte jogos JSON para formato PGN"""
        pgn_content = ""

        for game in games:
            try:
                # Extrair informações do jogo
                white = game.get('white', {}).get('username', 'Unknown')
                black = game.get('black', {}).get('username', 'Unknown')
                white_rating = game.get('white', {}).get('rating', 0)
                black_rating = game.get('black', {}).get('rating', 0)

                result = "1/2-1/2"
                if game.get('white', {}).get('result') == 'win':
                    result = "1-0"
                elif game.get('black', {}).get('result') == 'win':
                    result = "0-1"

                # Converter timestamp para data
                end_time = game.get('end_time', 0)
                date = datetime.fromtimestamp(end_time).strftime('%Y.%m.%d') if end_time else '????.??.??'

                time_control = game.get('time_control', 'unknown')
                rules = game.get('rules', 'chess')
                pgn_text = game.get('pgn', '')

                # Construir PGN
                pgn_game = f"""[Event "Chess.com"]
[Site "Chess.com"]
[Date "{date}"]
[Round "-"]
[White "{white}"]
[Black "{black}"]
[Result "{result}"]
[WhiteElo "{white_rating}"]
[BlackElo "{black_rating}"]
[TimeControl "{time_control}"]
[Termination "{game.get('white', {}).get('result', 'unknown')}"]

{pgn_text}

"""
                pgn_content += pgn_game
            except Exception as e:
                print(f"⚠️ Erro ao converter jogo: {e}")
                continue

        return pgn_content


class PGNAnalyzer:
    def __init__(self, pgn_content, player_name):
        self.pgn_content = pgn_content
        self.player_name = player_name.lower()
        self.games = []
        self.parse_pgn()

    def identify_opening(self, moves):
        """Identifica a abertura pelos primeiros lances"""
        if not moves or len(moves) < 2:
            return "Partida muito curta"

        try:
            first_move = moves[0] if moves else ""
            second_move = moves[1] if len(moves) > 1 else ""

            if first_move == 'e2e4':
                if second_move == 'e7e5':
                    if len(moves) >= 3:
                        third_move = moves[2]
                        if third_move == 'g1f3':
                            if len(moves) >= 4:
                                fourth_move = moves[3]
                                if fourth_move == 'b8c6':
                                    if len(moves) >= 5:
                                        fifth_move = moves[4]
                                        if fifth_move == 'f1b5':
                                            return "Ruy Lopez"
                                        elif fifth_move == 'f1c4':
                                            return "Italian Game"
                                        elif fifth_move == 'd2d3':
                                            return "King's Indian Attack"
                                    return "King's Knight Opening"
                                elif fourth_move == 'g8f6':
                                    return "Petroff Defense"
                            return "King's Knight Opening"
                        elif third_move == 'f2f4':
                            return "King's Gambit"
                        elif third_move == 'b1c3':
                            return "Vienna Game"
                        elif third_move == 'd2d4':
                            return "Center Game"
                    return "King's Pawn Game"
                elif second_move == 'c7c5':
                    if len(moves) >= 3:
                        third_move = moves[2]
                        if third_move == 'g1f3':
                            return "Sicilian Defense"
                        elif third_move == 'b1c3':
                            return "Sicilian Closed"
                        elif third_move == 'f2f4':
                            return "Sicilian Grand Prix"
                        elif third_move == 'c2c3':
                            return "Sicilian Alapin"
                    return "Sicilian Defense"
                elif second_move == 'c7c6':
                    return "Caro-Kann Defense"
                elif second_move == 'd7d6':
                    return "Pirc Defense"
                elif second_move == 'g8f6':
                    return "Alekhine's Defense"
                elif second_move == 'd7d5':
                    return "Scandinavian Defense"
                elif second_move == 'g7g6':
                    return "Modern Defense"
                elif second_move == 'e7e6':
                    return "French Defense"
                else:
                    return "King's Pawn Opening"

            elif first_move == 'd2d4':
                if second_move == 'd7d5':
                    if len(moves) >= 3 and moves[2] == 'c2c4':
                        return "Queen's Gambit"
                    elif len(moves) >= 3 and moves[2] == 'g1f3':
                        return "Queen's Pawn Game"
                    elif len(moves) >= 3 and moves[2] == 'e2e3':
                        return "Colle System"
                    return "Queen's Pawn Game"
                elif second_move == 'g8f6':
                    if len(moves) >= 4:
                        third_move = moves[2]
                        fourth_move = moves[3]
                        if third_move == 'c2c4':
                            if fourth_move == 'e7e6':
                                return "Nimzo-Indian Defense"
                            elif fourth_move == 'g7g6':
                                return "King's Indian Defense"
                        elif third_move == 'g1f3' and fourth_move == 'g7g6':
                            return "King's Indian Attack"
                    return "Indian Defense"
                elif second_move == 'f7f5':
                    return "Dutch Defense"
                elif second_move == 'e7e6':
                    return "Queen's Pawn Game"
                else:
                    return "Queen's Pawn Opening"

            elif first_move == 'g1f3':
                if second_move == 'd7d5':
                    return "Réti Opening"
                elif second_move == 'g8f6':
                    if len(moves) >= 3:
                        third_move = moves[2]
                        if third_move == 'c2c4':
                            return "English Opening"
                        elif third_move == 'd2d4':
                            return "Queen's Pawn Game"
                        elif third_move == 'g2g3':
                            return "King's Indian Attack"
                    return "Réti Opening"
                elif second_move == 'c7c5':
                    return "English Opening"
                else:
                    return "Réti Opening"

            elif first_move == 'c2c4':
                if second_move == 'e7e5':
                    return "English Opening"
                elif second_move == 'g8f6':
                    return "English Opening"
                elif second_move == 'c7c5':
                    return "English Symmetrical"
                else:
                    return "English Opening"

            elif first_move == 'f2f4':
                return "Bird's Opening"
            elif first_move == 'b2b3':
                return "Nimzowitsch-Larsen Attack"
            elif first_move == 'g2g3':
                return "Benko's Opening"
            elif first_move == 'b1c3':
                return "Van't Kruijs Opening"
            else:
                return "Irregular Opening"

        except Exception as e:
            print(f"Erro na identificação de abertura: {e}")
            return "Unknown Opening"

    def parse_pgn(self):
        """Parse o conteúdo PGN e extrai informações das partidas"""
        pgn_io = io.StringIO(self.pgn_content)

        while True:
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break

                white = game.headers.get("White", "").lower()
                black = game.headers.get("Black", "").lower()
                result = game.headers.get("Result", "")
                white_elo = game.headers.get("WhiteElo", "0")
                black_elo = game.headers.get("BlackElo", "0")
                eco = game.headers.get("ECO", "")
                date = game.headers.get("Date", "")

                # Converter moves para lista
                moves = []
                node = game
                while node.variations:
                    next_node = node.variation(0)
                    if next_node.move:
                        moves.append(next_node.move.uci())
                    node = next_node

                opening = self.identify_opening(moves)

                game_info = {
                    'white': white,
                    'black': black,
                    'result': result,
                    'white_elo': int(white_elo) if white_elo.isdigit() else 0,
                    'black_elo': int(black_elo) if black_elo.isdigit() else 0,
                    'opening': opening,
                    'eco': eco,
                    'moves': moves,
                    'date': date,
                    'game_length': len(moves) // 2,
                    'termination': game.headers.get("Termination", "Normal"),
                    'time_control': game.headers.get("TimeControl", "Unknown"),
                    'pgn_text': str(game)
                }

                if self.player_name in white or self.player_name in black:
                    self.games.append(game_info)

            except Exception as e:
                print(f"Erro ao processar partida: {e}")
                continue

    def is_player_white(self, game):
        return self.player_name in game['white']

    def did_player_win(self, game):
        is_white = self.is_player_white(game)
        return (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1')

    def did_player_lose(self, game):
        is_white = self.is_player_white(game)
        return (is_white and game['result'] == '0-1') or (not is_white and game['result'] == '1-0')

    def is_draw(self, game):
        return game['result'] == '1/2-1/2'

    def get_opening_stats(self):
        white_openings = []
        black_openings = []

        for game in self.games:
            if self.is_player_white(game):
                white_openings.append(game['opening'])
            else:
                black_openings.append(game['opening'])

        return Counter(white_openings), Counter(black_openings)

    def get_winning_openings(self):
        white_wins = defaultdict(int)
        black_wins = defaultdict(int)

        for game in self.games:
            if self.did_player_win(game):
                if self.is_player_white(game):
                    white_wins[game['opening']] += 1
                else:
                    black_wins[game['opening']] += 1

        return dict(white_wins), dict(black_wins)

    def get_losing_openings(self):
        """NOVA FUNCIONALIDADE: Analisa aberturas que mais perdeu"""
        white_losses = defaultdict(int)
        black_losses = defaultdict(int)

        for game in self.games:
            if self.did_player_lose(game):
                if self.is_player_white(game):
                    white_losses[game['opening']] += 1
                else:
                    black_losses[game['opening']] += 1

        return dict(white_losses), dict(black_losses)

    def get_opening_win_rates(self):
        """NOVA FUNCIONALIDADE: Calcula win rate por abertura"""
        white_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})
        black_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})

        for game in self.games:
            opening = game['opening']
            if self.is_player_white(game):
                if self.did_player_win(game):
                    white_stats[opening]['wins'] += 1
                elif self.did_player_lose(game):
                    white_stats[opening]['losses'] += 1
                elif self.is_draw(game):
                    white_stats[opening]['draws'] += 1
            else:
                if self.did_player_win(game):
                    black_stats[opening]['wins'] += 1
                elif self.did_player_lose(game):
                    black_stats[opening]['losses'] += 1
                elif self.is_draw(game):
                    black_stats[opening]['draws'] += 1

        # Calcular win rates
        white_win_rates = {}
        black_win_rates = {}

        for opening, stats in white_stats.items():
            total = stats['wins'] + stats['losses'] + stats['draws']
            if total >= 3:  # Só considerar aberturas com pelo menos 3 jogos
                win_rate = (stats['wins'] / total) * 100
                white_win_rates[opening] = {
                    'win_rate': win_rate,
                    'total_games': total,
                    **stats
                }

        for opening, stats in black_stats.items():
            total = stats['wins'] + stats['losses'] + stats['draws']
            if total >= 3:
                win_rate = (stats['wins'] / total) * 100
                black_win_rates[opening] = {
                    'win_rate': win_rate,
                    'total_games': total,
                    **stats
                }

        return white_win_rates, black_win_rates

    def analyze_performance_vs_rating(self):
        rating_ranges = {
            'Under 1200': (0, 1199),
            '1200-1399': (1200, 1399),
            '1400-1599': (1400, 1599),
            '1600-1799': (1600, 1799),
            '1800-1999': (1800, 1999),
            '2000+': (2000, 9999)
        }

        performance = {}

        for range_name, (min_rating, max_rating) in rating_ranges.items():
            wins = losses = draws = 0

            for game in self.games:
                is_white = self.is_player_white(game)
                opponent_rating = game['black_elo'] if is_white else game['white_elo']

                if min_rating <= opponent_rating <= max_rating:
                    if self.did_player_win(game):
                        wins += 1
                    elif self.did_player_lose(game):
                        losses += 1
                    elif self.is_draw(game):
                        draws += 1

            total = wins + losses + draws
            if total > 0:
                win_rate = (wins / total) * 100
                performance[range_name] = {
                    'wins': wins, 'losses': losses, 'draws': draws,
                    'total': total, 'win_rate': win_rate
                }

        return performance

    def get_top_defeated_opponents(self):
        defeated_opponents = []

        for game in self.games:
            date_str = game.get('date', '')
            year = 'N/A'
            if date_str and '.' in date_str:
                try:
                    year = date_str.split('.')[0]
                except:
                    year = 'N/A'

            if self.did_player_win(game):
                is_white = self.is_player_white(game)
                if is_white and game['black_elo'] > 0:
                    defeated_opponents.append({
                        'opponent': game['black'],
                        'rating': game['black_elo'],
                        'color': 'black',
                        'opening': game['opening'],
                        'year': year
                    })
                elif not is_white and game['white_elo'] > 0:
                    defeated_opponents.append({
                        'opponent': game['white'],
                        'rating': game['white_elo'],
                        'color': 'white',
                        'opening': game['opening'],
                        'year': year
                    })

        defeated_opponents.sort(key=lambda x: x['rating'], reverse=True)
        return defeated_opponents[:20]

    def generate_report(self):
        """Gera relatório completo da análise"""
        print("=" * 80)
        print(f"📊 RELATÓRIO COMPLETO DE ANÁLISE - {self.player_name.upper()}")
        print("=" * 80)
        print(f"Total de partidas analisadas: {len(self.games)}")
        print()

        # 1. Estatísticas básicas
        wins = losses = draws = 0
        for game in self.games:
            if self.did_player_win(game):
                wins += 1
            elif self.did_player_lose(game):
                losses += 1
            elif self.is_draw(game):
                draws += 1

        total_decided = wins + losses + draws
        if total_decided > 0:
            print("📈 ESTATÍSTICAS GERAIS:")
            print(f"• Vitórias: {wins} ({wins / total_decided * 100:.1f}%)")
            print(f"• Derrotas: {losses} ({losses / total_decided * 100:.1f}%)")
            print(f"• Empates: {draws} ({draws / total_decided * 100:.1f}%)")
            print(f"• Win Rate: {wins / total_decided * 100:.1f}%")
            print()

        # 2. Performance vs Rating
        perf_vs_rating = self.analyze_performance_vs_rating()
        print("🎯 PERFORMANCE VS RATING DOS OPONENTES:")
        for rating_range, stats in perf_vs_rating.items():
            print(f"• {rating_range}: {stats['wins']}/{stats['total']} "
                  f"({stats['win_rate']:.1f}% win rate)")
        print()

        # 3. Aberturas mais jogadas
        white_openings, black_openings = self.get_opening_stats()

        print("🔸 TOP 5 ABERTURAS MAIS JOGADAS DE BRANCAS:")
        for i, (opening, count) in enumerate(white_openings.most_common(5), 1):
            print(f"{i}. {opening}: {count} partidas")
        print()

        print("🔹 TOP 5 ABERTURAS MAIS JOGADAS DE PRETAS:")
        for i, (opening, count) in enumerate(black_openings.most_common(5), 1):
            print(f"{i}. {opening}: {count} partidas")
        print()

        # 4. Aberturas que mais ganharam
        white_wins, black_wins = self.get_winning_openings()

        print("🏆 TOP 3 ABERTURAS QUE MAIS GANHARAM DE BRANCAS:")
        for opening, wins_count in sorted(white_wins.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"• {opening}: {wins_count} vitórias")
        print()

        print("🏆 TOP 3 ABERTURAS QUE MAIS GANHARAM DE PRETAS:")
        for opening, wins_count in sorted(black_wins.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"• {opening}: {wins_count} vitórias")
        print()

        # 5. NOVA SEÇÃO: Aberturas que mais perdeu
        white_losses, black_losses = self.get_losing_openings()

        print("💔 TOP 3 ABERTURAS QUE MAIS PERDEU DE BRANCAS:")
        if white_losses:
            for opening, loss_count in sorted(white_losses.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"• {opening}: {loss_count} derrotas")
        else:
            print("• Nenhuma derrota significativa encontrada")
        print()

        print("💔 TOP 3 ABERTURAS QUE MAIS PERDEU DE PRETAS:")
        if black_losses:
            for opening, loss_count in sorted(black_losses.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"• {opening}: {loss_count} derrotas")
        else:
            print("• Nenhuma derrota significativa encontrada")
        print()

        # 6. NOVA SEÇÃO: Win rate por abertura
        white_rates, black_rates = self.get_opening_win_rates()

        print("📊 MELHORES WIN RATES DE BRANCAS (min 3 jogos):")
        if white_rates:
            sorted_rates = sorted(white_rates.items(), key=lambda x: x[1]['win_rate'], reverse=True)[:5]
            for opening, stats in sorted_rates:
                print(f"• {opening}: {stats['win_rate']:.1f}% ({stats['wins']}/{stats['total_games']})")
        print()

        print("📊 MELHORES WIN RATES DE PRETAS (min 3 jogos):")
        if black_rates:
            sorted_rates = sorted(black_rates.items(), key=lambda x: x[1]['win_rate'], reverse=True)[:5]
            for opening, stats in sorted_rates:
                print(f"• {opening}: {stats['win_rate']:.1f}% ({stats['wins']}/{stats['total_games']})")
        print()

        print("📉 PIORES WIN RATES DE BRANCAS (min 3 jogos):")
        if white_rates:
            sorted_rates = sorted(white_rates.items(), key=lambda x: x[1]['win_rate'])[:5]
            for opening, stats in sorted_rates:
                print(f"• {opening}: {stats['win_rate']:.1f}% ({stats['wins']}/{stats['total_games']})")
        print()

        print("📉 PIORES WIN RATES DE PRETAS (min 3 jogos):")
        if black_rates:
            sorted_rates = sorted(black_rates.items(), key=lambda x: x[1]['win_rate'])[:5]
            for opening, stats in sorted_rates:
                print(f"• {opening}: {stats['win_rate']:.1f}% ({stats['wins']}/{stats['total_games']})")
        print()

        # 7. Top oponentes derrotados
        top_defeated = self.get_top_defeated_opponents()
        print("👑 TOP 10 MAIORES RATINGS DERROTADOS:")
        for i, opponent in enumerate(top_defeated[:10], 1):
            year_info = f"({opponent['year']}) - " if opponent['year'] != 'N/A' else ""
            print(f"{i:2d}. {opponent['opponent']} - {opponent['rating']} {year_info}{opponent['opening']}")
        print()

        print("=" * 80)
        print("📝 RELATÓRIO COMPLETO FINALIZADO!")
        print("=" * 80)


def analyze_player_from_chesscom(username, months=6):
    """
    Baixa e analisa partidas de um jogador do Chess.com

    Args:
        username (str): Nome de usuário do Chess.com
        months (int): Número de meses para baixar (padrão: 6)
    """
    print(f"🚀 Iniciando análise completa do jogador: {username}")
    print(f"📥 Baixando partidas dos últimos {months} meses...")
    print("-" * 60)

    # 1. Baixar partidas
    downloader = ChessComDownloader(username)
    games = downloader.download_recent_games(months)

    if not games:
        print("❌ Nenhuma partida encontrada!")
        return None

    # 2. Converter para PGN
    print("🔄 Convertendo para formato PGN...")
    pgn_content = downloader.convert_to_pgn(games)

    # 3. Analisar
    print("📊 Analisando partidas...")
    analyzer = PGNAnalyzer(pgn_content, username)

    if not analyzer.games:
        print("❌ Nenhuma partida válida encontrada!")
        return None

    # 4. Gerar relatório
    analyzer.generate_report()

    return analyzer


def analyze_from_pgn_file(pgn_file_path, player_name):
    """
    Analisa partidas a partir de um arquivo PGN

    Args:
        pgn_file_path (str): Caminho para o arquivo PGN
        player_name (str): Nome do jogador para filtrar
    """
    try:
        with open(pgn_file_path, 'r', encoding='utf-8') as file:
            pgn_content = file.read()

        analyzer = PGNAnalyzer(pgn_content, player_name)
        analyzer.generate_report()
        return analyzer

    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {pgn_file_path}")
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")


# Execução principal
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        username = sys.argv[1]
        months = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    else:
        username = "steniosousa"  # Padrão
        months = 6

    print("🔍 ANALISADOR COMPLETO DE XADREZ")
    print("=" * 50)
    print(f"🎯 Jogador: {username}")
    print(f"📅 Período: últimos {months} meses")
    print("=" * 50)

    # Tentar download automático primeiro
    print("🤖 TENTANDO DOWNLOAD AUTOMÁTICO...")
    analyzer = analyze_player_from_chesscom(username, months)

    if not analyzer:
        print("\n" + "=" * 60)
        print("⚠️  DOWNLOAD AUTOMÁTICO FALHOU!")
        print("=" * 60)
        print("📋 OPÇÕES ALTERNATIVAS:")
        print()
        print("OPÇÃO 1 - Download manual do Chess.com:")
        print(f"  1. Acesse: https://www.chess.com/member/{username}")
        print("  2. Aba 'Games' → Botão 'Download'")
        print("  3. Salve como 'games.pgn'")
        print(f"  4. Execute: analyze_from_pgn_file('games.pgn', '{username}')")
        print()
        print("OPÇÃO 2 - Se você já tem o arquivo PGN:")
        print(f"  analyze_from_pgn_file('seu_arquivo.pgn', '{username}')")
        print()
        print("OPÇÃO 3 - Testar com outro jogador:")
        print("  python script.py outro_username")
        print("=" * 60)

        # Tentar com arquivo local se existir
        import os

        possible_files = [f'{username}.pgn', 'games.pgn', f'{username}_games.pgn']

        for filename in possible_files:
            if os.path.exists(filename):
                print(f"\n🎉 Arquivo encontrado: {filename}")
                print("📊 Analisando arquivo local...")
                analyzer = analyze_from_pgn_file(filename, username)
                if analyzer:
                    print(f"\n✅ Análise concluída! {len(analyzer.games)} partidas processadas.")
                break
        else:
            print(f"\n❌ Nenhum arquivo PGN encontrado localmente.")
            print(f"💡 Crie um arquivo '{username}.pgn' com as partidas do jogador.")
    else:
        print(f"\n✅ Análise concluída! {len(analyzer.games)} partidas processadas.")