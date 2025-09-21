import re
import chess.pgn
from collections import Counter, defaultdict
import io


class PGNAnalyzer:
    def __init__(self, pgn_content):
        self.pgn_content = pgn_content
        self.games = []
        self.parse_pgn()

    def identify_opening(self, moves):
        """Identifica a abertura pelos primeiros lances"""
        if not moves or len(moves) < 2:
            return "Partida muito curta"

        # Dicionário de aberturas baseado nos primeiros lances
        opening_patterns = {
            # Aberturas com e4
            ('e2e4', 'e7e5'): {
                ('g1f3', 'b8c6', 'f1b5'): "Ruy Lopez",
                ('g1f3', 'b8c6', 'f1c4'): "Italian Game",
                ('g1f3', 'b8c6', 'd2d3'): "King's Indian Attack",
                ('g1f3', 'g8f6'): "Petroff Defense",
                ('f2f4',): "King's Gambit",
                ('b1c3',): "Vienna Game",
                ('d2d4',): "Center Game"
            },
            ('e2e4', 'c7c5'): {
                ('g1f3', 'd7d6', 'd2d4'): "Sicilian Najdorf",
                ('g1f3', 'b8c6', 'd2d4'): "Sicilian Accelerated Dragon",
                ('g1f3', 'g8f6'): "Sicilian Nimzowitsch",
                ('b1c3',): "Sicilian Closed",
                ('f2f4',): "Sicilian Grand Prix",
                ('c2c3',): "Sicilian Alapin"
            },
            ('e2e4', 'c7c6'): "Caro-Kann Defense",
            ('e2e4', 'd7d6'): "Pirc Defense",
            ('e2e4', 'g8f6'): "Alekhine's Defense",
            ('e2e4', 'd7d5'): "Scandinavian Defense",
            ('e2e4', 'g7g6'): "Modern Defense",
            ('e2e4', 'e7e6'): "French Defense",

            # Aberturas com d4
            ('d2d4', 'd7d5'): {
                ('c2c4',): "Queen's Gambit",
                ('g1f3', 'g8f6', 'c2c4'): "Queen's Gambit Declined",
                ('g1f3', 'g8f6', 'b1c3'): "Queen's Pawn Game",
                ('e2e3',): "Colle System"
            },
            ('d2d4', 'g8f6'): {
                ('c2c4', 'e7e6'): "Nimzo-Indian Defense",
                ('c2c4', 'g7g6'): "King's Indian Defense",
                ('g1f3', 'g7g6'): "King's Indian Attack",
                ('b1c3', 'd7d5'): "Queen's Gambit Declined"
            },
            ('d2d4', 'f7f5'): "Dutch Defense",
            ('d2d4', 'e7e6'): "Queen's Pawn Game",

            # Aberturas com Nf3
            ('g1f3', 'd7d5'): "Réti Opening",
            ('g1f3', 'g8f6'): {
                ('c2c4',): "English Opening",
                ('d2d4',): "Queen's Pawn Game",
                ('g2g3',): "King's Indian Attack"
            },
            ('g1f3', 'c7c5'): "Réti Opening",

            # English Opening
            ('c2c4', 'e7e5'): "English Opening",
            ('c2c4', 'g8f6'): "English Opening",
            ('c2c4', 'c7c5'): "English Symmetrical",

            # Outras aberturas
            ('f2f4',): "Bird's Opening",
            ('b2b3',): "Nimzowitsch-Larsen Attack",
            ('g2g3',): "Benko's Opening",
            ('b1c3',): "Van't Kruijs Opening"
        }

        # Converter moves UCI para formato legível
        try:
            # Pegar os primeiros 6 lances (3 de cada lado)
            first_moves = tuple(moves[:6])

            # Buscar padrão exato
            for pattern, opening in opening_patterns.items():
                if isinstance(opening, dict):
                    # Verificar se os primeiros lances batem
                    if len(first_moves) >= len(pattern) and first_moves[:len(pattern)] == pattern:
                        # Verificar continuações
                        remaining_moves = first_moves[len(pattern):]
                        for continuation, name in opening.items():
                            if len(remaining_moves) >= len(continuation) and remaining_moves[
                                                                             :len(continuation)] == continuation:
                                return name
                        # Se não encontrou continuação específica, usar abertura geral
                        return list(opening.values())[0] if opening else "Unknown Variation"
                else:
                    # Padrão simples
                    if len(first_moves) >= len(pattern) and first_moves[:len(pattern)] == pattern:
                        return opening

            # Identificação por primeiro lance apenas
            first_move = moves[0] if moves else ""
            if first_move == 'e2e4':
                second_move = moves[1] if len(moves) > 1 else ""
                if second_move == 'e7e5':
                    return "King's Pawn Game"
                elif second_move == 'c7c5':
                    return "Sicilian Defense"
                else:
                    return "King's Pawn Opening"
            elif first_move == 'd2d4':
                return "Queen's Pawn Opening"
            elif first_move == 'g1f3':
                return "Réti Opening"
            elif first_move == 'c2c4':
                return "English Opening"
            else:
                return "Irregular Opening"

        except Exception:
            return "Unknown Opening"

    def parse_pgn(self):
        """Parse o conteúdo PGN e extrai informações das partidas"""
        pgn_io = io.StringIO(self.pgn_content)

        while True:
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break

                # Extrair informações básicas
                white = game.headers.get("White", "").lower()
                black = game.headers.get("Black", "").lower()
                result = game.headers.get("Result", "")
                white_elo = game.headers.get("WhiteElo", "0")
                black_elo = game.headers.get("BlackElo", "0")
                eco = game.headers.get("ECO", "")

                # Converter moves para lista
                moves = []
                node = game
                while node.variations:
                    next_node = node.variation(0)
                    if next_node.move:
                        moves.append(next_node.move.uci())
                    node = next_node

                # Identificar abertura pelos lances
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
                    'pgn_text': str(game)
                }

                # Só adicionar se juniorsatanas estava jogando
                if 'juniorsatanas' in white or 'juniorsatanas' in black:
                    self.games.append(game_info)

            except Exception as e:
                print(f"Erro ao processar partida: {e}")
                continue

    def get_opening_stats(self):
        """Analisa estatísticas de aberturas"""
        white_openings = []
        black_openings = []

        for game in self.games:
            if 'juniorsatanas' in game['white']:
                white_openings.append(game['opening'])
            elif 'juniorsatanas' in game['black']:
                black_openings.append(game['opening'])

        white_counter = Counter(white_openings)
        black_counter = Counter(black_openings)

        return white_counter, black_counter

    def get_winning_openings(self):
        """Analisa aberturas que mais ganharam"""
        white_wins = defaultdict(int)
        black_wins = defaultdict(int)

        for game in self.games:
            if 'juniorsatanas' in game['white'] and game['result'] == '1-0':
                white_wins[game['opening']] += 1
            elif 'juniorsatanas' in game['black'] and game['result'] == '0-1':
                black_wins[game['opening']] += 1

        return dict(white_wins), dict(black_wins)

    def analyze_sacrifices(self):
        """Analisa sacrifícios nas partidas"""
        sacrifice_games = []
        queen_sacrifices = 0

        sacrifice_patterns = [
            r'[NBRQ]x[a-h][1-8](?:\+|#)?!',  # Capturas com exclamação
            r'[NBRQ][a-h]?[1-8]?x[a-h][1-8](?:\+|#)?!',
            r'Qx[a-h][1-8](?:\+|#)?',  # Sacrifícios de dama
            r'Q[a-h]?[1-8]?x[a-h][1-8](?:\+|#)?'
        ]

        for game in self.games:
            pgn_text = game['pgn_text']
            has_sacrifice = False

            # Procurar por padrões de sacrifício
            for pattern in sacrifice_patterns:
                if re.search(pattern, pgn_text):
                    has_sacrifice = True

                    # Verificar sacrifício de dama especificamente
                    if 'Qx' in pattern and re.search(pattern, pgn_text):
                        queen_sacrifices += 1

            # Procurar por comentários indicando sacrifícios
            if any(word in pgn_text.lower() for word in ['sacrifice', 'sacrificio', 'brilliant', 'brilhante']):
                has_sacrifice = True

            if has_sacrifice:
                sacrifice_games.append(game)

        return sacrifice_games, queen_sacrifices

    def get_attack_combinations(self):
        """Identifica combinações de ataque mais usadas"""
        attack_patterns = {
            'Pin': r'(Bb5|Ba4|Bg5|Bf4)',
            'Fork': r'N[a-h][1-8](?:\+|#)?',
            'Skewer': r'[RQ][a-h1-8]*x[a-h][1-8]',
            'Double Attack': r'Q[a-h][1-8](?:\+|#)?',
            'Discovery': r'[NBRQ][a-h1-8]*\+',
            'Back Rank': r'[RQ][a-h][18](?:#|\+)',
            'Smothered Mate': r'N[a-h][1-8]#'
        }

        attack_counter = Counter()

        for game in self.games:
            pgn_text = game['pgn_text']
            for attack_type, pattern in attack_patterns.items():
                matches = re.findall(pattern, pgn_text)
                if matches:
                    attack_counter[attack_type] += len(matches)

        return attack_counter

    def analyze_performance_vs_rating(self):
        """Analisa performance contra diferentes faixas de rating"""
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
                opponent_rating = 0
                is_white = 'juniorsatanas' in game['white']

                if is_white:
                    opponent_rating = game['black_elo']
                    if min_rating <= opponent_rating <= max_rating:
                        if game['result'] == '1-0':
                            wins += 1
                        elif game['result'] == '0-1':
                            losses += 1
                        elif game['result'] == '1/2-1/2':
                            draws += 1
                else:
                    opponent_rating = game['white_elo']
                    if min_rating <= opponent_rating <= max_rating:
                        if game['result'] == '0-1':
                            wins += 1
                        elif game['result'] == '1-0':
                            losses += 1
                        elif game['result'] == '1/2-1/2':
                            draws += 1

            total = wins + losses + draws
            if total > 0:
                win_rate = (wins / total) * 100
                performance[range_name] = {
                    'wins': wins, 'losses': losses, 'draws': draws,
                    'total': total, 'win_rate': win_rate
                }

        return performance

    def analyze_game_length_stats(self):
        """Analisa estatísticas de duração das partidas"""
        white_lengths = []
        black_lengths = []

        for game in self.games:
            # Verificação de segurança
            length = game.get('game_length', 0)
            if length is None:
                length = 0

            if 'juniorsatanas' in game['white']:
                white_lengths.append(length)
            else:
                black_lengths.append(length)

        def get_stats(lengths):
            if not lengths:
                return {}
            # Filtrar valores inválidos
            valid_lengths = [x for x in lengths if x > 0]
            if not valid_lengths:
                return {'avg': 0, 'min': 0, 'max': 0, 'short': 0, 'medium': 0, 'long': 0}

            return {
                'avg': sum(valid_lengths) / len(valid_lengths),
                'min': min(valid_lengths),
                'max': max(valid_lengths),
                'short': len([x for x in valid_lengths if x <= 20]),  # <= 20 lances
                'medium': len([x for x in valid_lengths if 21 <= x <= 40]),
                'long': len([x for x in valid_lengths if x > 40])
            }

        return {
            'white': get_stats(white_lengths),
            'black': get_stats(black_lengths)
        }

    def analyze_termination_methods(self):
        """Analisa como as partidas terminaram"""
        terminations = Counter()
        wins_by_termination = Counter()

        for game in self.games:
            # Verificação de segurança para termination
            term = game.get('termination', 'Normal')
            if not term or term.strip() == '':
                term = 'Normal'

            terminations[term] += 1

            # Se juniorsatanas ganhou
            is_white = 'juniorsatanas' in game['white']
            won = (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1')

            if won:
                wins_by_termination[term] += 1

        return terminations, wins_by_termination

    def analyze_time_control_performance(self):
        """Analisa performance por controle de tempo"""
        time_controls = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})

        for game in self.games:
            # Verificação de segurança para time_control
            tc = game.get('time_control', 'Unknown')
            if not tc or tc.strip() == '':
                tc = 'Unknown'

            is_white = 'juniorsatanas' in game['white']

            if (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1'):
                time_controls[tc]['wins'] += 1
            elif (is_white and game['result'] == '0-1') or (not is_white and game['result'] == '1-0'):
                time_controls[tc]['losses'] += 1
            elif game['result'] == '1/2-1/2':
                time_controls[tc]['draws'] += 1

        # Calcular win rate
        for tc in time_controls:
            total = time_controls[tc]['wins'] + time_controls[tc]['losses'] + time_controls[tc]['draws']
            if total > 0:
                time_controls[tc]['total'] = total
                time_controls[tc]['win_rate'] = (time_controls[tc]['wins'] / total) * 100

        return dict(time_controls)

    def find_consecutive_wins(self):
        """Encontra sequências de vitórias consecutivas"""
        # Filtrar apenas jogos com data válida
        games_with_date = []
        for game in self.games:
            date_str = game.get('date', '')
            if date_str and date_str != '' and '.' in date_str:
                games_with_date.append(game)

        if not games_with_date:
            return 0, []

        # Ordenar jogos por data
        try:
            sorted_games = sorted(games_with_date, key=lambda x: x['date'])
        except:
            return 0, []

        max_streak = current_streak = 0
        streaks = []
        current_start = 0

        for i, game in enumerate(sorted_games):
            is_white = 'juniorsatanas' in game['white']
            won = (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1')

            if won:
                if current_streak == 0:
                    current_start = i
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                if current_streak > 0:
                    streaks.append((current_streak, current_start, i - 1))
                current_streak = 0

        if current_streak > 0:
            streaks.append((current_streak, current_start, len(sorted_games) - 1))

        return max_streak, sorted(streaks, reverse=True)[:5]

    def analyze_opponent_patterns(self):
        """Analisa padrões contra oponentes específicos"""
        opponent_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0, 'games': []})

        for game in self.games:
            is_white = 'juniorsatanas' in game['white']
            opponent = game['black'] if is_white else game['white']

            opponent_stats[opponent]['games'].append(game)

            if (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1'):
                opponent_stats[opponent]['wins'] += 1
            elif (is_white and game['result'] == '0-1') or (not is_white and game['result'] == '1-0'):
                opponent_stats[opponent]['losses'] += 1
            elif game['result'] == '1/2-1/2':
                opponent_stats[opponent]['draws'] += 1

        # Filtrar oponentes com pelo menos 3 jogos
        frequent_opponents = {}
        for opp, stats in opponent_stats.items():
            total_games = len(stats['games'])
            if total_games >= 3:
                win_rate = (stats['wins'] / total_games) * 100 if total_games > 0 else 0
                frequent_opponents[opp] = {
                    **stats,
                    'total_games': total_games,
                    'win_rate': win_rate
                }

        return frequent_opponents

    def analyze_chess_tactics(self):
        """Análise avançada de táticas de xadrez"""
        tactics = {
            'Checkmate Patterns': {
                'Back Rank Mate': 0,
                'Smothered Mate': 0,
                'Queen Mate': 0,
                'Rook Mate': 0
            },
            'Tactical Motifs': {
                'Discovered Attack': 0,
                'Double Check': 0,
                'Zugzwang': 0,
                'Clearance': 0,
                'Deflection': 0
            },
            'Piece Sacrifices': {
                'Queen Sacrifice': 0,
                'Rook Sacrifice': 0,
                'Knight Sacrifice': 0,
                'Bishop Sacrifice': 0,
                'Exchange Sacrifice': 0
            }
        }

        tactical_patterns = {
            'Back Rank Mate': r'R[a-h][18]#|Q[a-h][18]#',
            'Smothered Mate': r'N[a-h][1-8]#',
            'Discovered Attack': r'[NBR][a-h1-8]*\+.*[QRN][a-h][1-8]',
            'Double Check': r'\+\+',
            'Queen Sacrifice': r'Qx[a-h][1-8]',
            'Rook Sacrifice': r'Rx[a-h][1-8]',
            'Knight Sacrifice': r'Nx[a-h][1-8]',
            'Bishop Sacrifice': r'Bx[a-h][1-8]',
            'Exchange Sacrifice': r'Rx[NBRQ]'
        }

        for game in self.games:
            pgn_text = game['pgn_text']
            for tactic, pattern in tactical_patterns.items():
                matches = len(re.findall(pattern, pgn_text))
                if 'Sacrifice' in tactic:
                    tactics['Piece Sacrifices'][tactic] += matches
                elif 'Mate' in tactic:
                    tactics['Checkmate Patterns'][tactic] += matches
                else:
                    tactics['Tactical Motifs'][tactic] += matches

    def get_top_defeated_opponents(self):
        """Encontra os 20 maiores ratings que perderam para juniorsatanas"""
        defeated_opponents = []

        for game in self.games:
            # Extrair ano da data
            date_str = game.get('date', '')
            year = 'N/A'
            if date_str and '.' in date_str:
                try:
                    # Formato esperado: YYYY.MM.DD
                    year = date_str.split('.')[0]
                except:
                    year = 'N/A'

            # juniorsatanas jogando de brancas e ganhando
            if ('juniorsatanas' in game['white'] and game['result'] == '1-0' and
                    game['black_elo'] > 0):
                defeated_opponents.append({
                    'opponent': game['black'],
                    'rating': game['black_elo'],
                    'color': 'black',
                    'opening': game['opening'],
                    'year': year
                })

            # juniorsatanas jogando de pretas e ganhando
            elif ('juniorsatanas' in game['black'] and game['result'] == '0-1' and
                  game['white_elo'] > 0):
                defeated_opponents.append({
                    'opponent': game['white'],
                    'rating': game['white_elo'],
                    'color': 'white',
                    'opening': game['opening'],
                    'year': year
                })

        # Ordenar por rating (maior primeiro)
        defeated_opponents.sort(key=lambda x: x['rating'], reverse=True)
        return defeated_opponents[:20]
        """Encontra os 10 maiores ratings que perderam para juniorsatanas"""
        defeated_opponents = []

        for game in self.games:
            # juniorsatanas jogando de brancas e ganhando
            if ('juniorsatanas' in game['white'] and game['result'] == '1-0' and
                    game['black_elo'] > 0):
                defeated_opponents.append({
                    'opponent': game['black'],
                    'rating': game['black_elo'],
                    'color': 'black',
                    'opening': game['opening']
                })

            # juniorsatanas jogando de pretas e ganhando
            elif ('juniorsatanas' in game['black'] and game['result'] == '0-1' and
                  game['white_elo'] > 0):
                defeated_opponents.append({
                    'opponent': game['white'],
                    'rating': game['white_elo'],
                    'color': 'white',
                    'opening': game['opening']
                })

        # Ordenar por rating (maior primeiro)
        defeated_opponents.sort(key=lambda x: x['rating'], reverse=True)
        return defeated_opponents[:20]

    def generate_report(self):
        """Gera relatório completo da análise"""
        print("=" * 80)
        print("📊 RELATÓRIO COMPLETO DE ANÁLISE - JUNIORSATANAS")
        print("=" * 80)
        print(f"Total de partidas analisadas: {len(self.games)}")
        print()

        # 1. Estatísticas básicas de resultado
        wins = losses = draws = 0
        for game in self.games:
            is_white = 'juniorsatanas' in game['white']
            if (is_white and game['result'] == '1-0') or (not is_white and game['result'] == '0-1'):
                wins += 1
            elif (is_white and game['result'] == '0-1') or (not is_white and game['result'] == '1-0'):
                losses += 1
            elif game['result'] == '1/2-1/2':
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
        for opening, wins in sorted(white_wins.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"• {opening}: {wins} vitórias")
        print()

        print("🏆 TOP 3 ABERTURAS QUE MAIS GANHARAM DE PRETAS:")
        for opening, wins in sorted(black_wins.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"• {opening}: {wins} vitórias")
        print()

        # 5. Análise de duração das partidas
        length_stats = self.analyze_game_length_stats()
        print("⏱️ DURAÇÃO DAS PARTIDAS:")
        if length_stats['white'] and length_stats['white'].get('avg', 0) > 0:
            print(f"• Como brancas - Média: {length_stats['white']['avg']:.1f} lances")
            print(f"  Curtas (≤20): {length_stats['white']['short']}, "
                  f"Médias (21-40): {length_stats['white']['medium']}, "
                  f"Longas (>40): {length_stats['white']['long']}")
        else:
            print("• Como brancas - Dados de duração não disponíveis")

        if length_stats['black'] and length_stats['black'].get('avg', 0) > 0:
            print(f"• Como pretas - Média: {length_stats['black']['avg']:.1f} lances")
            print(f"  Curtas (≤20): {length_stats['black']['short']}, "
                  f"Médias (21-40): {length_stats['black']['medium']}, "
                  f"Longas (>40): {length_stats['black']['long']}")
        else:
            print("• Como pretas - Dados de duração não disponíveis")
        print()

        # 6. Métodos de finalização
        terminations, wins_by_term = self.analyze_termination_methods()
        print("🏁 COMO AS PARTIDAS TERMINARAM:")
        for term, count in terminations.most_common(5):
            wins = wins_by_term[term]
            print(f"• {term}: {count} jogos ({wins} vitórias)")
        print()

        # 7. Performance por controle de tempo
        time_perf = self.analyze_time_control_performance()
        print("⏰ PERFORMANCE POR CONTROLE DE TEMPO:")
        for tc, stats in sorted(time_perf.items(), key=lambda x: x[1]['total'], reverse=True)[:5]:
            if stats['total'] >= 10:  # Só mostrar controles com pelo menos 10 jogos
                print(f"• {tc}: {stats['wins']}/{stats['total']} "
                      f"({stats['win_rate']:.1f}% win rate)")
        print()

        # 8. Sequências de vitórias
        max_streak, top_streaks = self.find_consecutive_wins()
        print("🔥 SEQUÊNCIAS DE VITÓRIAS:")
        print(f"• Maior sequência: {max_streak} vitórias consecutivas")
        if top_streaks:
            print("• Top 3 sequências:")
            for i, (streak, start, end) in enumerate(top_streaks[:3], 1):
                print(f"  {i}. {streak} vitórias consecutivas")
        print()

        # 9. Oponentes frequentes
        freq_opponents = self.analyze_opponent_patterns()
        print("🤝 OPONENTES MAIS ENFRENTADOS (3+ jogos):")
        sorted_opponents = sorted(freq_opponents.items(),
                                  key=lambda x: x[1]['total_games'], reverse=True)[:5]
        for opp, stats in sorted_opponents:
            print(f"• {opp}: {stats['wins']}/{stats['total_games']} "
                  f"({stats['win_rate']:.1f}% win rate)")
        print()

        # 10. Análise tática avançada
        try:
            tactics = self.analyze_chess_tactics()
            print("⚔️ ANÁLISE TÁTICA AVANÇADA:")

            for category, motifs in tactics.items():
                if motifs and any(count > 0 for count in motifs.values()):
                    print(f"🔸 {category}:")
                    sorted_tactics = sorted(motifs.items(), key=lambda x: x[1], reverse=True)[:3]
                    for tactic, count in sorted_tactics:
                        if count > 0:
                            print(f"  • {tactic}: {count} vezes")
            print()
        except Exception as e:
            print(f"⚔️ ANÁLISE TÁTICA AVANÇADA:")
            print(f"• Erro na análise tática: {e}")
            print()

        # 11. Análise de ataques (original)
        attacks = self.get_attack_combinations()
        print("⚔️ COMBINAÇÕES DE ATAQUE MAIS USADAS:")
        for attack, count in attacks.most_common(5):
            print(f"• {attack}: {count} vezes")
        print()

        # 12. Análise de sacrifícios (original)
        sacrifice_games, queen_sacrifices = self.analyze_sacrifices()
        print("🎯 ANÁLISE DE SACRIFÍCIOS:")
        print(f"• Jogos com sacrifícios: {len(sacrifice_games)}")
        print(f"• Sacrifícios de dama: {queen_sacrifices}")
        print()

        # 13. Top oponentes derrotados (original)
        top_defeated = self.get_top_defeated_opponents()
        print("👑 TOP 20 MAIORES RATINGS DERROTADOS:")
        for i, opponent in enumerate(top_defeated[:20], 1):  # Garantir 20
            print(f"{i:2d}. {opponent['opponent']} ({opponent['rating']}) - "
                  f"Ano: {opponent['year']} - Abertura: {opponent['opening']}")
        print()

        print("=" * 80)
        print("📝 RELATÓRIO COMPLETO FINALIZADO!")
        print("=" * 80)


# Função principal para usar o analisador
def analyze_juniorsatanas_games(pgn_file_path):
    """
    Função principal para analisar as partidas de juniorsatanas

    Args:
        pgn_file_path (str): Caminho para o arquivo PGN
    """
    try:
        # Ler arquivo PGN
        with open(pgn_file_path, 'r', encoding='utf-8') as file:
            pgn_content = file.read()

        # Criar analisador e gerar relatório
        analyzer = PGNAnalyzer(pgn_content)
        analyzer.generate_report()

    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {pgn_file_path}")
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")


# Exemplo de uso alternativo com conteúdo PGN diretamente
def analyze_from_pgn_content(pgn_content):
    """
    Analisa partidas a partir do conteúdo PGN fornecido diretamente

    Args:
        pgn_content (str): Conteúdo do arquivo PGN como string
    """
    analyzer = PGNAnalyzer(pgn_content)
    analyzer.generate_report()
    return analyzer


# Execução automática
if __name__ == "__main__":
    print("🔍 Iniciando análise das partidas de juniorsatanas...")
    print("📁 Procurando arquivo: juniorsatanas.pgn")
    print("-" * 60)

    # Carrega automaticamente o arquivo juniorsatanas.pgn
    analyze_juniorsatanas_games("juniorsatanas.pgn")