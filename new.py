import random
import os
import time
import copy

# --- БАЗОВЫЕ ЗНАЧНИЕ ---
sizeX, sizeY = (80, 40) or map(int, input("ВВедите размеры мира:").split())
# for i in range(sizeY):
# print(*["." for _ in range(sizeX)])
free_place = " "
plante = "*"
animal = "8"
maxSpawnTree = 1
max_hp_animal = random.randint(3, 5)
max_hp_plante = 10
durating = 0.02
start_tree = int((sizeX * sizeY) * 0.1)


class World:
    def __init__(self, x, y):
        self.free_place = {(nx, ny) for ny in range(y) for nx in range(x)}

    def occupy(self, pos):
        self.free_place.discard(pos)

    def rewind(self, pos):
        self.free_place.add(pos)

    def __iter__(self):
        return iter(list(self.free_place))

    def __len__(self):
        return len(self.free_place)


class Entitiy:
    def __init__(self, x, y, gen):
        self.x = x
        self.y = y
        mutation = random.choice([-3, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
        self.hp = max(mutation + gen, 1)
        self.maximka = self.hp

    @property
    def pos(self):
        return (self.x, self.y)


class Animal(Entitiy):
    def __init__(self, x, y, gen=max_hp_animal):
        super().__init__(x, y, gen)
        self.hungry = 1
        if self.hp >= max_hp_animal * 2:
            self.hungry += int((self.hp // max_hp_animal - 1) ** 1.42)

    def think(self, viev, display):
        target = []
        posible_move = []
        for x, y in viev:
            if display[y][x] == plante:
                target.append((x, y))
            elif display[y][x] == " ":
                posible_move.append((x, y))

        # ЕДА ЕСТЬ
        if target:
            return "ЕДА", target
        self.hp -= self.hungry
        return "ДВИЖЕНИЕ", (
            random.choice(posible_move) if posible_move else (self.x, self.y)
        )


class Plante(Entitiy):
    def __init__(self, x, y, gen=max_hp_plante):
        super().__init__(x, y, gen)
        self.repro = self.hp // random.randint(1, 3)
        self.repro_timer = 0


# СПАВН ДЕРЕВЬЕВ
def SpawnTrees(maxSpawnTree, world):
    tree_spawned = set()
    for _ in range(maxSpawnTree):
        if world.free_place:
            treeX, treeY = random.choice(list(world.free_place))
            tree_spawned.add(Plante(treeX, treeY))
            world.occupy((treeX, treeY))

        else:
            break
    return list(tree_spawned)


def budding(plante, world):
    burned = []
    possible_move = set()
    count_burn = random.randint(1, 4)
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            if i == j == 0:
                continue
            coorX = plante.x + i
            coorY = plante.y + j
            if (coorX, coorY) in world.free_place:
                possible_move.add((coorX, coorY))

    if possible_move:
        num_real_born = min(len(possible_move), count_burn)
        real_burn = random.sample(list(possible_move), num_real_born)
        for i in real_burn:
            burned.append(i)
    return burned


def viev_animal(animal_one):
    viev_an = []
    for dx in range(-animal_one.hungry, animal_one.hungry + 1):
        for dy in range(-animal_one.hungry, animal_one.hungry + 1):
            if dx == dy == 0:
                continue
            numX = animal_one.x + dx
            numY = animal_one.y + dy
            if sizeX > numX >= 0 and sizeY > numY >= 0:
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
    display_world = [[" " for _ in range(sizeX)] for _ in range(sizeY)]
    world = World(sizeX, sizeY)
    unit = set()
    tree = set()
    # СТАРТОВОЕ ЖИВОТНОЕ
    free_place = random.sample(list(world), 1)
    for pos in free_place:
        posX = pos[0]
        posY = pos[1]
        el = Animal(*pos)
        unit.add(el)
        world.occupy(pos)
        display_world[posY][posX] = animal

    # СТАРТОВЫЕ ДЕРЕВЬЯ
    free_place = random.sample(list(world), start_tree)
    for pos in free_place:
        posX = pos[0]
        posY = pos[1]
        tree.add(Plante(*pos))
        world.occupy(pos)
        display_world[posY][posX] = plante

    maxim = 0
    const = 0
    while True:

        # СПАВН ДЕРЕВЬЕВ
        dop = SpawnTrees(maxSpawnTree, world)
        for pos in dop:
            posX = pos.x
            posY = pos.y
            display_world[posY][posX] = plante
            tree.add(pos)

        # ЖИВОТНЫЕ
        next_gen = []
        lookup = {p.pos: p for p in tree}
        for org in unit:
            if org.hp < 1:
                display_world[org.y][org.x] = " "
                world.rewind(org.pos)
                continue
            viev_org = viev_animal(org)

            action, aff_food = org.think(viev_org, display_world)
            possible_move = {i for i in viev_org if i in world.free_place}
            if action == "ЕДА":
                how_many_eat = min(len(aff_food), org.hungry)
                really_eat = random.sample(aff_food, how_many_eat)
                org.hp -= org.hungry - len(really_eat)
                lookup = {p.pos: p for p in tree}
                for i in really_eat:
                    plante_obj = lookup.get(i)
                    if plante_obj:
                        tree.remove(plante_obj)
                    world.rewind(i)
                    display_world[i[1]][i[0]] = " "
                    possible_move.add(i)
                org.hp += len(really_eat)
                count_child = min(len(possible_move), random.choice([0, 0, 1, 1, 1]))

                gen = org.maximka
                where_born = random.sample(list(possible_move), count_child)

                for possibl in where_born:
                    el = Animal(*possibl, gen)
                    next_gen.append(el)
                    maxim = el.maximka if el.maximka > maxim else maxim
                    world.occupy(possibl)
                    possible_move.discard(possibl)
                    display_world[possibl[1]][possibl[0]] = animal

            else:
                if possible_move:
                    # ОСВОБОЖДАЕМ СТАРОЕ МЕСТО
                    display_world[org.y][org.x] = " "
                    world.rewind(org.pos)

                    # делаем шаг
                    org.x, org.y = random.choice(list(possible_move))
                    org.hp -= org.hungry
                    if org.hp > 0:
                        world.occupy(org.pos)
                        display_world[org.y][org.x] = animal
                    else:
                        world.rewind((org.x, org.y))

                    maxim = org.hp if org.hp > maxim else maxim
            next_gen.append(org)

        # РАСТЕНИЯ
        tree_time = []
        for pl in tree:
            if pl.hp <= 0:
                display_world[pl.y][pl.x] = " "
                world.rewind(pl.pos)
                continue
            pl.repro_timer += 1
            if pl.repro_timer == pl.repro:
                pl.repro -= 1
                pl.repro_timer = 0
                num_borned = budding(pl, world)
                for i in num_borned:
                    tree_time.append(Plante(*i))
                    world.occupy(i)
                    display_world[i[1]][i[0]] = plante
            pl.hp -= 1
            tree_time.append(pl)
        tree = {i for i in tree_time if i.hp > 0}

        const = maxim if maxim > const else const
        unit = [org for org in next_gen if org.hp > 0]

        # СТИРАЕМ КОНСОЛЬ
        os.system("cls" if os.name == "nt" else "clear")

        # РИСУЕМ
        print("-" * (sizeX + 2))
        for row in display_world:
            print("|" + "".join(row) + "|")
        print("-" * (sizeX + 2))

        print(f"День {day}")
        print(f"Популяция: {len(unit)}")
        print(f"Максимальная продолжительность жизни сегодня {maxim}")
        print(f"Максимальная продолжительность жизни {const}")
        maxim = 0
        if not unit:
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
