import cv2
import json

VIDEO_PATH = "myvideo.mp4"
SAVE_PATH = "exit_point.json"

drawing = False
ix, iy = -1, -1
roi_coords = None
frame = None

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, roi_coords, frame

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            temp_frame = frame.copy()
            cv2.rectangle(temp_frame, (ix, iy), (x, y), (0, 255, 0), 2)
            cv2.imshow("Calibrate Exit Point", temp_frame)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi_coords = (ix, iy, x, y)
        cv2.rectangle(frame, (ix, iy), (x, y), (0, 255, 0), 2)
        cv2.imshow("Calibrate Exit Point", frame)

def main():
    global frame
    cap = cv2.VideoCapture(VIDEO_PATH)

    # Grab first frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Error: Could not load video.")
        return

    cv2.namedWindow("Calibrate Exit Point")
    cv2.setMouseCallback("Calibrate Exit Point", draw_rectangle)

    print("Draw a rectangle around the gate area and press 's' to save.")

    while True:
        cv2.imshow("Calibrate Exit Point", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s') and roi_coords:
            # Save ROI to file
            with open(SAVE_PATH, "w") as f:
                json.dump({"exit_point": roi_coords}, f)
            print(f"Saved ROI: {roi_coords}")
            break

        elif key == 27:  # ESC to cancel
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()