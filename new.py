import random
import os
import time

# --- БАЗОВЫЕ ЗНАЧНИЕ ---
sizeX, sizeY = (80, 40) or map(int, input("ВВедите размеры мира:").split())
free_place = " "
plante = "*"
animal = "8"
maxSpawnTree = random.randint(1, 3)
max_hp_animal = random.randint(3, 5)
max_hp_plante = 10
durating = 0.02
start_tree = int((sizeX * sizeY) * 0.1)


class World:
    def __init__(self, x, y):
        self.width = x
        self.height = y
        self.registry = {}
        self.all_place = {(nx, ny): None for ny in range(y) for nx in range(x)}
        self.all_free_pos = [pos for pos in self.all_place]

    def occupy(self, pos, obj):

        self.all_place[pos] = obj
        self.all_free_pos.remove(pos)

        obj_type = type(obj)

        if obj_type not in self.registry:
            self.registry[obj_type] = set()
            self.registry[obj_type].add(obj)
        else:
            self.registry[obj_type].add(obj)

    def rewind(self, pos):
        if pos != None:
            old_obj = self.all_place[pos]
            old_obj_type = type(old_obj)
            self.registry[old_obj_type].discard(old_obj)

            self.all_place[pos] = None
            self.all_free_pos.append(pos)

    def get_empty_place(self):
        if self.all_free_pos:
            return random.choice(self.all_free_pos)
        return None

    def __iter__(self):
        return iter(list(self.all_place.keys()))

    def __len__(self):
        return len(self.all_place)


