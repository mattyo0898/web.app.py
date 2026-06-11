import streamlit as st
import cv2
from ultralytics import YOLO

# 1. Webアプリの画面構成
st.set_page_config(layout="wide") # 画面を広く使う
st.title("🪑 1列4席・リアルタイム空席状況確認システム")
st.write("カメラの前にいる人の位置をAIが自動で判定し、4つの席の空席状況をリアルタイムに更新します。")

# 画面を2分割（左：カメラ、右：レイアウト）
col1, col2 = st.columns(2)

with col1:
    st.subheader("📷 AI認識カメラ")
    frame_placeholder = st.empty()

with col2:
    st.subheader("🗺️ カウンター席レイアウト（1列4席）")
    layout_placeholder = st.empty()

# サイドバーにコントロール用のチェックボックスを配置
run_camera = st.sidebar.checkbox("カメラを開始", value=False)

# 2. YOLOモデルの読み込み
@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")

model = load_model()

# 3. カメラ処理のメインループ
if run_camera:
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened() and run_camera:
        success, frame = cap.read()
        if not success:
            st.error("カメラの読み込みに失敗しました。")
            break

        # カメラ画像の横幅を取得（エリア分割に使う）
        height, width, _ = frame.shape
        area_width = width // 4  # 4等分した1席分の幅

        # 各席の初期状態（True = 空席、False = 満席）
        seats_vacant = [True, True, True, True]

        # AIに「人」だけを認識させる
        results = model(frame, stream=True, classes=[0])

        annotated_frame = frame.copy()
        for r in results:
            annotated_frame = r.plot()
            
            # 人が検出された場合、その位置（座標）をチェック
            if r.boxes is not None:
                for box in r.boxes:
                    # 人の中心の横座標（X座標）を計算
                    x1, y1, x2, y2 = box.xyxy[0]
                    center_x = (x1 + x2) / 2
                    
                    # 中心の座標が、4つのエリアのどこにあるか判定
                    if center_x < area_width:
                        seats_vacant[0] = False  # 席1に人がいる
                    elif center_x < area_width * 2:
                        seats_vacant[1] = False  # 席2に人がいる
                    elif center_x < area_width * 3:
                        seats_vacant[2] = False  # 席3に人がいる
                    else:
                        seats_vacant[3] = False  # 席4に人がいる

        # ---- 映像にエリアの区切り線（ガイド線）を描く ----
        for i in range(1, 4):
            cv2.line(annotated_frame, (area_width * i, 0), (area_width * i, height), (255, 255, 255), 2)
            cv2.putText(annotated_frame, f"Seat {i}", (area_width * (i-1) + 10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(annotated_frame, "Seat 4", (area_width * 3 + 10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # ---- 右側の4連席レイアウトの表示 ----
        with layout_placeholder.container():
            # 横並びに4つのカラム（席）を作る
            seat_cols = st.columns(4)
            
            for i in range(4):
                with seat_cols[i]:
                    if not seats_vacant[i]:
                        st.error(f"🟥 席 {i+1}\n\n満席")
                    else:
                        st.success(f"🟩 席 {i+1}\n\n空席")
            
            # 全体の空席数を表示するおまけ機能
            vacant_count = seats_vacant.count(True)
            st.info(f"📊 現在の空席状況: **4席中 {vacant_count} 席が空いています**")

        # BGRからRGBに変換してStreamlitに表示
        annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(annotated_frame_rgb, channels="RGB", use_container_width=True)

    # 後片付け
    cap.release()
    frame_placeholder.empty()
    layout_placeholder.empty()
    st.write("カメラを停止しました。")
else:
    st.info("左側の『カメラを開始』をチェックすると起動します。")