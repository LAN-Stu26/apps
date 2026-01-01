/**
 * LAN Apps Studio - 核心 UI 組件 (v2.1)
 * 整合：Firebase Google Auth, Dropdown 下拉選單, 404 自動跳轉, 麵包屑導覽
 */

// 1. 引入 Firebase SDK (CDN 版本)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// 2. Firebase 配置 (已連結至 lan-member-studio)
const firebaseConfig = {
    apiKey: "AIzaSyCjG4P9ZNX2OYOdXw69oFboPoilvAZLG_Q",
    authDomain: "lan-member-studio.firebaseapp.com",
    projectId: "lan-member-studio",
    storageBucket: "lan-member-studio.firebasestorage.app",
    messagingSenderId: "239900590732",
    appId: "1:239900590732:web:f37b953aa04d0cab3a71a9",
    measurementId: "G-TTWM9YD7KF"
};

// 初始化 Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// 3. CSS 樣式表
const style = `
<style>
    /* 基礎與字體 */
    html { scroll-behavior: smooth; }
    body {
        font-family: 'Noto Sans TC', sans-serif !important;
        margin: 0 !important; padding: 0 !important;
        display: flex !important; flex-direction: column !important;
        min-height: 100vh !important; background-color: #1d1d1d;
    }

    /* 內容補償 (防止導覽列遮擋) */
    body > *:not(#custom-navbar):not(#custom-footer) {
        flex: 1 0 auto;
        padding-top: 70px;
    }

    /* 導覽列核心 */
    #custom-navbar {
        position: fixed; top: 0; left: 0; width: 100%; height: 70px;
        background: #000000 !important; display: flex !important;
        justify-content: space-between; align-items: center;
        padding: 0 40px; box-sizing: border-box;
        z-index: 2147483647 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }

    #custom-navbar .logo { color: #ffd966; font-weight: bold; font-size: 1.4rem; }
    #custom-navbar ul { list-style: none; display: flex; gap: 15px; margin: 0; padding: 0; align-items: center; }
    #custom-navbar ul li { position: relative; }

    #custom-navbar ul li a, .dropbtn {
        color: #ffffff; text-decoration: none; font-size: 1.05rem; 
        padding: 10px 15px; display: block; transition: 0.3s; cursor: pointer;
    }

    #custom-navbar ul li a:hover, .dropdown:hover .dropbtn { color: #ffd966; }

    /* 下拉選單樣式 */
    .dropdown-content {
        display: none; position: absolute; background-color: #1a1a1a;
        min-width: 190px; box-shadow: 0px 8px 16px rgba(0,0,0,0.6);
        border-radius: 8px; top: 100%; left: 0; overflow: hidden; border: 1px solid #333;
    }

    .dropdown-content a {
        color: #ccc !important; padding: 12px 16px !important;
        font-size: 0.95rem !important; border-bottom: 1px solid #222;
    }

    .dropdown-content a:last-child { border-bottom: none; }
    .dropdown-content a:hover { background-color: #ffd966 !important; color: #000 !important; }

    .dropdown:hover .dropdown-content {
        display: block; animation: fadeInDown 0.3s ease;
    }

    /* 會員區塊樣式 */
    #auth-area img { width: 35px; height: 35px; border-radius: 50%; border: 2px solid #ffd966; cursor: pointer; vertical-align: middle; }
    #login-btn { border: 1px solid #ffd966; padding: 5px 15px !important; border-radius: 20px; color: #ffd966 !important; }
    #login-btn:hover { background: #ffd966; color: #000 !important; }

    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Tooltip 與 頁尾 */
    .tooltip-text {
        visibility: hidden; width: 180px; background-color: #e74c3c; color: #fff;
        text-align: center; border-radius: 6px; padding: 8px; position: absolute;
        top: 130%; left: 50%; transform: translateX(-50%); font-size: 0.8rem;
        opacity: 0; transition: 0.3s; pointer-events: none; z-index: 100;
    }
    .nav-item:hover .tooltip-text { visibility: visible; opacity: 1; }

    #custom-footer { background-color: #000000 !important; color: #ecf0f1 !important; padding: 40px 40px 25px 40px !important; margin-top: auto !important; width: 100% !important; box-sizing: border-box !important; display: flex !important; flex-direction: column !important; }
    .footer-top { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #ffffff1a; padding-bottom: 25px; margin-bottom: 20px; }
    .breadcrumb-box p { margin: 5px 0 0 0; font-size: 1.15rem; font-weight: bold; }
    .ai-notice { font-size: 0.9rem; text-align: right; background: linear-gradient(90deg, #4285f4 0%, #9b72cb 30%, #d96570 70%, #f3af5f 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; color: transparent; font-weight: 500; }
    .footer-bottom { text-align: center; font-size: 0.85rem; color: #7f8c8d; }
    #redirect-timer { color: #e74c3c; font-weight: bold; }

    @media (max-width: 768px) {
        #custom-navbar { padding: 0 15px; }
        #custom-navbar ul { gap: 5px; }
        .footer-top { flex-direction: column; align-items: flex-start; gap: 20px; }
    }
</style>
`;

