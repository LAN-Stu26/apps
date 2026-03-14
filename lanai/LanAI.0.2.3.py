import math
import random
import time
import re

# --- 基礎數學與激活函數 ---
def sigmoid(x):
    return 1 / (1 + math.exp(-max(min(x, 20), -20)))

def tanh(x):
    return math.tanh(max(min(x, 20), -20))

# --- LanAI 0.2.3 核心架構 (GRU) ---
class LanAIGRU:
    def __init__(self, vocab_size, hidden_size=96):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        
        limit = math.sqrt(6 / (vocab_size + hidden_size))
        def init_matrix(r, c): return [[random.uniform(-limit, limit) for _ in range(c)] for _ in range(r)]
        
        # 權重初始化 (Reset, Update, Hidden)
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

    def train_sequence(self, input_indices, target_indices, lr=0.1):
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

# --- LanAI 0.2.3 主系統 ---
class LanAI:
    def __init__(self):
        # 擴充詞彙：包含基礎形容詞、連結詞與數學指令
        self.vocab = [
            "<PAD>", "<EOS>", "hello", "hi", "how", "are", "you", "i", "am", "is", "it", "they", "we",
            "fine", "good", "great", "well", "happy", "sad", "fast", "slow", "smart", "big", "small",
            "what", "your", "name", "lanai", "ai", "who", "creator", "human", "thanks", "welcome",
            "bye", "see", "later", "can", "do", "help", "think", "understand", "very", "much",
            "plus", "minus", "times", "divided", "by", "equals", "is", "calculate", "solve",
            "a", "the", "an", "this", "that", "working", "learning", "system", "version", "0.2.3"
        ]
        self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
        self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
        self.model = LanAIGRU(len(self.vocab))
        self.context_h = None 
        
        # 訓練資料：強化現在簡單式與基礎對話
        self.training_data = [
            (["hello"], ["hi", "i", "am", "happy"]),
            (["how", "are", "you"], ["i", "am", "good", "and", "smart"]),
            (["what", "is", "your", "name"], ["i", "am", "lanai", "system"]),
            (["who", "are", "you"], ["i", "am", "your", "ai", "friend"]),
            (["are", "you", "fast"], ["i", "am", "very", "fast"]),
            (["is", "it", "good"], ["yes", "it", "is", "very", "good"]),
            (["thanks"], ["you", "are", "welcome"]),
            (["bye"], ["see", "you", "later"]),
            (["can", "you", "help"], ["i", "can", "help", "you", "calculate"]),
            (["what", "is", "lanai"], ["lanai", "is", "a", "learning", "ai"])
        ]

    def pre_train(self, max_epochs=1200):
        print("LanAI 0.2.3 正在初始化文法邏輯與數學電路...")
        lr = 0.1
        for epoch in range(max_epochs):
            random.shuffle(self.training_data)
            epoch_loss = 0
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                epoch_loss += self.model.train_sequence(indices, t_indices, lr=lr)
            
            if epoch % 200 == 0:
                avg_l = epoch_loss / len(self.training_data)
                print(f"Epoch: {epoch} | Loss: {avg_l:.4f}")
                if avg_l < 0.1: break
        print("LanAI 0.2.3 升級完成：現在簡單式文法已載入。\n")

    def solve_math(self, text):
        """基礎數學解算器 (意圖偵測)"""
        text = text.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
        # 提取數字
        nums = re.findall(r'\d+\.?\d*', text)
        if len(nums) >= 2:
            try:
                a, b = float(nums[0]), float(nums[1])
                if "+" in text: res = a + b
                elif "-" in text: res = a - b
                elif "*" in text: res = a * b
                elif "/" in text: res = a / b if b != 0 else "undefined"
                else: return None
                return f"The calculation is {res}. I am smart!"
            except: return None
        return None

    def generate_response(self, input_indices):
        res_indices = []
        h = self.context_h
        curr_input = input_indices
        
        for _ in range(8):
            y, h = self.model.forward(curr_input, h)
            best_idx = y.index(max(y))

            if len(res_indices) == 0 and (best_idx == self.word_to_idx["<EOS>"] or best_idx == 0):
                temp_y = y[:]
                temp_y[0] = -999; temp_y[1] = -999
                best_idx = temp_y.index(max(temp_y))

            if best_idx == self.word_to_idx["<EOS>"] or best_idx == 0: break
            res_indices.append(best_idx)
            curr_input = [best_idx]
            
        self.context_h = h
        return res_indices

    def chat(self):
        print("="*60)
        print("         LanAI 0.2.3 (Grammar & Math Engine)         ")
        print("  Try: 'How are you?', 'What is 15 plus 30?', 'Bye'  ")
        print("="*60)
        while True:
            try:
                user_input = input("User: ")
                if not user_input.strip(): continue
                low_input = user_input.lower().strip()
                
                if low_input in ['exit', 'quit']: break
                
                # 優先檢查是否為數學問題
                math_res = self.solve_math(low_input)
                if math_res:
                    print(f"AI: {math_res}\n")
                    continue

                # 否則進入神經網路對話
                clean_input = low_input.replace("?", "").replace("!", "")
                indices = [self.word_to_idx.get(w, 0) for w in clean_input.split()]
                res_indices = self.generate_response(indices)
                
                if not res_indices:
                    print("AI: I am thinking... Can you repeat that?")
                else:
                    print("AI: ", end="", flush=True)
                    for idx in res_indices:
                        word = self.idx_to_word[idx]
                        for char in word:
                            print(char, end="", flush=True); time.sleep(0.02)
                        print(" ", end="", flush=True); time.sleep(0.04)
                    print("\n")
            except KeyboardInterrupt: break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.pre_train()
    lanai.chat()