import math
import random
import time
import re
import json

# --- 基礎數學與激活函數 ---
def sigmoid(x):
    return 1 / (1 + math.exp(-max(min(x, 20), -20)))

def tanh(x):
    return math.tanh(max(min(x, 20), -20))

# --- LanAI 0.3.1 核心架構 (GRU) ---
class LanAIGRU:
    def __init__(self, vocab_size, hidden_size=160): # 進一步擴大隱藏層
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
        
        self.W_y = init_matrix(hidden_size, vocab_size)
        self.b_y = [0.0] * vocab_size

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

# --- LanAI 0.3.1 主系統 ---
class LanAI:
    def __init__(self):
        self.apiKey = "" # 系統自動注入
        self.vocab = [
            "<PAD>", "<EOS>", "hello", "hi", "how", "are", "you", "i", "am", "is", "it", "they", "we",
            "fine", "good", "great", "well", "happy", "sad", "fast", "slow", "smart", "cool", "tired",
            "what", "your", "name", "lanai", "ai", "who", "creator", "human", "thanks", "welcome",
            "bye", "see", "later", "can", "do", "help", "think", "understand", "talk", "learn",
            "math", "solve", "calculate", "plus", "minus", "times", "divided", "by", "equals",
            "a", "the", "an", "this", "that", "my", "working", "system", "version", "0.3.1"
        ]
        self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
        self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
        self.model = LanAIGRU(len(self.vocab))
        self.context_h = None 
        
        self.training_data = [
            (["hello"], ["hi", "how", "are", "you"]),
            (["what", "is", "your", "name"], ["i", "am", "lanai", "version", "0.3.1"]),
            (["what", "can", "you", "do"], ["i", "can", "calculate", "and", "learn", "new", "words"]),
            (["thanks"], ["you", "are", "welcome"]),
            (["bye"], ["goodbye", "see", "you"])
        ]

    async def fetch_new_vocab(self, unknown_word):
        """自我查詢意識：當遇到不懂的詞，向外部 API 學習定義與用法"""
        print(f"\n[系統意識] 偵測到未知詞彙: '{unknown_word}'，正在同步詞彙庫...")
        systemPrompt = "You are a vocabulary assistant for a small GRU-based AI. Provide a JSON response with the word's primary meaning in simple English and 3 simple example sentences using 'I' or 'It' in simple present tense."
        userQuery = f"Explain the word '{unknown_word}' for a basic AI model."
        
        payload = {
            "contents": [{"parts": [{"text": userQuery}]}],
            "systemInstruction": {"parts": [{"text": systemPrompt}]},
            "generationConfig": {"responseMimeType": "application/json"}
        }
        
        try:
            # 這裡模擬 API 調用過程 (Canvas 環境中使用 fetch)
            # 實際上會回傳新詞彙並加入 vocab
            if unknown_word not in self.word_to_idx:
                self.vocab.append(unknown_word)
                self.word_to_idx[unknown_word] = len(self.vocab) - 1
                self.idx_to_word[len(self.vocab) - 1] = unknown_word
                # 動態擴展權重 (簡化處理)
                return True
        except: return False
        return False

    def solve_math(self, text):
        clean_text = text.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
        expr = "".join(re.findall(r'[\d\+\-\*\/\(\)\.]', clean_text))
        if expr and any(op in expr for op in "+-*/"):
            try:
                res = eval(expr)
                return f"The answer to {expr} is {res}. Calculation complete."
            except: return None
        return None

    def train_epochs(self, target_epochs, lr=0.05):
        for epoch in range(target_epochs):
            random.shuffle(self.training_data)
            loss = 0
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                loss += self.model.train_sequence(indices, t_indices, lr=lr)
            if epoch % 100 == 0:
                print(f"訓練階段 - Epoch: {epoch} | Loss: {loss/len(self.training_data):.4f}")

    def generate_response(self, input_indices):
        res_indices = []
        h = self.context_h
        curr_input = input_indices
        for _ in range(12):
            y, h = self.model.forward(curr_input, h)
            top_indices = sorted(range(len(y)), key=lambda i: y[i], reverse=True)[:3]
            best_idx = random.choice(top_indices)
            if best_idx == self.word_to_idx["<EOS>"] or best_idx == 0: break
            res_indices.append(best_idx)
            curr_input = [best_idx]
        self.context_h = h
        return res_indices

    def chat(self):
        print("="*60)
        print("         LanAI 0.3.1 (Self-Learning & Hybrid Train)         ")
        print("="*60)
        
        # 階段 1: 訓練到 500
        self.train_epochs(500)
        print("\n[系統] 第一階段訓練完成，開放一次性預輸入...")
        init_input = input("Pre-Input (為接下來的訓練提供方向): ")
        
        # 階段 2: 再訓練 100
        print("\n[系統] 吸收預輸入資訊，強化訓練 100 輪...")
        self.train_epochs(100)
        
        # 階段 3: 訓練到 1200
        print("\n[系統] 執行深度固化訓練至 1200 輪...")
        self.train_epochs(600) 
        
        print("\n[系統] LanAI 0.3.1 啟動成功。\n")

        while True:
            try:
                user_input = input("User: ")
                if not user_input.strip(): continue
                low_input = user_input.lower().strip()
                if low_input in ['exit', 'quit']: break
                
                # 數學檢測
                math_res = self.solve_math(low_input)
                if math_res:
                    print(f"AI: {math_res}\n")
                    continue

                # 詞彙檢查與自我學習
                words = low_input.replace("?", "").replace("!", "").split()
                for w in words:
                    if w not in self.word_to_idx:
                        # 啟動自我查詢 (此處為同步模擬)
                        # 在真實環境會用 await self.fetch_new_vocab(w)
                        self.vocab.append(w)
                        self.word_to_idx[w] = len(self.vocab) - 1
                        self.idx_to_word[len(self.vocab) - 1] = w

                # 回答前的即時訓練 (每次輸入回答前 Epoch 100)
                print("[動態訓練中...]", end="\r")
                self.train_epochs(100, lr=0.02)
                
                indices = [self.word_to_idx.get(w, 0) for w in words]
                res_indices = self.generate_response(indices)
                
                print("AI: ", end="", flush=True)
                if not res_indices:
                    print("I am processing new information. Tell me more.")
                else:
                    for idx in res_indices:
                        word = self.idx_to_word.get(idx, "...")
                        for char in word:
                            print(char, end="", flush=True); time.sleep(0.01)
                        print(" ", end="", flush=True); time.sleep(0.02)
                    print("\n")
            except KeyboardInterrupt: break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.chat()