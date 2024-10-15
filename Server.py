from ursinanetworking import *
from pickle import *
from jproperties import Properties
from World import World
import threading
import logging


block_types = ['grass', 'stone', 'wood', 'leaves', 'planks']

level_dict = {}
level_list = []
banned_players = []
connected_players = {}
bi = 0
bid = f"block_{bi}"

cfg = Properties()
with open('server.properties', 'rb') as prop:
    cfg.load(prop)

serverIP = cfg.get("server-ip").data
serverPORT = cfg.get("server-port").data
worldSize = int(cfg.get("world-size").data)
worldHeight = int(cfg.get("world-height").data)

if os.path.exists('./banned.txt'):
    with open('banned.txt', 'r') as bpf:
        lines = bpf.readlines()
        for line in lines:
            banned_players.append(line.strip())

Server = UrsinaNetworkingServer(serverIP, int(serverPORT))
Easy = EasyUrsinaNetworkingServer(Server)

world = World(chunk_size=4, world_size=worldSize, world_height=worldHeight)

level_dict = world.getWorldDict()
level_list = world.getWorldList()

server_running = True  # Флаг для управления работой сервера

# Destroy Block Func
def destroy_block(position):
    world.destroy_block(position)
    Easy.remove_replicated_variable_by_name(position)

# Spawn Block Func
def spawn_block(block_type, position, investigator):
    global bi
    global block_types
    block_name = f"blocks_{bi}"
    if block_type in block_types:
        Easy.create_replicated_variable(position, { "type" : "block", "block_type" : block_type, "inv": investigator})
        world.create_block(position, block_type)
        bi += 1 
    if investigator == "client":
        world.save_world()

# Инициализация мира
for item in level_list:
    position = (item[0], item[1], item[2])
    btype = item[3]
    spawn_block(btype, position, "server")
    if position == (63, 8, 63):
        print('World succefully sended to clients')

@Server.event
def onClientConnected(Client):
    print(f"{Client} has been connected!")
    Easy.create_replicated_variable(f"player_{Client.id}", { "type" : "player", "id" : Client.id, "position" : (worldSize/2, 10, worldSize/2) })
    Client.send_message("GetId", Client.id)
    Client.send_message("setSpawnPos", (worldSize/2, 10, worldSize/2))
    Client.send_message("getWorldList", world.getWorldList())

@Server.event
def onClientDisconnected(Client):
    Easy.remove_replicated_variable_by_name(f"player_{Client.id}")
    print(f"{Client} has been disconnected")
    for player in connected_players:
        client2 = connected_players[player]
        if client2 == Client:
            del connected_players[player]

@Server.event
def getPlayerName(Client, playerName):
    if playerName not in banned_players:
        if playerName not in connected_players:
            connected_players[playerName] = Client
            print(f"pname: {playerName}, connected_players: {connected_players}")
        else:
            Client.send_message("disconnect", "name")
    else:
        Client.send_message("disconnect", "ban")

@Server.event
def place_block(Client, Content):
    print(Content)
    spawn_block(Content["block_type"], Content["position"], "client")

@Server.event
def replace_block(Client, position):
    destroy_block(tuple(position))

@Server.event
def MyPosition(Client, Position):
    Easy.update_replicated_variable_by_name(f"player_{Client.id}", "position", Position)

@Server.event
def MyHeadRotate(Client, Rotate):
    Easy.update_replicated_variable_by_name(f"player_{Client.id}", "rotate", Rotate)

# Функция для обработки ввода команд
def command_input():
    while True:
        cmd = input()
        if cmd.strip().lower() == 'stop':
            print("Остановка сервера...")
            global server_running
            global world
            world.save_world()
            server_running = False
            stop_server()  # Вызываем функцию для остановки сервера
            break
        elif cmd.strip().lower().startswith('ban'):
            try:
                global banned_players
                global connected_players
                elements = cmd.strip().lower().split()
                banned_players.append(elements[1].strip())
                client = connected_players[elements[1].strip()]
                client.send_message("disconnect", "ban")
                with open('banned.txt', 'w') as bpf:
                    strF = ""
                    for player in banned_players:
                        strF += f"{player}\n"
                    bpf.write(strF)
                print(f"player {elements[1].strip()} banned")
            except Exception as e:
                print(f"error: {e}")

        elif cmd.strip().lower().startswith('unban'):
            try:
                elements = cmd.strip().lower().split()
                banned_players.remove(elements[1].strip())
                with open('banned.txt', 'w') as bpf:
                    strF = ""
                    for player in banned_players:
                        strF += f"{player}\n"
                    bpf.write(strF)
                print(f"player {elements[1].strip()} unbanned")
            except Exception as e:
                print(f"error: {e}")

        elif cmd.strip().lower() == 'list':
            print('----Connected Players----')
            for player in connected_players:
                print(player)


        else:
            print(f"Неизвестная команда: {cmd}")

# Функция для остановки сервера
def stop_server():
    # Закрываем все клиентские соединения
    for client in list(Server.clients):
        try:
            send_message("disconnect", "stop")
            print(f"Клиент {client.ID} был отключен.")
        except Exception as e:
            print(f"Ошибка при отключении клиента {client.ID}: {e}")

    # Закрываем серверный сокет
    try:
        Server.server.close()
        print("Серверный сокет закрыт.")
    except Exception as e:
        print(f"Ошибка при закрытии серверного сокета: {e}")

# Основной цикл сервера
def server_loop():
    while server_running:
        Easy.process_net_events()
    print("Серверный цикл остановлен.")

# Запускаем основной цикл сервера в отдельном потоке
server_thread = threading.Thread(target=server_loop)
server_thread.start()

# Запускаем поток для ввода команд
input_thread = threading.Thread(target=command_input)
input_thread.start()

# Ждем завершения потоков перед выходом
server_thread.join()
input_thread.join()
print("Сервер остановлен.")
