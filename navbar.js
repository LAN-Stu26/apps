/**
 * LAN Apps Studio - 核心 UI 組件 (導覽列 & 頁尾)
 * 更新：導覽列永久不透明、新增 404 自動跳轉邏輯
 */

const style = `
<style>
    /* 1. 引用字體 */
    @font-face {
        font-family: 'MyCustomFont'; 
        src: url('TaipeiSansTCBeta-Bold.ttf') format('truetype');
        font-weight: normal; font-style: normal;
    }

    html { scroll-behavior: smooth; }

    body {
        font-family: 'MyCustomFont', 'Noto Sans TC', sans-serif !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        min-height: 100vh !important;
    }

    /* 確保內容不被固定的導覽列遮住 */
    body > *:not(#custom-navbar):not(#custom-footer) {
        flex: 1 0 auto;
        padding-top: 70px; /* 預留導覽列高度 */
    }

    /* 3. 頂部導覽列：永久不透明 */
    #custom-navbar {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 70px;
        background: rgba(44, 62, 80, 1) !important; /* 直接設定為不透明 */
        display: flex !important;
        justify-content: space-between;
        align-items: center;
        padding: 0 40px;
        box-sizing: border-box;
        z-index: 999999 !important;
        font-family: 'MyCustomFont', sans-serif;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }

    #custom-navbar .logo {
        color: #ffffff; font-weight: bold; font-size: 1.4rem;
    }

    #custom-navbar ul {
        list-style: none; display: flex; gap: 25px; margin: 0; padding: 0;
    }

    #custom-navbar ul li a {
        color: #ffffff; text-decoration: none; font-size: 1.05rem; transition: color 0.3s;
    }

    #custom-navbar ul li a:hover { color: #3498db; }

    /* Tooltip */
    .nav-item { position: relative; }
    .tooltip-text {
        visibility: hidden; width: 220px; background-color: #e74c3c; color: #fff;
        text-align: center; border-radius: 6px; padding: 10px; position: absolute;
        top: 150%; left: 50%; transform: translateX(-50%); font-size: 0.85rem;
        opacity: 0; transition: opacity 0.3s; z-index: 1000000;
    }
    .nav-item:hover .tooltip-text { visibility: visible; opacity: 1; }

    /* 4. 頁尾 */
    #custom-footer {
        background-color: #2c3e50 !important;
        color: #ecf0f1 !important;
        padding: 40px 40px 25px 40px !important;
        margin-top: auto !important;
        width: 100% !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        z-index: 99999 !important;
    }

    .footer-top {
        display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 25px; margin-bottom: 20px;
    }

    .breadcrumb-box h4 { margin: 0 0 8px 0; font-size: 0.85rem; color: #bdc3c7; font-weight: normal; }
    .breadcrumb-box p { margin: 0; font-size: 1.15rem; font-weight: bold; }
    .ai-notice { font-size: 0.9rem; color: #95a5a6; }
    .footer-bottom { text-align: center; font-size: 0.85rem; color: #7f8c8d; }

    /* 404 倒數計時文字樣式 */
    #redirect-timer { color: #e74c3c; font-weight: bold; }

    @media (max-width: 600px) {
        #custom-navbar { padding: 0 15px; }
        #custom-navbar ul { gap: 10px; }
        .footer-top { flex-direction: column; align-items: flex-start; gap: 20px; }
    }
</style>
`;

// 5. 邏輯偵測
let pageTitle = document.title.split('-')[0].trim();
const isHomePage = window.location.pathname.includes('index.html') || window.location.pathname.endsWith('/');
const is404Page = window.location.pathname.includes('404.html');
const breadcrumbName = isHomePage ? '首頁' : pageTitle;

// 6. 生成 HTML
const navbarHTML = `
<nav id="custom-navbar">
    <div class="logo">LAN Apps Studio</div>
    <ul>
        <li class="nav-item"><a href="index.html">首頁</a></li>
        <li class="nav-item"><a href="marquee.html">跑馬燈</a></li>
        <li class="nav-item"><a href="pomodoro_technique.html">番茄鐘</a></li>
        <li class="nav-item">
            <a href="字數計算器 1.0.html">字數計數</a>
            <span class="tooltip-text">此工具由 .sb3 檔案轉成 html，會有相容問題</span>
        </li>
        <li class="nav-item"><a href="r_c-timer.html">魔方計時器</a></li>
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

// 7. 渲染
document.head.insertAdjacentHTML('beforeend', style);
document.body.insertAdjacentHTML('afterbegin', navbarHTML);
document.body.insertAdjacentHTML('beforeend', footerHTML);

// 8. 自動注入 Favicon (.png)
(function() {
    const link = document.createElement('link');
    link.rel = 'icon';
    link.type = 'image/png';
    link.href = '標籤頭像.png'; 
    document.getElementsByTagName('head')[0].appendChild(link);
    
    // Apple Touch Icon
    const appleLink = document.createElement('link');
    appleLink.rel = 'apple-touch-icon';
    appleLink.href = '標籤頭像.png';
    document.getElementsByTagName('head')[0].appendChild(appleLink);
})();

// 9. 404 自動跳轉邏輯
if (is404Page) {
    const errorMsg = document.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.innerHTML += `<br><span style="font-size:1rem; opacity:0.8; margin-top:20px; display:block;">系統將在 <span id="redirect-timer">5</span> 秒後自動返回首頁</span>`;
        let timeLeft = 5;
        const timerElement = document.getElementById('redirect-timer');
        const countdown = setInterval(() => {
            timeLeft--;
            if(timerElement) timerElement.textContent = timeLeft;
            if (timeLeft <= 0) {
                clearInterval(countdown);
                window.location.href = 'index.html';
            }
        }, 1000);
    }
}