// 4. 邏輯偵測
let pageTitle = document.title.split('-')[0].trim();
const isHomePage = window.location.pathname.includes('index.html') || window.location.pathname.endsWith('/');
const is404Page = window.location.pathname.includes('404.html');
const breadcrumbName = isHomePage ? '首頁' : pageTitle;

// 5. 生成 HTML 結構
const navbarHTML = `
<nav id="custom-navbar">
    <div class="logo">LAN Apps Studio</div>
    <ul>
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
            <a href="https://www.apps.lan-stu.x10.mx/">返回舊版網站</a>
            <span class="tooltip-text">部分地區無法使用此網域!</span>
        </li>
        <li class="nav-item" id="auth-area">
            <a id="login-btn">載入中...</a>
        </li>
    </ul>
</nav>
`;

const breadcrumbContent = isHomePage
    ? `<a href="index.html" style="color:inherit; text-decoration:none;">首頁</a>`
    : `<a href="index.html" style="color:inherit; text-decoration:none; opacity:0.7;">首頁</a> > ${breadcrumbName}`;

const footerHTML = `
<footer id="custom-footer">
    <div class="footer-top">
        <div class="breadcrumb-box">
            <h4 style="margin:0; font-size:0.85rem; color:#aaa; font-weight:normal;">你現在的位置是...</h4>
            <p>${breadcrumbContent}</p>
        </div>
        <div class="ai-notice">
            js 版本: 2.2 Bate <br> 所有頁面皆由 AI 生成
        </div>
    </div>
    <div class="footer-bottom">©2026 LAN Studio 擁有網站所有版權。</div>
</footer>
`;

// 6. 渲染到頁面
document.head.insertAdjacentHTML('beforeend', style);
document.body.insertAdjacentHTML('afterbegin', navbarHTML);
document.body.insertAdjacentHTML('beforeend', footerHTML);

// 7. 會員狀態監聽與 UI 更新
onAuthStateChanged(auth, (user) => {
    const authArea = document.getElementById('auth-area');
    if (user) {
        // 登入狀態
        authArea.innerHTML = `
            <div class="dropdown">
                <img src="${user.photoURL}" alt="User Avatar">
                <div class="dropdown-content" style="right:0; left:auto;">
                    <a href="#" style="pointer-events:none; color:#ffd966 !important; font-weight:bold;">Hi, ${user.displayName}</a>
                    <a id="logout-btn" href="#">登出帳號</a>
                </div>
            </div>
        `;
        document.getElementById('logout-btn').onclick = (e) => {
            e.preventDefault();
            signOut(auth);
        };
    } else {
        // 未登入狀態
        authArea.innerHTML = `<a id="login-btn">會員登入</a>`;
        document.getElementById('login-btn').onclick = (e) => {
            e.preventDefault();
            signInWithPopup(auth, provider).catch(err => console.error("登入失敗:", err));
        };
        
        // 如果頁面標註為需要登入
        if (document.body.dataset.requiresAuth === "true") {
            alert("🔒 此頁面為會員專屬，請先登入！");
            window.location.href = "index.html";
        }
    }
});

// 8. 其他自動化功能 (Favicon & 404)
(function() {
    const link = document.createElement('link'); link.rel = 'icon'; link.type = 'image/png'; link.href = '標籤頭像.png';
    document.getElementsByTagName('head')[0].appendChild(link);
    const appleLink = document.createElement('link'); appleLink.rel = 'apple-touch-icon'; appleLink.href = '標籤頭像.png';
    document.getElementsByTagName('head')[0].appendChild(appleLink);
})();

if (is404Page) {
    const errorMsg = document.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.innerHTML += `<br><span style="font-size:1rem; opacity:0.8;">系統將在 <span id="redirect-timer">5</span> 秒後自動返回首頁</span>`;
        let timeLeft = 5;
        const timerElement = document.getElementById('redirect-timer');
        const countdown = setInterval(() => {
            timeLeft--;
            if (timerElement) timerElement.textContent = timeLeft;
            if (timeLeft <= 0) {
                clearInterval(countdown);
                window.location.href = 'index.html';
            }
        }, 1000);
    }
}
