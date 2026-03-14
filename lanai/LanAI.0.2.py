import math
import random
import time
import sys

# --- 基礎數學工具 ---
def sigmoid(x):
    return 1 / (1 + math.exp(-max(min(x, 20), -20)))

def tanh(x):
    return math.tanh(max(min(x, 20), -20))

# --- LanAI 0.2 核心架構 (強化版 GRU 生成器) ---
class LanAIGRU:
    def __init__(self, vocab_size, hidden_size=128): # 擴大隱藏層以存儲複雜句法
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        
        limit = math.sqrt(6 / (vocab_size + hidden_size))
        # 門控權重
        self.W_r = [[random.uniform(-limit, limit) for _ in range(hidden_size)] for _ in range(vocab_size)]
        self.U_r = [[random.uniform(-limit, limit) for _ in range(hidden_size)] for _ in range(hidden_size)]
        self.b_r = [0.0] * hidden_size
        
        self.W_z = [[random.uniform(-limit, limit) for _ in range(hidden_size)] for _ in range(vocab_size)]
        self.U_z = [[random.uniform(-limit, limit) for _ in range(hidden_size)] for _ in range(hidden_size)]
        self.b_z = [0.0] * hidden_size
        
        self.W_h = [[random.uniform(-limit, limit) for _ in range(hidden_size)] for _ in range(vocab_size)]
        self.U_h = [[random.uniform(-limit, limit) for _ in range(hidden_size)] for _ in range(hidden_size)]
        self.b_h = [0.0] * hidden_size
        
        self.W_y = [[random.uniform(-limit, limit) for _ in range(vocab_size)] for _ in range(hidden_size)]
        self.b_y = [0.0] * vocab_size

    def forward(self, inputs, h_prev=None):
        h = h_prev[:] if h_prev else [0.0] * self.hidden_size
        self.gates = []
        
        for idx in inputs:
            Wr_idx = self.W_r[idx]; Wz_idx = self.W_z[idx]; Wh_idx = self.W_h[idx]
            
            r = [sigmoid(Wr_idx[j] + sum(h[k] * self.U_r[k][j] for k in range(self.hidden_size)) + self.b_r[j]) for j in range(self.hidden_size)]
            z = [sigmoid(Wz_idx[j] + sum(h[k] * self.U_z[k][j] for k in range(self.hidden_size)) + self.b_z[j]) for j in range(self.hidden_size)]
            h_tilde = [tanh(Wh_idx[j] + sum((r[k] * h[k]) * self.U_h[k][j] for k in range(self.hidden_size)) + self.b_h[j]) for j in range(self.hidden_size)]
            
            h = [(1 - z[j]) * h[j] + z[j] * h_tilde[j] for j in range(self.hidden_size)]
            self.gates.append((r, z, h_tilde, h))
            
        y = [sum(h[k] * self.W_y[k][j] for k in range(self.hidden_size)) + self.b_y[j] for j in range(self.vocab_size)]
        return y, h

    def train_sequence(self, input_indices, target_indices, lr=0.03):
        """序列訓練：強化對多單詞回覆的預測能力"""
        total_loss = 0
        h_state = None
        
        # 逐詞訓練預測
        current_input = input_indices
        for target_word_idx in target_indices:
            y, h_state = self.forward(current_input, h_state)
            
            # Softmax & Cross-Entropy
            max_y = max(y)
            exp_y = [math.exp(val - max_y) for val in y]
            sum_exp = sum(exp_y)
            probs = [e / sum_exp for e in exp_y]
            
            dy = probs[:]
            dy[target_word_idx] -= 1.0
            
            # 更新輸出層
            for i in range(self.hidden_size):
                for j in range(self.vocab_size):
                    self.W_y[i][j] -= lr * dy[j] * h_state[i]
            
            total_loss -= math.log(max(probs[target_word_idx], 1e-10))
            # 自回歸：將當前目標作為下一次的輸入
            current_input = [target_word_idx]
            
        return total_loss

# --- LanAI 0.2 主系統 ---
class LanAI:
    def __init__(self):
        # 擴展詞彙表，加入結束標籤 <EOS> 與常用標點
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
        
        # 訓練資料升級：改為多單詞回覆
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
            (["tell", "joke"], ["sorry", "i", "am", "still", "learning", "jokes"]),
            (["how", "is", "the", "weather"], ["it", "looks", "very", "good", "today"])
        ]

    def pre_train(self, max_epochs=5000):
        print("LanAI 0.2 正在重構語義生成鏈...")
        start_time = time.time()
        lr = 0.05
        
        for epoch in range(max_epochs):
            random.shuffle(self.training_data)
            total_epoch_loss = 0
            
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                
                loss = self.model.train_sequence(indices, t_indices, lr=lr)
                total_epoch_loss += loss
            
            lr *= 0.9999 # 極緩慢衰減
            
            if epoch % 1000 == 0:
                avg_loss = total_epoch_loss / len(self.training_data)
                print(f"進度: {epoch}/{max_epochs} | 平均損失: {avg_loss:.4f} | 策略: 多詞生成強化")
                if avg_loss < 0.1: break # 達標提前停止
                
        print(f"LanAI 0.2 部署完成！耗時: {time.time() - start_time:.2f} 秒\n")

    def generate_response(self, input_indices):
        """自回歸生成：逐字產生句子直到出現 <EOS>"""
        res_indices = []
        h = self.context_h
        curr_input = input_indices
        
        for _ in range(8): # 限制最大長度為 8 個字
            y, h = self.model.forward(curr_input, h)
            # 增加隨機擾動以避免總是重複同一個詞 (Temperature Sampling 簡化版)
            best_idx = y.index(max(y))
            
            if best_idx == self.word_to_idx["<EOS>"] or self.idx_to_word[best_idx] == "<PAD>":
                break
                
            res_indices.append(best_idx)
            curr_input = [best_idx] # 下一次的輸入是這一次的輸出
            
        self.context_h = h # 更新對話記憶
        return res_indices

    def chat(self):
        print("="*60)
        print("               LanAI 0.2 (Generative GRU)               ")
        print("        [精準語義增強版] | [多詞回覆模式已啟動]         ")
        print("="*60)
        
        while True:
            try:
                user_input = input("User: ")
                if not user_input.strip(): continue
                
                low_input = user_input.lower().strip().replace("?", "").replace("!", "")
                if low_input in ['exit', 'quit']:
                    print("AI: Goodbye! LanAI 0.2 offline.")
                    break
                if low_input == 'reset':
                    self.context_h = None
                    print("AI: [Memory Cleared]")
                    continue
                
                words = low_input.split()
                indices = [self.word_to_idx.get(w, 0) for w in words]
                
                # 模擬思考過程
                print("\n» LanAI 正在建構語句...", end="", flush=True)
                for _ in range(3):
                    time.sleep(0.3)
                    print(".", end="", flush=True)
                print("\n")
                
                res_indices = self.generate_response(indices)
                
                print("AI: ", end="", flush=True)
                for idx in res_indices:
                    word = self.idx_to_word[idx]
                    for char in word:
                        print(char, end="", flush=True)
                        time.sleep(0.05) # 模擬打字機速度
                    print(" ", end="", flush=True)
                    time.sleep(0.1)
                print("\n")
                
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.pre_train()
    lanai.chat()