class Entitiy:
    def __init__(self, x, y, gen):
        self.x = x
        self.y = y
        mutation = random.choice([-3, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
        self.hp = max(mutation + gen, 1)
        self.max_hp_with_burn = self.hp

    @property
    def pos(self):
        return (self.x, self.y)


class Animal(Entitiy):
    def __init__(self, x, y, gen=max_hp_animal):
        super().__init__(x, y, gen)
        self.hungry = 1
        self.look = "8"
        if self.hp >= max_hp_animal * 2:
            self.hungry += int((self.hp // max_hp_animal - 1) ** 1.42)

    def think(self, viev, world):
        target = []
        posible_move = []
        for pos in viev:
            coor = world.all_place.get(pos)
            if isinstance(coor, Plante):
                target.append(pos)
            elif pos is None:
                posible_move.append(pos)

        # ЕДА ЕСТЬ
        if target:
            return "ЕДА", target
        return "ДВИЖЕНИЕ", (
            random.choice(posible_move) if posible_move else (self.x, self.y)
        )


class Plante(Entitiy):
    def __init__(self, x, y, gen=max_hp_plante):
        super().__init__(x, y, gen)
        self.look = "*"
        self.repro = self.hp // random.randint(1, 3)
        self.repro_timer = 0


# СПАВН ДЕРЕВЬЕВ
def SpawnTrees(maxSpawnTree, world):
    for _ in range(maxSpawnTree):
        tree_pos = world.get_empty_place()
        if tree_pos:
            world.occupy(tree_pos, Plante(*tree_pos))


def budding(plante, world):
    possible_place_for_born = set()
    count_burn = random.randint(1, 4)
    for x in [-1, 0, 1]:
        coorX = plante.x + x
        if not world.width > coorX >= 0:
            continue
        for y in [-1, 0, 1]:
            if x == y == 0:
                continue

            coorY = plante.y + y
            if not world.height > coorY >= 0:
                continue
            if (coorX, coorY) in world.all_free_pos:
                possible_place_for_born.add((coorX, coorY))

    if possible_place_for_born:
        max_seed = min(len(possible_place_for_born), count_burn)
        return random.sample(list(possible_place_for_born), max_seed)
    return []


def viev_animal(animal_one, world):
    viev_an = []
    radius = animal_one.hungry
    for dx in range(-radius, radius + 1):
        numX = animal_one.x + dx
        if not world.width > numX >= 0:
            continue
        for dy in range(-radius, radius + 1):
            if dx == dy == 0:
                continue
            numY = animal_one.y + dy
            if not world.height > numY >= 0:
                continue
            viev_an.append((numX, numY))
    return viev_an


def working():
    day = 0
    count = 0
    while day < 20:
        day = 0
        day = run_simulator(day)
        time.sleep(durating)
        count += 1
    print(f"Симуляций было {count}")


def run_simulator(day):
    world = World(sizeX, sizeY)
    display_world = [[" " for _ in range(world.width)] for _ in range(world.height)]
    # СТАРТОВОЕ ЖИВОТНОЕ
    first_animal = world.get_empty_place()
    world.occupy(first_animal, Animal(*first_animal))

    # СТАРТОВЫЕ ДЕРЕВЬЯ
    for _ in range(start_tree):
        firsts_tree = world.get_empty_place()
        world.occupy(firsts_tree, Plante(*firsts_tree))

    maxim = 0
    const = 0
    while True:

        # СПАВН ДЕРЕВЬЕВ
        SpawnTrees(maxSpawnTree, world)

        # ЖИВОТНЫЕ
        for org in world.registry.get(Animal, set()).copy():
            if org.hp < 1:
                world.rewind(org.pos)
                continue

            # Зрение
            viev_org = viev_animal(org, world)
            # действие
            action, eat_or_move = org.think(viev_org, world)
            possible_move = [i for i in viev_org if world.all_place[i] is None]
            if action == "ЕДА":
                # доступные кусты
                available_plants = eat_or_move
                # сколько может съесть (добавил жадность, чтобы можно было реально много жить)
                max_can_eat = min(len(available_plants), org.hungry + 1)
                # выбираем кусты
                chosen_plants_coords = random.sample(eat_or_move, max_can_eat)
                org.hp -= org.hungry - len(chosen_plants_coords)

                # едим
                for pos in chosen_plants_coords:
                    world.rewind(pos)
                    possible_move.append(pos)
                count_child = min(len(possible_move), random.choice([0, 0, 1, 1, 1, 2]))

                gen = org.max_hp_with_burn
                where_born = random.sample(possible_move, count_child)

                # Рождение
                for possibl in where_born:
                    animals = Animal(*possibl, gen)
                    world.occupy(possibl, animals)
                    maxim = max(animals.max_hp_with_burn, maxim)

            elif action == "ДВИЖЕНИЕ":
                if possible_move:
                    # ОСВОБОЖДАЕМ СТАРОЕ МЕСТО И ИЩЕМ НОВОЕ
                    free = random.choice(possible_move)
                    world.rewind(org.pos)
                    possible_move.append(org.pos)
                    # делаем шаг

                    org.x, org.y = free
                    world.occupy(free, org)
                    possible_move.remove(free)
                    org.hp -= org.hungry
                    maxim = max(org.hp, maxim)

        # РАСТЕНИЯ
        for pl in world.registry.get(Plante, set()).copy():
            if pl.hp <= 0:
                world.rewind(pl.pos)
                continue
            pl.repro_timer += 1
            if pl.repro_timer == pl.repro:
                pl.repro -= 1
                pl.repro_timer = 0
                for pos in budding(pl, world):
                    world.occupy(pos, Plante(*pos))
            pl.hp -= 1

        const = max(maxim, const)

        # СТИРАЕМ КОНСОЛЬ
        os.system("cls" if os.name == "nt" else "clear")

        # РИСУЕМ
        print("-" * (world.width + 2))
        for row in world:
            if world.all_place[row] is not None:
                display_world[row[1]][row[0]] = world.all_place[row].look
            else:
                display_world[row[1]][row[0]] = " "
        for strs in display_world:
            print("|" + "".join(strs) + "|")
        print("-" * (world.width + 2))

        print(f"День {day}")
        print(f"Популяция: {len(world.registry.get(Animal, set()))}")
        print(f"Максимальная продолжительность жизни сегодня {maxim}")
        print(f"Максимальная продолжительность жизни {const}")
        maxim = 0
        if not world.registry.get(Animal, set()):
            if day < 20:
                return day
            else:
                if day < 100:
                    print("Они не смогли...")
                else:
                    print("Они держались дойстойно!")
                return day
        time.sleep(durating)
        day += 1


if __name__ == "__main__":
    working()
