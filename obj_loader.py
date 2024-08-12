import numpy as np

def parse_vertex(line):
    return list(map(float, line.split()[1:]))

def parse_face(line):
    face_parts = line.split()[1:]
    vertices = []
    for part in face_parts:
        vertex_index = part.split('/')[0]
        vertices.append(int(vertex_index) - 1)
    return vertices

def load_obj(filename):
    vertices = []
    faces = []

    with open(filename, 'r') as file:
        for line in file:
            if line.startswith('v '):
                vertex = parse_vertex(line)
                vertices.append(vertex)
            elif line.startswith('f '):
                face = parse_face(line)
                faces.append(face)

    vertices = np.array(vertices)
    centroid = np.mean(vertices, axis=0)
    vertices -= centroid

    edges = set()
    for face in faces:
        for i in range(len(face)):
            edge = (face[i], face[(i + 1) % len(face)])
            edges.add(tuple(sorted(edge)))

    edges = list(edges)

    return vertices, faces, edges
