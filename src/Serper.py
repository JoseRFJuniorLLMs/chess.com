import re
import chess.pgn
from collections import Counter, defaultdict
import io
import sys


class PGNAnalyzer:
    def __init__(self, pgn_content, player_name):
        self.pgn_content = pgn_content
        self.player_name = player_name.lower()
        self.games = []
        self.parse_pgn()

    def identify_opening(self, moves):
        if not moves or len(moves) < 2:
            return "Partida muito curta"
        try:
            first_move = moves[0]
            second_move = moves[1] if len(moves) > 1 else ""
            if first_move == 'e2e4':
                if second_move == 'e7e5':
                    if len(moves) >= 3 and moves[2] == 'g1f3':
                        if len(moves) >= 4 and moves[3] == 'b8c6':
                            if len(moves) >= 5 and moves[4] == 'f1b5':
                                return "Ruy Lopez"
                            if len(moves) >= 5 and moves[4] == 'f1c4':
                                return "Italian Game"
                            return "King's Knight Opening"
                        if len(moves) >= 4 and moves[3] == 'g8f6':
                            return "Petroff Defense"
                    if len(moves) >= 3 and moves[2] == 'f2f4':
                        return "King's Gambit"
                    return "King's Pawn Game"
                if second_move == 'c7c5': return "Sicilian Defense"
                if second_move == 'c7c6': return "Caro-Kann Defense"
                if second_move == 'd7d6': return "Pirc Defense"
                if second_move == 'e7e6': return "French Defense"
            if first_move == 'd2d4':
                if second_move == 'd7d5':
                    if len(moves) >= 3 and moves[2] == 'c2c4': return "Queen's Gambit"
                    return "Queen's Pawn Game"
                if second_move == 'g8f6':
                    if len(moves) >= 4 and moves[2] == 'c2c4':
                        if moves[3] == 'e7e6': return "Nimzo-Indian Defense"
                        if moves[3] == 'g7g6': return "King's Indian Defense"
                    return "Indian Defense"
            if first_move == 'g1f3': return "Réti Opening"
            if first_move == 'c2c4': return "English Opening"
            if first_move == 'f2f4': return "Bird's Opening"
            return "Irregular Opening"
        except Exception:
            return "Unknown Opening"

    def parse_pgn(self):
        pgn_io = io.StringIO(self.pgn_content)
        while True:
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break

                white = game.headers.get("White", "").lower()
                black = game.headers.get("Black", "").lower()
                if self.player_name not in white and self.player_name not in black:
                    continue

                result = game.headers.get("Result", "")
                white_elo = game.headers.get("WhiteElo", "0")
                black_elo = game.headers.get("BlackElo", "0")

                game_length = game.end().ply()

                moves = []
                node = game
                while node.variations:
                    next_node = node.variation(0)
                    if next_node.move:
                        moves.append(next_node.move.uci())
                    node = next_node

                opening = self.identify_opening(moves)

                game_info = {
                    'white': white, 'black': black, 'result': result,
                    'white_elo': int(white_elo) if white_elo.isdigit() else 0,
                    'black_elo': int(black_elo) if black_elo.isdigit() else 0,
                    'opening': opening, 'moves': moves,
                    'pgn_text': str(game), 'game_length': game_length,
                    'termination': game.headers.get("Termination", "Normal"),
                    'time_control': game.headers.get("TimeControl", "Unknown"),
                    'date': game.headers.get("Date", "")
                }
                self.games.append(game_info)

            except Exception:
                sys.stderr.write("⚠️ Aviso: Ocorreu um erro ao processar uma partida. Pulando...\n")
                continue

    def get_opening_stats(self):
        white_openings = [g['opening'] for g in self.games if self.player_name in g['white']]
        black_openings = [g['opening'] for g in self.games if self.player_name in g['black']]
        return Counter(white_openings), Counter(black_openings)

    def get_winning_openings(self):
        white_wins = defaultdict(int)
        black_wins = defaultdict(int)
        for game in self.games:
            if self.player_name in game['white'] and game['result'] == '1-0':
                white_wins[game['opening']] += 1
            elif self.player_name in game['black'] and game['result'] == '0-1':
                black_wins[game['opening']] += 1
        return dict(white_wins), dict(black_wins)

    def analyze_sacrifices(self):
        sacrifice_games = []
        queen_sacrifices = 0
        sacrifice_patterns = [r'x[NBRQ]', r'Qx[a-h][1-8]', r'![!]']
        for game in self.games:
            pgn_text = game['pgn_text']
            has_sacrifice = any(re.search(pattern, pgn_text) for pattern in sacrifice_patterns)
            if has_sacrifice:
                sacrifice_games.append(game)
            if re.search(r'Qx', pgn_text) and any(word in pgn_text.lower() for word in ['!', 'brilliant', 'brilhante']):
                queen_sacrifices += 1
        return sacrifice_games, queen_sacrifices

    def get_attack_combinations(self):
        attack_patterns = {'Pin': r'B[a-h][1-8]', 'Fork': r'N[a-h][1-8]\+', 'Double Attack': r'Q[a-h][1-8]\+',
                           'Discovery': r'[NBRQ][a-h][1-8]\+'}
        attack_counter = Counter()
        for game in self.games:
            for attack_type, pattern in attack_patterns.items():
                attack_counter[attack_type] += len(re.findall(pattern, game['pgn_text']))
        return attack_counter

    def analyze_performance_vs_rating(self):
        rating_ranges = {'Under 1200': (0, 1199), '1200-1399': (1200, 1399), '1400-1599': (1400, 1599),
                         '1600-1799': (1600, 1799), '1800-1999': (1800, 1999), '2000+': (2000, 9999)}
        performance = {}
        for range_name, (min_rating, max_rating) in rating_ranges.items():
            wins, losses, draws = 0, 0, 0
            for game in self.games:
                is_white = self.player_name in game['white']
                opponent_rating = game['black_elo'] if is_white else game['white_elo']
                if min_rating <= opponent_rating <= max_rating:
                    if (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1'):
                        wins += 1
                    elif (is_white and game['result'] == '0-1') or (not is_white and game['result'] == '1-0'):
                        losses += 1
                    elif game['result'] == '1/2-1/2':
                        draws += 1
            total = wins + losses + draws
            if total > 0:
                performance[range_name] = {'wins': wins, 'losses': losses, 'draws': draws, 'total': total,
                                           'win_rate': (wins / total) * 100}
        return performance

    def analyze_game_length_stats(self):
        white_lengths = [g['game_length'] for g in self.games if self.player_name in g['white']]
        black_lengths = [g['game_length'] for g in self.games if self.player_name in g['black']]

        def get_stats(lengths):
            if not lengths: return {}
            avg = sum(lengths) / len(lengths) if lengths else 0
            return {'avg': avg}

        return {'white': get_stats(white_lengths), 'black': get_stats(black_lengths)}

    def analyze_termination_methods(self):
        terminations = Counter(g.get('termination', 'Normal') for g in self.games)
        wins_by_termination = Counter(g.get('termination', 'Normal') for g in self.games if
                                      (self.player_name in g['white'] and g['result'] == '1-0') or (
                                                  self.player_name in g['black'] and g['result'] == '0-1'))
        return terminations, wins_by_termination

    def analyze_time_control_performance(self):
        time_controls = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0, 'total': 0})
        for game in self.games:
            tc = game.get('time_control', 'Unknown')
            is_white = self.player_name in game['white']
            time_controls[tc]['total'] += 1
            if (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1'):
                time_controls[tc]['wins'] += 1
            elif (is_white and game['result'] == '0-1') or (not is_white and game['result'] == '1-0'):
                time_controls[tc]['losses'] += 1
            elif game['result'] == '1/2-1/2':
                time_controls[tc]['draws'] += 1
        for tc in time_controls:
            if time_controls[tc]['total'] > 0:
                time_controls[tc]['win_rate'] = (time_controls[tc]['wins'] / time_controls[tc]['total']) * 100
        return dict(time_controls)

    def find_consecutive_wins(self):
        if not self.games: return 0, []
        sorted_games = sorted([g for g in self.games if g.get('date')], key=lambda x: x['date'])
        max_streak, current_streak = 0, 0
        for game in sorted_games:
            is_white = self.player_name in game['white']
            won = (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1')
            current_streak = current_streak + 1 if won else 0
            max_streak = max(max_streak, current_streak)
        return max_streak, []

    def analyze_opponent_patterns(self):
        opponent_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0, 'total_games': 0})
        for game in self.games:
            is_white = self.player_name in game['white']
            opponent = game['black'] if is_white else game['white']
            opponent_stats[opponent]['total_games'] += 1
            if (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1'):
                opponent_stats[opponent]['wins'] += 1
            elif (is_white and game['result'] == '0-1') or (not is_white and game['result'] == '1-0'):
                opponent_stats[opponent]['losses'] += 1
            elif game['result'] == '1/2-1/2':
                opponent_stats[opponent]['draws'] += 1
        for opp, stats in opponent_stats.items():
            if stats['total_games'] > 0: stats['win_rate'] = (stats['wins'] / stats['total_games']) * 100
        return {k: v for k, v in opponent_stats.items() if v['total_games'] >= 3}

    def get_top_defeated_opponents(self):
        defeated = []
        for game in self.games:
            date_str = game.get('date', '')
            year = date_str.split('.')[0] if date_str else 'N/A'
            if self.player_name in game['white'] and game['result'] == '1-0' and game['black_elo'] > 0:
                defeated.append({'opponent': game['black'], 'rating': game['black_elo'], 'color': 'black',
                                 'opening': game['opening'], 'year': year})
            elif self.player_name in game['black'] and game['result'] == '0-1' and game['white_elo'] > 0:
                defeated.append({'opponent': game['white'], 'rating': game['white_elo'], 'color': 'white',
                                 'opening': game['opening'], 'year': year})
        defeated.sort(key=lambda x: x['rating'], reverse=True)
        return defeated[:20]

    def generate_report(self):
        print("=" * 80)
        print(f"📊 RELATÓRIO COMPLETO DE ANÁLISE - {self.player_name.upper()}")
        print("=" * 80)
        print(f"Total de partidas analisadas: {len(self.games)}")
        print()

        wins, losses, draws = 0, 0, 0
        for game in self.games:
            is_white = self.player_name in game['white']
            if (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1'):
                wins += 1
            elif (is_white and game['result'] == '0-1') or (not is_white and game['result'] == '1-0'):
                losses += 1
            elif game['result'] == '1/2-1/2':
                draws += 1

        total_games_analyzed = len(self.games)
        if total_games_analyzed > 0:
            print("📈 ESTATÍSTICAS GERAIS:")
            print(f"• Vitórias: {wins} ({wins / total_games_analyzed * 100:.1f}%)")
            print(f"• Derrotas: {losses} ({losses / total_games_analyzed * 100:.1f}%)")
            print(f"• Empates: {draws} ({draws / total_games_analyzed * 100:.1f}%)")
            print(f"• Win Rate: {(wins + draws / 2) / total_games_analyzed * 100:.1f}%")
            print()

        print("🎯 PERFORMANCE VS RATING DOS OPONENTES:")
        perf_vs_rating = self.analyze_performance_vs_rating()
        for r, stats in perf_vs_rating.items():
            if stats['total'] > 0: print(f"• {r}: {stats['wins']}/{stats['total']} ({stats['win_rate']:.1f}% win rate)")
        print()

        white_openings, black_openings = self.get_opening_stats()
        print("🔸 TOP 5 ABERTURAS MAIS JOGADAS DE BRANCAS:")
        for i, (o, c) in enumerate(white_openings.most_common(5), 1): print(f"{i}. {o}: {c} partidas")
        print("🔹 TOP 5 ABERTURAS MAIS JOGADAS DE PRETAS:")
        for i, (o, c) in enumerate(black_openings.most_common(5), 1): print(f"{i}. {o}: {c} partidas")
        print()

        white_wins, black_wins = self.get_winning_openings()
        print("🏆 TOP 3 ABERTURAS QUE MAIS GANHARAM DE BRANCAS:")
        for o, w in sorted(white_wins.items(), key=lambda i: i[1], reverse=True)[:3]: print(f"• {o}: {w} vitórias")
        print("🏆 TOP 3 ABERTURAS QUE MAIS GANHARAM DE PRETAS:")
        for o, w in sorted(black_wins.items(), key=lambda i: i[1], reverse=True)[:3]: print(f"• {o}: {w} vitórias")
        print()

        print("⏱️ DURAÇÃO DAS PARTIDAS:")
        length_stats = self.analyze_game_length_stats()
        if 'avg' in length_stats['white']: print(f"• Como brancas - Média: {length_stats['white']['avg']:.1f} lances")
        if 'avg' in length_stats['black']: print(f"• Como pretas - Média: {length_stats['black']['avg']:.1f} lances")
        print()

        print("🔥 SEQUÊNCIAS DE VITÓRIAS:")
        max_streak, _ = self.find_consecutive_wins()
        print(f"• Maior sequência: {max_streak} vitórias consecutivas")
        print()

        print("🤝 OPONENTES MAIS ENFRENTADOS (3+ jogos):")
        freq_opponents = self.analyze_opponent_patterns()
        sorted_opponents = sorted(freq_opponents.items(), key=lambda x: x[1]['total_games'], reverse=True)[:5]
        for opp, stats in sorted_opponents:
            print(f"• {opp}: {stats['wins']}/{stats['total_games']} ({stats['win_rate']:.1f}% win rate)")
        print()

        top_defeated = self.get_top_defeated_opponents()
        print(f"👑 TOP 20 MAIORES RATINGS DERROTADOS POR {self.player_name.upper()}:")
        for i, opp in enumerate(top_defeated, 1):
            year_info = f"Ano: {opp['year']} - " if opp['year'] != 'N/A' else ""
            print(f"{i:2d}. {opp['opponent']} ({opp['rating']}) - {year_info}Abertura: {opp['opening']}")
        print()

        print("=" * 80)
        print("📝 RELATÓRIO COMPLETO FINALIZADO!")
        print("=" * 80)


# --- FUNÇÃO PRINCIPAL ---
def main():
    if len(sys.argv) < 3:
        print("Uso: python seu_script.py <caminho_do_arquivo.pgn> <nome_do_jogador>")
        sys.exit(1)

    pgn_file_path = sys.argv[1]
    player_name = sys.argv[2]

    try:
        with open(pgn_file_path, 'r', encoding='utf-8') as file:
            pgn_content = file.read()

        analyzer = PGNAnalyzer(pgn_content, player_name)
        analyzer.generate_report()

    except FileNotFoundError:
        print(f"Erro: O arquivo '{pgn_file_path}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()