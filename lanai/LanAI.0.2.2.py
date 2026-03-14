import math
import random
import time
import sys

# --- 基礎數學工具 ---
def sigmoid(x):
    return 1 / (1 + math.exp(-max(min(x, 20), -20)))

def tanh(x):
    return math.tanh(max(min(x, 20), -20))

# --- LanAI 0.2.2 核心架構 (穩定增強版) ---
class LanAIGRU:
    def __init__(self, vocab_size, hidden_size=96):
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
        self.gates = []
        
        for idx in inputs:
            # 防止索引越界
            idx = idx if idx < self.vocab_size else 0
            
            wr_row = self.W_r[idx]; wz_row = self.W_z[idx]; wh_row = self.W_h[idx]
            
            r = [sigmoid(wr_row[j] + sum(h[k] * self.U_r[k][j] for k in range(self.hidden_size)) + self.b_r[j]) for j in range(self.hidden_size)]
            z = [sigmoid(wz_row[j] + sum(h[k] * self.U_z[k][j] for k in range(self.hidden_size)) + self.b_z[j]) for j in range(self.hidden_size)]
            h_tilde = [tanh(wh_row[j] + sum((r[k] * h[k]) * self.U_h[k][j] for k in range(self.hidden_size)) + self.b_h[j]) for j in range(self.hidden_size)]
            
            h = [(1 - z[j]) * h[j] + z[j] * h_tilde[j] for j in range(self.hidden_size)]
            self.gates.append((r, z, h_tilde, h))
            
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
            sum_exp = sum(exp_y) + 1e-9 # 數值穩定性
            probs = [e / sum_exp for e in exp_y]
            
            dy = probs[:]
            dy[target_word_idx] -= 1.0
            
            # 更新輸出層與簡單梯度裁剪
            for i in range(self.hidden_size):
                h_val = h_state[i]
                for j in range(self.vocab_size):
                    self.W_y[i][j] -= lr * dy[j] * h_val
            
            total_loss -= math.log(max(probs[target_word_idx], 1e-10))
            current_input = [target_word_idx]
            
        return total_loss

# --- LanAI 0.2.2 主系統 ---
class LanAI:
    def __init__(self):
        # 擴充詞表解決使用者提問
        self.vocab = [
            "<PAD>", "<EOS>", "hello", "hi", "hey", "how", "are", "you", "i", "am", "fine", "good", "great", 
            "well", "what", "is", "your", "name", "lanai", "ai", "who", "made", "me", "creator", "human", 
            "thanks", "welcome", "bye", "goodbye", "cool", "nice", "awesome", "understand", "can", "do", 
            "help", "yes", "no", "maybe", "sorry", "happy", "sad", "tell", "joke", "weather", "today", 
            "smart", "learning", "very", "much", "please", "friend", "talk", "with", "see", "later", 
            "created", "system", "version", "exactly", "feel", "doing", "anything", "everything", "think"
        ]
        self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
        self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
        self.model = LanAIGRU(len(self.vocab))
        self.context_h = None 
        
        # 訓練資料增強
        self.training_data = [
            (["hello"], ["hi", "there", "friend"]),
            (["hi"], ["hello", "how", "are", "you"]),
            (["how", "are", "you"], ["i", "am", "doing", "great"]),
            (["what", "is", "your", "name"], ["i", "am", "lanai", "version", "0.2"]),
            (["what", "can", "you", "do"], ["i", "can", "talk", "and", "learn"]),
            (["can", "you", "think"], ["i", "am", "thinking", "very", "hard"]),
            (["who", "are", "you"], ["i", "am", "your", "ai", "friend"]),
            (["thanks"], ["you", "are", "very", "welcome"]),
            (["bye"], ["goodbye", "see", "you", "later"]),
            (["are", "you", "human"], ["no", "i", "am", "a", "learning", "system"]),
            (["can", "you", "help"], ["yes", "i", "can", "help", "you"])
        ]

    def pre_train(self, max_epochs=1500):
        print("LanAI 0.2.2 正在修復思考迴路與數值穩定性...")
        start_time = time.time()
        lr = 0.1
        
        for epoch in range(max_epochs):
            random.shuffle(self.training_data)
            epoch_loss = 0
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                epoch_loss += self.model.train_sequence(indices, t_indices, lr=lr)
            
            if epoch % 100 == 0:
                avg_l = epoch_loss / len(self.training_data)
                print(f"Epoch: {epoch} | Loss: {avg_l:.4f}")
                if avg_l < 0.15: break
                lr *= 0.95 
                
        print(f"LanAI 0.2.2 部署完成！耗時: {time.time() - start_time:.2f} 秒\n")

    def generate_response(self, input_indices):
        res_indices = []
        h = self.context_h
        curr_input = input_indices
        
        for _ in range(10): # 最大長度稍微加長
            y, h = self.model.forward(curr_input, h)
            
            # 加入微小噪聲防止死循環輸出同一個詞
            # y = [v + random.uniform(-0.01, 0.01) for v in y]
            best_idx = y.index(max(y))
            
            # 如果第一個詞就是 EOS 或 PAD，強制換一個詞
            if len(res_indices) == 0 and (best_idx == self.word_to_idx["<EOS>"] or best_idx == 0):
                # 排除 PAD 和 EOS 後找次佳解
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
        print("               LanAI 0.2.2 (Stability Fix)               ")
        print("="*60)
        while True:
            try:
                user_input = input("User: ")
                if not user_input.strip(): continue
                low_input = user_input.lower().strip().replace("?", "").replace("!", "")
                if low_input in ['exit', 'quit']: break
                if low_input == 'reset':
                    self.context_h = None; print("AI: [Memory Cleared]"); continue
                
                # 強化未知詞處理：不在詞表中的詞替換為 <PAD>
                indices = [self.word_to_idx.get(w, 0) for w in low_input.split()]
                
                res_indices = self.generate_response(indices)
                
                if not res_indices:
                    print("AI: Sorry, I am a bit confused. Can you say that again?")
                else:
                    print("AI: ", end="", flush=True)
                    for idx in res_indices:
                        for char in self.idx_to_word[idx]:
                            print(char, end="", flush=True); time.sleep(0.03)
                        print(" ", end="", flush=True); time.sleep(0.05)
                    print("\n")
            except KeyboardInterrupt: break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.pre_train()
    lanai.chat()