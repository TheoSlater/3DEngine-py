import pygame as pg
import numpy as np
import random
from pygame.locals import *

pg.init()

WIDTH, HEIGHT = 800, 600
SSAA_SCALE = 2  # Scale factor for SSAA, use 2 for 2x SSAA

# Define high-resolution surface for SSAA
high_res_surface = pg.Surface((WIDTH * SSAA_SCALE, HEIGHT * SSAA_SCALE))

screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("3D Camera Orbit with Mouse")

font = pg.font.SysFont(None, 36)

# Define vertices, edges, faces, and face colors
vertices = np.array([
    [-1, -1, -1],
    [1, -1, -1],
    [1, 1, -1],
    [-1, 1, -1],
    [-1, -1, 1],
    [1, -1, 1],
    [1, 1, 1],
    [-1, 1, 1]
])
faces = [
    [0, 1, 2, 3],  # Front face
    [4, 5, 6, 7],  # Back face
    [0, 1, 5, 4],  # Bottom face
    [2, 3, 7, 6],  # Top face
    [1, 2, 6, 5],  # Right face
    [0, 3, 7, 4]   # Left face
]

# Define texture coordinates for each face of the cube
texture_coords = [
    [(0, 0), (1, 0), (1, 1), (0, 1)],  # Front face
    [(0, 0), (1, 0), (1, 1), (0, 1)],  # Back face
    [(0, 0), (1, 0), (1, 1), (0, 1)],  # Bottom face
    [(0, 0), (1, 0), (1, 1), (0, 1)],  # Top face
    [(0, 0), (1, 0), (1, 1), (0, 1)],  # Right face
    [(0, 0), (1, 0), (1, 1), (0, 1)]   # Left face
]

# Load texture
try:
    texture = pg.image.load('./gravel.png').convert()
    texture = pg.transform.scale(texture, (256, 256))  # Adjust size if needed
except Exception as e:
    print(f"Error loading texture: {e}")
    pg.quit()
    exit()

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

def calculate_face_depth(face_vertices):
    cam_pos = np.array([0, 0, 0])  # Camera at the origin
    depths = [np.dot(v - cam_pos, np.array([0, 0, 1])) for v in face_vertices]
    return np.mean(depths)

def compute_face_normal(face_vertices):
    v0, v1, v2 = face_vertices[0], face_vertices[1], face_vertices[2]
    edge1 = v1 - v0
    edge2 = v2 - v0
    normal = np.cross(edge1, edge2)
    norm_length = np.linalg.norm(normal)
    return normal / norm_length if norm_length > 0 else normal

def compute_lighting(normal, face_center):
    light_dir = light_pos - face_center
    light_dir = light_dir / np.linalg.norm(light_dir)
    dot_product = np.dot(normal, light_dir)
    diffuse = max(dot_product, 0) * diffuse_light
    return ambient_light + diffuse

def is_face_facing_light(normal, face_center):
    light_dir = light_pos - face_center
    light_dir = light_dir / np.linalg.norm(light_dir)
    return np.dot(normal, light_dir) > 0

def draw_textured_polygon(surface, texture, polygon, tex_coords):
    if len(polygon) >= 3:
        tex_coords = [(tc[0] * texture.get_width(), tc[1] * texture.get_height()) for tc in tex_coords]
        pg.draw.polygon(surface, (255, 255, 255), polygon)  # Draw base polygon for masking
        texture_polygon = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        pg.draw.polygon(texture_polygon, (255, 255, 255), polygon)
        texture_polygon.blit(texture, (0, 0))
        texture_polygon.set_clip(pg.Rect(min([p[0] for p in polygon]), min([p[1] for p in polygon]), max([p[0] for p in polygon]) - min([p[0] for p in polygon]), max([p[1] for p in polygon]) - min([p[1] for p in polygon])))
        surface.blit(texture_polygon, (0, 0), special_flags=pg.BLEND_RGBA_MULT)

