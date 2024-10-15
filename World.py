from ursina import *
import asyncio
import pickle
import os
from noise import pnoise2 
from Structures import Structures  

# Глобальный словарь для хранения состояния всех блоков в мире
world_dict = {}
world_list = []

class World(Entity):
    def __init__(self, chunk_size=4, world_size=64, world_height=20):
        super().__init__()
        self.world_size = world_size
        self.chunk_size = chunk_size
        self.world_height = world_height
        self.structures = Structures()  # Инициализируем класс Structures
        self.initialize_world_blocks()

    def getWorldDict(self):
        global world_dict
        return world_dict

    def getWorldList(self):
        global world_list
        return world_list

    def save_world(self):
        """Сохраняет состояние мира в файл level.dat."""
        with open('level.dat', 'wb') as file:
            pickle.dump(world_list, file)
        #print(f"Level saved in level.dat")

    def initialize_world_blocks(self):
        global world_dict, world_list

        if os.path.exists('level.dat'):
            with open('level.dat', 'rb') as file:
                world_list = pickle.load(file)
                #print(world_list)

            for block in world_list:
                x, y, z, block_type = block
                world_dict[(x, y, z)] = block_type
            print("Level loaded from level.dat")
            
        else:
            # Инициализация мира с использованием шума Перлина
            scale = 50.0  # Масштаб для шума Перлина
            octaves = 35  # Количество октав
            persistence = 0.5  # Стойкость
            lacunarity = 2.0  # Лакунарность

            for x in range(self.world_size):
                for z in range(self.world_size):
                    height = int((pnoise2(x / scale, z / scale, octaves=octaves, 
                                          persistence=persistence, lacunarity=lacunarity) + 1) / 2 * self.world_height)
                    height = max(1, height)

                    for y in range(height):
                        pos = (x, y, z)
                        if y < height - 1:
                            world_dict[tuple(pos)] = 'stone'
                        else:
                            world_dict[tuple(pos)] = 'grass'

                    # Добавляем деревья с некоторой вероятностью
                    if height > 1 and random.random() < 0.02:  # 10% шанс появления дерева
                        self.add_structure('tree', x, height, z)

            world_list = [[x, y, z, block_type] for (x, y, z), block_type in world_dict.items()]
            print("Level initialized using perlin noise")
            
    def add_structure(self, structure_name, x, y, z):
        structure = self.structures.get_structure(structure_name)
        for (dx, dy, dz), block_type in structure.items():
            world_dict[(x + dx, y + dy, z + dz)] = block_type

    def destroy_block(self, position):
        del world_dict[position]
        self.remove_from_world_list(position)

    def create_block(self, position, block_type):
        # Создаем блок в чанке и добавляем в world_list
        self.add_to_world_list(position, block_type)
        world_dict[position] = block_type

    def add_to_world_list(self, position, block_type):
        global world_list
        entry = [position[0], position[1], position[2], block_type]
        #print(entry)
        if entry not in world_list:
            world_list.append(entry)

    def remove_from_world_list(self, position):
        global world_list
        world_list = [entry for entry in world_list if entry[:3] != list(position)]
        #print(world_list)

    def get_block_type_at_position(self, position):
        pos_tuple = (int(position[0]), int(position[1]), int(position[2]))
        return self.world_dict.get(pos_tuple)