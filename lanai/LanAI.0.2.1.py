import math
import random
import time
import sys

# --- 基礎數學工具 ---
def sigmoid(x):
    return 1 / (1 + math.exp(-max(min(x, 20), -20)))

def tanh(x):
    return math.tanh(max(min(x, 20), -20))

# --- LanAI 0.2.1 核心架構 (效能優化版) ---
class LanAIGRU:
    def __init__(self, vocab_size, hidden_size=96): # 稍微調低以換取速度，效能依然優異
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        
        # Xavier 初始化
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
        self.gates = []
        
        for idx in inputs:
            # 獲取當前詞的權重行 (Row Access 最佳化)
            wr_row = self.W_r[idx]; wz_row = self.W_z[idx]; wh_row = self.W_h[idx]
            
            r = [sigmoid(wr_row[j] + sum(h[k] * self.U_r[k][j] for k in range(self.hidden_size)) + self.b_r[j]) for j in range(self.hidden_size)]
            z = [sigmoid(wz_row[j] + sum(h[k] * self.U_z[k][j] for k in range(self.hidden_size)) + self.b_z[j]) for j in range(self.hidden_size)]
            h_tilde = [tanh(wh_row[j] + sum((r[k] * h[k]) * self.U_h[k][j] for k in range(self.hidden_size)) + self.b_h[j]) for j in range(self.hidden_size)]
            
            h = [(1 - z[j]) * h[j] + z[j] * h_tilde[j] for j in range(self.hidden_size)]
            self.gates.append((r, z, h_tilde, h))
            
        y = [sum(h[k] * self.W_y[k][j] for k in range(self.hidden_size)) + self.b_y[j] for j in range(self.vocab_size)]
        return y, h

    def train_sequence(self, input_indices, target_indices, lr=0.1): # 提高學習率
        h_state = None
        current_input = input_indices
        total_loss = 0
        
        for target_word_idx in target_indices:
            y, h_state = self.forward(current_input, h_state)
            
            # Softmax 最佳化
            max_y = max(y)
            exp_y = [math.exp(v - max_y) for v in y]
            sum_exp = sum(exp_y)
            probs = [e / sum_exp for e in exp_y]
            
            dy = probs[:]
            dy[target_word_idx] -= 1.0
            
            # 權重更新與梯度剪裁模擬
            grad_scale = min(1.0, 5.0 / (sum(abs(d) for d in dy) + 1e-6))
            
            for i in range(self.hidden_size):
                h_val = h_state[i]
                wy_row = self.W_y[i]
                for j in range(self.vocab_size):
                    wy_row[j] -= lr * dy[j] * h_val * grad_scale
            
            total_loss -= math.log(max(probs[target_word_idx], 1e-10))
            current_input = [target_word_idx]
            
        return total_loss

# --- LanAI 0.2.1 主系統 ---
class LanAI:
    def __init__(self):
        self.vocab = [
            "<PAD>", "<EOS>", "hello", "hi", "hey", "how", "are", "you", "i", "am", "fine", "good", "great", 
            "well", "what", "is", "your", "name", "lanai", "ai", "who", "made", "me", "creator", "human", 
            "thanks", "welcome", "bye", "goodbye", "cool", "nice", "awesome", "understand", "can", "do", 
            "help", "yes", "no", "maybe", "sorry", "happy", "sad", "tell", "joke", "weather", "today", 
            "smart", "learning", "very", "much", "please", "friend", "talk", "with", "see", "later", 
            "created", "system", "version", "thinking", "correct", "exactly", "feel", "doing", "bit", "busy"
        ]
        self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
        self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
        self.model = LanAIGRU(len(self.vocab))
        self.context_h = None 
        
        self.training_data = [
            (["hello"], ["hi", "there", "friend"]),
            (["hi"], ["hello", "how", "are", "you"]),
            (["how", "are", "you"], ["i", "am", "doing", "great"]),
            (["what", "is", "your", "name"], ["i", "am", "lanai", "0.2"]),
            (["who", "are", "you"], ["i", "am", "your", "ai", "friend"]),
            (["thanks"], ["you", "are", "very", "welcome"]),
            (["bye"], ["goodbye", "see", "you", "later"]),
            (["are", "you", "human"], ["no", "i", "am", "a", "learning", "system"]),
            (["can", "you", "help"], ["yes", "i", "can", "help", "you"]),
            (["do", "you", "understand"], ["yes", "i", "understand", "exactly"]),
            (["tell", "joke"], ["sorry", "i", "am", "still", "learning", "jokes"])
        ]

    def pre_train(self, max_epochs=1200): # 縮減 Epoch，利用高學習率快速收斂
        print(f"LanAI 0.2.1 正在優化訓練管線 (目標週期: {max_epochs})...")
        start_time = time.time()
        
        # 初始高學習率以加快初期收斂
        lr = 0.12 
        
        for epoch in range(max_epochs):
            random.shuffle(self.training_data)
            epoch_loss = 0
            
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                epoch_loss += self.model.train_sequence(indices, t_indices, lr=lr)
            
            # 快速衰減策略
            if epoch % 100 == 0:
                avg_l = epoch_loss / len(self.training_data)
                print(f"週期: {epoch} | 平均損失: {avg_l:.4f} | LR: {lr:.4f}")
                if avg_l < 0.2: 
                    print("精準度已達標，提早完成訓練。")
                    break
                lr *= 0.92 # 每 100 次顯著調低學習率確保穩定
                
        print(f"LanAI 0.2.1 部署完成！耗時: {time.time() - start_time:.2f} 秒\n")

    def generate_response(self, input_indices):
        res_indices = []
        h = self.context_h
        curr_input = input_indices
        for _ in range(8):
            y, h = self.model.forward(curr_input, h)
            best_idx = y.index(max(y))
            if best_idx == self.word_to_idx["<EOS>"] or self.idx_to_word[best_idx] == "<PAD>": break
            res_indices.append(best_idx)
            curr_input = [best_idx]
        self.context_h = h
        return res_indices

    def chat(self):
        print("="*60)
        print("               LanAI 0.2.1 (Fast-Training Version)               ")
        print("="*60)
        while True:
            try:
                user_input = input("User: ")
                if not user_input.strip(): continue
                low_input = user_input.lower().strip().replace("?", "").replace("!", "")
                if low_input in ['exit', 'quit']: break
                if low_input == 'reset':
                    self.context_h = None; print("AI: [Memory Cleared]"); continue
                
                indices = [self.word_to_idx.get(w, 0) for w in low_input.split()]
                res_indices = self.generate_response(indices)
                
                print("AI: ", end="", flush=True)
                for idx in res_indices:
                    for char in self.idx_to_word[idx]:
                        print(char, end="", flush=True); time.sleep(0.04)
                    print(" ", end="", flush=True); time.sleep(0.05)
                print("\n")
            except KeyboardInterrupt: break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.pre_train()
    lanai.chat()