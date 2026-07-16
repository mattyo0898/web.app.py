from ultralytics import YOLO

# ローカル（USB内）のモデルを読み込む
model = YOLO("./yolov8n.pt") 

# サンプル画像をネットから自動で読み込んで認識させる
results = model("https://ultralytics.com/images/bus.jpg", save=True)