import streamlit as st
import time

# スマホ向けに画面タイトルなどを設定
st.set_page_config(page_title="リアルタイム空席状況", layout="centered", page_icon="🪑")

st.title("🪑 カウンター席 空席状況")
st.write("現在のリアルタイムな空席状況です（5秒ごとに自動更新）")

# --- 🛰️ ローカルファイルから直接status.txtを読み込む関数 ---
def fetch_status():
    try:
        # パソコン内の同じフォルダにある status.txt を直接開いて読み込む
        with open("status.txt", "r", encoding="utf-8") as f:
            lines = f.read().split("\n")
            
            if lines and lines[0]:
                # 1行目：True,False... 2行目：時間
                seats_data = lines[0].split(",")
                last_time = lines[1] if len(lines) > 1 else "不明"
                
                # 文字列をBool型（True/False）に変換
                seats_vacant = [status.strip() == "True" for status in seats_data]
                return seats_vacant, last_time
    except Exception as e:
        pass
    return None, None

# --- 📱 スマホ画面の見た目を作る（フロントエンド） ---
seats_vacant, last_time = fetch_status()

if seats_vacant and len(seats_vacant) == 4:
    st.caption(f"🕒 最終更新時刻: {last_time}")
    st.write("---")
    
    # スマホで見やすいように、縦（カード型）に綺麗に並べる
    for i in range(4):
        with st.container():
            col_icon, col_text = st.columns([1, 4]) # アイコンと文字の幅の比率
            with col_icon:
                if not seats_vacant[i]:
                    st.write("🟥") # 満席アイコン
                else:
                    st.write("🟩") # 空席アイコン
            with col_text:
                if not seats_vacant[i]:
                    st.error(f"席 {i+1} ： 満席")
                else:
                    st.success(f"席 {i+1} ： 空席（座れます）")
            
    st.write("---")
    # 全体の空席数を表示するおまけ機能
    vacant_count = seats_vacant.count(True)
    if vacant_count > 0:
        st.info(f"💡 現在、4席中 **{vacant_count} 席** 空いています！")
    else:
        st.warning("⚠️ 現在、すべての席が満席です。")
else:
    st.warning("🔄 現在、お店からのデータ（status.txt）を読み込み中です。")
    st.caption("※店側のPCでカメラが動いていて、status.txtが作られているか確認してください。")

# --- 🔄 【ここを修正】5秒後に画面全体を強制リロードする仕組み ---
time.sleep(5)
st.rerun()