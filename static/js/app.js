document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Logic
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if(savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    }

    const header = document.querySelector('.sidebar');
    if(header) {
        const toggleWrapper = document.createElement('div');
        toggleWrapper.style.cssText = "display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: auto; padding-top: 20px; border-top: 1px solid var(--glass-border);";
        toggleWrapper.innerHTML = `
            <span id="theme-label" style="font-size: 14px; font-weight: 600; color: var(--text-main);">Dark Mode</span>
            <label style="position: relative; display: inline-block; width: 48px; height: 26px; cursor: pointer;">
              <input type="checkbox" id="theme-toggle" style="opacity: 0; width: 0; height: 0;">
              <span id="theme-slider" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(255,255,255,0.2); transition: .4s; border-radius: 26px; border: 1px solid var(--text-muted);">
                <span class="slider-ball" style="position: absolute; height: 18px; width: 18px; left: 4px; bottom: 3px; background-color: #fff; transition: .4s; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></span>
              </span>
            </label>
        `;
        
        const footer = document.querySelector('.sidebar-footer');
        if(footer) {
            footer.parentNode.insertBefore(toggleWrapper, footer);
        } else {
            header.appendChild(toggleWrapper);
        }

        const checkbox = document.getElementById('theme-toggle');
        const label = document.getElementById('theme-label');
        const sliderBall = toggleWrapper.querySelector('.slider-ball');
        const sliderBg = document.getElementById('theme-slider');

        if(savedTheme === 'light') {
            checkbox.checked = true;
            label.innerText = 'Light Mode';
            sliderBall.style.transform = 'translateX(20px)';
            sliderBg.style.backgroundColor = 'rgba(0,0,0,0.1)';
            sliderBall.style.backgroundColor = 'var(--primary-color)';
        }

        checkbox.addEventListener('change', function() {
            const newTheme = this.checked ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            label.innerText = newTheme === 'light' ? 'Light Mode' : 'Dark Mode';
            sliderBall.style.transform = this.checked ? 'translateX(20px)' : 'translateX(0)';
            sliderBg.style.backgroundColor = this.checked ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)';
            sliderBall.style.backgroundColor = this.checked ? 'var(--primary-color)' : '#fff';
            
            // Fix header text readability if light theme applied
            document.querySelectorAll('h1').forEach(h => {
               if(newTheme === 'light') h.style.color = '#111827'; 
               else h.style.color = '';
            });
        });
        
        // Initial setup
        if (savedTheme === 'light') {
            document.querySelectorAll('h1').forEach(h => h.style.color = '#111827');
        }
    }

    // 2. Low stock URL interpret
    if(window.location.pathname === '/inventory' && window.location.search.includes('filter=low')) {
        const rows = document.querySelectorAll('.data-table tbody tr');
        rows.forEach(r => {
            if(!r.querySelector('.badge-danger') && !r.querySelector('.tx-credit')) {
                r.style.display = 'none';
            }
        });
    }

    // 3. Hamburger Menu logic
    const topHeader = document.querySelector('.page-header');
    if(topHeader) {
        if(!document.getElementById('mobile-menu-btn')) {
            const hamburger = document.createElement('button');
            hamburger.id = 'mobile-menu-btn';
            hamburger.className = 'mobile-menu-btn';
            hamburger.innerHTML = '☰';
            
            const greeting = topHeader.querySelector('.greeting');
            if (greeting) {
               greeting.style.display = 'flex';
               greeting.style.alignItems = 'center';
               greeting.insertBefore(hamburger, greeting.firstChild);
            }
            
            hamburger.onclick = (e) => {
                e.stopPropagation();
                document.querySelector('.sidebar').classList.toggle('active');
            };
        }

        document.addEventListener('click', (e) => {
            const sidebar = document.querySelector('.sidebar');
            const hamburger = document.getElementById('mobile-menu-btn');
            if(sidebar && sidebar.classList.contains('active') && !sidebar.contains(e.target) && e.target !== hamburger) {
                sidebar.classList.remove('active');
            }
        });
    }
});
