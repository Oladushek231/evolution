import random
from collections import defaultdict
import math
import os

max_spawn_tree = 3

basic_animal_hp = 5
basic_plante_hp = 5


class World:
    def __init__(self, heigth: int = 30, width: int = 60):
        # счетчики для прочитывания стеков существ
        self.count_animal = 0
        self.count_plante = 0
        self.heigth = heigth
        self.width = width
        # матрица 2д мира
        self.all_pos_in_world = dict()
        # словарь всех реальных сущностей
        self.entities = defaultdict(set)
        # все пустные клетки
        self.free_pos = list()

        # списки болванок для быстрого спавна
        self.animal_list = [Animals(self) for _ in range(int(self.heigth * self.width))]
        self.plante_list = [Plante(self) for _ in range(int(self.heigth * self.width))]

    # Дергаем болванки животных из стека, если они не активны
    def catch_animal(self):
        while True:
            # прокручиваем счетчик
            self.count_animal += 1
            if (
                animal := self.animal_list[self.count_animal % len(self.animal_list)]
            ).is_active:
                continue
            return animal

    # Дергаем болванки растений из стека, если они не активны
    def catch_plante(self):

        while True:
            # прокручиваем счетчик
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

    # создание деревьев в мире
    def tree_spawn(self, start: int = 0):
        # если значение задано, то выводим именно столько деревьев, в противном случае генерируем
        if start > 0:
            count_to_spawn = start
        else:
            count_to_spawn = random.randint(1, max_spawn_tree)

        # смотрим, сколько можно создать впринцепи
        count_to_spawn = (
            count_to_spawn
            if count_to_spawn <= len(self.free_pos)
            else len(self.free_pos)
        )
        # если нисколько, то закрываем
        if count_to_spawn == 0:
            return

        # Берем случайные позиции из свободных
        sampled_positions = random.sample(self.free_pos, count_to_spawn)

        # начинаем их перебирать
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

    # создаение мира это не про спавн всего вокруг, а про очистку прошлых данных и убийство всех существ
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

    # отрисовка мира
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


# общий класс всех сщустве
class Entities:
    def __init__(self, world: World):
        self.world = world
        self.x = -1
        self.y = -1
        self.hp = 0
        # показывает, сколько было хп на момент рождения
        self.gen = 0
        # показывает, живо ли существо
        self.is_active = False

    # безболезненная выдача координаты
    @property
    def pos(self):
        return (self.x, self.y)

    # переезд на другую клетку
    def change_position(self, pos: tuple[int] = (-1, -1)):
        # очищение старой клетки
        self.world.all_pos_in_world[(self.x, self.y)] = None
        # добавление ее в список пустых клеток
        self.world.free_pos.append((self.x, self.y))
        # если клетка пустая, то удаляем ее из свободных
        if self.world.all_pos_in_world[pos] is None:
            self.world.free_pos.remove(pos)
        self.world.all_pos_in_world[pos] = self  # перемещение в глобальной карте
        self.x, self.y = pos  # смена координат объекта

    #
    def free_around(self) -> list:
        # создаем список пустых клеток в радиусе 1 клетки
        free_around_pos = list()
        for i in range(-1, 2):
            for j in range(-1, 2):
                # пропускаем себя
                if i == j == 0:
                    continue
                corr = (self.x + i, self.y + j)
                if not corr in self.world.all_pos_in_world:
                    continue
                if self.world.all_pos_in_world[corr] is None:
                    free_around_pos.append(corr)
        return free_around_pos

    # рождение
    def born(self, pos: tuple[int], gen: int):
        self.x, self.y = pos
        # создаем новое здоровье на основе роительского и мутации
        self.hp = gen + random.choice([-2, -1, 0, 0, 0, 0, 1, 2])
        # обновляем ген
        self.gen = self.hp
        self.is_active = True
        # занимаем место в мире
        self.world.all_pos_in_world[pos] = self
        self.world.free_pos.remove(pos)
        self.world.entities[type(self)].add(self)

    # смерть
    def die(self):
        # если существо и так мертво, то скип
        if not self.is_active:
            return None
        # выключаем
        self.is_active = False
        # удаляем существо из реестра всех существ
        if self in self.world.entities[type(self)]:
            self.world.entities[type(self)].discard(self)
        # очищаем клетку
        if self.world.all_pos_in_world[self.pos] == self:
            self.world.free_pos.append(self.pos)
            self.world.all_pos_in_world[self.pos] = None
        # обновляем список пустых клеток в любом случае
        elif self.world.all_pos_in_world.get(self.pos) is None:
            if self.pos not in self.world.free_pos:
                self.world.free_pos.append(self.pos)


