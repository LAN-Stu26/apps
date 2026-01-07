// 1. 引入 Firebase SDK (保持不變)
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

// 2. CSS 樣式 (重點修正：order 屬性與對齊)
const style = `
<style>
    html { scroll-behavior: smooth; }
    body {
        font-family: 'Noto Sans TC', sans-serif !important;
        margin: 0 !important; padding: 0 !important;
        display: flex !important; flex-direction: column !important;
        min-height: 100vh !important; background-color: #1d1d1d;
    }
    
    body > *:not(#custom-navbar):not(#custom-footer):not(#announcement-bar) { 
        flex: 1 0 auto; padding-top: 70px; 
        transition: padding-top 0.3s ease;
    }

    body.has-announcement > *:not(#custom-navbar):not(#custom-footer):not(#announcement-bar) { 
        padding-top: 115px !important; 
    }

    /* --- Navbar 佈局 --- */
    #custom-navbar {
        position: fixed; top: 0; left: 0; width: 100%; height: 70px;
        background: #000000 !important; display: flex !important;
        align-items: center; padding: 0 40px; box-sizing: border-box; 
        z-index: 2147483647 !important; box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }

    #custom-navbar .logo { 
        color: #ffd966; font-weight: bold; font-size: 1.4rem; 
        white-space: nowrap; margin-right: auto; /* 讓 Logo 靠左，其餘推向右邊 */
    }

    #nav-list { 
        list-style: none; display: flex !important; gap: 5px; 
        margin: 0; padding: 0; align-items: center; 
    }

    /* --- 經緯線地球語系 --- */
    .lang-sphere {
        width: 22px; height: 22px; border: 1.5px solid #ffd966; border-radius: 50%;
        position: relative; display: inline-block; vertical-align: middle;
        overflow: hidden; transition: 0.3s;
    }
    .lang-sphere::before {
        content: ""; position: absolute; top: 0; left: 50%; width: 40%; height: 100%;
        border: 1px solid #ffd966; border-radius: 50%; transform: translateX(-50%);
    }
    .lang-sphere::after {
        content: ""; position: absolute; top: 50%; left: 0; width: 100%; height: 1px;
        background: #ffd966; transform: translateY(-50%);
    }

    /* --- 漢堡按鈕 --- */
    .menu-toggle { 
        display: none; flex-direction: column; gap: 6px; cursor: pointer; 
        z-index: 10001; padding: 10px; margin-left: 15px; 
    }
    .menu-toggle span { width: 28px; height: 3px; background: #ffd966; transition: 0.4s; border-radius: 2px; }
    
    .menu-toggle.active span:nth-child(1) { transform: translateY(9px) rotate(45deg); }
    .menu-toggle.active span:nth-child(2) { opacity: 0; }
    .menu-toggle.active span:nth-child(3) { transform: translateY(-9px) rotate(-45deg); }

    /* 下拉選單樣式 */
    #nav-list li { position: relative; }
    #nav-list li a, .dropbtn { color: #ffffff; text-decoration: none; font-size: 1.05rem; padding: 10px 15px; display: block; transition: 0.3s; cursor: pointer; }
    .dropdown-content { 
        display: none; position: absolute; background-color: #1a1a1a; 
        min-width: 160px; box-shadow: 0px 8px 16px rgba(0,0,0,0.6); 
        border-radius: 8px; top: 100%; right: 0; overflow: hidden; border: 1px solid #333; 
    }
    .dropdown-content a { color: #ccc !important; padding: 12px 16px !important; font-size: 0.95rem !important; border-bottom: 1px solid #222; text-decoration: none; display: block; }
    .dropdown-content a:hover { background-color: #ffd966 !important; color: #000 !important; }
    
    @media (hover: hover) {
        .dropdown:hover .dropdown-content { display: block; animation: fadeInDown 0.3s ease; }
        #nav-list li a:hover, .dropdown:hover .dropbtn { color: #ffd966; }
    }

    /* 公告橫幅 */
    #announcement-bar { position: fixed; top: 70px; left: 0; width: 100%; background-color: #ffd966; color: #000; padding: 8px 40px; box-sizing: border-box; display: flex; justify-content: space-between; align-items: center; z-index: 2147483646; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .bar-actions { display: flex; align-items: center; gap: 12px; }
    .btn-bar-go { background: #000; color: #ffd966; border: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; text-decoration: none; }
    .btn-bar-close { background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #000; font-weight: bold; }

    #auth-area img { width: 35px; height: 35px; border-radius: 50%; border: 2px solid #ffd966; cursor: pointer; vertical-align: middle; }
    #login-btn { border: 1px solid #ffd966; padding: 5px 15px !important; border-radius: 20px; color: #ffd966 !important; cursor: pointer; }

    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

    @media (max-width: 850px) {
        #custom-navbar { padding: 0 20px; }
        .menu-toggle { display: flex; order: 10; /* 確保漢堡在最右邊 */ }
        #nav-list { 
            position: fixed; top: 0; left: -100%; width: 280px; height: 100vh; 
            background: #0a0a0a !important; flex-direction: column !important; 
            align-items: flex-start !important; padding: 80px 20px !important; 
            margin: 0 !important; transition: 0.4s ease; box-shadow: 10px 0 20px rgba(0,0,0,0.8); 
        }
        #nav-list.active { left: 0 !important; }
        .dropdown-content { position: static; background: #111; border: none; width: 100%; display: block; max-height: 0; overflow: hidden; transition: 0.4s ease; }
        .dropdown.mobile-open .dropdown-content { max-height: 500px; }
    }

    #custom-footer { background-color: #000; color: #ecf0f1; padding: 40px 20px; border-top: 1px solid #222; }
    .footer-top { display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 20px; }
    .ai-notice { font-size: 0.9rem; text-align: right; background: linear-gradient(90deg, #4285f4 0%, #9b72cb 30%, #d96570 70%, #f3af5f 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; font-weight: 500; }
</style>
`;

