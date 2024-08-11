import pygame as pg
import numpy as np

# Initialize Pygame
pg.init()

WIDTH, HEIGHT = 800, 600
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("3D Camera Orbit with Mouse")

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
edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7)
]
faces = [
    [0, 1, 2, 3],  # Front face
    [4, 5, 6, 7],  # Back face
    [0, 1, 5, 4],  # Bottom face
    [2, 3, 7, 6],  # Top face
    [1, 2, 6, 5],  # Right face
    [0, 3, 7, 4]   # Left face
]
face_colors = [
    (255, 0, 0),   # Red
    (0, 255, 0),   # Green
    (0, 0, 255),   # Blue
    (255, 255, 0), # Yellow
    (255, 0, 255), # Magenta
    (0, 255, 255)  # Cyan
]

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

def calculate_normal(v1, v2, v3):
    edge1 = v2 - v1
    edge2 = v3 - v1
    normal = np.cross(edge1, edge2)
    return normal / np.linalg.norm(normal)  # Normalize the normal vector

class Camera:
    def __init__(self):
        self.angle_pitch = self.angle_yaw = 0
        self.distance = 5
        self.rotation_speed = 0.01
        self.last_mouse_pos = None

    def control(self):
        if pg.mouse.get_pressed()[2]:  # Right mouse button
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
    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        camera.control()
        screen.fill((0, 0, 0))

        cam_pos = camera.get_position()
        translated_vertices = vertices
        rotation_matrix = np.dot(rotate_x(camera.angle_pitch), rotate_y(camera.angle_yaw))
        rotated_vertices = np.dot(translated_vertices, rotation_matrix)
        projected_vertices = project(rotated_vertices)

        # List to keep track of visible faces
        visible_faces = []

        for i, face in enumerate(faces):
            face_vertices = [rotated_vertices[v] for v in face]
            normal = calculate_normal(*face_vertices[:3])
            face_center = np.mean(face_vertices, axis=0)
            to_camera = cam_pos - face_center

            if np.dot(normal, to_camera) < 0:  # Face is visible
                visible_faces.append((i, [projected_vertices[v] for v in face]))

        # Draw faces
        for i, polygon in visible_faces:
            pg.draw.polygon(screen, face_colors[i], polygon)  # Fill face
            pg.draw.polygon(screen, (0, 0, 0), polygon, 1)    # Outline face

        pg.display.flip()
        clock.tick(60)

    pg.quit()

if __name__ == "__main__":
    main()
