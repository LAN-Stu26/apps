import random

def show_all_rules():
    """顯示所有遊戲模式的規則"""
    print("\n================ 遊戲規則說明 ================")
    print("【模式 1：使用者猜】")
    print("由你設定數字範圍，電腦會想一個該範圍內的數字。")
    print("你進行猜測，電腦會提示『太大』或『太小』，並自動縮小顯示範圍，直到你猜中。")
    print("\n【模式 2：電腦猜】")
    print("範圍固定在 1-100。你在心中想一個數字。")
    print("電腦會進行猜測，你需要回饋：1(太大)、2(太小)、3(正確)。")
    print("\n【模式 3：變數模式】")
    print("最具挑戰性的模式！答案會隨著你的猜測次數定期改變。")
    print("- 簡單：每 5 次換答案。")
    print("- 普通：每 3 次換答案。")
    print("- 困難：每 1 次換答案。")
    print("- 地獄：範圍固定 1-100，每 1 次換答案。")
    print("==============================================")

def user_guesses():
    """模式 1: 使用者猜電腦想的數字"""
    print("\n--- 模式 1: 使用者猜數字 ---")
    print("(提示：輸入 'r' 可查看此模式規則)")
    
    # 1. 使用者自訂數字範圍
    try:
        min_input = input("請輸入範圍最小值: ")
        if min_input.lower() == 'r':
            print("【規則】電腦會想一個範圍內的數字，由你來猜。猜錯時會自動更新範圍提示，直到猜中為止。")
            min_input = input("請輸入範圍最小值: ")
        min_val = int(min_input)

        max_input = input("請輸入範圍最大值: ")
        if max_input.lower() == 'r':
            print("【規則】電腦會想一個範圍內的數字，由你來猜。猜錯時會自動更新範圍提示，直到猜中為止。")
            max_input = input("請輸入範圍最大值: ")
        max_val = int(max_input)

        if min_val >= max_val:
            print("錯誤：最小值必須小於最大值！")
            return
    except ValueError:
        print("錯誤：請輸入有效的整數！")
        return

    target = random.randint(min_val, max_val)
    attempts = 0
    # current_min 和 current_max 用於自動更改顯示範圍
    current_min = min_val
    current_max = max_val

    print(f"遊戲開始！我已經想好了一個 {current_min} 到 {current_max} 之間的數字。")

    while True:
        try:
            user_input = input(f"\n請輸入你的猜測 ({current_min}-{current_max})，或輸入 'r' 查看規則: ")
            
            if user_input.lower() == 'r':
                print(f"【規則】請猜一個 {current_min} 到 {current_max} 之間的數字。")
                continue
                
            guess = int(user_input)
            attempts += 1

            if guess < target:
                # 自動更新最小值邊界
                if guess >= current_min:
                    current_min = guess 
                print(f"太小了！再試一次。範圍 {current_min}-{current_max}")
            elif guess > target:
                # 自動更新最大值邊界
                if guess <= current_max:
                    current_max = guess
                print(f"太大了！再試一次。範圍 {current_min}-{current_max}")
            else:
                print(f"恭喜你答對了！答案就是 {target}。")
                print(f"你總共猜了 {attempts} 次。")
                break
        except ValueError:
            print("請輸入有效的數字或 'r'！")

