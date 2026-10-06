from pathlib import Path

import cv2
import numpy as np
import yaml


class TripwireEditor:
    """
    Interactive tripwire editor for NEXORA M03.

    Controls:
        LEFT CLICK  -> Select first point
        LEFT CLICK  -> Select second point
        RIGHT CLICK -> Reset line
        S            -> Save tripwire
        R            -> Reset line
        Q / ESC      -> Quit without saving

    A tripwire consists of exactly two points.
    """

    def __init__(self, video_path: str, config_path: str):
        self.video_path = Path(video_path).resolve()
        self.config_path = Path(config_path).resolve()

        if not self.video_path.exists():
            raise FileNotFoundError(
                f"Video not found: {self.video_path}"
            )

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config not found: {self.config_path}"
            )

        with open(
            self.config_path,
            "r",
            encoding="utf-8"
        ) as file:
            self.config = yaml.safe_load(file)

        self.points = []
        self.frame = None

    def mouse_callback(
        self,
        event,
        x,
        y,
        flags,
        param
    ):
        if event == cv2.EVENT_LBUTTONDOWN:

            if len(self.points) < 2:
                self.points.append([x, y])

                print(
                    f"Point {len(self.points)} selected: "
                    f"({x}, {y})"
                )

            else:
                print(
                    "Tripwire already has 2 points. "
                    "Press R to reset."
                )

        elif event == cv2.EVENT_RBUTTONDOWN:
            self.points = []

            print(
                "Tripwire reset."
            )

    def draw(self):
        display = self.frame.copy()

        # Draw selected points
        for index, point in enumerate(self.points):
            x, y = point

            cv2.circle(
                display,
                (x, y),
                8,
                (0, 255, 255),
                -1
            )

            cv2.putText(
                display,
                f"P{index + 1}",
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

        # Draw line after two points
        if len(self.points) == 2:

            point1 = tuple(self.points[0])
            point2 = tuple(self.points[1])

            cv2.line(
                display,
                point1,
                point2,
                (0, 0, 255),
                4
            )

            # Direction arrow
            midpoint_x = int(
                (point1[0] + point2[0]) / 2
            )

            midpoint_y = int(
                (point1[1] + point2[1]) / 2
            )

            cv2.arrowedLine(
                display,
                point1,
                point2,
                (255, 0, 0),
                3,
                tipLength=0.08
            )

            cv2.putText(
                display,
                "A -> B",
                (
                    midpoint_x + 10,
                    midpoint_y - 10
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )

        # Instructions
        instructions = (
            "LEFT CLICK: select points | "
            "RIGHT CLICK: reset | "
            "R: reset | "
            "S: save | "
            "Q/ESC: quit"
        )

        cv2.rectangle(
            display,
            (0, 0),
            (
                display.shape[1],
                50
            ),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            display,
            instructions,
            (10, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        return display

    def save_tripwire(self):
        if len(self.points) != 2:
            print()
            print(
                "ERROR: Tripwire needs exactly 2 points."
            )
            return False

        zones = self.config.setdefault(
            "zones",
            {}
        )

        zones["tripwires"] = [
            {
                "name": "Main Entrance Tripwire",
                "line": self.points
            }
        ]

        with open(
            self.config_path,
            "w",
            encoding="utf-8"
        ) as file:
            yaml.safe_dump(
                self.config,
                file,
                sort_keys=False
            )

        print()
        print(
            "========================================"
        )
        print(
            "TRIPWIRE SAVED SUCCESSFULLY"
        )
        print(
            "========================================"
        )
        print(
            f"Config: {self.config_path}"
        )
        print(
            f"Point A: {self.points[0]}"
        )
        print(
            f"Point B: {self.points[1]}"
        )
        print(
            "Direction reference: A -> B"
        )

        return True

    def run(self):
        capture = cv2.VideoCapture(
            str(self.video_path)
        )

        if not capture.isOpened():
            raise RuntimeError(
                f"Could not open video: "
                f"{self.video_path}"
            )

        success, frame = capture.read()

        capture.release()

        if not success:
            raise RuntimeError(
                "Could not read the first "
                "video frame."
            )

        self.frame = frame

        window_name = (
            "NEXORA - M03 Tripwire Editor"
        )

        cv2.namedWindow(
            window_name
        )

        cv2.setMouseCallback(
            window_name,
            self.mouse_callback
        )

        while True:

            display = self.draw()

            cv2.imshow(
                window_name,
                display
            )

            key = cv2.waitKey(20) & 0xFF

            if key == ord("r"):
                self.points = []

                print(
                    "Tripwire reset."
                )

            elif key == ord("s"):

                if self.save_tripwire():
                    break

            elif (
                key == ord("q")
                or key == 27
            ):
                print(
                    "Exited without saving."
                )
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":

    module_root = Path(
        __file__
    ).resolve().parents[1]

    video_path = (
        module_root
        / "test_videos"
        / "test.mp4"
    )

    config_path = (
        module_root
        / "config"
        / "config.yaml"
    )

    editor = TripwireEditor(
        video_path=str(video_path),
        config_path=str(config_path)
    )

    editor.run()