import random
import math
from collections import defaultdict
import os
import time

world_size_x = 70
world_size_y = 30

start_trees = int(world_size_y * world_size_x * 0.3)
max_spawn_tree = random.randint(1, 3)

basic_animal_hp = 5
basic_plante_hp = 5


class World:
    def __init__(self, heigth: int = 30, width: int = 60):
        self.count_animal = 0
        self.count_plante = 0
        self.heigth = heigth
        self.width = width
        self.all_pos_in_world = dict()
        self.entities = defaultdict(set)
        self.free_pos = list()
        self.animal_list = [Animals(self) for i in range(int(self.heigth * self.width))]
        self.plante_list = [Plante(self) for i in range(int(self.heigth * self.width))]

    def catch_animal(self):
        count = 0
        while True:
            count += 1
            self.count_animal += 1
            if (
                animal := self.animal_list[self.count_animal % len(self.animal_list)]
            ).is_active:
                continue
            return animal

    def catch_plante(self):
        while True:
            self.count_plante += 1
            if (
                plante := self.plante_list[self.count_plante % len(self.plante_list)]
            ).is_active:
                continue
            return plante

    def free_around(self, pos: tuple[int]) -> list:
        free_around_pos = list()
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == j == 0:
                    continue
                corr = (pos[0] + i, pos[1] + j)
                if not corr in self.all_pos_in_world:
                    continue
                if self.all_pos_in_world[corr] is None:
                    free_around_pos.append(corr)
        return free_around_pos

    # def tree_spawn(self, start: int = 0):
    #     for pos in random.sample(
    #         self.free_pos,
    #         min(random.randint(0, max_spawn_tree), len(self.free_pos)),
    #     ):
    #         if any(isinstance(i, Animals) for i in self.free_around(pos=pos)):
    #             plante = self.catch_plante()
    #             plante.born(pos)

    def tree_spawn(self, start: int = 0):
        if start > 0:
            count_to_spawn = start
        else:
            count_to_spawn = random.randint(1, max_spawn_tree)

        count_to_spawn = min(count_to_spawn, len(self.free_pos))
        if count_to_spawn == 0:
            return

        # Берем случайные позиции из свободных
        sampled_positions = random.sample(self.free_pos, count_to_spawn)

        for pos in sampled_positions:
            # На старте (start > 0) игнорируем любые проверки и заселяем карту!
            if start > 0:
                plante = self.catch_plante()
                plante.born(pos)
            else:
                # В обычные тики: спавним только если вокруг НЕТ животных
                # (Проверьте, что free_around возвращает объекты, а не координаты клеток!)
                neighbors = self.free_around(pos=pos)

                # Если среди соседей нет ни одного животного, то спавним куст
                if not any(isinstance(i, Animals) for i in neighbors):
                    plante = self.catch_plante()
                    plante.born(pos)

    def spawn_world(self):
        self.all_pos_in_world.clear()
        self.free_pos.clear()
        self.free_pos.extend(
            [(x, y) for x in range(self.width) for y in range(self.heigth)]
        )
        self.all_pos_in_world.update(
            {(x, y): None for x in range(self.width) for y in range(self.heigth)}
        )
        for animal in self.animal_list:
            animal.die()
        for plante in self.plante_list:
            plante.die()

        self.entities.clear()
        self.tree_spawn(max_spawn_tree)

    # захват клетки
    def catch(self, position: tuple[int], entity: Entities):
        self.all_pos_in_world[position] = entity

    # очистка клетки
    def clean(self, position: tuple[int]):
        self.all_pos_in_world[position] = None

    def draw(self):
        os.system("cls" if os.name == "nt" else "clear")
        print("-" * (self.width + 2))
        for y in range(self.heigth):
            print("|", end="")
            for x in range(self.width):
                print(
                    (
                        self.all_pos_in_world[(x, y)].look
                        if self.all_pos_in_world[(x, y)] is not None
                        else " "
                    ),
                    end="",
                )
            print("|")
        print("-" * (self.width + 2))

    # в случае вызова мира как функции ()
    def __call__(self):
        return self.all_pos_in_world


