import random
import time
import os
import sys
from colorama import Fore, Style, Back, init

# Inicializa o Colorama para que as cores funcionem
init(autoreset=True)


def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def matrix_effect_loop():
    """
    Simula o efeito de chuva de código do Matrix em loop infinito, com
    contagem de tempo e barra de carregamento que se reinicia.
    """
    try:
        # Tenta obter o tamanho do terminal
        cols, rows = os.get_terminal_size()
    except OSError:
        # Valores padrão se não for possível obter o tamanho
        cols, rows = 80, 24

    characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-=[]{}|;':\",.<>/?`~"

    # Inicia a contagem de tempo real e o tempo do ciclo atual
    total_start_time = time.time()
    cycle_start_time = time.time()

    # Define o tempo de cada ciclo (ficcional)
    fictional_cycle_duration = 3600  # 3600 segundos (1 hora)
    loading_bar_length = 50

    while True:  # Loop principal e infinito
        # Desenha a "chuva de código" em uma única linha, mantendo o cursor na mesma posição
        line = ""
        for _ in range(cols):
            if random.random() < 0.1:
                line += Fore.GREEN + random.choice(characters)
            else:
                line += " "
        sys.stdout.write(Back.BLACK + line + Style.RESET_ALL)
        sys.stdout.write(f"\033[F" * 1)

        # === INFORMAÇÕES DE STATUS ===

        # Volta ao topo da tela para imprimir o status
        sys.stdout.write(f"\033[F" * (rows - 1))

        # Limpa as 3 linhas superiores para o texto
        for _ in range(3):
            sys.stdout.write("\033[K\n")
        sys.stdout.write(f"\033[F" * 3)

        # Calcula o tempo total real e o tempo no ciclo atual
        elapsed_total_real_time = time.time() - total_start_time
        elapsed_cycle_real_time = time.time() - cycle_start_time

        # Calcula o progresso do ciclo (de 0 a 100%)
        progress_percentage = min(100, (elapsed_cycle_real_time / (fictional_cycle_duration / 60)) * 100)

        # Se o ciclo terminar, reinicia o cronômetro do ciclo
        if progress_percentage >= 100:
            progress_percentage = 0
            cycle_start_time = time.time()

        # Formata o tempo total de processamento em dias, horas, minutos e segundos
        simulated_seconds = elapsed_total_real_time * 60  # Cada segundo real conta como 1 minuto
        days = int(simulated_seconds / 86400)
        hours = int((simulated_seconds % 86400) / 3600)
        minutes = int((simulated_seconds % 3600) / 60)
        seconds = int(simulated_seconds % 60)

        time_display = f"{days} d, {hours} h, {minutes} m, {seconds} s"

        # Monta a barra de carregamento
        filled_bar = int((progress_percentage / 100) * loading_bar_length)
        bar = Fore.GREEN + "█" * filled_bar + Style.DIM + "░" * (loading_bar_length - filled_bar) + Style.RESET_ALL

        # Imprime o status, sobrescrevendo o efeito de fundo
        sys.stdout.write(f"\r{Back.BLACK}{Fore.GREEN}PROCESSANDO DADOS...{Style.RESET_ALL}\n")
        sys.stdout.write(f"\r{Back.BLACK}{Fore.GREEN}[{bar}]{Style.RESET_ALL} {progress_percentage:.1f}%\n")
        sys.stdout.write(f"\r{Back.BLACK}{Fore.GREEN}Tempo de processamento: {time_display}{Style.RESET_ALL}")

        # Volta o cursor para a linha inicial da animação
        sys.stdout.write(f"\033[{rows - 2}B")
        sys.stdout.flush()

        # Pequeno atraso para a animação
        time.sleep(0.05)


if __name__ == "__main__":
    clear_screen()
    print("Iniciando simulação de processamento da Matrix. Pressione Ctrl+C para sair.")
    time.sleep(2)
    clear_screen()
    matrix_effect_loop()