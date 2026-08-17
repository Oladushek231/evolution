import random
from entities import World, Animals, Plante
import time

world_size_x = 60
world_size_y = 30

start_trees = int(world_size_y * world_size_x * 0.3)


def work(world: World):
    day = 0
    fps = 0
    tick = 0
    time_now = time.time()

    world.spawn_world()
    positin_first_animal = random.choice(world.free_pos)
    first_animal = world.catch_animal()
    first_animal.born(positin_first_animal)
    world.tree_spawn(start_trees)
    while True:
        day += 1
        tick += 1

        world.tree_spawn()
        for animal in world.entities[Animals].copy():
            if animal.hp < 1:
                animal.die()
                continue
            review = animal.review()
            animal.manager_action(review)

        for plante in world.entities[Plante].copy():
            if plante.hp < 1:
                plante.die()
                continue
            plante.budding()

        if len(world.entities[Animals]) == 0:
            return

        if time.time() - time_now > 1:
            fps = tick
            tick = 0
            time_now = time.time()
        world.draw()
        print(f"{day} день")
        # print(f"{time.time()-time_now} время отработки")
        print(f"{len(world.entities[Animals])} животных")
        print(f"{len(world.entities[Plante])} растений")
        print(f"{fps} FPS")


world = World(heigth=world_size_y, width=world_size_x)
work(world=world)
