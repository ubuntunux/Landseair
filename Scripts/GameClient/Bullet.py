import math

from PyEngine3D.Utilities import *
from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND

from GameClient.Constants import *


class BulletActor:
    fire_offset = 2.0
    fire_term = 0.3
    max_distance = 100.0
    bullet_speed = 1000.0
    max_bullet_count = max(2, int(math.ceil((bullet_speed / max_distance) / fire_term)))

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

        for i in range(self.bullet_count):
            bullet_pos0 = self.bullet_transforms[i].get_prev_pos()
            bullet_pos1 = self.bullet_transforms[i].get_pos()
            bullet_delta = bullet_pos1 - bullet_pos0
            bullet_dir = normalize(bullet_delta)
            to_actor = bound_box_pos - bullet_pos0
            d = length(to_actor - np.dot(bullet_dir, to_actor) * bullet_dir)

            if d <= bound_box.radius:
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
                target_position = bullet_position
            matrix = Matrix4()
            lookat(matrix, actor_position, target_position, WORLD_UP)

            bullet_transform.rotationMatrix[0][:3] = matrix[0][:3]
            bullet_transform.rotationMatrix[1][:3] = matrix[1][:3]
            bullet_transform.rotationMatrix[2][:3] = matrix[2][:3]
            bullet_transform.matrix_to_vectors()
            bullet_transform.set_prev_pos(actor_position)
            bullet_transform.set_pos(bullet_position)
            bullet_transform.update_transform()
            self.bullet_object.set_instance_render_count(self.bullet_count)
            self.current_fire_term = self.fire_term

    def update(self, delta_time, actor_transform):
        actor_position = actor_transform.get_pos()
        self.bullet_object.transform.set_pos(actor_position)

        bullet_index = 0
        for i in range(self.bullet_count):
            bullet_transform = self.bullet_transforms[bullet_index]
            if length(bullet_transform.get_pos() - actor_position) < self.max_distance:
                bullet_transform.move_front(self.bullet_speed * delta_time)
                bullet_transform.update_transform()
                self.bullet_object.instance_matrix[i][...] = bullet_transform.matrix
                matrix_translate(self.bullet_object.instance_matrix[i], *(-actor_position))
                bullet_index += 1
            else:
                self.destroy_bullet(bullet_index)
        if 0.0 < self.current_fire_term:
            self.current_fire_term -= delta_time
