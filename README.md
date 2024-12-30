# UDPRIP: Distance Vector Routing Protocol

Este repositório contém uma implementação de um **Protocolo de Roteamento por Vetor de Distâncias (UDPRIP)** em Python. Os roteadores trocam **mensagens UDP** na porta 55151, enviando periódicas mensagens de update para manter a rede atualizada. Além disso, eles podem transferir dados (`data`), rastrear caminhos (`trace`) e detectar vizinhos inativos para remover rotas obsoletas.

---

## Índice
1. [Visão Geral](#visão-geral)
2. [Como Executar](#como-executar)
3. [Comandos Disponíveis](#comandos-disponíveis)
4. [Exemplo de Teste Mínimo](#exemplo-de-teste-mínimo)
5. [Exemplo de Topologia em Árvore](#exemplo-de-topologia-em-árvore)
6. [Arquivos Principais](#arquivos-principais)

---

## Visão Geral

O **UDPRIP** (UDP Routing Information Protocol) é um roteador simples baseado em **Vetor de Distâncias**, onde cada nó (roteador) mantém uma tabela com o **custo** para chegar a outros destinos e o **próximo salto**. Os roteadores enviam periodicamente **updates** para seus vizinhos, que contêm as rotas conhecidas. Se um roteador encontra um caminho mais barato, atualiza a sua tabela e passa adiante a informação.

Destaques do projeto:
- **Mensagens** `update`, `data` e `trace` em formato JSON via **UDP**.
- **Encaminhamento de pacotes** para o destino (ou descarte, se não houver rota).
- **Split Horizon** para minimizar loops de roteamento.
- Remoção de rotas obsoletas quando um roteador não responde por `4 × period`.

---

## Como Executar

```bash
python3 main.py <address> <period> [startup]
```
- `<address>`: Endereço de IP (loopback) onde o roteador fará bind, por exemplo `127.0.1.1`.
- `<period>`: Intervalo (em segundos) para envio dos updates de roteamento.
- `[startup]`: (Opcional) Caminho para um arquivo com comandos iniciais (`add`, `del`, etc.).

**Observação**: Antes de rodar vários roteadores em `127.0.1.x, certifique-se de ter adicionado esses endereços à interface de loopback do seu sistema operacional.

---

## Comandos Disponíveis

- `add <ip> <peso>`: Adiciona um vizinho ao roteador atual, com o custo de link `<peso>`. Exemplo: `add 127.0.1.2 10`

- `del <ip>`: Remove o vizinho `<ip>` do roteador atual e todas as rotas que dependem dele. Exemplo: `del 127.0.1.2`

- `send <ip> <mensagem>`: Envia um pacote de dados para `<ip>` contendo `<mensagem>`. Se o roteador não for o destino, encaminha conforme a tabela de rotas. Exemplo: `send 127.0.1.2 Olá R2!`

- `trace <ip>`: Inicia um rastreamento para `<ip>`, que registra todos os roteadores percorridos. Quando chega ao destino, a rota coletada retorna ao remetente em uma mensagem `data`. Exemplo: `trace 127.0.1.3`

- `quit` / `done`: Encerra a execução do roteador.

---

## Exemplo de Teste Mínimo
### Cenário
Dois roteadores em IPs `127.0.1.1` e `127.0.1.2`, ambos com **period=5** segundos.
#### Passo a Passo
1. **Terminal 1** (`127.0.1.1`):
  ```bash
  python3 main.py 127.0.1.1 5
  ```
  *Comandos:*
  ```bash
  add 127.0.1.2 10
  send 127.0.1.2 Oi router 2!
  ```
2. **Terminal 2** (`127.0.1.2`):
 ```bash
  python3 main.py 127.0.1.1 5
 ```
 *Comandos:*
```bash
add 127.0.1.1 10
```
*Resultado esperado:* Roteador `127.0.1.2` recebe `[DATA]` com `Oi Router 2!` originado de `127.0.1.1`.

3. (Opcional) Faça `trace 127.0.1.2` no primeiro terminal para ver a rota. Como há apenas 2 roteadores, a rota será `[127.0.1.1, 127.0.1.2]`.

---

## Exemplo de Topologia em Árvore

Neste exemplo, trata-se de um cenário maior, onde há 5 roteadores formando uma árvore (R1 como raiz, e outros como “ramos”).
Suponha a seguinte estrutura:
```bash
         (R1) 127.0.1.1
         /           \
        5             7
       /               \
  (R2)127.0.1.2     127.0.1.4(R4)
       \               /
        10           2
         \          /
         (R3)127.0.1.3
                \
                 1
                  \
                (R5)127.0.1.5
```
Os custos de cada link estão indicados ao lado das linhas. Por exemplo, `R1->R2 = 5`, `R2->R3 = 10`, etc.
### Configuração

- **Terminal 1** (`R1` = 127.0.1.1):
```bash
python3 main.py 127.0.1.1 5
Comando: add 127.0.1.2 5
Comando: add 127.0.1.4 7
```
- **Terminal 2** (`R2` = 127.0.1.2):
```bash
python3 main.py 127.0.1.2 5
Comando: add 127.0.1.1 5
Comando: add 127.0.1.3 10
```
- **Terminal 3** (`R3` = 127.0.1.3):
```bash
python3 main.py 127.0.1.3 5
Comando: add 127.0.1.2 10
Comando: add 127.0.1.5 1
```
- **Terminal 4** (`R4` = 127.0.1.4):
```bash
python3 main.py 127.0.1.4 5
Comando: add 127.0.1.1 7
Comando: add 127.0.1.3 2
```
- **Terminal 5** (`R5` = 127.0.1.5):
```bash
python3 main.py 127.0.1.5 5
Comando: add 127.0.1.3 1
```
### Testando

  - No **Terminal 1** (R1), faça:
```bash
trace 127.0.1.5
```
*Resultado esperado:* O trace pode indicar um caminho como `[127.0.1.1, 127.0.1.4, 127.0.1.3, 127.0.1.5]` se essa for a rota de menor custo.

- Se quiser mandar dados:
```bash
send 127.0.1.5 "Mensagem para R5"
```
*Resultado:* O R5 imprime `[DATA] Recebido de 127.0.1.1, payload: Mensagem para R5`.

- Experimente fazer `del 127.0.1.3` no R2 (removendo o link R2->R3) e veja se a rota se recalcula via outro caminho (talvez passando por R1->R4->R3).

---

## Arquivos Principais
- `main.py`
  
  Ponto de entrada, cria a instância do roteador e lê comandos do usuário.

- `router.py`
  
  Classe Router, contendo:
  
  - Estruturas `neighbors`, `routing_table`, `last_update_received`.
  
  - Threads para receber pacotes (`receive_loop`) e enviar updates (`update_loop`).
  
  - Métodos para lidar com mensagens `update`, `data`, `trace`.

- `commands.py`
  
  Processa o que o usuário digita (`add`, `del`, `trace`, `send`, etc.), chamando os métodos do router.

- `distance_vector.py`
  
  Função `update_routing_table`, que implementa o algoritmo de vetor de distâncias (soma de custos, atualização de rotas).

