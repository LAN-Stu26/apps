
import math
import random
import time
import sys

# --- 基礎數學工具 ---
def sigmoid(x):
    return 1 / (1 + math.exp(-max(min(x, 20), -20)))

def tanh(x):
    return math.tanh(max(min(x, 20), -20))

# --- LanAI 0.1 核心架構 (GRU) ---
class LanAIGRU:
    def __init__(self, vocab_size, hidden_size=64):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        
        # 使用 Xavier/Glorot 初始化以加速收斂
        limit = math.sqrt(6 / (vocab_size + hidden_size))
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
            # 預計算與輸入相關的部分以加速
            Wr_idx = self.W_r[idx]; Wz_idx = self.W_z[idx]; Wh_idx = self.W_h[idx]
            
            r = [sigmoid(Wr_idx[j] + sum(h[k] * self.U_r[k][j] for k in range(self.hidden_size)) + self.b_r[j]) for j in range(self.hidden_size)]
            z = [sigmoid(Wz_idx[j] + sum(h[k] * self.U_z[k][j] for k in range(self.hidden_size)) + self.b_z[j]) for j in range(self.hidden_size)]
            h_tilde = [tanh(Wh_idx[j] + sum((r[k] * h[k]) * self.U_h[k][j] for k in range(self.hidden_size)) + self.b_h[j]) for j in range(self.hidden_size)]
            
            h_next = [(1 - z[j]) * h[j] + z[j] * h_tilde[j] for j in range(self.hidden_size)]
            self.gates.append((r, z, h_tilde, h))
            h = h_next
            
        y = [sum(h[k] * self.W_y[k][j] for k in range(self.hidden_size)) + self.b_y[j] for j in range(self.vocab_size)]
        return y, h

    def train(self, inputs, target_idx, lr=0.05):
        y, last_h = self.forward(inputs)
        
        # 穩定化 Softmax
        max_y = max(y)
        exp_y = [math.exp(val - max_y) for val in y]
        sum_exp = sum(exp_y)
        probs = [e / sum_exp for e in exp_y]
        
        dy = probs[:]
        dy[target_idx] -= 1.0
        
        # 更新輸出層
        for i in range(self.hidden_size):
            h_val = last_h[i]
            W_yi = self.W_y[i]
            for j in range(self.vocab_size):
                W_yi[j] -= lr * dy[j] * h_val
        for j in range(self.vocab_size):
            self.b_y[j] -= lr * dy[j]
            
        # 快速 Backprop (針對最後一個 Step)
        if inputs:
            last_idx = inputs[-1]
            r, z, h_tilde, h_prev = self.gates[-1]
            dh = [sum(dy[j] * self.W_y[i][j] for j in range(self.vocab_size)) for i in range(self.hidden_size)]
            
            for j in range(self.hidden_size):
                common_grad = dh[j] * lr
                self.W_z[last_idx][j] -= common_grad * (h_tilde[j] - h_prev[j]) * z[j] * (1 - z[j])
                self.W_h[last_idx][j] -= common_grad * z[j] * (1 - h_tilde[j]**2)
        
        return -math.log(max(probs[target_idx], 1e-10)) # 返回 Loss