// 3. HTML 生成
const navbarHTML = `
<nav id="custom-navbar">
    <div class="logo">LAN Studio</div>
    <ul id="nav-list">
        <li><a href="home.html"><b>首頁</b></a></li>
        <li class="dropdown">
            <span class="dropbtn"><b>網頁應用工具 ▾</b></span>
            <div class="dropdown-content">
                <a href="classroom.html"><b>抽號器</b></a>
                <a href="editor.html"><b>Html Editor</b></a>
                <a href="marquee.html"><b>跑馬燈</b></a>
                <a href="pomodoro_technique.html"><b>番茄鐘</b></a>
                <a href="r_c-timer.html"><b>魔方計時器</b></a>
                <a href="#" style="color:#555 !important;">字數計算器</a>
            </div>
        </li>
        <li><a href="news.html"><b>最新消息</b></a></li>
        <li class="dropdown">
            <span class="dropbtn"><b>會員專屬/升級程式 ▾</b></span>
            <div class="dropdown-content">
                <a href="#" style="color:#555 !important;">會員專屬▾▾▾</a>
                <a href="note.html"><b>加密雲端筆記</b></a>
                <a href="#" style="color:#555 !important;">體驗升級!!!▾▾▾</a>
                <a href="editor.html"><b>Html Editor</b></a>
            </div>
        </li>            
        <li id="auth-area" class="dropdown"><a id="login-btn">載入中...</a></li>
        <li class="dropdown">
            <span class="dropbtn" style="padding: 10px;">
                <div class="lang-sphere"></div>
            </span>
            <div class="dropdown-content">
                <a href="home.html"><b>繁體中文</b></a>
                <a href="en/home.html"><b>English</b></a>
            </div>
        </li>
    </ul>
    <div class="menu-toggle" id="mobile-menu-btn">
        <span></span><span></span><span></span>
    </div>
</nav>

<div id="announcement-bar">
    <div class="bar-content">📢 歡迎來到 LAN Studio！我們現在支援 English 啦!!!</br>📢 Welcome to LAN Studio! We now support English!!!</div>
    <div class="bar-actions">
        <a href="en/home.html" class="btn-bar-go">Change language</a>
        <button class="btn-bar-close" id="close-bar">×</button>
    </div>
</div>
`;

// (其餘變數與 Footer 部分保持不變)
let pageTitle = document.title.split('-')[0].trim();
const isHomePage = window.location.pathname.match(/\/($|home$|home\.html$)/) !== null;
const breadcrumbContent = isHomePage ? `首頁` : `<a href="home.html" style="color:inherit; text-decoration:none; opacity:0.7;">首頁</a> > ${pageTitle}`;

const footerHTML = `
<footer id="custom-footer">
    <div class="footer-top">
        <div class="breadcrumb-box">
            <h4 style="margin:0; font-size:0.85rem; color:#aaa;">您現在位置...</h4>
            <p style="margin:5px 0 0 0; font-size:1.1rem; font-weight:bold;">${breadcrumbContent}</p>
        </div>
        <div class="ai-notice">Studio JS v2.9 <br> 所有頁面皆由 AI 生成</div>
    </div>
    <div style="text-align:center; font-size:0.85rem; color:#555; border-top:1px solid #222; padding-top:20px; margin-top:20px;">©2026 LAN Studio 版權所有</div>
</footer>
`;

document.head.insertAdjacentHTML('beforeend', style);
document.body.insertAdjacentHTML('afterbegin', navbarHTML);
document.body.insertAdjacentHTML('beforeend', footerHTML);

// 4. 互動邏輯
const menuBtn = document.getElementById('mobile-menu-btn');
const navList = document.getElementById('nav-list');
const annBar = document.getElementById('announcement-bar');
const closeBarBtn = document.getElementById('close-bar');

if (sessionStorage.getItem('ann-closed') === 'true') {
    annBar.style.display = 'none';
} else {
    document.body.classList.add('has-announcement');
}
if (closeBarBtn) {
    closeBarBtn.addEventListener('click', () => {
        annBar.style.display = 'none';
        document.body.classList.remove('has-announcement');
        sessionStorage.setItem('ann-closed', 'true');
    });
}

if (menuBtn) {
    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        menuBtn.classList.toggle('active');
        navList.classList.toggle('active');
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

onAuthStateChanged(auth, (user) => {
    const area = document.getElementById('auth-area');
    if (user) {
        area.innerHTML = `
            <div class="dropbtn" style="padding:0;">
                <img src="${user.photoURL}" style="width:35px; height:35px; border-radius:50%; border:2px solid #ffd966;">
            </div>
            <div class="dropdown-content">
                <a style="color:#ffd966 !important; pointer-events:none; border-bottom:1px solid #333;"><b>Hi, ${user.displayName || '會員'}</b></a>
                <a id="logout-btn" style="cursor:pointer;"><b>登出</b></a>
            </div>
        `;
        document.getElementById('logout-btn').onclick = () => { if(confirm("確定要登出嗎？")) signOut(auth); };
    } else {
        area.innerHTML = `<a id="login-btn"><b>登入</b></a>`;
        document.getElementById('login-btn').onclick = () => signInWithPopup(auth, provider);
    }
});

(function() {
    const link = document.createElement('link'); link.rel = 'icon'; link.href = '標籤頭像.png';
    document.head.appendChild(link);
})();

export { auth };
