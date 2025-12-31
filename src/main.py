import flet as ft
import requests
import json
from datetime import datetime
import subprocess
import threading
import time

WEEK_STRING="月火水木金土日"

jma_weather_codes = {}
with open('jma-weather-images/codes.json') as f:
    jma_weather_codes = json.load(f)


def create_weather_row(weather_info_list, width, first_row):
    """
    天気情報表示処理
    1row分のcontrolリストを策せ薄る
    
    :param weather_info_list: 天気情報リスト
    :param width: タイル横幅
    :param first_row: 1行目かどうか
    """

    if weather_info_list is None:
        return []

    day_font_size = 24
    if not first_row:
        day_font_size = 16

    column_list = []
    for winfo in weather_info_list:
        controls = []
        for key, value in winfo.items():
            if key == 'time_defines':
                controls.append(
                    ft.Container(
                        content=ft.Text(value, size=day_font_size),
                        alignment=ft.alignment.center,
                        
                    )
                )
            elif key == 'weatherCodes':
                controls.append(
                    ft.Container(
                        content=ft.Image(
                            src=f"jma-weather-images/output_refs/{value}.png",
                            width=width,
                            fit=ft.ImageFit.CONTAIN,
                        ),
                        margin=5,
                        padding=0,
                        alignment=ft.alignment.center,
                    )
                )
                controls.append(
                    ft.Container(
                        content=ft.Text(jma_weather_codes[value]['desc'], size=11),
                        margin=5,
                        padding=5,
                        alignment=ft.alignment.center,
                        border=ft.Border(top=ft.BorderSide(width=1), right=ft.BorderSide(width=1), bottom=ft.BorderSide(width=1), left=ft.BorderSide(width=1)),
                        border_radius=5,
                    )
                )
    
        column_list.append(ft.Column(controls=controls, spacing=0, width=width))
    
    return column_list


