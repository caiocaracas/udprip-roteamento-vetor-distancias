import json
import sys

def process_command(line, router):
  """
  Processa o comando digitado pelo usuário (ex: add, del, trace, send).
  router: instância da classe Router, onde chamamos add_neighbor, del_neighbor etc.
  """
  parts = line.split(maxsplit=2)
  cmd = parts[0]
  
  if cmd == "add":
    # add <ip> <peso>
    if len(parts) < 3:
      print("[ERRO] Use: add <ip> <weight>")
      return
    ip_neighbor = parts[1]
    weight = int(parts[2])
    # Aqui NÃO imprime nada, pois o router.add_neighbor já imprime
    router.add_neighbor(ip_neighbor, weight)

  elif cmd == "del":
    # del <ip>
    if len(parts) < 2:
      print("[ERRO] Use: del <ip>")
      return
    ip_neighbor = parts[1]
    router.del_neighbor(ip_neighbor)
    # Também não imprime nada extra aqui, pois del_neighbor já imprime
  
  elif cmd == "send":
    # send <ip_destino> <mensagem>
    if len(parts) < 3:
      print("[ERRO] Use: send <ip_destino> <mensagem>")
      return
    dest_ip = parts[1]
    payload = parts[2]
    
    msg_dict = {
      "type": "data",
      "source": router.my_ip,
      "destination": dest_ip,
      "payload": payload
    }
    router.sock.sendto(json.dumps(msg_dict).encode('utf-8'), (dest_ip, 55151))
    print(f"[INFO] Enviando DATA para {dest_ip}")

  elif cmd == "trace":
    # trace <ip>
    if len(parts) < 2:
      print("[ERRO] Use: trace <ip>")
      return
    dest_ip = parts[1]
    
    trace_msg = {
      "type": "trace",
      "source": router.my_ip,
      "destination": dest_ip,
      "routers": [router.my_ip]
    }
    router.forward_message(trace_msg)
    print(f"[INFO] Trace enviado para {dest_ip}")

  elif cmd == "quit" or cmd == "done":
    print("[INFO] Encerrando roteador.")
    sys.exit(0)
  
  else:
    print("[ERRO] Comando não reconhecido:", cmd)