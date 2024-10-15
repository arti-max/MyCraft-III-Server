class Structures:
    def __init__(self):
        # Инициализация структур
        self.structures = {
            'tree': self.create_tree_structure()
        }

    def create_tree_structure(self):
        tree_structure = {
            (0, 0, 0): 'wood',
            (0, 1, 0): 'wood',
            (0, 2, 0): 'wood',
            (0, 3, 0): 'wood',

            (-1, 2, 0): 'leaves',
            (1, 2, 0): 'leaves',
            (0, 2, -1): 'leaves',
            (0, 2, 1): 'leaves',

            (-1, 3, 0): 'leaves',
            (1, 3, 0): 'leaves',
            (0, 3, -1): 'leaves',
            (0, 3, 1): 'leaves',

            (0, 4, 0): 'leaves',
        }
        return tree_structure

    def get_structure(self, name):
        return self.structures.get(name, {})