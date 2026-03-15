import numpy as np
import random
import time
import re
import os
import ast
import operator

# --- 基礎數學與安全的 AST 數學運算 ---
def safe_math_eval(expr):
    """安全地解析並計算數學表達式，取代危險的 eval()"""
    allowed_operators = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.USub: operator.neg, ast.UAdd: operator.pos
    }
    def evaluate(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return allowed_operators[type(node.op)](evaluate(node.left), evaluate(node.right))
        elif isinstance(node, ast.UnaryOp):
            return allowed_operators[type(node.op)](evaluate(node.operand))
        else:
            raise TypeError("Unsupported operation")
    try:
        tree = ast.parse(expr, mode='eval')
        return evaluate(tree.body)
    except Exception:
        return None

def sigmoid(x):
    # 使用 np.clip 防止溢出 (Overflow)
    return 1 / (1 + np.exp(-np.clip(x, -20, 20)))

def tanh(x):
    return np.tanh(np.clip(x, -20, 20))

# --- LanAI 0.5.0 核心架構 (NumPy 加速 + Embedding + 梯度裁剪) ---
class LanAIGRU:
    def __init__(self, vocab_size, embedding_dim=64, hidden_size=160): 
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_size = hidden_size
        
        # Xavier 初始化界限
        limit = np.sqrt(6 / (vocab_size + hidden_size))
        
        # [0.5.0 新增] 詞向量嵌入層 (Embedding Layer)
        self.E = np.random.uniform(-limit, limit, (vocab_size, embedding_dim))
        
        # 矩陣化 GRU 權重
        self.W_r = np.random.uniform(-limit, limit, (embedding_dim, hidden_size))
        self.U_r = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        self.b_r = np.zeros(hidden_size)
        
        self.W_z = np.random.uniform(-limit, limit, (embedding_dim, hidden_size))
        self.U_z = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        self.b_z = np.zeros(hidden_size)
        
        self.W_h = np.random.uniform(-limit, limit, (embedding_dim, hidden_size))
        self.U_h = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        self.b_h = np.zeros(hidden_size)
        
        # 輸出層維度: [hidden_size, vocab_size]
        self.W_y = np.random.uniform(-limit, limit, (hidden_size, vocab_size))
        self.b_y = np.zeros(vocab_size)

    def expand_weights(self, new_vocab_size):
        """O(1) 動態擴展：利用 NumPy vstack/hstack 瞬間擴充矩陣維度"""
        diff = new_vocab_size - self.vocab_size
        if diff <= 0: return
        
        limit = np.sqrt(6 / (new_vocab_size + self.hidden_size))
        
        # 擴充 Embedding 層
        new_E = np.random.uniform(-limit, limit, (diff, self.embedding_dim))
        self.E = np.vstack((self.E, new_E))
            
        # 擴充輸出層
        new_Wy = np.random.uniform(-limit, limit, (self.hidden_size, diff))
        self.W_y = np.hstack((self.W_y, new_Wy))
        self.b_y = np.concatenate((self.b_y, np.zeros(diff)))
        
        self.vocab_size = new_vocab_size

    def forward(self, inputs, h_prev=None):
        """完全向量化的前向傳播，速度提升數十倍"""
        if h_prev is None:
            h_prev = np.zeros(self.hidden_size)
        h = h_prev.copy()
        
        for idx in inputs:
            idx = idx if idx < self.vocab_size else 0
            x = self.E[idx] # 取得詞向量
            
            # 矩陣內積運算
            r = sigmoid(np.dot(x, self.W_r) + np.dot(h, self.U_r) + self.b_r)
            z = sigmoid(np.dot(x, self.W_z) + np.dot(h, self.U_z) + self.b_z)
            h_tilde = tanh(np.dot(x, self.W_h) + np.dot(r * h, self.U_h) + self.b_h)
            h = (1 - z) * h + z * h_tilde
            
        y = np.dot(h, self.W_y) + self.b_y
        return y, h

    def clip_gradient(self, grad, threshold=5.0):
        """[0.5.0 新增] 梯度裁剪：防止訓練過程中發生梯度爆炸導致 NaN"""
        norm = np.linalg.norm(grad)
        if norm > threshold:
            return grad * (threshold / norm)
        return grad

    def train_sequence(self, input_indices, target_indices, lr=0.08):
        """包含 1-Step BPTT (反向傳播) 的訓練，讓 GRU 閥門真正參與學習"""
        h_state = np.zeros(self.hidden_size)
        current_input = input_indices
        total_loss = 0
        
        for target_word_idx in target_indices:
            h_prev = h_state.copy()
            x_idx = current_input[-1] if len(current_input) > 0 else 0
            x = self.E[x_idx]

            # 前向傳播 (單步)
            r = sigmoid(np.dot(x, self.W_r) + np.dot(h_prev, self.U_r) + self.b_r)
            z = sigmoid(np.dot(x, self.W_z) + np.dot(h_prev, self.U_z) + self.b_z)
            h_tilde = tanh(np.dot(x, self.W_h) + np.dot(r * h_prev, self.U_h) + self.b_h)
            h_state = (1 - z) * h_prev + z * h_tilde
            y = np.dot(h_state, self.W_y) + self.b_y
            
            # Softmax
            y_shifted = y - np.max(y)
            exp_y = np.exp(y_shifted)
            probs = exp_y / (np.sum(exp_y) + 1e-9)
            total_loss -= np.log(max(probs[target_word_idx], 1e-10))

            # --- 反向傳播 (Backpropagation) ---
            dy = probs.copy()
            dy[target_word_idx] -= 1.0

            dW_y = np.outer(h_state, dy)
            db_y = dy
            dh = np.dot(self.W_y, dy) # 傳遞回隱藏層的梯度

            # GRU 內部梯度
            dh_tilde = dh * z * (1 - h_tilde**2)
            dz = dh * (h_tilde - h_prev) * z * (1 - z)
            dr = np.dot(self.U_h, dh_tilde) * h_prev * r * (1 - r)

            dW_h = np.outer(x, dh_tilde); dU_h = np.outer(r * h_prev, dh_tilde); db_h = dh_tilde
            dW_z = np.outer(x, dz);       dU_z = np.outer(h_prev, dz);           db_z = dz
            dW_r = np.outer(x, dr);       dU_r = np.outer(h_prev, dr);           db_r = dr
            dx = np.dot(self.W_h, dh_tilde) + np.dot(self.W_z, dz) + np.dot(self.W_r, dr)

            # --- 權重更新 (應用梯度裁剪) ---
            self.W_y -= lr * self.clip_gradient(dW_y); self.b_y -= lr * self.clip_gradient(db_y)
            self.W_h -= lr * self.clip_gradient(dW_h); self.U_h -= lr * self.clip_gradient(dU_h); self.b_h -= lr * self.clip_gradient(db_h)
            self.W_z -= lr * self.clip_gradient(dW_z); self.U_z -= lr * self.clip_gradient(dU_z); self.b_z -= lr * self.clip_gradient(db_z)
            self.W_r -= lr * self.clip_gradient(dW_r); self.U_r -= lr * self.clip_gradient(dU_r); self.b_r -= lr * self.clip_gradient(db_r)
            self.E[x_idx] -= lr * self.clip_gradient(dx) # 更新詞向量

            current_input = [target_word_idx]
            
        return total_loss

# --- LanAI 0.5.0 主系統 ---
class LanAI:
    def __init__(self, model_path="lanai_memory.npz"):
        self.model_path = model_path
        self.context_h = None 
        
        self.base_training_data = [
            (["hello"], ["hi", "how", "are", "you"]),
            (["what", "is", "your", "name"], ["i", "am", "lanai", "version", "0.5.0"]),
            (["what", "can", "you", "do"], ["i", "can", "calculate", "and", "learn", "new", "grammar"]),
            (["thanks"], ["you", "are", "welcome"]),
            (["bye"], ["goodbye", "see", "you"]),
            (["have", "you", "eaten", "yet"], ["yes", "i", "have", "already", "eaten"]),
            (["what", "have", "you", "done"], ["i", "have", "learned", "new", "things", "recently"]),
            (["she", "has", "been", "there"], ["since", "last", "year"]),
            (["although", "it", "is", "hard"], ["i", "will", "never", "give", "up"]),
            (["because", "it", "is", "raining"], ["we", "cannot", "go", "out", "to", "play"]),
            (["if", "it", "rains", "tomorrow"], ["we", "will", "stay", "at", "home"]),
            (["unless", "you", "study", "hard"], ["you", "will", "not", "pass", "the", "test"]),
            (["he", "is", "too", "tired"], ["to", "walk", "any", "farther"]),
            (["it", "is", "so", "beautiful"], ["that", "everyone", "likes", "it"]),
            (["what", "is", "passive", "voice"], ["the", "action", "is", "done", "to", "the", "subject"]),
            (["the", "book", "was", "written"], ["by", "a", "very", "famous", "writer"]),
            (["do", "you", "know", "the", "boy"], ["who", "is", "playing", "basketball"]),
            (["this", "is", "the", "house"], ["where", "i", "lived", "before", "with", "my", "family"]),
            (["the", "apple", "which", "is", "red"], ["looks", "very", "delicious"])
        ]
        self.training_data = list(self.base_training_data)
        
        self.default_vocab = [
            "<PAD>", "<EOS>", "hello", "hi", "how", "are", "you", "i", "am", "is", "it", "they", "we",
            "fine", "good", "great", "well", "happy", "sad", "fast", "slow", "smart", "cool", "tired",
            "what", "your", "name", "lanai", "ai", "who", "creator", "human", "thanks", "welcome",
            "bye", "see", "later", "can", "do", "help", "think", "understand", "talk", "learn",
            "math", "solve", "calculate", "plus", "minus", "times", "divided", "by", "equals",
            "a", "the", "an", "this", "that", "my", "working", "system", "version", "0.5.0",
            "have", "has", "had", "been", "done", "finished", "written", "eaten", "seen", "gone", "played",
            "because", "although", "though", "however", "therefore", "if", "unless",
            "already", "yet", "since", "recently", "still", "never",
            "whom", "whose", "which", "where", "when", "why",
            "too", "to", "so", "such", "enough", "very",
            "experience", "knowledge", "foreign", "language", "successful", "environment", 
            "pollution", "protect", "serious", "consider", "depend", "famous", "writer",
            "careful", "dangerous", "exciting", "interesting", "surprised", "boring", "bored",
            "grammar", "tense", "passive", "voice", "relative", "clause", "subject", "object",
            "boy", "basketball", "house", "lived", "before", "with", "family", "apple", "red", "looks", "delicious",
            "raining", "cannot", "go", "out", "play", "tomorrow", "stay", "at", "home", "study", "hard", "not", "pass", "test",
            "walk", "any", "farther", "beautiful", "everyone", "likes", "action", "new", "things", "she", "there", "last", "year", "give", "up"
        ]

        if not self.load_model():
            print("[系統] 找不到 0.5.0 相容記憶 (.npz)，初始化全新高速矩陣模型...")
            self.vocab = list(self.default_vocab)
            self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
            self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
            self.model = LanAIGRU(len(self.vocab))
            self.is_new_model = True
        else:
            self.is_new_model = False
            self.merge_new_knowledge() 

    def merge_new_knowledge(self):
        new_words_count = 0
        for word in self.default_vocab:
            if word not in self.word_to_idx:
                self.vocab.append(word)
                self.word_to_idx[word] = len(self.vocab) - 1
                self.idx_to_word[len(self.vocab) - 1] = word
                new_words_count += 1
                
        if new_words_count > 0:
            print(f"[系統升級] 偵測到舊記憶，已成功注入 {new_words_count} 個新詞彙與文法結構！")
            self.model.expand_weights(len(self.vocab))
            self.training_data.extend(self.base_training_data)
            self.save_model() 

    def save_model(self):
        """[0.5.0 改版] 使用高效的 Numpy 壓縮二進制儲存"""
        print("[系統] 正在將記憶高速寫入磁碟 (.npz)...")
        np.savez(self.model_path,
                 vocab=np.array(self.vocab),
                 E=self.model.E,
                 W_r=self.model.W_r, U_r=self.model.U_r, b_r=self.model.b_r,
                 W_z=self.model.W_z, U_z=self.model.U_z, b_z=self.model.b_z,
                 W_h=self.model.W_h, U_h=self.model.U_h, b_h=self.model.b_h,
                 W_y=self.model.W_y, b_y=self.model.b_y)
        print("[系統] 記憶儲存成功！")

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                print(f"[系統] 偵測到高速記憶檔 {self.model_path}，正在喚醒...")
                data = np.load(self.model_path, allow_pickle=True)
                self.vocab = data["vocab"].tolist()
                self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
                self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
                
                self.model = LanAIGRU(len(self.vocab))
                self.model.E = data["E"]
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
        if word not in self.word_to_idx:
            self.vocab.append(word)
            self.word_to_idx[word] = len(self.vocab) - 1
            self.idx_to_word[len(self.vocab) - 1] = word
            self.model.expand_weights(len(self.vocab))
            return True
        return False

    def solve_math(self, text):
        num_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
                   "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
        for k, v in num_map.items():
            text = re.sub(rf'\b{k}\b', v, text)
            
        clean_text = text.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
        expr = "".join(re.findall(r'[\d\+\-\*\/\(\)\.]', clean_text))
        
        if expr and any(op in expr for op in "+-*/"):
            res = safe_math_eval(expr)
            if res is not None:
                res = int(res) if res == int(res) else round(res, 4)
                return f"The answer is {res}."
        return None

    def train_epochs(self, target_epochs, initial_lr=0.05):
        for epoch in range(target_epochs):
            random.shuffle(self.training_data)
            loss = 0
            current_lr = initial_lr * (1 - (epoch / (target_epochs * 1.5))) 
            
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                loss += self.model.train_sequence(indices, t_indices, lr=current_lr)
            if epoch > 0 and epoch % 50 == 0:
                print(f"訓練進度 - Epoch: {epoch} | Loss: {loss/len(self.training_data):.4f} | LR: {current_lr:.4f}  ", end="\r")

    def generate_response(self, input_indices, temperature=0.6):
        res_indices = []
        h = self.context_h if self.context_h is not None else np.zeros(self.model.hidden_size)
        curr_input = input_indices
        
        for _ in range(15):
            y, h = self.model.forward(curr_input, h)
            
            # 使用 NumPy 的溫度取樣 (加上數值穩定度保護)
            logits = y / temperature
            logits = logits - np.max(logits)
            exp_l = np.exp(logits)
            probs = exp_l / (np.sum(exp_l) + 1e-9)
            
            # 確保機率總和為 1
            probs /= np.sum(probs)
            
            best_idx = np.random.choice(len(probs), p=probs)
            
            if best_idx == self.word_to_idx["<EOS>"] or best_idx == 0: 
                break
            res_indices.append(best_idx)
            curr_input = [best_idx]
            
        self.context_h = h
        return res_indices

    def thinking_layer(self, user_input, words):
        print("» [系統思考中] 向量語境映射與意圖解析...", end="\r")
        time.sleep(0.5) 
        
        math_res = self.solve_math(user_input)
        
        logic_keywords = ["why", "how", "can", "what", "math", "solve", "calculate", "think", "who"]
        grammar_keywords = ["grammar", "tense", "passive", "active", "voice", "sentence", "clause", "relative"]
        
        if any(w in words for w in grammar_keywords): intent = "grammar"
        elif any(w in words for w in logic_keywords): intent = "logic"
        else: intent = "chat"
            
        print(" " * 45, end="\r") 
        if math_res: print("» [思考結果] 偵測到明確數學算式，啟動 AST 安全運算。")
        elif intent == "grammar": print("» [思考結果] 偵測到文法探討，啟用結構性回答模式...")
        elif intent == "logic": print("» [思考結果] 偵測到邏輯需求，準備強化推論與權重微調...")
        else: print("» [思考結果] 一般閒聊模式。")
            
        return math_res, intent

    def chat(self):
        print("="*65)
        print("     LanAI 0.5.0 (NumPy Vectorized | BPTT GRU Engine)     ")
        print("="*65)
        
        if self.is_new_model:
            print("[系統] 模型為初始狀態，執行高速向量訓練 (800 Epochs)...")
            # 得益於 NumPy 加速與 BPTT，不需要到 1200 epochs 也能收斂得更好
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
                    self.save_model()
                    break
                
                words = low_input.replace("?", "").replace("!", "").replace(",", "").split()
                math_res, intent = self.thinking_layer(low_input, words)

                if math_res:
                    print(f"AI (Logic Mode): {math_res}")
                    continue
                
                new_words_learned = False
                for w in words:
                    if self.add_new_word(w):
                        print(f"[系統意識] 動態矩陣擴增！學習到新詞彙: '{w}'")
                        new_words_learned = True

                if intent == "grammar":
                    print("[動態微調] 文法結構強化訓練中...", end="\r")
                    if new_words_learned: self.training_data.append((words, ["this", "is", "a", "grammar", "rule"]))
                    self.train_epochs(80, initial_lr=0.03)
                elif intent == "logic":
                    print("[動態微調] 邏輯強化深度訓練中...", end="\r")
                    if new_words_learned: self.training_data.append((words, ["i", "think", "and", "learn"] + words))
                    self.train_epochs(100, initial_lr=0.04)
                elif new_words_learned:
                    print("[動態微調] 吸收新知識中...", end="\r")
                    self.training_data.append((words, ["i", "learned", "about"] + words))
                    self.train_epochs(50, initial_lr=0.03)
                else:
                    self.train_epochs(5, initial_lr=0.01)
                
                indices = [self.word_to_idx.get(w, 0) for w in words]
                temp = 0.2 if intent in ["logic", "grammar"] else 0.7
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