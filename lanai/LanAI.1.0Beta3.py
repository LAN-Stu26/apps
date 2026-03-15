import numpy as np
import random
import time
import re
import os
import ast
import operator

# --- 基礎數學與安全的 AST 數學運算 ---
def safe_math_eval(expr):
    """安全地解析並計算數學表達式"""
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
    return 1 / (1 + np.exp(-np.clip(x, -20, 20)))

def tanh(x):
    return np.tanh(np.clip(x, -20, 20))

# --- LanAI 1.0 Beta 3 核心架構 (引入 Context-Conditioned Attention) ---
class LanAISeq2Seq:
    def __init__(self, vocab_size, embedding_dim=128, hidden_size=384): 
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_size = hidden_size
        
        limit = np.sqrt(6 / (vocab_size + hidden_size))
        
        self.E = np.random.uniform(-limit, limit, (vocab_size, embedding_dim))
        
        # 基礎 GRU 權重
        self.W_r = np.random.uniform(-limit, limit, (embedding_dim, hidden_size))
        self.U_r = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        self.b_r = np.zeros(hidden_size)
        
        self.W_z = np.random.uniform(-limit, limit, (embedding_dim, hidden_size))
        self.U_z = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        self.b_z = np.zeros(hidden_size)
        
        self.W_h = np.random.uniform(-limit, limit, (embedding_dim, hidden_size))
        self.U_h = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        self.b_h = np.zeros(hidden_size)
        
        # [Beta 3 新增] 上下文條件矩陣 (Context-Conditioned Matrices)
        # 確保在解碼的每一步，都會強制注入問題的語意，解決遺忘問題
        self.C_r = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        self.C_z = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        self.C_h = np.random.uniform(-limit, limit, (hidden_size, hidden_size))
        
        self.W_y = np.random.uniform(-limit, limit, (hidden_size, vocab_size))
        self.b_y = np.zeros(vocab_size)

    def expand_weights(self, new_vocab_size):
        diff = new_vocab_size - self.vocab_size
        if diff <= 0: return
        
        limit = np.sqrt(6 / (new_vocab_size + self.hidden_size))
        
        new_E = np.random.uniform(-limit, limit, (diff, self.embedding_dim))
        self.E = np.vstack((self.E, new_E))
            
        new_Wy = np.random.uniform(-limit, limit, (self.hidden_size, diff))
        self.W_y = np.hstack((self.W_y, new_Wy))
        self.b_y = np.concatenate((self.b_y, np.zeros(diff)))
        
        self.vocab_size = new_vocab_size

    def clip_gradient(self, grad, threshold=3.0):
        norm = np.linalg.norm(grad)
        if norm > threshold:
            return grad * (threshold / norm)
        return grad

    def train_sequence(self, input_indices, target_indices, word_to_idx, lr=0.05):
        # === 1. Encoder 階段 ===
        h_state = np.zeros(self.hidden_size)
        for idx in input_indices:
            idx = idx if idx < self.vocab_size else 0
            x = self.E[idx]
            r = sigmoid(np.dot(x, self.W_r) + np.dot(h_state, self.U_r) + self.b_r)
            z = sigmoid(np.dot(x, self.W_z) + np.dot(h_state, self.U_z) + self.b_z)
            h_tilde = tanh(np.dot(x, self.W_h) + np.dot(r * h_state, self.U_h) + self.b_h)
            h_state = (1 - z) * h_state + z * h_tilde
            
        enc_context = h_state.copy() # 保存整個問題的語意精華
            
        # === 2. Decoder 階段 ===
        total_loss = 0
        # [Beta 3 修復] 強制使用 <SOS> 作為解碼起點，切斷跨句子的記憶污染
        current_x_idx = word_to_idx.get("<SOS>", 0) 
        
        for target_word_idx in target_indices:
            x = self.E[current_x_idx]
            h_prev = h_state.copy()

            # [Beta 3 新增] 注入 enc_context，讓 GRU 在生成每一個字時都能「看到」原來的問題
            r = sigmoid(np.dot(x, self.W_r) + np.dot(h_prev, self.U_r) + np.dot(enc_context, self.C_r) + self.b_r)
            z = sigmoid(np.dot(x, self.W_z) + np.dot(h_prev, self.U_z) + np.dot(enc_context, self.C_z) + self.b_z)
            h_tilde = tanh(np.dot(x, self.W_h) + np.dot(r * h_prev, self.U_h) + np.dot(enc_context, self.C_h) + self.b_h)
            h_state = (1 - z) * h_prev + z * h_tilde
            y = np.dot(h_state, self.W_y) + self.b_y
            
            y_shifted = y - np.max(y)
            exp_y = np.exp(y_shifted)
            probs = exp_y / (np.sum(exp_y) + 1e-9)
            total_loss -= np.log(max(probs[target_word_idx], 1e-10))

            dy = probs.copy()
            dy[target_word_idx] -= 1.0

            dW_y = np.outer(h_state, dy)
            db_y = dy
            dh = np.dot(self.W_y, dy)

            dh_tilde = dh * z * (1 - h_tilde**2)
            dz = dh * (h_tilde - h_prev) * z * (1 - z)
            dr = np.dot(self.U_h, dh_tilde) * h_prev * r * (1 - r)

            dW_h = np.outer(x, dh_tilde); dU_h = np.outer(r * h_prev, dh_tilde); db_h = dh_tilde
            dW_z = np.outer(x, dz);       dU_z = np.outer(h_prev, dz);           db_z = dz
            dW_r = np.outer(x, dr);       dU_r = np.outer(h_prev, dr);           db_r = dr
            dx = np.dot(self.W_h, dh_tilde) + np.dot(self.W_z, dz) + np.dot(self.W_r, dr)

            # [Beta 3 新增] 運算 Context 矩陣的梯度
            dC_h = np.outer(enc_context, dh_tilde)
            dC_z = np.outer(enc_context, dz)
            dC_r = np.outer(enc_context, dr)

            self.W_y -= lr * self.clip_gradient(dW_y); self.b_y -= lr * self.clip_gradient(db_y)
            self.W_h -= lr * self.clip_gradient(dW_h); self.U_h -= lr * self.clip_gradient(dU_h); self.b_h -= lr * self.clip_gradient(db_h)
            self.W_z -= lr * self.clip_gradient(dW_z); self.U_z -= lr * self.clip_gradient(dU_z); self.b_z -= lr * self.clip_gradient(db_z)
            self.W_r -= lr * self.clip_gradient(dW_r); self.U_r -= lr * self.clip_gradient(dU_r); self.b_r -= lr * self.clip_gradient(db_r)
            
            self.C_h -= lr * self.clip_gradient(dC_h)
            self.C_z -= lr * self.clip_gradient(dC_z)
            self.C_r -= lr * self.clip_gradient(dC_r)
            
            self.E[current_x_idx] -= lr * self.clip_gradient(dx)

            current_x_idx = target_word_idx
            
        return total_loss

    def generate(self, input_indices, word_to_idx, top_k=3, temperature=0.5):
        h_state = np.zeros(self.hidden_size)
        for idx in input_indices:
            idx = idx if idx < self.vocab_size else 0
            x = self.E[idx]
            r = sigmoid(np.dot(x, self.W_r) + np.dot(h_state, self.U_r) + self.b_r)
            z = sigmoid(np.dot(x, self.W_z) + np.dot(h_state, self.U_z) + self.b_z)
            h_tilde = tanh(np.dot(x, self.W_h) + np.dot(r * h_state, self.U_h) + self.b_h)
            h_state = (1 - z) * h_state + z * h_tilde
            
        enc_context = h_state.copy()
            
        res_indices = []
        current_x_idx = word_to_idx.get("<SOS>", 0)
        
        for _ in range(25): 
            x = self.E[current_x_idx]
            
            # 引入 Context Injection
            r = sigmoid(np.dot(x, self.W_r) + np.dot(h_state, self.U_r) + np.dot(enc_context, self.C_r) + self.b_r)
            z = sigmoid(np.dot(x, self.W_z) + np.dot(h_state, self.U_z) + np.dot(enc_context, self.C_z) + self.b_z)
            h_tilde = tanh(np.dot(x, self.W_h) + np.dot(r * h_state, self.U_h) + np.dot(enc_context, self.C_h) + self.b_h)
            h_state = (1 - z) * h_state + z * h_tilde
            y = np.dot(h_state, self.W_y) + self.b_y
            
            logits = y / temperature
            logits = logits - np.max(logits)
            exp_l = np.exp(logits)
            probs = exp_l / (np.sum(exp_l) + 1e-9)
            
            if top_k > 0:
                indices_to_remove = probs < np.sort(probs)[-top_k]
                probs[indices_to_remove] = 0
                probs /= np.sum(probs) 
            
            best_idx = np.random.choice(len(probs), p=probs)
            
            if (best_idx == word_to_idx["<EOS>"] or best_idx == 0) and len(res_indices) == 0:
                probs[best_idx] = 0
                probs /= np.sum(probs)
                best_idx = np.random.choice(len(probs), p=probs)
                
            if best_idx == word_to_idx["<EOS>"] or best_idx == 0:
                break
                
            res_indices.append(best_idx)
            current_x_idx = best_idx
            
        return res_indices, h_state

