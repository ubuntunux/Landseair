import math
import random

from PyEngine3D.Utilities import *
from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND

from GameClient.Constants import *


class BulletManager:
    def __init__(self):
        self.core_manager = None
        self.scene_manager = None
        self.sound_manager = None
        self.resource_manager = None
        self.game_effect_manager = None
        self.game_client = None
        self.actor_manager = None
        self.bullets = []

    def initialize(self, game_client):
        self.game_client = game_client
        self.core_manager = game_client.core_manager
        self.sound_manager = game_client.sound_manager
        self.scene_manager = game_client.scene_manager
        self.resource_manager = game_client.resource_manager
        self.game_effect_manager = game_client.game_effect_manager
        self.actor_manager = game_client.actor_manager
        self.bullets = []

    def add_bullet(self):
        bullet_model = self.resource_manager.get_model("Cube")
        bullet_object = self.scene_manager.add_object(model=bullet_model, instance_count=BulletActor.max_bullet_count, instance_render_count=0)
        bullet = BulletActor(self, bullet_object)
        self.bullets.append(bullet)
        return bullet

    def destroy(self):
        for bullet in self.bullets:
            bullet.destroy(self.scene_manager)

    def set_damage(self, bullet, target_actor):
        target_actor.set_damage(bullet.damage)

    def update_bullets(self, delta_time, actors):
        player_actor = self.actor_manager.player_actor
        for bullet in self.bullets:
            if bullet.actor is player_actor:
                for actor in actors:
                    if bullet.check_collide(actor):
                        self.set_damage(bullet, actor)
            else:
                if bullet.check_collide(player_actor):
                    self.set_damage(bullet, player_actor)
            bullet.update_bullet(self.core_manager.debug_line_manager, delta_time)


class BulletActor:
    fire_offset = 0.5
    fire_term = 0.1
    max_distance = 1000.0
    bullet_speed = 1000.0
    damage = 1
    max_bullet_count = max(10, int(math.ceil((bullet_speed / max_distance) / fire_term)))

    def __init__(self, bullet_manager, bullet_object):
        self.bullet_manager = bullet_manager
        self.game_client = bullet_manager.game_client
        self.sound_manager = bullet_manager.sound_manager
        self.game_effect_manager = self.game_client.game_effect_manager
        self.actor = None
        self.bullet_object = bullet_object

        assert(1 < self.max_bullet_count and self.bullet_object.is_instancing())

        self.bullet_transforms = []
        for i in range(self.bullet_object.instance_count):
            self.bullet_transforms.append(TransformObject())
        self.bullet_count = 0
        self.elapsed_time = 0.0
        self.current_fire_term = 0.0

    def set_actor(self, actor):
        self.actor = actor

    def destroy(self, scene_manager):
        scene_manager.delete_object(self.bullet_object.name)

    def get_pos(self):
        return self.bullet_object.transform.get_pos()

    def get_transform(self):
        return self.bullet_object.transform

    def destroy_bullet(self, index, create_effect=False):
        if index < self.bullet_count:
            if create_effect:
                destroy_position = self.bullet_transforms[index].get_pos()
                self.game_effect_manager.create_damage_particle(destroy_position)
                self.sound_manager.play_sound(random.choice(SOUND_BULLET_HITS), volume=0.2, position=destroy_position)

            last_index = self.bullet_count - 1
            if 0 < last_index:
                self.bullet_transforms[index], self.bullet_transforms[last_index] = self.bullet_transforms[last_index], self.bullet_transforms[index]
            self.bullet_count = last_index
            self.bullet_object.set_instance_render_count(self.bullet_count)

    def check_collide(self, actor):
        bound_box = actor.actor_object.bound_box
        bound_box_pos = bound_box.bound_center
        radius = bound_box.radius * 0.5

        for i in range(self.bullet_count):
            collide = False
            bullet_pos0 = self.bullet_transforms[i].get_prev_pos()
            bullet_pos1 = self.bullet_transforms[i].get_pos()
            to_actor0 = bound_box_pos - bullet_pos0
            to_actor1 = bound_box_pos - bullet_pos1
            if length(to_actor0) <= radius or length(to_actor1) <= radius:
                collide = True
            elif np.dot(to_actor0, to_actor1) <= 0.0:
                bullet_dir = normalize(bullet_pos1 - bullet_pos0)
                d = length(to_actor0 - bullet_dir * np.dot(to_actor0, bullet_dir))
                if d <= radius:
                    collide = True
            if collide:
                self.destroy_bullet(i, create_effect=True)
                return True
        return False

    def fire(self, fire_pos, fire_direction, camera_transform, target_actor_distance):
        if self.bullet_count < self.max_bullet_count and self.current_fire_term <= 0.0:
            bullet_transform = self.bullet_transforms[self.bullet_count]
            self.bullet_count += 1

            bullet_position = fire_pos + fire_direction * self.fire_offset

            # fire sound
            self.sound_manager.play_sound(SOUND_FIRE, position=bullet_position)

            if 0.0 < target_actor_distance:
                target_position = camera_transform.get_pos() - camera_transform.front * target_actor_distance
            else:
                target_position = bullet_position + bullet_position - fire_pos
            matrix = Matrix4()
            lookat(matrix, bullet_position, target_position, WORLD_UP)

            bullet_transform.rotationMatrix[0][:3] = matrix[0][:3]
            bullet_transform.rotationMatrix[1][:3] = matrix[1][:3]
            bullet_transform.rotationMatrix[2][:3] = matrix[2][:3]
            bullet_transform.matrix_to_vectors()
            bullet_transform.set_prev_pos(fire_pos)
            bullet_transform.set_pos(bullet_position)
            bullet_transform.update_transform()
            self.bullet_object.set_instance_render_count(self.bullet_count)
            self.current_fire_term = self.fire_term

    def update_bullet(self, debug_line_manager, delta_time):
        actor_pos = self.actor.actor_object.get_pos()
        self.bullet_object.transform.set_pos(actor_pos)

        bullet_index = 0
        for i in range(self.bullet_count):
            bullet_transform = self.bullet_transforms[bullet_index]
            current_pos = bullet_transform.get_pos()
            next_pos = current_pos + bullet_transform.front * self.bullet_speed * delta_time
            collide = self.game_client.check_collide(current_pos, next_pos)
            if length(current_pos - actor_pos) < self.max_distance and not collide:
                bullet_transform.set_pos(next_pos)
                bullet_transform.update_transform()

                # bullet_pos0 = bullet_transform.get_prev_pos()
                # bullet_pos1 = bullet_transform.get_pos()
                # debug_line_manager.draw_debug_line_3d(bullet_pos0, bullet_pos1, Float4(1.0, 1.0, 0.0, 1.0), 5.0, is_infinite=True)

                self.bullet_object.instance_matrix[i][...] = bullet_transform.matrix
                matrix_translate(self.bullet_object.instance_matrix[i], *(-actor_pos))
                bullet_index += 1
            else:
                self.destroy_bullet(bullet_index, create_effect=collide)
        if 0.0 < self.current_fire_term:
            self.current_fire_term -= delta_time
