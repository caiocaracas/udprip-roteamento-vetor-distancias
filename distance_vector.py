def update_routing_table(router, neighbor_ip, distances_received):
  """
  Recalcula as distâncias na tabela de rotas do 'router'
  usando as informações do 'neighbor_ip' (vizinho) e
  'distances_received' (dict {dest: custo}).

  - router: instância da classe Router
  - neighbor_ip: IP do vizinho que enviou o update
  - distances_received: dicionário {destino -> custo}
  """
  cost_to_neighbor = router.neighbors[neighbor_ip]  # custo até o vizinho

  for dest, cost_vizinho in distances_received.items():
    if dest == router.my_ip:
      continue  # ignora rota para mim mesmo
    
    possible_cost = cost_to_neighbor + cost_vizinho
    
    current_route = router.routing_table.get(dest)
    # Se não existe rota ou a rota encontrada é melhor (menor custo), atualiza
    if not current_route or possible_cost < current_route[0]:
      router.routing_table[dest] = (possible_cost, neighbor_ip)
