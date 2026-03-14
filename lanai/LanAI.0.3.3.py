import math
import random
import time
import re
import json
import os

# --- 基礎數學與激活函數 ---
def sigmoid(x):
    return 1 / (1 + math.exp(-max(min(x, 20), -20)))

def tanh(x):
    return math.tanh(max(min(x, 20), -20))

# --- LanAI 0.3.2 核心架構 (GRU) ---
class LanAIGRU:
    def __init__(self, vocab_size, hidden_size=160): 
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        
        limit = math.sqrt(6 / (vocab_size + hidden_size))
        def init_matrix(r, c): return [[random.uniform(-limit, limit) for _ in range(c)] for _ in range(r)]
        
        self.W_r = init_matrix(vocab_size, hidden_size)
        self.U_r = init_matrix(hidden_size, hidden_size)
        self.b_r = [0.0] * hidden_size
        
        self.W_z = init_matrix(vocab_size, hidden_size)
        self.U_z = init_matrix(hidden_size, hidden_size)
        self.b_z = [0.0] * hidden_size
        
        self.W_h = init_matrix(vocab_size, hidden_size)
        self.U_h = init_matrix(hidden_size, hidden_size)
        self.b_h = [0.0] * hidden_size
        
        # W_y 維度: [hidden_size, vocab_size]
        self.W_y = init_matrix(hidden_size, vocab_size)
        self.b_y = [0.0] * vocab_size

    def expand_weights(self, new_vocab_size):
        """[更新 1] 權重動態擴展機制：當詞彙庫增加時，動態擴充網路矩陣維度"""
        diff = new_vocab_size - self.vocab_size
        if diff <= 0: return
        
        limit = math.sqrt(6 / (new_vocab_size + self.hidden_size))
        
        # 擴充輸入層的詞彙列 (W_r, W_z, W_h) -> 增加 diff 列
        for _ in range(diff):
            self.W_r.append([random.uniform(-limit, limit) for _ in range(self.hidden_size)])
            self.W_z.append([random.uniform(-limit, limit) for _ in range(self.hidden_size)])
            self.W_h.append([random.uniform(-limit, limit) for _ in range(self.hidden_size)])
            
        # 擴充輸出層的詞彙行 (W_y, b_y)
        for i in range(self.hidden_size):
            self.W_y[i].extend([random.uniform(-limit, limit) for _ in range(diff)])
        self.b_y.extend([0.0] * diff)
        
        self.vocab_size = new_vocab_size

    def forward(self, inputs, h_prev=None):
        h = h_prev[:] if h_prev else [0.0] * self.hidden_size
        for idx in inputs:
            idx = idx if idx < self.vocab_size else 0
            wr_row = self.W_r[idx]; wz_row = self.W_z[idx]; wh_row = self.W_h[idx]
            r = [sigmoid(wr_row[j] + sum(h[k] * self.U_r[k][j] for k in range(self.hidden_size)) + self.b_r[j]) for j in range(self.hidden_size)]
            z = [sigmoid(wz_row[j] + sum(h[k] * self.U_z[k][j] for k in range(self.hidden_size)) + self.b_z[j]) for j in range(self.hidden_size)]
            h_tilde = [tanh(wh_row[j] + sum((r[k] * h[k]) * self.U_h[k][j] for k in range(self.hidden_size)) + self.b_h[j]) for j in range(self.hidden_size)]
            h = [(1 - z[j]) * h[j] + z[j] * h_tilde[j] for j in range(self.hidden_size)]
        y = [sum(h[k] * self.W_y[k][j] for k in range(self.hidden_size)) + self.b_y[j] for j in range(self.vocab_size)]
        return y, h

    def train_sequence(self, input_indices, target_indices, lr=0.08):
        h_state = None
        current_input = input_indices
        total_loss = 0
        for target_word_idx in target_indices:
            y, h_state = self.forward(current_input, h_state)
            max_y = max(y)
            exp_y = [math.exp(v - max_y) for v in y]
            sum_exp = sum(exp_y) + 1e-9
            probs = [e / sum_exp for e in exp_y]
            dy = probs[:]
            dy[target_word_idx] -= 1.0
            for i in range(self.hidden_size):
                h_val = h_state[i]
                for j in range(self.vocab_size):
                    self.W_y[i][j] -= lr * dy[j] * h_val
            total_loss -= math.log(max(probs[target_word_idx], 1e-10))
            current_input = [target_word_idx]
        return total_loss

