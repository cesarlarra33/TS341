
import cv2, os, glob, numpy as np, argparse

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", required=True)
    p.add_argument("--patterns", "-p", required=True)
    p.add_argument("--display", "-d", action="store_true")
    p.add_argument("--resize-width", type=int, default=960)
    p.add_argument("--step", type=int, default=10, help="intervalle entre deux détections SIFT")
    return p.parse_args()

def main():
    args = parse_args()
    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la vidéo"); return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = args.resize_width / w
    target = (args.resize_width, int(h * scale))

    sift = cv2.SIFT_create()
    # charge un seul pattern moyen (ou moyenne de plusieurs)
    pat_files = glob.glob(os.path.join(args.patterns, "*"))
    ref = cv2.imread(pat_files[0], cv2.IMREAD_COLOR)
    kp_ref, des_ref = sift.detectAndCompute(ref, None)

    flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=30))

    tracker, tracking = None, False
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame_idx += 1
        frame = cv2.resize(frame, target)
        display = frame.copy()

        
        if not tracking and frame_idx % args.step == 0:
            kp, des = sift.detectAndCompute(frame, None)
            if des is None or len(kp) < 2:
                continue
            matches = flann.knnMatch(des_ref, des, k=2)
            good = [m for m,n in matches if m.distance < 0.7*n.distance]
            if len(good) > 20:
                pts = np.float32([kp[m.trainIdx].pt for m in good])
                x,y,w,h = cv2.boundingRect(pts)
                cv2.rectangle(display, (x,y), (x+w, y+h), (0,255,0), 2)
                tracker = cv2.legacy.TrackerKCF_create() if hasattr(cv2,"legacy") else cv2.TrackerKCF_create()
                tracker.init(frame, (x,y,w,h))
                tracking = True
                print(f"🎯 Drone détecté à frame {frame_idx}")

        
        elif tracking and tracker is not None:
            ok, box = tracker.update(frame)
            if ok:
                x,y,w,h = [int(v) for v in box]
                cv2.rectangle(display, (x,y), (x+w, y+h), (0,0,255), 2)
            else:
                tracking = False

        if args.display:
            cv2.imshow("Drone light", display)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release(); cv2.destroyAllWindows()
    print("Terminé.")

if __name__ == "__main__":
    main()
