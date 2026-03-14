import math
import random
import time
import re

# --- 基礎數學與激活函數 ---
def sigmoid(x):
    return 1 / (1 + math.exp(-max(min(x, 20), -20)))

def tanh(x):
    return math.tanh(max(min(x, 20), -20))

# --- LanAI 3.0 核心架構 (GRU) ---
class LanAIGRU:
    def __init__(self, vocab_size, hidden_size=128): # 擴大隱藏層以存儲更多文法
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        
        limit = math.sqrt(6 / (vocab_size + hidden_size))
        def init_matrix(r, c): return [[random.uniform(-limit, limit) for _ in range(c)] for _ in range(r)]
        
        # 權重初始化
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

# --- LanAI 3.0 主系統 ---
class LanAI:
    def __init__(self):
        # 詞彙擴充：版本升級 3.0，增加動詞與多態形容詞
        self.vocab = [
            "<PAD>", "<EOS>", "hello", "hi", "how", "are", "you", "i", "am", "is", "it", "they", "we",
            "fine", "good", "great", "well", "happy", "sad", "fast", "slow", "smart", "cool", "tired",
            "what", "your", "name", "lanai", "ai", "who", "creator", "human", "thanks", "welcome",
            "bye", "see", "later", "can", "do", "help", "think", "understand", "talk", "learn",
            "plus", "minus", "times", "divided", "by", "equals", "calculate", "solve", "math",
            "a", "the", "an", "this", "that", "my", "working", "learning", "system", "version", "3.0",
            "everything", "anything", "nothing", "yes", "no", "okay", "sorry", "beautiful", "interesting",
            "eat", "sleep", "play", "code", "write", "read", "very", "really", "so", "much"
        ]
        self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
        self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
        self.model = LanAIGRU(len(self.vocab))
        self.context_h = None 
        
        # 訓練資料：強化「能力描述」與多樣化回應，避免重複
        self.training_data = [
            (["hello"], ["hi", "how", "is", "your", "day"]),
            (["hi"], ["hello", "i", "am", "working"]),
            (["how", "are", "you"], ["i", "am", "great", "thanks"]),
            (["what", "is", "your", "name"], ["i", "am", "lanai", "version", "3.0"]),
            (["who", "are", "you"], ["i", "am", "a", "smart", "ai", "system"]),
            (["what", "can", "you", "do"], ["i", "can", "talk", "learn", "and", "solve", "math"]),
            (["are", "you", "smart"], ["yes", "i", "am", "really", "smart"]),
            (["thanks"], ["you", "are", "welcome", "my", "friend"]),
            (["bye"], ["goodbye", "see", "you", "later"]),
            (["can", "you", "think"], ["i", "think", "so", "much", "every", "day"]),
            (["do", "you", "understand"], ["yes", "i", "understand", "everything"]),
            (["is", "it", "cool"], ["it", "is", "very", "interesting", "and", "cool"]),
            (["good", "job"], ["thanks", "i", "am", "happy", "now"])
        ]

    def pre_train(self, max_epochs=1500):
        print("LanAI 3.0 深度學習中：神經元連結中...")
        lr = 0.1
        for epoch in range(max_epochs):
            random.shuffle(self.training_data)
            epoch_loss = 0
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                epoch_loss += self.model.train_sequence(indices, t_indices, lr=lr)
            
            if epoch % 300 == 0:
                avg_l = epoch_loss / len(self.training_data)
                print(f"Epoch: {epoch} | Loss: {avg_l:.4f}")
                if avg_l < 0.05: break
                lr *= 0.98 # 學習率衰減，穩定文法
        print("LanAI 3.0 部署成功。數學引擎與文法邏輯已就緒。\n")

    def solve_math(self, text):
        """升級版數學解算器：支持四則運算優先級與複雜表達式"""
        # 過濾出數字與運算符號
        clean_text = text.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
        # 只保留合法字符以防止安全性問題
        expr = "".join(re.findall(r'[\d\+\-\*\/\(\)\.]', clean_text))
        
        if expr and any(op in expr for op in "+-*/"):
            try:
                # 使用 Python eval 來處理運算優先級 (由 re 過濾保護)
                res = eval(expr)
                return f"The answer to {expr} is {res}. I am much smarter now!"
            except:
                return None
        return None

    def generate_response(self, input_indices):
        res_indices = []
        h = self.context_h
        curr_input = input_indices
        
        # 引入 Temperature Sampling 概念，增加回應多樣性
        for _ in range(10):
            y, h = self.model.forward(curr_input, h)
            
            # 排除 PAD (0) 與極端負值
            # 找到前 3 個最可能的詞，從中隨機選一個，避免「已讀亂回」
            top_indices = sorted(range(len(y)), key=lambda i: y[i], reverse=True)[:3]
            best_idx = random.choice(top_indices)

            # 防止一開始就 EOS
            if len(res_indices) == 0 and (best_idx == self.word_to_idx["<EOS>"] or best_idx == 0):
                best_idx = top_indices[1] if top_indices[1] != 0 else top_indices[2]

            if best_idx == self.word_to_idx["<EOS>"] or best_idx == 0: break
            res_indices.append(best_idx)
            curr_input = [best_idx]
            
        self.context_h = h
        return res_indices

    def chat(self):
        print("="*60)
        print("         LanAI 3.0 (Advanced Grammar & Math)         ")
        print("  Improved: Math Priority, Vocabulary, Logic Flow    ")
        print("="*60)
        while True:
            try:
                user_input = input("User: ")
                if not user_input.strip(): continue
                low_input = user_input.lower().strip()
                
                if low_input in ['exit', 'quit']: break
                if low_input == 'reset': self.context_h = None; print("AI: Memory reset."); continue
                
                # 1. 優先數學解算 (現在支持 $2+5*7$)
                math_res = self.solve_math(low_input)
                if math_res:
                    print(f"AI: {math_res}\n")
                    continue

                # 2. 語義回應
                clean_input = low_input.replace("?", "").replace("!", "").replace(",", "")
                words = clean_input.split()
                indices = [self.word_to_idx.get(w, 0) for w in words]
                
                # 如果輸入內容完全不在詞表內，給予通用回應
                if all(idx == 0 for idx in indices):
                    print("AI: That is very interesting! Tell me more.\n")
                    continue

                res_indices = self.generate_response(indices)
                
                if not res_indices:
                    print("AI: I am learning from you. Can you say that again?")
                else:
                    print("AI: ", end="", flush=True)
                    for idx in res_indices:
                        word = self.idx_to_word[idx]
                        for char in word:
                            print(char, end="", flush=True); time.sleep(0.015)
                        print(" ", end="", flush=True); time.sleep(0.03)
                    print("\n")
            except KeyboardInterrupt: break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.pre_train()
    lanai.chat()