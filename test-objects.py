import pygame as pg
import numpy as np
from obj_loader import load_obj

pg.init()

WIDTH, HEIGHT = 800, 600
SSAA_SCALE = 12

high_res_surface = pg.Surface((WIDTH * SSAA_SCALE, HEIGHT * SSAA_SCALE))

screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("3D Camera Orbit with Mouse")

light_pos = np.array([5, 5, 5])
ambient_light = 0.2
diffuse_light = 0.8

def rotate_x(angle):
    cos_angle, sin_angle = np.cos(angle), np.sin(angle)
    return np.array([
        [1, 0, 0],
        [0, cos_angle, -sin_angle],
        [0, sin_angle, cos_angle]
    ])

def rotate_y(angle):
    cos_angle, sin_angle = np.cos(angle), np.sin(angle)
    return np.array([
        [cos_angle, 0, sin_angle],
        [0, 1, 0],
        [-sin_angle, 0, cos_angle]
    ])

def project(points, scale=100):
    return [(int(p[0] * scale) + WIDTH // 2, int(p[1] * scale) + HEIGHT // 2) for p in points]

class Camera:
    def __init__(self):
        self.angle_pitch = self.angle_yaw = 0
        self.distance = 5
        self.rotation_speed = 0.01
        self.last_mouse_pos = None

    def control(self):
        if pg.mouse.get_pressed()[1]:
            mouse_x, mouse_y = pg.mouse.get_pos()
            if self.last_mouse_pos:
                dx, dy = mouse_x - self.last_mouse_pos[0], mouse_y - self.last_mouse_pos[1]
                self.angle_yaw += dx * self.rotation_speed
                self.angle_pitch -= dy * self.rotation_speed
            self.last_mouse_pos = (mouse_x, mouse_y)
        else:
            self.last_mouse_pos = None

    def get_position(self):
        x = self.distance * np.cos(self.angle_pitch) * np.sin(self.angle_yaw)
        y = self.distance * np.sin(self.angle_pitch)
        z = self.distance * np.cos(self.angle_pitch) * np.cos(self.angle_yaw)
        return np.array([x, y, z])

def main():
    clock = pg.time.Clock()
    camera = Camera()

    vertices, faces, edges = load_obj('./objects/car.obj')

    show_rays = False

    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    show_rays = not show_rays

        camera.control()

        if SSAA_SCALE > 1:
            high_res_surface.fill((0, 0, 0))

        cam_pos = camera.get_position()
        translated_vertices = np.array(vertices)
        rotation_matrix = np.dot(rotate_x(camera.angle_pitch), rotate_y(camera.angle_yaw))
        rotated_vertices = np.dot(translated_vertices, rotation_matrix)
        projected_vertices = project(rotated_vertices)

        if SSAA_SCALE > 1:
            for v in projected_vertices:
                pg.draw.circle(high_res_surface, (0, 255, 0), (int(v[0] * SSAA_SCALE), int(v[1] * SSAA_SCALE)), 3)
            for edge in edges:
                pg.draw.line(high_res_surface, (0, 255, 0), 
                             (int(projected_vertices[edge[0]][0] * SSAA_SCALE), int(projected_vertices[edge[0]][1] * SSAA_SCALE)),
                             (int(projected_vertices[edge[1]][0] * SSAA_SCALE), int(projected_vertices[edge[1]][1] * SSAA_SCALE)), 1)

            scaled_surface = pg.transform.scale(high_res_surface, (WIDTH, HEIGHT))
            screen.blit(scaled_surface, (0, 0))
        else:
            for v in projected_vertices:
                pg.draw.circle(screen, (0, 255, 0), (int(v[0]), int(v[1])), 3)
            for edge in edges:
                pg.draw.line(screen, (0, 255, 0), 
                             projected_vertices[edge[0]], 
                             projected_vertices[edge[1]], 1)

        pg.display.flip()
        clock.tick(60)

    pg.quit()

if __name__ == "__main__":
    main()