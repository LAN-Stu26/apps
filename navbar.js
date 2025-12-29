/**
 * LAN Apps Studio - 核心 UI 組件 (導覽列 & 頁尾)
 * 功能：
 * 1. 自動偵測頁面標題並顯示麵包屑導覽
 * 2. 捲動自動變色 (透明 -> 深色)
 * 3. 強制修正各頁面 Flexbox 佈局衝突
 */

const style = `
<style>
    /* 1. 引用你的自定義字體 */
    @font-face {
        font-family: 'MyCustomFont'; 
        src: url('TaipeiSansTCBeta-Bold.ttf') format('truetype');
        font-weight: normal;
        font-style: normal;
    }

    /* 2. 強制初始化所有頁面的 Body 排版，解決置中或遮擋問題 */
    html {
        scroll-behavior: smooth;
    }

    body {
        font-family: 'MyCustomFont', 'Noto Sans TC', sans-serif !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        min-height: 100vh !important;
        background-color: transparent; /* 讓原本頁面的背景顯示出來 */
    }

    /* 確保頁面主內容不會被導覽列遮住 (除非是首頁有 GIF) */
    body > *:not(#custom-navbar):not(#custom-footer) {
        flex: 1 0 auto;
    }

    /* 3. 頂部導覽列樣式 */
    #custom-navbar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 70px;
        background: rgba(44, 62, 80, 0); /* 預設透明 */
        display: flex !important;
        justify-content: space-between;
        align-items: center;
        padding: 0 40px;
        box-sizing: border-box;
        z-index: 999999 !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        font-family: 'MyCustomFont', sans-serif;
    }

    /* 捲動後的狀態 */
    #custom-navbar.scrolled {
        background: rgba(44, 62, 80, 0.98) !important;
        height: 60px;
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 15px rgba(0,0,0,0.3);
    }

    #custom-navbar .logo {
        color: #ffffff;
        font-weight: bold;
        font-size: 1.4rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    #custom-navbar ul {
        list-style: none;
        display: flex;
        gap: 25px;
        margin: 0;
        padding: 0;
    }

    #custom-navbar ul li a {
        color: #ffffff;
        text-decoration: none;
        font-size: 1.05rem;
        transition: color 0.3s;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    #custom-navbar ul li a:hover {
        color: #3498db;
    }

    /* Tooltip 警告樣式 (針對字數計數) */
    .nav-item { position: relative; }
    .tooltip-text {
        visibility: hidden; width: 220px; background-color: #e74c3c; color: #fff;
        text-align: center; border-radius: 6px; padding: 10px; position: absolute;
        top: 150%; left: 50%; transform: translateX(-50%); font-size: 0.85rem;
        opacity: 0; transition: opacity 0.3s; line-height: 1.4;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .nav-item:hover .tooltip-text { visibility: visible; opacity: 1; }

    /* 4. 頁尾 Footer 樣式 */
    #custom-footer {
        background-color: #2c3e50 !important;
        color: #ecf0f1 !important;
        padding: 40px 40px 25px 40px !important;
        margin-top: auto !important; /* 強制置底 */
        width: 100% !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        z-index: 99999 !important;
        font-family: 'MyCustomFont', sans-serif;
    }

    .footer-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 25px;
        margin-bottom: 20px;
    }

    .breadcrumb-box h4 {
        margin: 0 0 8px 0;
        font-size: 0.85rem;
        color: #bdc3c7;
        font-weight: normal;
        letter-spacing: 1px;
    }

    .breadcrumb-box p {
        margin: 0;
        font-size: 1.15rem;
        font-weight: bold;
    }

    .ai-notice {
        font-size: 0.9rem;
        color: #95a5a6;
        background: rgba(255,255,255,0.05);
        padding: 5px 12px;
        border-radius: 20px;
    }

    .footer-bottom {
        text-align: center;
        font-size: 0.85rem;
        color: #7f8c8d;
    }

    /* 針對手機版的微調 */
    @media (max-width: 600px) {
        #custom-navbar { padding: 0 15px; }
        #custom-navbar ul { gap: 10px; }
        #custom-navbar ul li a { font-size: 0.9rem; }
        .footer-top { flex-direction: column; align-items: flex-start; gap: 20px; }
    }
</style>
`;

// 5. 動態獲取當前頁面標題
let pageTitle = document.title;
if (pageTitle.includes('-')) {
    pageTitle = pageTitle.split('-')[0].trim();
}
const isHomePage = window.location.pathname.includes('home.html') || window.location.pathname.endsWith('/');
const breadcrumbName = isHomePage ? '首頁' : pageTitle;

// 6. 生成 HTML 結構 (更新版：加入超連結並優化首頁路徑)
const navbarHTML = `
<nav id="custom-navbar">
    <div class="logo">LAN Apps Studio</div>
    <ul>
        <li class="nav-item"><a href="index.html">首頁</a></li>
        <li class="nav-item"><a href="跑馬燈.html">跑馬燈</a></li>
        <li class="nav-item"><a href="番茄鐘 1.0.html">番茄鐘</a></li>
        <li class="nav-item">
            <a href="字數計算器 1.0.html">字數計數</a>
            <span class="tooltip-text">此工具由 .sb3 檔案轉成 html，會有相容問題</span>
        </li>
        <li class="nav-item"><a href="魔術方塊計時器 2.0.html">魔方計時器</a></li>
    </ul>
</nav>
`;

// 判斷麵包屑顯示內容：如果是首頁就只顯示「首頁」，否則顯示「首頁 > 頁面名」
const breadcrumbContent = isHomePage 
    ? `<a href="index.html" style="color:inherit; text-decoration:none;">首頁</a>` 
    : `<a href="index.html" style="color:inherit; text-decoration:none; opacity:0.7;">首頁</a> > ${breadcrumbName}`;

const footerHTML = `
<footer id="custom-footer">
    <div class="footer-top">
        <div class="breadcrumb-box">
            <h4>你現在的位置是...</h4>
            <p>${breadcrumbContent}</p>
        </div>
        <div class="ai-notice">
            所有頁面皆由 AI 生成
        </div>
    </div>
    <div class="footer-bottom">
        ©2025 LAN Studio 擁有網站所有版權。
    </div>
</footer>
`;

// 7. 渲染至頁面
document.head.insertAdjacentHTML('beforeend', style);
document.body.insertAdjacentHTML('afterbegin', navbarHTML);
document.body.insertAdjacentHTML('beforeend', footerHTML);

// 8. 捲動監聽
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('custom-navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});