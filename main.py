import sys
from router import Router
from commands import process_command

def main():
  if len(sys.argv) < 3:
    print("Uso: main.py <address> <period> [startup]")
    sys.exit(1)

  my_ip = sys.argv[1]
  period = float(sys.argv[2])
  startup_file = sys.argv[3] if len(sys.argv) > 3 else None
  
  # Cria instância do Router
  r = Router(my_ip, period)
  
  # Se houver arquivo de startup, executa os comandos nele
  if startup_file:
    try:
      with open(startup_file, 'r') as f:
        for line in f:
          line = line.strip()
          if line:
            process_command(line, r)
    except Exception as e:
      print("[ERRO] Falha ao ler arquivo startup:", e)
  
  # Loop de leitura de comandos do usuário
  while True:
    try:
      cmd_line = input("Comando: ").strip()
      if cmd_line:
        process_command(cmd_line, r)
    except KeyboardInterrupt:
      print("\n[INFO] Encerrando (CTRL-C).")
      break

if __name__ == "__main__":
  main()