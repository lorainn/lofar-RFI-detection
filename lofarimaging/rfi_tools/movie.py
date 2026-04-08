import cv2

__all__ = [
    "generate_movie",
    "generate_movie_from_list",
]


def generate_movie(sources, output_path, fps=10):
    if not sources:
        print("Image list is empty.")
        return

    # Use the first image to get the size of the frame
    image = cv2.imread(sources[0])
    if image is None:
        print(f"Error reading image: {sources[0]}. Aborting.")
        return

    height, width, _ = image.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Iterate through the images and write them to the movie
    for path in sources:
        image = cv2.imread(path)
        if image is None:
            print(f"Error reading image: {path}. It will be skipped.")
            continue
        out.write(image)

    out.release()
    cv2.destroyAllWindows()


def generate_movie_from_list(list_path, output_path, fps=10):
    with open(list_path, "r") as file:
        sources = file.read().splitlines()
    generate_movie(sources, output_path, fps=fps)
