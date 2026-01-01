// 1. 引入 Firebase SDK
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyCjG4P9ZNX2OYOdXw69oFboPoilvAZLG_Q",
    authDomain: "lan-member-studio.firebaseapp.com",
    projectId: "lan-member-studio",
    storageBucket: "lan-member-studio.firebasestorage.app",
    messagingSenderId: "239900590732",
    appId: "1:239900590732:web:f37b953aa04d0cab3a71a9",
    measurementId: "G-TTWM9YD7KF"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// 2. CSS 樣式
const style = `
<style>
    html { scroll-behavior: smooth; }
    body {
        font-family: 'Noto Sans TC', sans-serif !important;
        margin: 0 !important; padding: 0 !important;
        display: flex !important; flex-direction: column !important;
        min-height: 100vh !important; background-color: #1d1d1d;
    }
    body > *:not(#custom-navbar):not(#custom-footer) { flex: 1 0 auto; padding-top: 70px; }

    /* 導覽列核心 */
    #custom-navbar {
        position: fixed; top: 0; left: 0; width: 100%; height: 70px;
        background: #000000 !important; display: flex !important;
        justify-content: space-between; align-items: center;
        padding: 0 40px; box-sizing: border-box; z-index: 2147483647 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    #custom-navbar .logo { color: #ffd966; font-weight: bold; font-size: 1.4rem; z-index: 1001; }

    /* 漢堡按鈕 (手機版顯示) */
    .menu-toggle {
        display: none; flex-direction: column; gap: 6px; cursor: pointer; z-index: 1001;
    }
    .menu-toggle span { width: 28px; height: 3px; background: #ffd966; transition: 0.3s; border-radius: 2px; }

    /* 電腦版選單清單 */
    #nav-list { list-style: none; display: flex; gap: 15px; margin: 0; padding: 0; align-items: center; transition: 0.4s ease; }
    #nav-list li { position: relative; }
    #nav-list li a, .dropbtn { color: #ffffff; text-decoration: none; font-size: 1.05rem; padding: 10px 15px; display: block; transition: 0.3s; cursor: pointer; }
    #nav-list li a:hover, .dropdown:hover .dropbtn { color: #ffd966; }

    /* 下拉選單樣式 */
    .dropdown-content {
        display: none; position: absolute; background-color: #1a1a1a;
        min-width: 190px; box-shadow: 0px 8px 16px rgba(0,0,0,0.6);
        border-radius: 8px; top: 100%; left: 0; overflow: hidden; border: 1px solid #333;
    }
    .dropdown-content a { color: #ccc !important; padding: 12px 16px !important; font-size: 0.95rem !important; border-bottom: 1px solid #222; }
    .dropdown-content a:hover { background-color: #ffd966 !important; color: #000 !important; }
    .dropdown:hover .dropdown-content { display: block; animation: fadeInDown 0.3s ease; }

    /* 會員樣式 */
    #auth-area img { width: 35px; height: 35px; border-radius: 50%; border: 2px solid #ffd966; cursor: pointer; vertical-align: middle; }
    #login-btn { border: 1px solid #ffd966; padding: 5px 15px !important; border-radius: 20px; color: #ffd966 !important; }

    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

    /* 📱 行動裝置優化 (RWD) */
    @media (max-width: 850px) {
        #custom-navbar { padding: 0 20px; }
        .menu-toggle { display: flex; }

        #nav-list {
            position: absolute; top: 0; left: -100%; width: 250px; height: 100vh;
            background: #000; flex-direction: column; align-items: flex-start;
            padding: 80px 20px; box-sizing: border-box; gap: 10px;
            box-shadow: 5px 0 15px rgba(0,0,0,0.5);
        }
        #nav-list.active { left: 0; }
        #nav-list li { width: 100%; }
        #nav-list li a, .dropbtn { border-bottom: 1px solid #222; padding: 15px 10px; }

        .dropdown-content { position: static; background: #111; border: none; width: 100%; box-shadow: none; display: block; max-height: 0; overflow: hidden; transition: 0.3s; }
        .dropdown:hover .dropdown-content { max-height: 300px; }
        
        .tooltip-text { display: none !important; }
    }

    /* 頁尾與其他 */
    .tooltip-text { visibility: hidden; width: 180px; background-color: #e74c3c; color: #fff; text-align: center; border-radius: 6px; padding: 8px; position: absolute; top: 130%; left: 50%; transform: translateX(-50%); font-size: 0.8rem; opacity: 0; transition: 0.3s; pointer-events: none; z-index: 100; }
    .nav-item:hover .tooltip-text { visibility: visible; opacity: 1; }
    #custom-footer { background-color: #000; color: #ecf0f1; padding: 40px 20px; border-top: 1px solid #222; }
    .footer-top { display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 20px; }
    .ai-notice { font-size: 0.9rem; text-align: right; background: linear-gradient(90deg, #4285f4 0%, #9b72cb 30%, #d96570 70%, #f3af5f 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; font-weight: 500; }
    #redirect-timer { color: #e74c3c; font-weight: bold; }
</style>
`;