# --- LanAI 0.3.2 主系統 ---
class LanAI:
    def __init__(self, model_path="lanai_memory.json"):
        self.model_path = model_path
        self.context_h = None 
        
        self.training_data = [
            (["hello"], ["hi", "how", "are", "you"]),
            (["what", "is", "your", "name"], ["i", "am", "lanai", "version", "0.3.3"]),
            (["what", "can", "you", "do"], ["i", "can", "calculate", "and", "learn", "new", "words", "now"]),
            (["thanks"], ["you", "are", "welcome"]),
            (["bye"], ["goodbye", "see", "you"])
        ]
        
        # 嘗試載入記憶，若無則初始化
        if not self.load_model():
            print("[系統] 找不到既有記憶，初始化預設模型...")
            self.vocab = [
                "<PAD>", "<EOS>", "hello", "hi", "how", "are", "you", "i", "am", "is", "it", "they", "we",
                "fine", "good", "great", "well", "happy", "sad", "fast", "slow", "smart", "cool", "tired",
                "what", "your", "name", "lanai", "ai", "who", "creator", "human", "thanks", "welcome",
                "bye", "see", "later", "can", "do", "help", "think", "understand", "talk", "learn",
                "math", "solve", "calculate", "plus", "minus", "times", "divided", "by", "equals",
                "a", "the", "an", "this", "that", "my", "working", "system", "version", "0.3.3"
            ]
            self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
            self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
            self.model = LanAIGRU(len(self.vocab))
            self.is_new_model = True
        else:
            self.is_new_model = False

    def save_model(self):
        """[更新 2] 持久化記憶：將模型權重與詞彙表存入硬碟"""
        print("[系統] 正在儲存記憶到磁碟...")
        data = {
            "vocab": self.vocab,
            "W_r": self.model.W_r, "U_r": self.model.U_r, "b_r": self.model.b_r,
            "W_z": self.model.W_z, "U_z": self.model.U_z, "b_z": self.model.b_z,
            "W_h": self.model.W_h, "U_h": self.model.U_h, "b_h": self.model.b_h,
            "W_y": self.model.W_y, "b_y": self.model.b_y
        }
        with open(self.model_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print("[系統] 記憶儲存成功！")

    def load_model(self):
        """[更新 2] 持久化記憶：從硬碟讀取模型"""
        if os.path.exists(self.model_path):
            try:
                print("[系統] 偵測到既有記憶，正在喚醒...")
                with open(self.model_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.vocab = data["vocab"]
                self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
                self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
                
                self.model = LanAIGRU(len(self.vocab))
                self.model.W_r = data["W_r"]; self.model.U_r = data["U_r"]; self.model.b_r = data["b_r"]
                self.model.W_z = data["W_z"]; self.model.U_z = data["U_z"]; self.model.b_z = data["b_z"]
                self.model.W_h = data["W_h"]; self.model.U_h = data["U_h"]; self.model.b_h = data["b_h"]
                self.model.W_y = data["W_y"]; self.model.b_y = data["b_y"]
                return True
            except Exception as e:
                print(f"[警告] 記憶載入失敗 ({e})，將重新初始化。")
                return False
        return False

    def add_new_word(self, word):
        """處理新詞彙並擴展模型矩陣"""
        if word not in self.word_to_idx:
            self.vocab.append(word)
            self.word_to_idx[word] = len(self.vocab) - 1
            self.idx_to_word[len(self.vocab) - 1] = word
            self.model.expand_weights(len(self.vocab))
            return True
        return False

    def solve_math(self, text):
        """[更新 4] 增強數學與邏輯模組：支援英文數字與安全評估"""
        # 文字轉數字
        num_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
                   "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
        for k, v in num_map.items():
            text = re.sub(rf'\b{k}\b', v, text)
            
        clean_text = text.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
        
        # 只允許安全的數學字符
        expr = "".join(re.findall(r'[\d\+\-\*\/\(\)\.]', clean_text))
        
        # 簡單的安全檢查：確保結構成立且不為空
        if expr and any(op in expr for op in "+-*/"):
            try:
                # 限制 eval 使用的環境，避免安全風險
                res = eval(expr, {"__builtins__": None}, {})
                return f"The answer is {res}."
            except:
                return None
        return None

    def train_epochs(self, target_epochs, initial_lr=0.05):
        """[更新 3] 引入 Learning Rate Decay"""
        for epoch in range(target_epochs):
            random.shuffle(self.training_data)
            loss = 0
            # 隨 epoch 增加，學習率微幅遞減 (Decay)
            current_lr = initial_lr * (1 - (epoch / (target_epochs * 1.5))) 
            
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                loss += self.model.train_sequence(indices, t_indices, lr=current_lr)
            if epoch > 0 and epoch % 100 == 0:
                print(f"訓練進度 - Epoch: {epoch} | Loss: {loss/len(self.training_data):.4f} | LR: {current_lr:.4f}", end="\r")

    def generate_response(self, input_indices, temperature=0.6):
        """[更新 5] 輸出層取樣策略：引入 Temperature 係數"""
        res_indices = []
        h = self.context_h
        curr_input = input_indices
        for _ in range(15): # 稍微加長回覆句長
            y, h = self.model.forward(curr_input, h)
            
            # 套用 Temperature 取樣
            logits = [v / temperature for v in y]
            max_l = max(logits)
            exp_l = [math.exp(l - max_l) for l in logits]
            sum_exp = sum(exp_l)
            probs = [e / sum_exp for e in exp_l]
            
            r = random.random()
            cum = 0
            best_idx = 0
            for i, p in enumerate(probs):
                cum += p
                if r <= cum:
                    best_idx = i
                    break
            
            if best_idx == self.word_to_idx["<EOS>"] or best_idx == 0: 
                break
            res_indices.append(best_idx)
            curr_input = [best_idx]
            
        self.context_h = h
        return res_indices

    def thinking_layer(self, user_input, words):
        """[新增 0.3.3] 思考預處理層：判斷意圖與提取數學邏輯"""
        print("» [系統思考中] 分析語境與意圖...", end="\r")
        time.sleep(0.5) # 模擬思考延遲
        
        # 1. 數學/邏輯初步掃描
        math_res = self.solve_math(user_input)
        
        # 2. 提取意圖 (關鍵字過濾)
        logic_keywords = ["why", "how", "can", "what", "math", "solve", "calculate", "think", "who"]
        intent = "logic" if any(w in words for w in logic_keywords) else "chat"
        
        print(" " * 40, end="\r") # 清除思考中的字元
        if math_res:
            print("» [思考結果] 偵測到明確數學算式。")
        elif intent == "logic":
            print("» [思考結果] 偵測到邏輯需求，準備強化推論與訓練...")
        else:
            print("» [思考結果] 一般閒聊模式。")
            
        return math_res, intent

    def chat(self):
        print("="*60)
        print("         LanAI 0.3.3 (Thinking Enhanced & Dynamic GRU)         ")
        print("="*60)
        
        # 只有在全新建立模型時，才進行大量初階訓練
        if self.is_new_model:
            print("[系統] 模型為初始狀態，執行基礎認知訓練 (800 Epochs)...")
            self.train_epochs(800, initial_lr=0.08)
            print("\n[系統] 基礎訓練完成。")
            self.save_model()
        else:
            print("\n[系統] 記憶載入完畢，準備就緒。")

        while True:
            try:
                user_input = input("\nUser: ")
                if not user_input.strip(): continue
                low_input = user_input.lower().strip()
                if low_input in ['exit', 'quit']:
                    self.save_model() # 離開前儲存
                    break
                
                words = low_input.replace("?", "").replace("!", "").replace(",", "").split()
                
                # --- [新增 0.3.3] 思考預處理層 ---
                math_res, intent = self.thinking_layer(low_input, words)

                # 數學檢測提前處理
                if math_res:
                    print(f"AI (Logic Mode): {math_res}")
                    continue
                
                new_words_learned = False
                for w in words:
                    if self.add_new_word(w):
                        print(f"[系統意識] 學習到新詞彙: '{w}'，模型神經元已擴增！")
                        new_words_learned = True

                # --- [修改 0.3.3] 根據意圖進行目標引導訓練 ---
                if intent == "logic":
                    print("[動態微調] 邏輯強化深度訓練中...", end="\r")
                    if new_words_learned:
                        self.training_data.append((words, ["i", "think", "and", "learn"] + words))
                    self.train_epochs(150, initial_lr=0.04)
                elif new_words_learned:
                    print("[動態微調] 吸收新知識中...", end="\r")
                    self.training_data.append((words, ["i", "learned", "about"] + words))
                    self.train_epochs(50, initial_lr=0.03)
                else:
                    self.train_epochs(5, initial_lr=0.01)
                
                indices = [self.word_to_idx.get(w, 0) for w in words]
                
                # --- [修改 0.3.3] 動態 Temperature 採樣 ---
                temp = 0.2 if intent == "logic" else 0.7
                res_indices = self.generate_response(indices, temperature=temp)
                
                print("AI: ", end="", flush=True)
                if not res_indices:
                    print("I am processing new information. Tell me more.")
                else:
                    for idx in res_indices:
                        word = self.idx_to_word.get(idx, "...")
                        for char in word:
                            print(char, end="", flush=True); time.sleep(0.01)
                        print(" ", end="", flush=True); time.sleep(0.02)
                    print()
                    
            except KeyboardInterrupt: 
                print("\n[系統] 收到中斷訊號。")
                self.save_model()
                break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.chat()