# --- LanAI 0.1 主系統 ---
class LanAI:
    def __init__(self):
        self.vocab = [
            "<PAD>", "hello", "hi", "hey", "how", "are", "you", "i", "am", "fine", "good", "great", "well",
            "what", "is", "your", "name", "lanai", "ai", "who", "made", "me", "creator", "human", "thanks", 
            "thank", "welcome", "bye", "goodbye", "cool", "nice", "awesome", "understand", "can", "do", 
            "help", "yes", "no", "maybe", "sorry", "happy", "sad", "tell", "joke", "weather", "today", 
            "smart", "learning", "very", "much", "please", "friend", "talk", "with", "see", "later", "who",
            "created", "system", "version", "thinking", "deep", "correct", "wrong", "exactly"
        ]
        self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
        self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
        
        self.model = LanAIGRU(len(self.vocab))
        self.context_h = None 
        
        # 擴展語意資料庫：強化意圖識別
        self.training_data = [
            (["hello"], "hi"), (["hi"], "hello"), (["hey"], "hi"),
            (["how", "are", "you"], "fine"), (["how", "well"], "great"),
            (["what", "is", "your", "name"], "lanai"), (["who", "are", "you"], "ai"),
            (["who", "made", "you"], "me"), (["who", "is", "your", "creator"], "me"),
            (["what", "version"], "0.1"), (["are", "you", "smart"], "very"),
            (["thanks"], "welcome"), (["thank", "you"], "welcome"),
            (["bye"], "goodbye"), (["see", "you", "later"], "bye"),
            (["do", "you", "understand"], "yes"), (["are", "you", "human"], "no"),
            (["can", "you", "help"], "yes"), (["tell", "joke"], "sorry"),
            (["happy", "today"], "great"), (["you", "are", "right"], "exactly"),
            (["is", "it", "correct"], "yes"), (["deep", "learning"], "smart")
        ]

    def pre_train(self, max_epochs=3000):
        print("LanAI 0.1 正在優化核心語意邏輯並加速訓練...")
        start_time = time.time()
        lr = 0.06
        
        for epoch in range(max_epochs):
            random.shuffle(self.training_data)
            epoch_loss = 0
            correct_preds = 0
            
            for words, target in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_idx = self.word_to_idx.get(target, 0)
                
                loss = self.model.train(indices, t_idx, lr=lr)
                epoch_loss += loss
                
                # 測試當前是否預測正確
                y, _ = self.model.forward(indices)
                if y.index(max(y)) == t_idx: correct_preds += 1
            
            # 學習率動態衰減
            lr *= 0.9998
            
            # Early Stopping: 如果連續表現完美則提早結束
            accuracy = correct_preds / len(self.training_data)
            if accuracy > 0.98 and epoch > 500:
                print(f"訓練提前達標！週期: {epoch}/{max_epochs} | 準確度: {accuracy*100:.1f}%")
                break
                
            if epoch % 500 == 0:
                print(f"週期: {epoch} | 損失: {epoch_loss/len(self.training_data):.4f} | 準度: {accuracy*100:.1f}%")
                
        print(f"LanAI 0.1 預訓練完成！耗時: {time.time() - start_time:.2f} 秒\n")

    def analyze_thinking(self, words, confidence):
        print("\n" + "·"*20 + " [ LanAI 思考中 ] " + "·"*20)
        time.sleep(0.25)
        print(f"» 意圖解析: 辨識到「{len(words)}」組關鍵語意，正在映射至隱藏向量空間...")
        time.sleep(0.15)
        print(f"» 記憶檢索: {'[深度上下文模式]' if self.context_h else '[初次對話模式]'}")
        time.sleep(0.15)
        prob_val = min(100.0, max(0.0, confidence * 10)) # 視覺化轉換
        print(f"» 預測置信度: {prob_val:.2f}% | 模型版本: LanAI 0.1")
        print("·" * 57 + "\n")

    def chat(self):
        print("="*60)
        print("               LanAI 0.1 (GRU Architecture)               ")
        print("        Powered by Pure-Python | Enhanced Thinking         ")
        print("      輸入 'reset' 重置記憶，輸入 'exit' 結束對話      ")
        print("="*60)
        
        while True:
            try:
                user_input = input("User: ")
                if not user_input.strip(): continue
                
                low_input = user_input.lower().strip().replace("?", "").replace("!", "")
                if low_input in ['exit', 'quit']:
                    print("AI: Goodbye! LanAI 0.1 power off.")
                    break
                if low_input == 'reset':
                    self.context_h = None
                    print("AI: [Memory Cleared]")
                    continue
                
                words = low_input.split()
                indices = [self.word_to_idx.get(w, 0) for w in words]
                
                y, new_h = self.model.forward(indices, self.context_h)
                self.context_h = new_h 
                
                best_idx = y.index(max(y))
                confidence = max(y)
                
                self.analyze_thinking(words, confidence)
                
                response = self.idx_to_word[best_idx].capitalize()
                print(f"AI: {response}\n")
                
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.pre_train()
    lanai.chat()