# подкласс существ - Животные
class Animals(Entities):
    def __init__(self, world: World):
        super().__init__(world)
        # появляется голод
        self.hungry = 0

    # создано для более удобного просмотра происходящего, вместо животного показывает его здоровье
    @property
    def look(self):
        return "8" or f"!{self.hp}!"

    # в рождении прописывается специальная формула голода
    def born(self, pos: tuple[int], gen: int = basic_animal_hp):
        super().born(pos, gen)
        self.hungry = max(1, int(self.hp / basic_animal_hp**1.62))

    # переосмысленная free-around
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
        return answer

    # прием пищи и смещение на их позицию
    def eat(self, plants_position: dict) -> None:
        how_many_eat = (
            self.hungry + 1
            if self.hungry + 1 < len(plants_position)
            else len(plants_position)
        )
        # находим ближайший куст
        nearest_positions = sorted(plants_position, key=plants_position.get)[
            : how_many_eat + 1
        ]

        #
        for i in nearest_positions:
            #
            plante = self.world.all_pos_in_world[i]
            plante.die()
            #
            self.hp += 1
        # смещение на позицию растения
        self.change_position(i)
        # раз поели, то можно и родить
        self.childbirth()

    def childbirth(self):
        # Рожаем, только если накоплен избыток здоровья (хотя бы в 1.5 раза больше нормы)
        if self.hp < (self.gen * 1.5):
            return

        # выбираем, сколько родим
        count_born = random.choice([0, 0, 0, 0, 0, 0, 1, 2])
        free_pos_for_born = self.free_around()
        count_born = (
            count_born
            if count_born <= len(free_pos_for_born)
            else len(free_pos_for_born)
        )

        for pos in random.sample(free_pos_for_born, count_born):
            # Проверяем, выдержит ли родитель передачу энергии
            if self.hp > self.gen + 2:
                self.hp -= (
                    self.gen
                )  # ЧЕСТНО отнимаем у родителя столько, сколько отдаем ребенку
                animal = self.world.catch_animal()
                animal.born(pos, self.gen)
            else:
                break

    # двигаемся, раз не поели
    def move(self, free_pos: dict):
        self.change_position(random.choice(list(free_pos.keys())))

    # выбираем, что будем делать
    def manager_action(self, answer_from_review: dict):

        self.hp -= self.hungry
        if answer_from_review["plants"]:
            self.eat(answer_from_review["plants"])
            return None
        elif answer_from_review["empty"]:
            self.move(answer_from_review["empty"])
        return None


# подкласс сущностей - Растения
class Plante(Entities):
    def __init__(self, world: World):
        super().__init__(world)
        self.look = "*"
        # добавляются репродуктивные циклы
        self.maturation_period = 0
        self.maturation_timer = 0

    def born(self, pos: tuple[int], gen: int = basic_plante_hp):
        super().born(pos, gen)
        self.maturation_period = self.hp // random.randint(1, 3)
        self.maturation_timer = 0

    # размножение
    def budding(self):
        self.hp -= 1
        self.maturation_timer += 1
        # с некоторым шансом размножение может случиться раньше
        if random.random() < 0.1:
            self.maturation_timer += 1
        # если счетчик дошел до отметки, то сбрасываем его и размножаемся
        if self.maturation_timer >= self.maturation_period:
            self.maturation_timer = 0
            # если есть где сажать, то сажаем
            if review_around := self.free_around():
                #
                random.shuffle(review_around)

                # сколько будем сажать?
                how_many_born = random.randint(0, 8)
                how_many_born = (
                    how_many_born
                    if how_many_born < len(review_around)
                    else len(review_around)
                )
                # выбираем позиции
                free_pos_for_born = random.sample(review_around, how_many_born)
                # сажаем
                for pos in free_pos_for_born:
                    plant = self.world.catch_plante()
                    plant.born(pos, plant.gen)