class Entities:
    def __init__(self, world: World):
        self.world = world
        self.x = -1
        self.y = -1
        self.hp = 0
        self.gen = 0
        self.is_active = False

    # безболезненная выдача координаты
    @property
    def pos(self):
        return (self.x, self.y)

    # переезд на другую клетку
    def change_position(self, pos: tuple[int] = (-1, -1)):
        self.world.all_pos_in_world[(self.x, self.y)] = None  # очищение старой клетки
        self.world.free_pos.append(
            (self.x, self.y)
        )  # добавление ее в список пустых клеток
        if (
            self.world.all_pos_in_world[pos] is None
        ):  # если клетка пустая, то удаляем ее из свободных
            self.world.free_pos.remove(pos)
        self.world.all_pos_in_world[pos] = self  # перемещение в глобальной карте
        self.x, self.y = pos  # смена координат объекта

    def free_around(self) -> list:
        free_around_pos = list()
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == j == 0:
                    continue
                corr = (self.x + i, self.y + j)
                if not corr in self.world.all_pos_in_world:
                    continue
                if self.world.all_pos_in_world[corr] is None:
                    free_around_pos.append(corr)
        return free_around_pos

    def born(self, pos: tuple[int], gen: int):
        self.x, self.y = pos
        self.hp = gen + random.choice([-2, -1, 0, 0, 0, 0, 1, 2])
        self.gen = self.hp
        self.is_active = True
        self.world.all_pos_in_world[pos] = self
        self.world.free_pos.remove(pos)
        self.world.entities[type(self)].add(self)

    def die(self):
        if not self.is_active:
            return None
        self.is_active = False
        if self in self.world.entities[type(self)]:
            self.world.entities[type(self)].discard(self)

        if self.world.all_pos_in_world[self.pos] == self:
            self.world.free_pos.append(self.pos)
            self.world.all_pos_in_world[self.pos] = None
        elif self.world.all_pos_in_world.get(self.pos) is None:
            if self.pos not in self.world.free_pos:
                self.world.free_pos.append(self.pos)


