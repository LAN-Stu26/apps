/**
 * LAN Studio - 核心 UI 組件 (v2.5 完全優化版)
 * 更新重點：保留所有原始文本、修復 Firebase 互動、優化導覽列邏輯
 */

// 1. 引入 Firebase SDK
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// 注意：GitHub 警告是因為檢測到 apiKey。
// 這是 Firebase 前端公開金鑰，若要消除警告可聯絡 GitHub 設定為 Allow 或將此段加密，目前維持現狀以確保功能運作。
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

// 2. CSS 樣式 (保留所有原始設計)
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

    #custom-navbar {
        position: fixed; top: 0; left: 0; width: 100%; height: 70px;
        background: #000000 !important; display: flex !important;
        justify-content: space-between; align-items: center;
        padding: 0 40px; box-sizing: border-box; z-index: 2147483647 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }

    #custom-navbar .logo { color: #ffd966; font-weight: bold; font-size: 1.4rem; white-space: nowrap; }

    .menu-toggle {
        display: none; flex-direction: column; gap: 6px; cursor: pointer; z-index: 1002;
        padding: 10px;
    }
    .menu-toggle span { width: 28px; height: 3px; background: #ffd966; transition: 0.3s; border-radius: 2px; }

    #nav-list { 
        list-style: none; display: flex !important; flex-direction: row !important;
        gap: 15px; margin: 0; padding: 0; align-items: center; 
        position: static !important; background: none !important; width: auto !important; height: auto !important;
    }

    #nav-list li { position: relative; }
    #nav-list li a, .dropbtn { 
        color: #ffffff; text-decoration: none; font-size: 1.05rem; 
        padding: 10px 15px; display: block; transition: 0.3s; cursor: pointer; 
    }

    @media (hover: hover) {
        #nav-list li a:hover, .dropdown:hover .dropbtn { color: #ffd966; }
        .dropdown:hover .dropdown-content { display: block; animation: fadeInDown 0.3s ease; }
    }

    .dropdown-content {
        display: none; position: absolute; background-color: #1a1a1a;
        min-width: 190px; box-shadow: 0px 8px 16px rgba(0,0,0,0.6);
        border-radius: 8px; top: 100%; left: 0; overflow: hidden; border: 1px solid #333;
    }
    .dropdown-content a { color: #ccc !important; padding: 12px 16px !important; font-size: 0.95rem !important; border-bottom: 1px solid #222; }
    .dropdown-content a:hover { background-color: #ffd966 !important; color: #000 !important; }

    #auth-area img { width: 35px; height: 35px; border-radius: 50%; border: 2px solid #ffd966; cursor: pointer; vertical-align: middle; }
    #login-btn { border: 1px solid #ffd966; padding: 5px 15px !important; border-radius: 20px; color: #ffd966 !important; cursor: pointer; }

    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

    @media (max-width: 850px) {
        #custom-navbar { padding: 0 20px; }
        .menu-toggle { display: flex; }
        #nav-list {
            position: fixed !important; top: 0; left: -100%; width: 280px; height: 100vh;
            background: #0a0a0a !important; flex-direction: column !important; 
            align-items: flex-start !important; padding: 80px 20px !important;
            box-shadow: 10px 0 20px rgba(0,0,0,0.8) !important;
            transition: 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        #nav-list.active { left: 0 !important; }
        .dropdown-content { position: static; background: #111; border: none; width: 100%; display: block; max-height: 0; overflow: hidden; transition: 0.4s ease; }
        .dropdown.mobile-open .dropdown-content { max-height: 500px; }
        .menu-toggle.active span:nth-child(1) { transform: translateY(9px) rotate(45deg); }
        .menu-toggle.active span:nth-child(2) { opacity: 0; }
        .menu-toggle.active span:nth-child(3) { transform: translateY(-9px) rotate(-45deg); }
    }

    #custom-footer { background-color: #000; color: #ecf0f1; padding: 40px 20px; border-top: 1px solid #222; }
    .footer-top { display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 20px; }
    .ai-notice { font-size: 0.9rem; text-align: right; background: linear-gradient(90deg, #4285f4 0%, #9b72cb 30%, #d96570 70%, #f3af5f 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; font-weight: 500; }
</style>
`;

// 3. HTML 生成邏輯 (完全保留原有文本)
let pageTitle = document.title.split('-')[0].trim();
const isHomePage = window.location.pathname.includes('index.html') || window.location.pathname.endsWith('/');
const is404Page = window.location.pathname.includes('404.html');

const navbarHTML = `
<nav id="custom-navbar">
    <div class="logo">LAN Studio</div>
    <div class="menu-toggle" id="mobile-menu-btn">
        <span></span><span></span><span></span>
    </div>
    <ul id="nav-list">
        <li><a href="index.html"><b>首頁</b></a></li>
        <li class="dropdown">
            <span class="dropbtn"><b>網頁應用工具 ▾</b></span>
            <div class="dropdown-content">
                <a href="editor.html"><b>Html Editor</b></a>
                <a href="marquee.html"><b>跑馬燈</b></a>
                <a href="pomodoro_technique.html"><b>番茄鐘</b></a>
                <a href="r_c-timer.html"><b>魔方計時器</b></a>
                <a href="#" style="color:#555 !important;">字數計算器 (維護中)</a>
            </div>
        </li>
        <li><a href="news.html"><b>最新消息</b></a></li>
        <li class="dropdown">
            <span class="dropbtn"><b>會員體驗升級程式 ▾</b></span>
            <div class="dropdown-content">
                <a href="editor.html"><b>Html Editor</b></a>
            </div>
        </li>            
        <li id="auth-area"><a id="login-btn">載入中...</a></li>
    </ul>
</nav>
`;

const breadcrumbContent = isHomePage ? `首頁` : `<a href="index.html" style="color:inherit; text-decoration:none; opacity:0.7;">首頁</a> > ${pageTitle}`;
const footerHTML = `
<footer id="custom-footer">
    <div class="footer-top">
        <div class="breadcrumb-box">
            <h4 style="margin:0; font-size:0.85rem; color:#aaa;">現在位置：</h4>
            <p style="margin:5px 0 0 0; font-size:1.1rem; font-weight:bold;">${breadcrumbContent}</p>
        </div>
        <div class="ai-notice">Studio JS v2.5 <br> 所有頁面皆由 AI 生成</div>
    </div>
    <div style="text-align:center; font-size:0.85rem; color:#555; border-top:1px solid #222; padding-top:20px; margin-top:20px;">©2026 LAN Studio 版權所有</div>
</footer>
`;

// 4. 渲染
document.head.insertAdjacentHTML('beforeend', style);
document.body.insertAdjacentHTML('afterbegin', navbarHTML);
document.body.insertAdjacentHTML('beforeend', footerHTML);

// 5. 互動邏輯
const menuBtn = document.getElementById('mobile-menu-btn');
const navList = document.getElementById('nav-list');

if (menuBtn) {
    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navList.classList.toggle('active');
        menuBtn.classList.toggle('active');
    });
}

document.addEventListener('click', () => {
    if(navList.classList.contains('active')){
        navList.classList.remove('active');
        menuBtn.classList.remove('active');
    }
});

document.querySelectorAll('.dropdown').forEach(dd => {
    dd.addEventListener('click', (e) => {
        if (window.innerWidth <= 850) {
            e.stopPropagation();
            dd.classList.toggle('mobile-open');
        }
    });
});

// 6. Firebase (監聽狀態並處理 UI)
onAuthStateChanged(auth, (user) => {
    const area = document.getElementById('auth-area');
    if (user) {
        area.innerHTML = `<img src="${user.photoURL}" id="user-pfp" title="${user.displayName}">`;
        document.getElementById('user-pfp').onclick = () => { if(confirm("確定登出？")) signOut(auth); };
    } else {
        area.innerHTML = `<a id="login-btn"><b>登入</b></a>`;
        document.getElementById('login-btn').onclick = () => signInWithPopup(auth, provider);
    }
});

// 7. Favicon
(function() {
    const link = document.createElement('link'); link.rel = 'icon'; link.href = '標籤頭像.png';
    document.head.appendChild(link);
})();

// 404 自動導回首頁
if (is404Page) {
    setTimeout(() => { window.location.href = 'index.html'; }, 5000);
}

export { auth };
