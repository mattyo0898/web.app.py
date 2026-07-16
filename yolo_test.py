import cv2
from ultralytics import YOLO

# 1. YOLOのAIモデルを読み込む（一番軽いモデルにして動きをスムーズにします）
model = YOLO("yolov8n.pt")

# 2. パソコンのカメラを起動
cap = cv2.VideoCapture(0)

print("--- AIカメラを起動しました（止めるにはカメラ画面で『q』を押してください） ---")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

   # AIに画面を認識させる（classes=[0] で「人」だけに絞り込む）
    results = model(frame, stream=True, classes=[0])

    # 認識した結果を画面に描く
    for r in results:
        annotated_frame = r.plot()

    # 画面を表示する
    cv2.imshow("YOLOv8 Detection", annotated_frame)

    # 【重要】1ミリ秒キー入力を待つ（これで「q」を確実に聞き取れるようになります）
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 3. 後片付け（カメラをオフにして画面を閉じる）
cap.release()
cv2.destroyAllWindows()

print("--- 正常に終了しました ---")