class Animals(Entities):
    def __init__(self, world: World):
        super().__init__(world)
        self.hungry = 0

    @property
    def look(self):
        return "8" or f"!{self.hp}!"

    def born(self, pos: tuple[int], gen: int = basic_animal_hp):
        super().born(pos, gen)
        self.hungry = max(1, int(self.hp / basic_animal_hp**1.62))

    # обзор, что есть вокруг, возвращает пустые клетки и деревья 'словарем' key = pos, value = distant
    def review(self) -> dict:
        answer = {"empty": dict(), "plants": dict()}
        for x in range(-1, 2):
            for y in range(-1, 2):
                position = (self.x + x, self.y + y)
                if position == (self.x, self.y):
                    continue
                dist = math.dist(position, (self.x, self.y))
                if position in self.world.all_pos_in_world:
                    if self.world.all_pos_in_world[position] is None:
                        answer["empty"][position] = dist
                    elif isinstance(self.world.all_pos_in_world[position], Plante):
                        answer["plants"][position] = dist
        # print(answer)

        # time.sleep(1)
        return answer

    # прием пищи и смещение на их позицию
    def eat(self, plants_position: dict) -> None:
        # находим ближайший куст
        nearest_positions = sorted(plants_position, key=plants_position.get)[
            : min(len(plants_position), self.hungry + 1)
        ]

        if not nearest_positions:
            return
        for i in nearest_positions:

            plante = self.world.all_pos_in_world[i]
            plante.die()

            self.hp += 1
        # смещение на позицию растения
        self.change_position(i)

        self.childbirth()

    # def eat(self, plants_position: dict) -> None:
    #     nearest_positions = sorted(plants_position, key=plants_position.get)[
    #         : min(len(plants_position), self.hungry + 2)
    #     ]
    #     random.shuffle(nearest_positions)

    #     if not nearest_positions:
    #         return

    #     # Считаем, сколько кустов реально съедим
    #     eaten_count = len(nearest_positions)

    #     for i in nearest_positions:
    #         plante = self.world.all_pos_in_world[i]
    #         plante.die()

    #     # Математика прототипа: меняем здоровье на разницу между аппетитом и съеденным
    #     # Если съел больше, чем hungry -> пойдет в плюс. Если меньше -> в минус.
    #     self.hp += eaten_count - self.hungry

    #     # Перемещаемся на место последнего съеденного куста
    #     self.change_position(i)
    #     self.childbirth()

    def childbirth(self):
        count_born = random.choice([0, 0, 0, 0, 0, 0, 1])
        free_pos_for_born = self.free_around()
        count_born = min(count_born, len(free_pos_for_born))
        for pos in random.sample(free_pos_for_born, count_born):
            self.hp -= 1
            animal = world.catch_animal()
            animal.born(pos, self.gen)

    # def childbirth(self):
    #     # Рожаем, только если накоплен избыток здоровья (хотя бы в 1.5 раза больше нормы)
    #     if self.hp < (self.gen * 1.5):
    #         return

    #     count_born = random.choice([0, 0, 0, 0, 0, 0, 1, 2])
    #     free_pos_for_born = self.free_around()
    #     count_born = min(count_born, len(free_pos_for_born))

    #     for pos in random.sample(free_pos_for_born, count_born):
    #         # Проверяем, выдержит ли родитель передачу энергии
    #         if self.hp > self.gen + 2:
    #             self.hp -= (
    #                 self.gen
    #             )  # ЧЕСТНО отнимаем у родителя столько, сколько отдаем ребенку
    #             animal = world.catch_animal()
    #             animal.born(pos, self.gen)
    #         else:
    #             break

    def move(self, free_pos: dict):
        self.change_position(random.choice(list(free_pos.keys())))

    def manager_action(self, answer_from_review: dict):

        self.hp -= self.hungry
        # print(answer_from_review)
        if answer_from_review["plants"]:
            self.eat(answer_from_review["plants"])
            return None
        elif answer_from_review["empty"]:
            self.move(answer_from_review["empty"])
        return None


class Plante(Entities):
    def __init__(self, world: World):
        super().__init__(world)
        self.look = "*"
        self.maturation_period = 0
        self.maturation_timer = 0

    def born(self, pos: tuple[int], gen: int = basic_plante_hp):
        super().born(pos, gen)
        self.maturation_period = self.hp // random.randint(1, 3)
        self.maturation_timer = 0

    def budding(self):
        self.maturation_timer += 1
        if random.random() < 0.1:
            self.maturation_timer += 1

        if self.maturation_timer >= self.maturation_period:
            self.maturation_timer = 0

            how_many_born = random.randint(0, 8)
            review_around = self.free_around()
            if review_around:
                random.shuffle(review_around)
                free_pos_for_born = iter(review_around)
                for _ in range(min(how_many_born, len(review_around))):
                    pos = next(free_pos_for_born)
                    plant = self.world.catch_plante()
                    plant.born(pos, plant.gen)


# def on


def work(world: World):
    day = 0

    world.spawn_world()
    positin_first_animal = random.choice(world.free_pos)
    first_animal = world.catch_animal()
    first_animal.born(positin_first_animal)
    world.tree_spawn(start_trees)
    while True:
        day += 1
        time_now = time.time()

        world.tree_spawn(max_spawn_tree)
        for animal in world.entities[Animals].copy():
            # print(animal.hungry, animal.hp)
            if animal.hp < 1:
                animal.die()
                continue
            review = animal.review()
            animal.manager_action(review)

        for plante in world.entities[Plante].copy():
            plante.hp -= 1
            if plante.hp < 1:
                plante.die()
                continue
            plante.budding()

        if len(world.entities[Animals]) == 0:
            return

        world.draw()
        print(f"{day} день")
        print(f"{time.time()-time_now} время отработки")
        print(f"{len(world.entities[Animals])} животных")
        print(f"{len(world.entities[Plante])} растений")

        time.sleep(0)


world = World(heigth=world_size_y, width=world_size_x)
work(world=world)
