import requests
import urllib3
import webbrowser
import time
import re

# SSL警告を非表示
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_game_data():
    """Live Client Data APIから試合情報を取得"""
    try:
        response = requests.get("https://127.0.0.1:2999/liveclientdata/allgamedata", verify=False)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None

def format_champion_name(raw_name):
    """言語依存しないrawChampionNameから英語名を抽出して整形"""
    if not raw_name:
        return ""
        
    # "game_character_displayname_Yasuo" のような形式から "Yasuo" を抽出
    base_name = raw_name.split('_')[-1]
    
    # 小文字化と記号・スペースの除去
    name = base_name.lower()
    name = re.sub(r'[^a-z0-9]', '', name)
    
    # 内部データ名とURL名の不一致を処理
    if name == 'monkeyking':
        return 'wukong'
    if name == 'renataglasc':
        return 'renata'
    if name == 'nunuwillump':
        return 'nunu'
    return name

def format_lane_name(position):
    """APIのポジション名をLolalyticsのレーン名に変換"""
    if not position:
        return ""
    pos = position.lower()
    if pos == 'utility':
        return 'support'
    return pos

def main():
    """メインループを処理"""
    print("試合の開始を待機中...")
    processed_game = False

    while True:
        game_data = get_game_data()

        if game_data and not processed_game:
            try:
                active_player = game_data.get('activePlayer', {})
                my_name = active_player.get('summonerName') or active_player.get('riotIdGameName')
                all_players = game_data.get('allPlayers', [])

                # 自身のプレイヤー情報を抽出
                my_player = next((p for p in all_players if p.get('summonerName') == my_name or p.get('riotIdGameName') == my_name), None)
                
                # ポジション情報が存在する（ARAM等ではない）か確認
                if my_player and my_player.get('position') and my_player.get('position') != 'None':
                    # 日本語名ではなく、内部データの英語名を取得
                    my_raw_champ = my_player.get('rawChampionName', '')
                    my_champ = format_champion_name(my_raw_champ)
                    my_pos = format_lane_name(my_player['position'])
                    my_team = my_player.get('team')

                    # 敵チームの同ポジションプレイヤーを抽出
                    enemy_player = next((p for p in all_players if p.get('team') != my_team and format_lane_name(p.get('position', '')) == my_pos), None)

                    if enemy_player:
                        enemy_raw_champ = enemy_player.get('rawChampionName', '')
                        enemy_champ = format_champion_name(enemy_raw_champ)
                        
                        # ロード直後でチャンピオン名が空の場合はリトライする
                        if not my_champ or not enemy_champ:
                            print("チャンピオン情報を読み込み中...")
                            time.sleep(2)
                            continue
                            
                        # LolalyticsのURLを構築
                        url = f"https://lolalytics.com/lol/{my_champ}/vs/{enemy_champ}/build/?lane={my_pos}"
                        print(f"対面を検出: {my_champ} vs {enemy_champ} ({my_pos} lane)")
                        
                        # 既定のブラウザでURLを起動
                        webbrowser.open(url)
                        processed_game = True
                    else:
                        print("対面プレイヤーの特定に失敗しました。")
                        processed_game = True
            except Exception as e:
                print(f"エラーが発生: {e}")
        
        # 試合終了後に状態を初期化
        elif not game_data and processed_game:
            print("試合終了を検知。次の試合を待機中...")
            processed_game = False
            
        # 負荷軽減のため5秒間隔で実行
        time.sleep(5)

if __name__ == "__main__":
    main()