# --- LanAI 1.0 Beta 3 主系統 ---
class LanAI:
    def __init__(self, model_path="lanai_v1_memory.npz"): 
        self.model_path = model_path
        self.context_h = None 
        
        self.base_training_data = [
            (["hello", "!"], ["hi", "there", ",", "how", "can", "i", "help", "you", "today", "?"]),
            (["hi"], ["hello", ",", "how", "are", "you", "doing", "?"]),
            (["hi", "there", "!"], ["hello", ",", "nice", "to", "meet", "you", "."]),
            (["how", "are", "you", "?"], ["i", "am", "doing", "great", ",", "thank", "you", "for", "asking", "."]),
            (["i", "am", "good", "."], ["that", "is", "great", "to", "hear", "."]),
            (["what", "is", "your", "name", "?"], ["my", "name", "is", "lanai", ",", "version", "1.0", "beta", "3", "."]),
            (["hi", ",", "what", "is", "your", "name", "?"], ["hello", ",", "my", "name", "is", "lanai", "."]),
            (["who", "are", "you", "?"], ["i", "am", "lanai", ",", "an", "artificial", "intelligence", "."]),
            (["who", "made", "you", "?"], ["i", "was", "created", "by", "a", "human", "developer", "."]),
            (["what", "can", "you", "do", "?"], ["i", "can", "chat", ",", "calculate", "math", ",", "and", "learn", "new", "things", "."]),
            (["ok", "."], ["okay", "then", "."]),
            (["yes", "."], ["i", "agree", "with", "you", "."]),
            (["thanks", "!"], ["you", "are", "very", "welcome", "."]),
            (["bye", "!"], ["goodbye", ",", "have", "a", "nice", "day", "."]),
            (["have", "you", "eaten", "yet", "?"], ["yes", ",", "i", "have", "already", "eaten", "."]),
            (["what", "is", "passive", "voice", "?"], ["the", "action", "is", "done", "to", "the", "subject", "."]),
            (["the", "book", "was", "written", "."], ["by", "a", "very", "famous", "writer", "."]),
            (["do", "you", "know", "the", "boy", "?"], ["who", "is", "playing", "basketball", "."]),
            (["this", "is", "the", "house", "."], ["where", "i", "lived", "before", "with", "my", "family", "."])
        ]
        self.training_data = list(self.base_training_data)
        
        # 加入 <SOS> 作為句子起始符號
        self.default_vocab = [
            "<PAD>", "<EOS>", "<SOS>", "hello", "hi", "there", "how", "can", "i", "help", "you", "today", "are", "doing", 
            "am", "great", "thank", "for", "asking", "good", "that", "is", "to", "hear", "fine", "glad",
            "what", "your", "name", "my", "lanai", "version", "1.0", "beta", "3", "who", "an", "artificial", "intelligence",
            "made", "was", "created", "by", "a", "human", "developer", "old", "do", "not", "have", "age", "ai",
            "calculate", "math", "and", "learn", "new", "things", "ok", "okay", "then", "yes", "agree", "with",
            "no", "understand", "thanks", "very", "welcome", "bye", "goodbye", "nice", "day", "eaten", "yet",
            "already", "done", "learned", "recently", "she", "has", "been", "since", "last", "year",
            "passive", "voice", "action", "subject", "book", "written", "famous", "writer", "know", "boy",
            "playing", "basketball", "this", "house", "where", "lived", "before", "family", "meet", 
            ".", ",", "?", "!" 
        ]

        if not self.load_model():
            print("[系統] 正在初始化 1.0 Beta 3 核心 (Context-Conditioned Seq2Seq)...")
            self.vocab = list(self.default_vocab)
            self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
            self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
            self.model = LanAISeq2Seq(len(self.vocab))
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
            self.model.expand_weights(len(self.vocab))
            self.training_data.extend(self.base_training_data)
            self.save_model() 

    def save_model(self):
        print("[系統] 正在寫入 Seq2Seq 記憶狀態 (.npz)...")
        np.savez(self.model_path,
                 vocab=np.array(self.vocab),
                 E=self.model.E,
                 W_r=self.model.W_r, U_r=self.model.U_r, b_r=self.model.b_r,
                 W_z=self.model.W_z, U_z=self.model.U_z, b_z=self.model.b_z,
                 W_h=self.model.W_h, U_h=self.model.U_h, b_h=self.model.b_h,
                 C_r=self.model.C_r, C_z=self.model.C_z, C_h=self.model.C_h, # 儲存 Context 神經元
                 W_y=self.model.W_y, b_y=self.model.b_y)
        print("[系統] 記憶儲存成功！")

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                print(f"[系統] 偵測到 V1.0 記憶檔 {self.model_path}，正在喚醒...")
                data = np.load(self.model_path, allow_pickle=True)
                self.vocab = data["vocab"].tolist()
                self.word_to_idx = {word: i for i, word in enumerate(self.vocab)}
                self.idx_to_word = {i: word for i, word in enumerate(self.vocab)}
                
                loaded_hidden_size = data["W_y"].shape[0]
                loaded_embedding_dim = data["E"].shape[1]
                
                self.model = LanAISeq2Seq(len(self.vocab), embedding_dim=loaded_embedding_dim, hidden_size=loaded_hidden_size)
                
                self.model.E = data["E"]
                self.model.W_r = data["W_r"]; self.model.U_r = data["U_r"]; self.model.b_r = data["b_r"]
                self.model.W_z = data["W_z"]; self.model.U_z = data["U_z"]; self.model.b_z = data["b_z"]
                self.model.W_h = data["W_h"]; self.model.U_h = data["U_h"]; self.model.b_h = data["b_h"]
                self.model.W_y = data["W_y"]; self.model.b_y = data["b_y"]
                
                # [向下相容機制] 如果是從 Beta 2 升級上來的，自動動態生成 Attention 神經元
                try:
                    self.model.C_r = data["C_r"]
                    self.model.C_z = data["C_z"]
                    self.model.C_h = data["C_h"]
                except KeyError:
                    print("[系統升級] 偵測到舊版記憶，正在為大腦注入 Context-Conditioned Attention 神經元...")
                    limit = np.sqrt(6 / (len(self.vocab) + loaded_hidden_size))
                    self.model.C_r = np.random.uniform(-limit, limit, (loaded_hidden_size, loaded_hidden_size))
                    self.model.C_z = np.random.uniform(-limit, limit, (loaded_hidden_size, loaded_hidden_size))
                    self.model.C_h = np.random.uniform(-limit, limit, (loaded_hidden_size, loaded_hidden_size))
                
                return True
            except Exception as e:
                print(f"[警告] 記憶載入失敗 ({e})。")
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
        num_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}
        for k, v in num_map.items():
            text = re.sub(rf'\b{k}\b', v, text)
            
        clean_text = text.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
        expr = "".join(re.findall(r'[\d\+\-\*\/\(\)\.]', clean_text))
        
        if expr and any(op in expr for op in "+-*/") and expr != ".":
            res = safe_math_eval(expr)
            if res is not None:
                res = int(res) if res == int(res) else round(res, 4)
                return f"The answer is {res}."
        return None

    def train_epochs(self, target_epochs, initial_lr=0.03): 
        for epoch in range(target_epochs):
            random.shuffle(self.training_data)
            loss = 0
            current_lr = initial_lr * (1 - (epoch / (target_epochs * 1.2))) 
            
            for words, targets in self.training_data:
                indices = [self.word_to_idx.get(w, 0) for w in words]
                t_indices = [self.word_to_idx.get(w, 0) for w in targets] + [self.word_to_idx["<EOS>"]]
                # 傳入 word_to_idx 以取得 <SOS> 的索引
                loss += self.model.train_sequence(indices, t_indices, self.word_to_idx, lr=current_lr)
            if epoch > 0 and epoch % 20 == 0:
                print(f"訓練進度 - Epoch: {epoch} | Loss: {loss/len(self.training_data):.4f} | LR: {current_lr:.4f}  ", end="\r")

    def thinking_layer(self, user_input, words):
        math_res = self.solve_math(user_input)
        
        logic_keywords = ["why", "how", "can", "what", "math", "solve"]
        grammar_keywords = ["grammar", "tense", "passive", "voice"]
        
        if any(w in words for w in grammar_keywords): intent = "grammar"
        elif any(w in words for w in logic_keywords): intent = "logic"
        else: intent = "chat"
            
        return math_res, intent

    def chat(self):
        print("="*65)
        print("  LanAI 1.0 Beta 3 (Context-Conditioned Seq2Seq)")
        print("="*65)
        
        if self.is_new_model:
            print("[系統] 全新 Seq2Seq 大腦建構中，執行深度語義壓縮 (800 Epochs)...")
            self.train_epochs(800, initial_lr=0.04)
            print("\n[系統] 基礎思維網路建立完成。")
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
                
                processed_input = re.sub(r'([.,!?])', r' \1 ', low_input)
                words = processed_input.split()
                
                math_res, intent = self.thinking_layer(low_input, words)

                if math_res:
                    print(f"AI (Logic Mode): {math_res}")
                    continue
                
                new_words_learned = False
                for w in words:
                    if self.add_new_word(w):
                        print(f"[系統意識] 擴充詞彙空間: '{w}'")
                        new_words_learned = True

                if new_words_learned and len(words) >= 3:
                    print("[動態微調] 正在將新句型寫入 Seq2Seq 記憶體...", end="\r")
                    self.training_data.append((words, ["i", "understand", ","] + words))
                    self.train_epochs(40, initial_lr=0.02)
                else:
                    self.train_epochs(3, initial_lr=0.005)
                
                print(" " * 60, end="\r") 
                
                indices = [self.word_to_idx.get(w, 0) for w in words]
                
                res_indices, self.context_h = self.model.generate(
                    indices, self.word_to_idx, top_k=3, temperature=0.4
                )
                
                print("AI: ", end="", flush=True)
                if not res_indices:
                    print("I am not sure how to respond to that.")
                else:
                    is_first_word = True
                    for idx in res_indices:
                        word = self.idx_to_word.get(idx, "...")
                        
                        if word in [".", ",", "?", "!"]:
                            print(word, end="", flush=True)
                            time.sleep(0.02)
                        else:
                            if not is_first_word:
                                print(" ", end="", flush=True)
                            for char in word:
                                print(char, end="", flush=True)
                                time.sleep(0.01)
                        is_first_word = False
                    print()
                    
            except KeyboardInterrupt: 
                print("\n[系統] 收到中斷訊號。")
                self.save_model()
                break

if __name__ == "__main__":
    lanai = LanAI()
    lanai.chat()