def draw_ui(surface):
    zoom_text = font.render(f"Zoom: {camera.scale_factor:.2f}", True, (255, 255, 255))
    surface.blit(zoom_text, (10, 10))

    lighting_status = "On" if lighting_enabled else "Off"
    lighting_text = font.render(f"Lighting: {lighting_status}", True, (255, 255, 255))
    surface.blit(lighting_text, (10, 50))

class Camera:
    def __init__(self):
        self.angle_pitch = self.angle_yaw = 0
        self.distance = 5
        self.rotation_speed = 0.01
        self.scale_factor = 1.0  # Scale factor for the cube
        self.zoom_speed = 0.1    # Speed at which the cube scales
        self.min_scale = 0.05    # Minimum scale factor
        self.max_scale = 10.0    # Maximum scale factor
        self.last_mouse_pos = None

    def control(self):
        if pg.mouse.get_pressed()[0]:
            mouse_x, mouse_y = pg.mouse.get_pos()
            if self.last_mouse_pos:
                dx, dy = mouse_x - self.last_mouse_pos[0], mouse_y - self.last_mouse_pos[1]
                self.angle_yaw += dx * self.rotation_speed
                self.angle_pitch -= dy * self.rotation_speed
            self.last_mouse_pos = (mouse_x, mouse_y)
        else:
            self.last_mouse_pos = None

    def get_position(self):
        x = self.distance * np.sin(self.angle_pitch) * np.cos(self.angle_yaw)
        y = self.distance * np.sin(self.angle_yaw)
        z = self.distance * np.cos(self.angle_pitch) * np.cos(self.angle_yaw)
        return np.array([x, y, z])

    def zoom_in(self):
        self.scale_factor = max(self.scale_factor - self.zoom_speed, self.min_scale)

    def zoom_out(self):
        self.scale_factor = min(self.scale_factor + self.zoom_speed, self.max_scale)

camera = Camera()

light_pos = np.array([0, 0, 10])  # Position of the light source
ambient_light = 0.1
diffuse_light = 0.9
lighting_enabled = True  # Define this variable

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                camera.zoom_in()
            elif event.key == pg.K_DOWN:
                camera.zoom_out()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                camera.zoom_in()
            elif event.button == 5:  # Scroll down
                camera.zoom_out()

    camera.control()
    high_res_surface.fill((0, 0, 0))

    cam_pos = camera.get_position()
    translated_vertices = vertices * camera.scale_factor
    rotation_matrix = np.dot(rotate_x(camera.angle_pitch), rotate_y(camera.angle_yaw))
    rotated_vertices = np.dot(translated_vertices, rotation_matrix)
    projected_vertices = project(rotated_vertices)

    face_distances = []
    for i, face in enumerate(faces):
        face_vertices = [rotated_vertices[v] for v in face]
        face_center = np.mean(face_vertices, axis=0)
        face_normal = compute_face_normal(face_vertices)
        
        if is_face_facing_light(face_normal, face_center):
            if lighting_enabled:
                face_lighting = compute_lighting(face_normal, face_center)
                face_color = np.array([255, 255, 255]) * face_lighting
            else:
                face_color = np.array([255, 255, 255])
        else:
            face_color = (0, 0, 0)  # Face not facing the light source
        
        face_color = np.clip(face_color, 0, 255).astype(int)
        face_distance = calculate_face_depth(face_vertices)
        face_distances.append((i, face_distance, [projected_vertices[v] for v in face], texture_coords[i]))

    face_distances.sort(key=lambda x: x[1], reverse=True)

    if SSAA_SCALE > 1:
        high_res_surface.fill((0, 0, 0))

    for i, _, polygon, tex_coords in face_distances:
        if len(polygon) > 2:  # Ensure the polygon has enough points
            draw_textured_polygon(high_res_surface, texture, polygon, tex_coords)

    if SSAA_SCALE > 1:
        scaled_surface = pg.transform.scale(high_res_surface, (WIDTH, HEIGHT))
        screen.blit(scaled_surface, (0, 0))
    else:
        screen.blit(high_res_surface, (0, 0))

    # Draw UI elements
    draw_ui(screen)

    pg.display.flip()

pg.quit()
