/**
 * LAN Apps Studio - 核心 UI 組件 (Dropdown 升級版)
 */

const style = `
<style>
    /* 1. 字體與基礎排版 */
    html { scroll-behavior: smooth; }
    body {
        font-family: 'Noto Sans TC', sans-serif !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        min-height: 100vh !important;
        background-color: #1d1d1d;
    }

    body > *:not(#custom-navbar):not(#custom-footer) {
        flex: 1 0 auto;
        padding-top: 70px;
    }

    /* 2. 導覽列核心 */
    #custom-navbar {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 70px;
        background: #000000 !important;
        display: flex !important;
        justify-content: space-between;
        align-items: center;
        padding: 0 40px;
        box-sizing: border-box;
        z-index: 2147483647 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }

    #custom-navbar .logo {
        color: #ffd966; font-weight: bold; font-size: 1.4rem;
    }

    #custom-navbar ul {
        list-style: none; display: flex; gap: 20px; margin: 0; padding: 0;
    }

    #custom-navbar ul li { position: relative; } /* 給子選單定位用 */

    #custom-navbar ul li a, .dropbtn {
        color: #ffffff; text-decoration: none; font-size: 1.05rem; 
        padding: 10px 15px; display: block; transition: 0.3s;
        cursor: pointer;
    }

    #custom-navbar ul li a:hover, .dropdown:hover .dropbtn { color: #ffd966; }

    /* 3. 下拉選單 (Dropdown) 樣式 */
    .dropdown-content {
        display: none; /* 預設隱藏 */
        position: absolute;
        background-color: #1a1a1a;
        min-width: 180px;
        box-shadow: 0px 8px 16px rgba(0,0,0,0.6);
        border-radius: 8px;
        top: 100%; /* 剛好在導覽列下方 */
        left: 0;
        overflow: hidden;
        border: 1px solid #333;
    }

    .dropdown-content a {
        color: #ccc !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
        border-bottom: 1px solid #222;
    }

    .dropdown-content a:last-child { border-bottom: none; }
    .dropdown-content a:hover {
        background-color: #ffd966 !important;
        color: #000 !important;
    }

    /* 滑鼠移入 li 時顯示下拉內容 */
    .dropdown:hover .dropdown-content {
        display: block;
        animation: fadeInDown 0.3s ease;
    }

    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Tooltip 樣式 */
    .tooltip-text {
        visibility: hidden; width: 200px; background-color: #e74c3c; color: #fff;
        text-align: center; border-radius: 6px; padding: 10px; position: absolute;
        top: 130%; left: 50%; transform: translateX(-50%); font-size: 0.8rem;
        opacity: 0; transition: 0.3s; pointer-events: none;
    }
    .nav-item:hover .tooltip-text { visibility: visible; opacity: 1; }

    /* 頁尾樣式 ... (保持你原本的 CSS 不變) */
    #custom-footer { background-color: #000000 !important; color: #ecf0f1 !important; padding: 40px 40px 25px 40px !important; margin-top: auto !important; width: 100% !important; box-sizing: border-box !important; display: flex !important; flex-direction: column !important; z-index: 99999 !important; }
    .footer-top { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #ffffff1a; padding-bottom: 25px; margin-bottom: 20px; }
    .breadcrumb-box h4 { margin: 0 0 8px 0; font-size: 0.85rem; color: #ffffffff; font-weight: normal; }
    .breadcrumb-box p { margin: 0; font-size: 1.15rem; font-weight: bold; }
    .ai-notice { font-size: 0.9rem; background: linear-gradient(90deg, #4285f4 0%, #9b72cb 30%, #d96570 70%, #f3af5f 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; color: transparent; font-weight: 500; display: inline-block; letter-spacing: 0.02em; }
    .footer-bottom { text-align: center; font-size: 0.85rem; color: #7f8c8d; }
    #redirect-timer { color: #e74c3c; font-weight: bold; }

    @media (max-width: 600px) {
        #custom-navbar { padding: 0 15px; }
        .footer-top { flex-direction: column; align-items: flex-start; gap: 20px; }
    }
</style>
`;

// 邏輯偵測 (省略部分保持原樣)
let pageTitle = document.title.split('-')[0].trim();
const isHomePage = window.location.pathname.includes('index.html') || window.location.pathname.endsWith('/');
const is404Page = window.location.pathname.includes('404.html');
const breadcrumbName = isHomePage ? '首頁' : pageTitle;

// 6. 生成帶有下拉選單的 HTML
const navbarHTML = `
<nav id="custom-navbar">
    <div class="logo">LAN Apps Studio</div>
    <ul>
        <li class="nav-item"><a href="index.html">首頁</a></li>
        
        <li class="nav-item dropdown">
            <span class="dropbtn">網頁應用工具 ▾</span>
            <div class="dropdown-content">
                <a href="marquee.html">跑馬燈</a>
                <a href="pomodoro_technique.html">番茄鐘</a>
                <a href="r_c-timer.html">魔方計時器</a>
                <a href="#" style="color:#5b5b5b !important; cursor:not-allowed;">字數計算器 (維護中)</a>
            </div>
        </li>

        <li class="nav-item"><a href="news.html">最新消息</a></li>
        
        <li class="nav-item">
            <a href="https://www.apps.lan-stu.x10.mx/">返回舊版網站</a>
            <span class="tooltip-text">部分地區無法使用此網域!</span>
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
            <h4>你現在的位置是...</h4>
            <p>${breadcrumbContent}</p>
        </div>
        <div class="ai-notice">
        js 版本: 2.1
    </br>所有頁面皆由 AI 生成
        </div>
    </div>
    <div class="footer-bottom">©2026 LAN Studio 擁有網站所有版權。</div>
</footer>
`;

// 7. 渲染
document.head.insertAdjacentHTML('beforeend', style);
document.body.insertAdjacentHTML('afterbegin', navbarHTML);
document.body.insertAdjacentHTML('beforeend', footerHTML);

// 8. Favicon & 404 邏輯 (保持你原本的內容)
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
            if (timeLeft <= 0) { clearInterval(countdown); window.location.href = 'index.html'; }
        }, 1000);
    }
}
