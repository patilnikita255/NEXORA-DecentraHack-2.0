from pathlib import Path

import cv2
import yaml


class ZoneEditor:
    """
    Simple interactive polygon zone editor for M03.

    Controls:
    - Left click  : Add polygon point
    - Right click : Remove last point
    - R           : Reset polygon
    - S           : Save polygon
    - Q / ESC     : Quit without saving
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

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append([x, y])

        elif event == cv2.EVENT_RBUTTONDOWN:
            if self.points:
                self.points.pop()

    def draw(self):
        display = self.frame.copy()

        for index, point in enumerate(self.points):
            x, y = point

            cv2.circle(
                display,
                (x, y),
                6,
                (0, 255, 255),
                -1
            )

            cv2.putText(
                display,
                str(index + 1),
                (x + 8, y - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

        if len(self.points) >= 2:
            for i in range(len(self.points) - 1):
                cv2.line(
                    display,
                    tuple(self.points[i]),
                    tuple(self.points[i + 1]),
                    (0, 255, 255),
                    2
                )

        if len(self.points) >= 3:
            cv2.line(
                display,
                tuple(self.points[-1]),
                tuple(self.points[0]),
                (0, 255, 255),
                2
            )

            overlay = display.copy()

            polygon = [
                tuple(point)
                for point in self.points
            ]

            cv2.fillPoly(
                overlay,
                [__import__("numpy").array(
                    polygon,
                    dtype="int32"
                )],
                (0, 255, 255)
            )

            display = cv2.addWeighted(
                overlay,
                0.20,
                display,
                0.80,
                0
            )

        instructions = (
            "LEFT CLICK: add point | "
            "RIGHT CLICK: undo | "
            "R: reset | "
            "S: save | "
            "Q/ESC: quit"
        )

        cv2.rectangle(
            display,
            (0, 0),
            (display.shape[1], 45),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            display,
            instructions,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        return display

    def save_zone(self):
        if len(self.points) < 3:
            print(
                "ERROR: A polygon needs at least 3 points."
            )
            return False

        zones = self.config.setdefault(
            "zones",
            {}
        )

        zones["restricted_zones"] = [
            {
                "name": "Restricted Zone 1",
                "polygon": self.points
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
        print("Restricted zone saved successfully.")
        print(
            f"Config: {self.config_path}"
        )
        print(
            f"Points: {self.points}"
        )

        return True

    def run(self):
        capture = cv2.VideoCapture(
            str(self.video_path)
        )

        if not capture.isOpened():
            raise RuntimeError(
                f"Could not open video: {self.video_path}"
            )

        success, frame = capture.read()
        capture.release()

        if not success:
            raise RuntimeError(
                "Could not read the first video frame."
            )

        self.frame = frame

        window_name = (
            "NEXORA - M03 Restricted Zone Editor"
        )

        cv2.namedWindow(window_name)

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
                print("Polygon reset.")

            elif key == ord("s"):
                if self.save_zone():
                    break

            elif key == ord("q") or key == 27:
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

    editor = ZoneEditor(
        video_path=str(video_path),
        config_path=str(config_path)
    )

    editor.run()
