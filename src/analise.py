import re
import chess.pgn
from collections import Counter, defaultdict
import io

class PGNAnalyzer:
    def __init__(self, pgn_content):
        self.pgn_content = pgn_content
        self.games = []
        self.parse_pgn()
    
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
                opening = game.headers.get("Opening", "Unknown")
                eco = game.headers.get("ECO", "")
                
                # Converter moves para lista
                moves = []
                node = game
                while node.variations:
                    next_node = node.variation(0)
                    if next_node.move:
                        moves.append(next_node.move.uci())
                    node = next_node
                
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
    
    def get_top_defeated_opponents(self):
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
        return defeated_opponents[:10]
    
    def generate_report(self):
        """Gera relatório completo da análise"""
        print("="*60)
        print("RELATÓRIO DE ANÁLISE - JUNIORSATANAS")
        print("="*60)
        print(f"Total de partidas analisadas: {len(self.games)}")
        print()
        
        # Aberturas mais jogadas
        white_openings, black_openings = self.get_opening_stats()
        
        print("🔸 TOP 3 ABERTURAS MAIS JOGADAS DE BRANCAS:")
        for i, (opening, count) in enumerate(white_openings.most_common(3), 1):
            print(f"{i}. {opening}: {count} partidas")
        print()
        
        print("🔹 TOP 3 ABERTURAS MAIS JOGADAS DE PRETAS:")
        for i, (opening, count) in enumerate(black_openings.most_common(3), 1):
            print(f"{i}. {opening}: {count} partidas")
        print()
        
        # Aberturas que mais ganharam
        white_wins, black_wins = self.get_winning_openings()
        
        print("🏆 ABERTURAS QUE MAIS GANHARAM DE BRANCAS:")
        for opening, wins in sorted(white_wins.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"• {opening}: {wins} vitórias")
        print()
        
        print("🏆 ABERTURAS QUE MAIS GANHARAM DE PRETAS:")
        for opening, wins in sorted(black_wins.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"• {opening}: {wins} vitórias")
        print()
        
        # Análise de ataques
        attacks = self.get_attack_combinations()
        print("⚔️ COMBINAÇÕES DE ATAQUE MAIS USADAS:")
        for attack, count in attacks.most_common(5):
            print(f"• {attack}: {count} vezes")
        print()
        
        # Análise de sacrifícios
        sacrifice_games, queen_sacrifices = self.analyze_sacrifices()
        print("🎯 ANÁLISE DE SACRIFÍCIOS:")
        print(f"• Jogos com sacrifícios: {len(sacrifice_games)}")
        print(f"• Sacrifícios de dama: {queen_sacrifices}")
        print()
        
        # Top oponentes derrotados
        top_defeated = self.get_top_defeated_opponents()
        print("👑 TOP 10 MAIORES RATINGS DERROTADOS:")
        for i, opponent in enumerate(top_defeated, 1):
            print(f"{i:2d}. {opponent['opponent']} ({opponent['rating']}) - "
                  f"Abertura: {opponent['opening']}")
        print()

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

# Exemplo de como usar:
if __name__ == "__main__":
    # Opção 1: Analisar de arquivo
    # analyze_juniorsatanas_games("caminho/para/arquivo.pgn")
    
    # Opção 2: Cole seu PGN aqui
    sample_pgn = """
    [Event "Exemplo"]
    [Site "Chess.com"]
    [Date "2024.01.01"]
    [Round "1"]
    [White "juniorsatanas"]
    [Black "Oponente1"]
    [Result "1-0"]
    [WhiteElo "2000"]
    [BlackElo "1950"]
    [Opening "Sicilian Defense"]
    [ECO "B20"]
    
    1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 1-0
    """
    
    print("Para usar este script:")
    print("1. Instale python-chess: pip install python-chess")
    print("2. Cole seu arquivo PGN ou use analyze_juniorsatanas_games('arquivo.pgn')")
    print("3. Execute o script para ver a análise completa!")