def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "Containers - clickable and not"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.theme = ft.Theme(font_family="TakaoPGothic")

    jma_url = "https://www.jma.go.jp/bosai/common/const/area.json"
    jma_json = requests.get(jma_url).json()
    jma_centers = jma_json['centers']
    jma_offices = jma_json['offices']
    jma_class10s = jma_json['class10s']

    default_centers = "010400"
    default_offices = "230000"
    default_areas = '230010'

    # タイトル
    content=ft.Text("場所")

    # ##################
    #  ダイアログ表示処理
    # ##################
    def create_confirm(title, message, yes_func=lambda e: page.close(e.control.parent), no_func=lambda e: page.close(e.control.parent)):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Yes", on_click=yes_func),
                ft.TextButton("No", on_click=no_func),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)
    def create_alert(title, message, ok_func=lambda e: page.close(e.control.parent)):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=ok_func),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)
    
    # ##################
    #  地方プルダウン
    # ##################
    centers_dropdown_list = [ft.dropdown.Option(text=' '), ]
    for key, value in jma_centers.items():
        centers_dropdown_list.append(ft.dropdown.Option(text=value['name'], key=key))

    def centers_dropdown_changed(e):
        for i in reversed(range(1, len(page.controls))):
            page.remove_at(i)
        offices_pulldown.value = ' '
        offices_pulldown.key = None
        offices_list = [ft.dropdown.Option(text=' '), ]
        offices_pulldown.options = offices_list
        areas_pulldown.value = ' '
        areas_pulldown.key = None
        areas_list = [ft.dropdown.Option(text=' '), ]
        areas_pulldown.options = areas_list
        if centers_pulldown.value not in jma_centers:
            page.update()
            return
        for key in jma_centers[centers_pulldown.value]['children']:
            offices_list.append(ft.dropdown.Option(text=jma_offices[key]['name'], key=key))

        page.update()

    centers_pulldown = ft.Dropdown(
        value =default_centers,
        on_change=centers_dropdown_changed,
        options=centers_dropdown_list,
        width=200,
    )

    # ##################
    #  県プルダウン
    # ##################
    offices_list = [ft.dropdown.Option(text=' '), ]
    for key in jma_centers[default_centers]['children']:
        offices_list.append(ft.dropdown.Option(text=jma_offices[key]['name'], key=key))

    def offices_dropdown_changed(e):
        for i in reversed(range(1, len(page.controls))):
            page.remove_at(i)
        print(centers_pulldown.value)
        print(offices_pulldown.value)
        areas_pulldown.value = ' '
        areas_pulldown.key = None
        areas_list = [ft.dropdown.Option(text=' '), ]
        areas_pulldown.options = areas_list

        if offices_pulldown.value == ' ':
            page.update()
            return

        for key in jma_offices[offices_pulldown.value]['children']:
            areas_list.append(ft.dropdown.Option(text=jma_class10s[key]['name'], key=key))
            print("class10s:"+str(jma_class10s[key]))

        page.update()

    offices_pulldown = ft.Dropdown(
        value = default_offices,
        on_change=offices_dropdown_changed,
        options=offices_list,
        width=200,
    )

    # ##################
    #  エリアプルダウン
    # ##################
    areas_list = [ft.dropdown.Option(text=' '), ]
    for key in jma_offices[default_offices]['children']:
        areas_list.append(ft.dropdown.Option(text=jma_class10s[key]['name'], key=key))

    def areas_dropdown_changed(e):
        weather_tile_disp()

    areas_pulldown = ft.Dropdown(
        value = default_areas,
        on_change=areas_dropdown_changed,
        options=areas_list,
        width=200,
    )

    # ##################
    #  シャットダウンボタン
    # ##################
    def shutdown_cmd(e):
        page.close(e.control.parent)
        try:
            subprocess.run(["sudo", "poweroff"], check=True)
        except subprocess.CalledProcessError as err:
            create_alert('シャットダウンに失敗しました', f"シャットダウンに失敗しました: {err}")
        except Exception as e:
            create_alert('エラーが発生しました', f"エラーが発生しました: {e}")
    
    shutdonw_button = ft.ElevatedButton(text="シャットダウン", on_click=lambda e: create_confirm('シャットダウン', 'シャットダウンします', shutdown_cmd))

    # ##################
    #  天気情報表示処理
    # ##################
    def weather_tile_disp():
        # いったん削除
        for i in reversed(range(1, len(page.controls))):
            page.remove_at(i)
        
        # 天気情報取得
        weather1, weather2 = get_weather_code()
        
        # 1行目表示
        col_list_1 = create_weather_row(weather_info_list=weather1, width=200, first_row=True)
        row1 = ft.Row(controls=col_list_1, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START)
        page.add(row1)

        # 2行目表示
        col_list_2 = create_weather_row(weather_info_list=weather2, width=100, first_row=False)
        row2 = ft.Row(controls=col_list_2, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START)
        page.add(row2)

        page.update()


    # ##################
    #  天気情報取得処理
    # ##################
    def get_weather_code():
        """
        天気情報取得処理

        気象庁のJSONから以下の構造のリストを作る
        [
            time_defines:日付文字列(フォーマット:"mm/dd(曜日)"),
            weatherCodes:天気コード("101"など)
        ]
        """
        jma_weather_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{offices_pulldown.value}.json"
        try:
            jma_weather_json_str = requests.get(jma_weather_url)
            jma_weather_json = jma_weather_json_str.json()
        except:
            return None, None
        
        today_str = datetime.now().strftime('%m/%d')
        # 当日分を1番目の配列から取得
        time_defines1 = jma_weather_json[0]['timeSeries'][0]['timeDefines']
        weather1_list = list(filter(lambda x: x['area']['code'] == areas_pulldown.value, jma_weather_json[0]['timeSeries'][0]['areas']))[0]
        weather1 = []
        for idx, time_def in enumerate(time_defines1):
            # 曜日はロケールを設定すればフォーマット指定で出るみたいだけど、うまく動かないので文字配列で表示
            tdate = datetime.strptime(time_def + '(JST)', '%Y-%m-%dT%H:%M:%S%z(%Z)')
            tdate_str ='{:%m/%d}'.format(tdate)
            if today_str != tdate_str:
                continue
            tdate_str = '{:%m/%d}'.format(tdate) + '(' + WEEK_STRING[tdate.weekday()] + ')'
            weather1.append({'time_defines': tdate_str, 'weatherCodes': weather1_list['weatherCodes'][idx]})

        # 翌日以降を2番目の配列から取得
        time_defines2 = jma_weather_json[1]['timeSeries'][0]['timeDefines']
        weather2_list = list(filter(lambda x: x['area']['code'] == offices_pulldown.value, jma_weather_json[1]['timeSeries'][0]['areas']))
        weather2 = []
        if len(weather2_list) == 0:
            weather2_list = list(filter(lambda x: x['area']['code'] == areas_pulldown.value, jma_weather_json[1]['timeSeries'][0]['areas']))
        if len(weather2_list) > 0:
            for idx, time_def in enumerate(time_defines2):
                # 曜日はロケールを設定すればフォーマット指定で出るみたいだけど、うまく動かないので文字配列で表示
                tdate = datetime.strptime(time_def + '(JST)', '%Y-%m-%dT%H:%M:%S%z(%Z)')
                tdate_str ='{:%m/%d}'.format(tdate)
                if today_str == tdate_str:
                    continue
                tdate_str = '{:%m/%d}'.format(tdate) + '(' + WEEK_STRING[tdate.weekday()] + ')'
                weather2.append({'time_defines': tdate_str, 'weatherCodes': weather2_list[0]['weatherCodes'][idx]})
        return weather1, weather2
    
    # ##################
    #  画面表示メイン処理
    # ##################
    # 場所プルダウン、シャットダウンボタン表示
    row = ft.Row(controls=[content, centers_pulldown, offices_pulldown, areas_pulldown, shutdonw_button], alignment=ft.MainAxisAlignment.CENTER)
    page.add(row)

    # 天気予報表示
    weather_tile_disp()

    # ##################
    #  定期画面更新(1時間)
    # ##################
    def timer_function():
        while True:
            time.sleep(3600)
            # 天気予報再表示
            weather_tile_disp()
    threading.Thread(target=timer_function, daemon=True).start()

ft.app(target=main)
