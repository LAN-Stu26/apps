#清除畫面
import os
os.system('cls')

# 變數初始化
ch = 0
en = 0
ma = 0
ss = 0
fs = 0
act_a = "n"
act_b = "n"
act_c = "n"
act_d = "n"
pr = 0
can = 0
txt = "學期成績"
more = "n"
title = "未知標題"

# 主程式
print("歡迎使用成績計算程式")
ch = float(input("請輸入國文領域成績: "))
en = float(input("請輸入英文領域成績: "))
ma = float(input("請輸入數學領域成績: "))
ss = float(input("請輸入社會領域成績: "))
fs = float(input("請輸入自然領域成績: "))

act_a = input("是否要計算平均成績？(y/n): ")
act_b = input("是否要計算總成績？(y/n): ")
act_c = input("是否要計算排名？ 計算需要 PR 值和考試人數 (y/n): ")
if act_c == "y":
    pr = float(input("請輸入 PR 值: "))
    can = float(input("請輸入考試人數: "))


# 判斷與計算
# 判斷是否計算平均成績
score = ch+en+ma+ss+fs

if act_a == "y":
    print('平均分數為:', score/5)

# 判斷是否計算總成績
if act_b == "y":
    print('總成績為:', score)

# 2次判斷是否計算排名
if act_c == "y":
    print('排名為:', int(can*(1-(pr/100))))

act_d = input("是否將輸出果存在 .txt 檔案中？(y/n): ")
if act_d == "y":
    txt = input("請輸入要儲存的檔案名稱（不含副檔名|輸入 N 不更改檔案名稱）: ")
    if txt == "N":
        txt = "學期成績"
    
    more = input("新增此次紀錄標題?(y/n): ")

    with open(f"{txt}.txt", "a", encoding="utf-8") as f:
        
        #填入標題
        if more == "y":
            title = input("請輸入標題名稱: ")
            f.write(f"\n===== {title} =====\n")

        # 填入計算時間
        from datetime import datetime
        now = datetime.now()
        f.write(f"\n----- 成績計算時間：{now.strftime('%Y-%m-%d %H:%M:%S')} -----\n")

        # 填入各科成績
        print('各科成績為:', ch, en, ma, ss, fs, '(國英數社自)', file=f)


        # 判斷是否計算平均成績
        if act_a == "y":
            print('平均分數為:', score/5, file=f)

        # 判斷是否計算總成績
        if act_b == "y":
            print('總成績為:', score, file=f)

        # 2次判斷是否計算排名
        if act_c == "y":
            print('排名為:', int(can*(1-(pr/100))), file=f)
        print("=========================", file=f)

print("感謝使用本程式，再見！")
