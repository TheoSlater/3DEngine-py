import pygame
import numpy as np

pygame.init()

width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("3D Cube")

# Colors
light_blue = (173, 216, 230)

vertices = np.array([
    [-1, -1, -1],
    [ 1, -1, -1],
    [ 1,  1, -1],
    [-1,  1, -1],
    [-1, -1,  1],
    [ 1, -1,  1],
    [ 1,  1,  1],
    [-1,  1,  1]
])

# Define cube edges
edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),  # Back face
    (4, 5), (5, 6), (6, 7), (7, 4),  # Front face
    (0, 4), (1, 5), (2, 6), (3, 7)   # Connecting edges
]

def project(point):
    """ Project 3D point to 2D point """
    scale = 100000 
    factor = scale / (point[2] + 5)
    x = point[0] * factor + width // 2
    y = -point[1] * factor + height // 2
    return np.array([x, y])

def draw_cube():
    """ Draw the 3D cube on the screen """
    for edge in edges:
        points = []
        for vertex in edge:
            projected_point = project(vertices[vertex])
            points.append(projected_point)
        pygame.draw.line(screen, light_blue, points[0], points[1], 2)

def rotate_cube(angle_x, angle_y, angle_z):
    """ Rotate the cube by the given angles around the X, Y, Z axes """
    rotation_x = np.array([
        [1, 0, 0],
        [0, np.cos(angle_x), -np.sin(angle_x)],
        [0, np.sin(angle_x), np.cos(angle_x)]
    ])

    rotation_y = np.array([
        [np.cos(angle_y), 0, np.sin(angle_y)],
        [0, 1, 0],
        [-np.sin(angle_y), 0, np.cos(angle_y)]
    ])

    rotation_z = np.array([
        [np.cos(angle_z), -np.sin(angle_z), 0],
        [np.sin(angle_z), np.cos(angle_z), 0],
        [0, 0, 1]
    ])

    for i in range(len(vertices)):
        vertices[i] = np.dot(rotation_x, vertices[i])
        vertices[i] = np.dot(rotation_y, vertices[i])
        vertices[i] = np.dot(rotation_z, vertices[i])

def main():
    clock = pygame.time.Clock()
    angle_x, angle_y, angle_z = 0, 0, 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))

        rotate_cube(angle_x, angle_y, angle_z)
        draw_cube()

        pygame.display.flip()
        clock.tick(60)

        angle_x += 0.02
        angle_y += 0.02
        angle_z += 0.02

    pygame.quit()

if __name__ == "__main__":
    main()
