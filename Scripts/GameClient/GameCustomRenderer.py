from GameClient.Constants import *

_game_client = None


class GameCustomRenderer:
    def __init__(self):
        self.actor_hit_material = None

    def initialize(self, game_client):
        global _game_client
        _game_client = game_client

        self.actor_hit_material = game_client.resource_manager.get_material_instance(name="actor_hit",
                                                                                     shader_name="actor_hit",
                                                                                     macros={"SKELETAL": 1})

    def render_actor_hit(self):
        material_instance = self.actor_hit_material
        hit_render_color = HIT_RENDER_COLOR.copy()

        if 0 < len(_game_client.actor_manager.hit_actors):
            material_instance.use_program()
            material_instance.bind_material_instance()

        for game_actor, hit_time in _game_client.actor_manager.hit_actors.items():
            actor = game_actor.actor_object
            geometries = actor.get_geometries()
            material_instance.bind_uniform_data('is_instancing', False)
            material_instance.bind_uniform_data('model', actor.transform.matrix)
            hit_render_color[3] = 1.0 - abs((hit_time / HIT_RENDER_TIME) * 2.0 - 1.0)
            material_instance.bind_uniform_data('color', hit_render_color)
            for geometry in geometries:
                if actor.is_skeletal_actor():
                    animation_buffer = actor.get_animation_buffer(geometry.skeleton.index)
                    prev_animation_buffer = actor.get_prev_animation_buffer(geometry.skeleton.index)
                    material_instance.bind_uniform_data('bone_matrices', animation_buffer, num=len(animation_buffer))
                    material_instance.bind_uniform_data('prev_bone_matrices', prev_animation_buffer,
                                                        num=len(prev_animation_buffer))
                # draw
                geometry.draw_elements()

    def render_custom_rendering(self):
        self.render_actor_hit()

    def update(self, dt):
        _game_client.renderer.render_custom_translucent(self.render_custom_rendering)
