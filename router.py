import socket
import json
import time
import threading

from distance_vector import update_routing_table


class Router:
	def __init__(self, my_ip, period):
		"""
		Inicializa o roteador, criando socket, tabelas e threads.
		:param my_ip: string com o IP do roteador (ex: "127.0.1.1")
		:param period: intervalo em segundos para enviar updates periódicos
		"""
		self.my_ip = my_ip
		self.period = period
		
		# Vizinhos: {ip_vizinho: peso}
		self.neighbors = {}
		
		# Tabela de rotas: {destino: (custo, proximo_salto)}
		self.routing_table = {
			self.my_ip: (0, self.my_ip)  # rota para mim mesmo
		}
		
		# Guarda o último instante em que recebi update de cada vizinho
		self.last_update_received = {}
		
		# Criar socket UDP, fazendo bind na porta 55151
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((my_ip, 55151))
		
		# Thread que fica recebendo pacotes
		self.recv_thread = threading.Thread(target=self.receive_loop, daemon=True)
		self.recv_thread.start()
		
		# Thread que envia updates periodicamente e checa vizinhos inativos
		self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
		self.update_thread.start()
	
	def add_neighbor(self, ip, weight):
		"""
		Adiciona um vizinho 'ip' com peso 'weight'.
		Se não havia rota para esse ip, cria uma rota inicial.
		"""
		self.neighbors[ip] = weight
		if ip not in self.routing_table:
			self.routing_table[ip] = (weight, ip)
		
		print(f"[INFO] Vizinho {ip} adicionado com peso {weight}")
	
	def del_neighbor(self, ip):
		"""
		Remove o vizinho 'ip' e apaga todas as rotas que usavam esse ip como próximo salto.
		"""
		if ip in self.neighbors:
			del self.neighbors[ip]
		
		to_remove = []
		for dest, (cost, nxt) in self.routing_table.items():
			if nxt == ip:
				to_remove.append(dest)
		for d in to_remove:
			del self.routing_table[d]
		
		print(f"[INFO] Vizinho {ip} removido.")
    
	def receive_loop(self):
		"""
		Loop que fica escutando mensagens (update, data, trace) e
		chama as funções de tratamento adequadas.
		"""
		while True:
			data, addr = self.sock.recvfrom(65535)
			msg_str = data.decode('utf-8')
			
			try:
				msg = json.loads(msg_str)
			except:
				print(f"[ERRO] Mensagem inválida (não é JSON): {msg_str}")
				continue
			
			mtype = msg.get("type")
			
			if mtype == "update":
				self.handle_update(msg)
			elif mtype == "data":
				self.handle_data(msg)
			elif mtype == "trace":
				self.handle_trace(msg)
			else:
				print(f"[ERRO] Tipo de mensagem desconhecido: {mtype}")
    
	def update_loop(self):
		"""
		Thread que, a cada 'period' segundos, envia um update
		para cada vizinho e verifica se algum vizinho está inativo.
		"""
		while True:
			time.sleep(self.period)
			
			# Enviar update
			self.send_updates()
			
			# Checar se algum vizinho ficou inativo
			self.check_inactive_neighbors()
    
	def handle_update(self, msg):
		"""
		Trata mensagem do tipo 'update':
			- atualiza 'last_update_received' para o remetente;
			- chama a lógica de Distance Vector para recalcular rotas.
		"""
		source = msg["source"]
		distances = msg["distances"]
		
		# Se não conheço 'source' como vizinho, posso ignorar ou só avisar
		if source not in self.neighbors:
			print(f"[AVISO] Recebi update de {source}, mas não o tenho como vizinho.")
			return
		
		# Marca o momento em que recebi update desse vizinho
		self.last_update_received[source] = time.time()
		
		# Aplica a lógica de Distance Vector
		update_routing_table(self, source, distances)
    
	def handle_data(self, msg):
		"""
		Trata mensagem do tipo 'data':
			- Se eu for o destino final, imprime o 'payload'.
			- Caso contrário, encaminha ao próximo salto.
		"""
		if msg["destination"] == self.my_ip:
			print(f"[DATA] Recebido de {msg['source']}, payload: {msg['payload']}")
		else:
				self.forward_message(msg)
    
	def handle_trace(self, msg):
		"""
		Trata mensagem do tipo 'trace':
			- Adiciona meu IP em 'routers';
			- Se sou o destino, devolve toda a info em um 'data' para o 'source';
			- Senão, encaminha para o próximo salto.
		"""
		msg["routers"].append(self.my_ip)
		
		if msg["destination"] == self.my_ip:
			# Sou o destino: enviar de volta ao source como payload de um 'data'
			response = {
				"type": "data",
				"source": self.my_ip,
				"destination": msg["source"],
				"payload": json.dumps(msg)
			}
			self.sock.sendto(json.dumps(response).encode('utf-8'), (msg["source"], 55151))
		else:
			self.forward_message(msg)
    
	def forward_message(self, msg):
		"""
		Encaminha a mensagem para o próximo salto, conforme a tabela de rotas.
		Se não houver rota, descarta.
		"""
		dest = msg["destination"]
		if dest not in self.routing_table:
			print(f"[ERRO] Não há rota para {dest}. Descartando mensagem.")
			return
		
		(cost, nxt) = self.routing_table[dest]
		
		data = json.dumps(msg).encode('utf-8')
		self.sock.sendto(data, (nxt, 55151))
    
	def send_updates(self):
		"""
		Envia 'update' para cada vizinho, aplicando Split Horizon:
		não enviar ao vizinho as rotas que aprendi dele mesmo.
		"""
		for v in self.neighbors:
			distances = {}
			for dest, (custo, nxt) in self.routing_table.items():
				if nxt == v:
					continue  # Split Horizon
				distances[dest] = custo
		
			update_msg = {
				"type": "update",
				"source": self.my_ip,
				"destination": v,
				"distances": distances
			}
			data = json.dumps(update_msg).encode('utf-8')
			self.sock.sendto(data, (v, 55151))
    
	def check_inactive_neighbors(self):
		"""
		Remove vizinhos que não enviam update há mais de 4 * self.period.
		Ao remover o vizinho, deleta também as rotas que dependem dele.
		"""
		now = time.time()
		for neighbor, last_t in list(self.last_update_received.items()):
			if now - last_t > 4 * self.period:
				print(f"[INFO] Vizinho {neighbor} inativo. Removendo rotas.")
				self.del_neighbor(neighbor)
				del self.last_update_received[neighbor]