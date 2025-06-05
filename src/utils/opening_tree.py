class OpeningTreeNode:
    def __init__(self, move=None):
        self.move = move
        self.eco_code = None
        self.family = None
        self.opening_name = None
        self.children = {}

class OpeningTree:
    def __init__(self):
        self.root = OpeningTreeNode()

    def insert(self, eco_code, family, moves_list, opening_name):
        node = self.root
        for move in moves_list:
            if move not in node.children:
                node.children[move] = OpeningTreeNode(move)
            node = node.children[move]
        node.eco_code = eco_code
        node.family = family
        node.opening_name = opening_name


    def search(self, moves_list):
        node = self.root
        last_valid_eco = None
        last_valid_family = None
        last_valid_opening = None

        for move in moves_list:
            if move in node.children:
                node = node.children[move]
                if node.opening_name:
                    last_valid_eco = node.eco_code
                    last_valid_family = node.family
                    last_valid_opening = node.opening_name
            else:
                break

        if last_valid_eco and last_valid_family and last_valid_opening:
            return last_valid_eco, last_valid_family, last_valid_opening
        else:
            return None, None



    def _get_depth(self, node):
        if not node.children:
            return 1
        return 1 + max(self._get_depth(child) for child in node.children.values())

    def get_max_depth(self):
        return self._get_depth(self.root)

    def _print_node(self, node, prefix="", eco_filter=None):
        for move, child in node.children.items():
            display = f"{prefix}{move}"
            if child.opening_name and (eco_filter is None or child.eco_code == eco_filter):
                display += f"  <-- {child.eco_code}: {child.opening_name}"
            if eco_filter is None or child.eco_code == eco_filter or any(
                c.eco_code == eco_filter for c in child.children.values()
            ):
                print(display)
                self._print_node(child, prefix + "  ", eco_filter)


    def print_tree(self, eco_filter=None):
        print("Opening Tree:")
        self._print_node(self.root, prefix="", eco_filter=eco_filter)
