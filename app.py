import streamlit as st
import cv2
from ultralytics import YOLO
import time
import subprocess

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

# --- 🔄 データ送信およびタイマー管理用の変数 ---
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = 0
if "last_seats_status" not in st.session_state:
    st.session_state.last_seats_status = []

# 各席の空席判定用タイマーの初期化（4席分）
# status: 現在画面に表示する状態（True=空席、False=満席）
# last_seen: 最後に人を検知した（見失った）時間
# is_timer_running: カウントダウン中かどうか
if "seat_timers" not in st.session_state:
    st.session_state.seat_timers = [
        {"status": True, "last_seen": 0, "is_timer_running": False},
        {"status": True, "last_seen": 0, "is_timer_running": False},
        {"status": True, "last_seen": 0, "is_timer_running": False},
        {"status": True, "last_seen": 0, "is_timer_running": False}
    ]

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

        # AIが「今この瞬間」検知したかどうかのフラグ（True=人がいる、False=人がいない）
        # 初期状態は全員「人がいない(False)」からスタート
        current_ai_detected = [False, False, False, False]

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
                    
                    # 中心の座標が、4つのエリアのどこにあるか判定（検出フラグをTrueにする）
                    if center_x < area_width:
                        current_ai_detected[0] = True  # 席1に人がいる
                    elif center_x < area_width * 2:
                        current_ai_detected[1] = True  # 席2に人がいる
                    elif center_x < area_width * 3:
                        current_ai_detected[2] = True  # 席3に人がいる
                    else:
                        current_ai_detected[3] = True  # 席4に人がいる

        # --------------------------------------------------
        # ⏱️ 【ここが新機能！】10秒間の空席保留（ディレイ）ロジック
        # --------------------------------------------------
        loop_time = time.time()
        # 最終的に画面やGitHubに送るための4席分のステータスリスト
        seats_vacant = [True, True, True, True]

        for i in range(4):
            if current_ai_detected[i]:
                # AIが人を検知したら、即座に「満席(False)」にしてタイマーをリセット
                st.session_state.seat_timers[i]["status"] = False
                st.session_state.seat_timers[i]["is_timer_running"] = False
            else:
                # AIが人を見失った（しゃがんだ・隠れた・一瞬外に出たなど）場合
                # 現在「満席(False)」で、まだタイマーが動いていないならカウントダウン開始
                if st.session_state.seat_timers[i]["status"] == False and not st.session_state.seat_timers[i]["is_timer_running"]:
                    st.session_state.seat_timers[i]["last_seen"] = loop_time
                    st.session_state.seat_timers[i]["is_timer_running"] = True
                
                # タイマーが動いている場合、10秒経過したかチェック
                if st.session_state.seat_timers[i]["is_timer_running"]:
                    elapsed_time = loop_time - st.session_state.seat_timers[i]["last_seen"]
                    if elapsed_time >= 10:  # 💡ここを「5」に変えれば5秒保留になります
                        # 10秒間ずっと誰も検知されなかったら、本当に「空席(True)」に変える
                        st.session_state.seat_timers[i]["status"] = True
                        st.session_state.seat_timers[i]["is_timer_running"] = False
            
            # タイマー処理が終わった最終的な状態をリストに格納
            seats_vacant[i] = st.session_state.seat_timers[i]["status"]
        # --------------------------------------------------

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
                        # 10秒経過するまでは、AIがロストしても「満席」をキープする
                        st.error(f"🟥 席 {i+1}\n\n満席")
                    else:
                        st.success(f"🟩 席 {i+1}\n\n空席")
            
            # 全体の空席数を表示するおまけ機能
            vacant_count = seats_vacant.count(True)
            st.info(f"📊 現在の空席状況: **4席中 {vacant_count} 席が空いています**")

        # ==================================================
        # 🎯 自動でGitHubに状況を送信
        # ==================================================
        current_time = time.time()
        
        # 席の状況が前回の判定から変わったか、または前回の送信から30秒経った場合
        if seats_vacant != st.session_state.last_seats_status or (current_time - st.session_state.last_update_time > 30):
            
            # スマホ用アプリが見るためのテキストファイル（status.txt）を作成
            with open("status.txt", "w", encoding="utf-8") as f:
                # 1つずつの席の状況（True/False）をカンマ区切りで書き込む
                status_str = ",".join(map(str, seats_vacant))
                f.write(f"{status_str}\n{time.strftime('%H:%M:%S')}")
            
            # バックグラウンドでGitHubに自動でプッシュする
            try:
                subprocess.run(["git", "add", "status.txt"], check=True)
                subprocess.run(["git", "commit", "-m", "Update seat status [auto]"], check=True)
                subprocess.run(["git", "push"], check=True)
                print(f"[{time.strftime('%H:%M:%S')}] GitHubへの状況自動アップデートに成功しました！")
            except Exception as e:
                print(f"GitHubへのアップロード失敗: {e}")
                
            # 状態を保存して記憶する
            st.session_state.last_seats_status = seats_vacant.copy()
            st.session_state.last_update_time = current_time
        # ==================================================

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
    