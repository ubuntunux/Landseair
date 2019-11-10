import math

from PyEngine3D.Utilities import *
from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND

from GameClient.Constants import *


class BulletManager:
    def __init__(self):
        self.core_manager = None
        self.scene_manager = None
        self.resource_manager = None
        self.game_effect_manager = None
        self.bullet_actor = None

    def initialize(self, core_manager, scene_manager, resource_manager, game_effect_manager):
        self.core_manager = core_manager
        self.scene_manager = scene_manager
        self.resource_manager = resource_manager
        self.game_effect_manager = game_effect_manager
        self.bullet_actor = BulletActor(scene_manager, resource_manager)

    def destroy(self):
        self.bullet_actor.destroy(self.scene_manager)
        self.bullet_actor = None

    def update_bullets(self, delta_time, player_actor_position, actors):
        for actor in actors:
            if self.bullet_actor.check_collide(actor):
                actor.set_damage(self.bullet_actor.damage)
                self.game_effect_manager.create_damage_particle(actor.get_pos())
        self.bullet_actor.update_bullet(self.core_manager.debug_line_manager, delta_time, player_actor_position)


class BulletActor:
    fire_offset = 0.5
    fire_term = 0.3
    max_distance = 1000.0
    bullet_speed = 1000.0
    damage = 1
    max_bullet_count = max(10, int(math.ceil((bullet_speed / max_distance) / fire_term)))

    def __init__(self, scene_manager, resource_manager):
        bullet_model = resource_manager.get_model("Cube")

        self.bullet_object = scene_manager.add_object(model=bullet_model, instance_count=self.max_bullet_count, instance_render_count=0)

        assert(1 < self.max_bullet_count and self.bullet_object.is_instancing())

        self.bullet_transforms = []
        for i in range(self.bullet_object.instance_count):
            self.bullet_transforms.append(TransformObject())
        self.bullet_count = 0
        self.elapsed_time = 0.0
        self.current_fire_term = 0.0

    def destroy(self, scene_manager):
        scene_manager.delete_object(self.bullet_object.name)

    def get_pos(self):
        return self.bullet_object.transform.get_pos()

    def get_transform(self):
        return self.bullet_object.transform

    def destroy_bullet(self, index):
        if index < self.bullet_count:
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
                self.destroy_bullet(i)
                return True
        return False

    def fire(self, actor_transform, camera_transform, target_actor_distance):
        if self.bullet_count < self.max_bullet_count and self.current_fire_term <= 0.0:
            bullet_transform = self.bullet_transforms[self.bullet_count]
            self.bullet_count += 1

            actor_position = actor_transform.get_pos()
            bullet_position = actor_position + actor_transform.front * self.fire_offset
            if 0.0 < target_actor_distance:
                target_position = camera_transform.get_pos() - camera_transform.front * target_actor_distance
            else:
                target_position = bullet_position + bullet_position - actor_position
            matrix = Matrix4()
            lookat(matrix, bullet_position, target_position, WORLD_UP)

            bullet_transform.rotationMatrix[0][:3] = matrix[0][:3]
            bullet_transform.rotationMatrix[1][:3] = matrix[1][:3]
            bullet_transform.rotationMatrix[2][:3] = matrix[2][:3]
            bullet_transform.matrix_to_vectors()
            bullet_transform.set_prev_pos(actor_position)
            bullet_transform.set_pos(bullet_position)
            bullet_transform.update_transform()
            self.bullet_object.set_instance_render_count(self.bullet_count)
            self.current_fire_term = self.fire_term

    def update_bullet(self, debug_line_manager, delta_time, player_actor_position):
        self.bullet_object.transform.set_pos(player_actor_position)

        bullet_index = 0
        for i in range(self.bullet_count):
            bullet_transform = self.bullet_transforms[bullet_index]
            if length(bullet_transform.get_pos() - player_actor_position) < self.max_distance:
                bullet_transform.move_front(self.bullet_speed * delta_time)
                bullet_transform.update_transform()

                bullet_pos0 = bullet_transform.get_prev_pos()
                bullet_pos1 = bullet_transform.get_pos()
                debug_line_manager.draw_debug_line_3d(bullet_pos0, bullet_pos1, Float4(1.0, 1.0, 0.0, 1.0), 30.0, is_infinite=True)

                self.bullet_object.instance_matrix[i][...] = bullet_transform.matrix
                matrix_translate(self.bullet_object.instance_matrix[i], *(-player_actor_position))
                bullet_index += 1
            else:
                self.destroy_bullet(bullet_index)
        if 0.0 < self.current_fire_term:
            self.current_fire_term -= delta_time