// 3. 邏輯與 HTML 生成
let pageTitle = document.title.split('-')[0].trim();
const isHomePage = window.location.pathname.includes('index.html') || window.location.pathname.endsWith('/');
const is404Page = window.location.pathname.includes('404.html');
const breadcrumbName = isHomePage ? '首頁' : pageTitle;

const navbarHTML = `
<nav id="custom-navbar">
    <div class="logo">LAN Apps Studio</div>
    <div class="menu-toggle" id="mobile-menu-btn">
        <span></span><span></span><span></span>
    </div>
    <ul id="nav-list">
        <li class="nav-item"><a href="index.html"><b>首頁</b></a></li>
        <li class="nav-item dropdown">
            <span class="dropbtn"><b>網頁應用工具 ▾</b></span>
            <div class="dropdown-content">
                <a href="marquee.html"><b>跑馬燈</b></a>
                <a href="pomodoro_technique.html"><b>番茄鐘</b></a>
                <a href="r_c-timer.html"><b>魔方計時器</b></a>
                <a href="#" style="color:#5b5b5b !important; cursor:not-allowed;">字數計算器 (維護中)</a>
            </div>
        </li>
        <li class="nav-item"><a href="news.html"><b>最新消息</b></a></li>
        <li class="nav-item">
            <a href="https://www.apps.lan-stu.x10.mx/">返回舊版</a>
            <span class="tooltip-text">部分地區無法使用！</span>
        </li>
        <li class="nav-item" id="auth-area">
            <a id="login-btn">載入中...</a>
        </li>
    </ul>
</nav>
`;

const breadcrumbContent = isHomePage ? `首頁` : `<a href="index.html" style="color:inherit; text-decoration:none; opacity:0.7;">首頁</a> > ${breadcrumbName}`;

const footerHTML = `
<footer id="custom-footer">
    <div class="footer-top">
        <div class="breadcrumb-box">
            <h4 style="margin:0; font-size:0.85rem; color:#aaa;">你現在的位置是...</h4>
            <p style="margin:5px 0 0 0; font-size:1.15rem; font-weight:bold;">${breadcrumbContent}</p>
        </div>
        <div class="ai-notice">js 版本: 2.2 <br> 所有頁面皆由 AI 生成</div>
    </div>
    <div style="text-align:center; font-size:0.85rem; color:#7f8c8d; border-top:1px solid #ffffff1a; padding-top:20px;">©2026 LAN Studio 擁有網站所有版權。</div>
</footer>
`;

// 4. 渲染
document.head.insertAdjacentHTML('beforeend', style);
document.body.insertAdjacentHTML('afterbegin', navbarHTML);
document.body.insertAdjacentHTML('beforeend', footerHTML);

// 5. 漢堡選單互動
const menuBtn = document.getElementById('mobile-menu-btn');
const navList = document.getElementById('nav-list');
menuBtn.onclick = () => navList.classList.toggle('active');

// 6. 會員監聽
onAuthStateChanged(auth, (user) => {
    const authArea = document.getElementById('auth-area');
    if (user) {
        authArea.innerHTML = `
            <div class="dropdown">
                <img src="${user.photoURL}" alt="User">
                <div class="dropdown-content" style="right:0; left:auto;">
                    <a href="#" style="pointer-events:none; color:#ffd966 !important;">Hi, ${user.displayName}</a>
                    <a id="logout-btn" href="#">登出帳號</a>
                </div>
            </div>`;
        document.getElementById('logout-btn').onclick = () => signOut(auth);
    } else {
        authArea.innerHTML = `<a id="login-btn">會員登入</a>`;
        document.getElementById('login-btn').onclick = () => signInWithPopup(auth, provider);
        if (document.body.dataset.requiresAuth === "true") {
            alert("🔒 此頁面為會員專屬，請先登入！");
            window.location.href = "index.html";
        }
    }
});

// 7. 其他功能 (Favicon & 404)
(function() {
    const link = document.createElement('link'); link.rel = 'icon'; link.href = '標籤頭像.png';
    document.getElementsByTagName('head')[0].appendChild(link);
})();

if (is404Page) {
    const errorMsg = document.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.innerHTML += `<br><span id="redirect-text" style="font-size:1rem; opacity:0.8;">系統將在 <span id="redirect-timer">5</span> 秒後自動返回首頁</span>`;
        let timeLeft = 5;
        setInterval(() => {
            if (timeLeft > 0) {
                timeLeft--;
                document.getElementById('redirect-timer').textContent = timeLeft;
                if (timeLeft === 0) window.location.href = 'index.html';
            }
        }, 1000);
    }
}
