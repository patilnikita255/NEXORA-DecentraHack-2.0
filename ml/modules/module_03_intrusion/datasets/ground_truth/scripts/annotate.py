import cv2
import os
import glob


IMAGE_DIR = "datasets/ground_truth/images"
ANNOTATION_DIR = "datasets/ground_truth/annotations"


drawing = False
start_x = 0
start_y = 0
current_x = 0
current_y = 0
boxes = []


def mouse_callback(event, x, y, flags, param):
    global drawing
    global start_x, start_y
    global current_x, current_y
    global boxes

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_x = x
        start_y = y
        current_x = x
        current_y = y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        current_x = x
        current_y = y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False

        x1 = min(start_x, x)
        y1 = min(start_y, y)
        x2 = max(start_x, x)
        y2 = max(start_y, y)

        if x2 > x1 and y2 > y1:
            boxes.append((x1, y1, x2, y2))
            print(f"Box added: ({x1}, {y1}) -> ({x2}, {y2})")


def convert_to_yolo(box, image_width, image_height):
    x1, y1, x2, y2 = box

    center_x = ((x1 + x2) / 2) / image_width
    center_y = ((y1 + y2) / 2) / image_height

    width = (x2 - x1) / image_width
    height = (y2 - y1) / image_height

    return 0, center_x, center_y, width, height


def save_annotations(annotation_path, image_width, image_height):
    with open(annotation_path, "w") as file:

        for box in boxes:
            class_id, center_x, center_y, width, height = convert_to_yolo(
                box,
                image_width,
                image_height
            )

            file.write(
                f"{class_id} "
                f"{center_x:.6f} "
                f"{center_y:.6f} "
                f"{width:.6f} "
                f"{height:.6f}\n"
            )


def main():

    os.makedirs(ANNOTATION_DIR, exist_ok=True)

    images = sorted(
        glob.glob(os.path.join(IMAGE_DIR, "*.jpg"))
    )

    if not images:
        print("No images found.")
        return

    print()
    print("=" * 60)
    print("NEXORA M03 - PERSON ANNOTATION TOOL")
    print("=" * 60)
    print()
    print("Controls:")
    print("  LEFT MOUSE  -> Draw person bounding box")
    print("  S            -> Save annotations and next image")
    print("  R            -> Reset boxes for current image")
    print("  Q            -> Quit")
    print()
    print("Class 0 = person")
    print("=" * 60)

    for image_index, image_path in enumerate(images):

        global boxes
        boxes = []

        image = cv2.imread(image_path)

        if image is None:
            print(f"Could not read: {image_path}")
            continue

        image_height, image_width = image.shape[:2]

        window_name = "NEXORA M03 - Annotate Persons"

        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, mouse_callback)

        while True:

            display = image.copy()

            # Draw already-created boxes
            for box in boxes:
                x1, y1, x2, y2 = box

                cv2.rectangle(
                    display,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    display,
                    "person",
                    (x1, max(y1 - 5, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            # Draw box currently being created
            if drawing:
                cv2.rectangle(
                    display,
                    (start_x, start_y),
                    (current_x, current_y),
                    (255, 0, 0),
                    2
                )

            cv2.putText(
                display,
                f"Image {image_index + 1}/{len(images)} | "
                f"Boxes: {len(boxes)} | "
                f"S=Save  R=Reset  Q=Quit",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow(window_name, display)

            key = cv2.waitKey(20) & 0xFF

            if key == ord("s"):

                annotation_name = (
                    os.path.splitext(
                        os.path.basename(image_path)
                    )[0]
                    + ".txt"
                )

                annotation_path = os.path.join(
                    ANNOTATION_DIR,
                    annotation_name
                )

                save_annotations(
                    annotation_path,
                    image_width,
                    image_height
                )

                print(
                    f"Saved {len(boxes)} boxes -> "
                    f"{annotation_path}"
                )

                break

            elif key == ord("r"):
                boxes = []
                print("Boxes reset.")

            elif key == ord("q"):
                cv2.destroyAllWindows()
                return

        cv2.destroyAllWindows()

    print()
    print("=" * 60)
    print("ANNOTATION COMPLETE")
    print("=" * 60)
    print(f"Images processed: {len(images)}")
    print(f"Annotations: {ANNOTATION_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