def computer_guesses():
    """模式 2: 電腦猜使用者心裡的數字"""
    print("\n--- 模式 2: 電腦猜使用者數字 ---")
    print("(提示：輸入 'r' 可查看此模式規則)")
    
    # 1. 電腦自訂範圍 (不可大於 100)
    low = 1
    high = 100
    print(f"請在心中想一個 {low} 到 {high} 之間的數字，讓我來猜。")
    
    attempts = 0
    while low <= high:
        # 電腦使用二分法進行邏輯猜測
        guess = (low + high) // 2
        attempts += 1
        print(f"\n電腦猜測: {guess} (目前範圍: {low}-{high})")
        
        # 2. 使用者負責檢查
        feedback = input("請提供回饋 (1: 太大, 2: 太小, 3: 正確, r: 規則): ").strip().lower()
        
        if feedback == 'r':
            print("【規則】根據電腦給出的數字，若太大請輸入 1，太小請輸入 2，正確請輸入 3。電腦會自動縮小範圍直到猜中。")
            attempts -= 1
            continue
        elif feedback == '1': # 太大
            if guess <= low:
                print("不要開玩笑了! 我不笨! 我有腦好嗎!!!! 你一定搞混了!!!!!!!!!!!!!!!")
                attempts -= 1
                continue
            high = guess - 1 # 修正：排除掉已經猜過且太大的數字
            print(f"太大了！電腦會再試一次。範圍 {low}-{high}")
        elif feedback == '2': # 太小
            if guess >= high:
                print("不要開玩笑了! 我不笨! 我有腦好嗎!!!! 你一定搞混了!!!!!!!!!!!!!!!")
                attempts -= 1
                continue
            low = guess + 1 # 修正：排除掉已經猜過且太小的數字
            print(f"太小了！電腦會再試一次。範圍 {low}-{high}")
        elif feedback == '3': # 正確
            print(f"電腦贏了！答案是 {guess}。")
            print(f"電腦總共猜了 {attempts} 次。")
            break
        else:
            print("輸入無效，請輸入 1, 2, 3 或 r。")
            attempts -= 1 # 無效輸入不計次
    else:
        # 這種情況通常發生在範圍被擠壓到沒有可能數字時
        print("不要開玩笑了! 我不笨! 我有腦好嗎!!!! 你一定搞混了!!!!!!!!!!!!!!!")

def variable_mode():
    """模式 3: 變數模式 (答案會改變)"""
    print("\n--- 模式 3: 變數模式 ---")
    print("(提示：輸入 'r' 可查看此模式規則)")
    print("難度說明：")
    print("1. 簡單 (每猜 5 次更換答案)")
    print("2. 普通 (每猜 3 次更換答案)")
    print("3. 困難 (每猜 1 次更換答案)")
    print("4. 地獄 (範圍固定 1-100，每猜 1 次更換答案)")
    
    choice = input("請選擇難度 (1-4) 或輸入 'r' 查看規則: ").lower()
    
    if choice == 'r':
        print("【規則】答案會隨著你的猜測次數定期改變。難度越高，更換頻率越高。地獄難度則會固定範圍並每回合換答案。")
        choice = input("請選擇難度 (1-4): ")
    
    if choice == '4':
        min_val, max_val = 1, 100
        change_rate = 1
    else:
        try:
            if choice == '1': change_rate = 5
            elif choice == '2': change_rate = 3
            elif choice == '3': change_rate = 1
            else: raise ValueError
            
            min_val = int(input("請輸入範圍最小值: "))
            max_val = int(input("請輸入範圍最大值: "))
        except ValueError:
            print("輸入錯誤，回主選單。")
            return

    target = random.randint(min_val, max_val)
    attempts = 0
    
    print(f"遊戲開始！範圍：{min_val}-{max_val}。")
    
    while True:
        try:
            user_input = input(f"\n({attempts}次) 請猜測，或輸入 'r' 查看規則: ")
            
            if user_input.lower() == 'r':
                print(f"【規則】目前難度每猜 {change_rate} 次答案就會重選。範圍固定在 {min_val}-{max_val}。")
                continue

            guess = int(user_input)
            attempts += 1
            
            if guess == target:
                print(f"太強了！竟然在答案改變的情況下猜中 {target}！")
                print(f"總共嘗試 {attempts} 次。")
                break
            elif guess < target:
                print(f"太小了！範圍 {min_val}-{max_val}")
            else:
                print(f"太大了！範圍 {min_val}-{max_val}")
            
            # 答案變動邏輯
            if attempts % change_rate == 0:
                target = random.randint(min_val, max_val)
                print("【注意】答案已經重新隨機產生了！")
                
        except ValueError:
            print("請輸入數字或 'r'！")

def main():
    while True:
        print("\n===== 猜數字遊戲選單 =====")
        print("1. 使用者猜 (模式 1)")
        print("2. 電腦猜 (模式 2)")
        print("3. 變數模式 (模式 3)")
        print("R. 查看所有規則")
        print("Q. 離開遊戲")
        
        choice = input("請選擇模式: ").upper()
        
        if choice == '1':
            user_guesses()
        elif choice == '2':
            computer_guesses()
        elif choice == '3':
            variable_mode()
        elif choice == 'R':
            show_all_rules()
        elif choice == 'Q':
            print("謝謝遊玩，再見！")
            break
        else:
            print("請選擇正確的選項。")

if __name__ == "__main__":
    main()