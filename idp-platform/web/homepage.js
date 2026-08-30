/* ╔══════════════════════════════════════════════════╗
   ║  PARSA HOMEPAGE — Interactive Logic               ║
   ║  Hero word rotator, counter animation,            ║
   ║  scroll-triggered reveals, and mobile nav.        ║
   ╚══════════════════════════════════════════════════╝ */

(function () {
  'use strict';

  // ─── HERO WORD ROTATOR ───
  const wordEl = document.getElementById('heroRotatingWord');
  if (wordEl) {
    const cyclingWords = ['complex', 'messy', 'medical', 'handwritten'];
    let wordIdx = 0;
    setInterval(() => {
      wordEl.classList.add('word-exit');
      setTimeout(() => {
        wordIdx = (wordIdx + 1) % cyclingWords.length;
        wordEl.textContent = cyclingWords[wordIdx];
        wordEl.classList.remove('word-exit');
        wordEl.classList.add('word-enter');
        setTimeout(() => {
          wordEl.classList.remove('word-enter');
        }, 50);
      }, 350);
    }, 2200);
  }


  // ─── PIPELINE STATUS CYCLING ───
  const statusEl = document.getElementById('pipelineStatus');
  if (statusEl) {
    const statuses = ['Receiving…', 'Parsing…', 'Extracting…', 'Verifying…', 'Extracted'];
    let statusIdx = 0;

    setInterval(() => {
      statusIdx = (statusIdx + 1) % statuses.length;
      statusEl.style.opacity = '0';
      setTimeout(() => {
        statusEl.textContent = statuses[statusIdx];
        statusEl.style.opacity = '1';
      }, 200);
    }, 3000);
  }


  // ─── COUNTER ANIMATION ───
  function animateCounter(el) {
    const target = parseInt(el.dataset.target, 10);
    const numberEl = el.querySelector('.proof__number');
    if (!numberEl || isNaN(target)) return;

    const duration = 2000;
    const startTime = performance.now();
    const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

    function tick(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutCubic(progress);
      const current = Math.round(easedProgress * target);

      numberEl.textContent = current.toLocaleString() + '+';

      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    }

    requestAnimationFrame(tick);
  }


  // ─── PROOF RING ANIMATION ───
  function animateRings() {
    const rings = document.querySelectorAll('.proof-ring');
    rings.forEach(ring => ring.classList.add('animate'));
  }


  // ─── INTERSECTION OBSERVER (Scroll reveals) ───
  const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -40px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.observe-in').forEach(el => {
    observer.observe(el);
  });

  // Counter & Rings observer (special triggers)
  const counterEl = document.getElementById('proofCounter');
  let counterAnimated = false;

  const specialObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !counterAnimated) {
        counterAnimated = true;
        animateCounter(entry.target);
        animateRings();
        specialObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  if (counterEl) {
    specialObserver.observe(counterEl);
  }


  // ─── MOBILE NAVIGATION ───
  const hamburger = document.getElementById('navHamburger');
  const mobileMenu = document.getElementById('mobileMenu');

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      const isOpen = mobileMenu.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    // Close on link click
    mobileMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileMenu.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      });
    });
  }


  // ─── NAV SCROLL SHADOW ───
  const nav = document.getElementById('mainNav');
  if (nav) {
    let lastScroll = 0;
    window.addEventListener('scroll', () => {
      const scrollY = window.scrollY;
      if (scrollY > 20) {
        nav.style.boxShadow = '0 1px 3px rgba(0,0,0,0.3), 0 8px 24px -8px rgba(0,0,0,0.4)';
      } else {
        nav.style.boxShadow = 'none';
      }
      lastScroll = scrollY;
    }, { passive: true });
  }


  // ─── CODE TAB SWITCHING ───
  const codeTabs = document.querySelectorAll('.code-tab');
  const codeContent = document.getElementById('codeContent');
  const codeFilename = document.getElementById('codeFilename');

  const codeSnippets = {
    curl: {
      filename: 'extract.sh',
      code: `curl -X POST https://api.parsa.ai/v1/documents/upload \\
  -H "X-API-Key: your_api_key" \\
  -H "X-LLM-Provider: gemini" \\
  -H "X-LLM-Model: gemini-2.0-flash" \\
  -F "file=@invoice.pdf"`
    },
    python: {
      filename: 'extract.py',
      code: `import requests

resp = requests.post(
    "https://api.parsa.ai/v1/documents/upload",
    headers={
        "X-API-Key": "your_api_key",
        "X-LLM-Provider": "gemini",
        "X-LLM-Model": "gemini-2.0-flash",
    },
    files={"file": open("invoice.pdf", "rb")}
)
print(resp.json())`
    },
    node: {
      filename: 'extract.js',
      code: `const form = new FormData();
form.append("file", fs.createReadStream("invoice.pdf"));

const res = await fetch(
  "https://api.parsa.ai/v1/documents/upload",
  {
    method: "POST",
    headers: {
      "X-API-Key": "your_api_key",
      "X-LLM-Provider": "gemini",
      "X-LLM-Model": "gemini-2.0-flash",
    },
    body: form,
  }
);
console.log(await res.json());`
    }
  };

  codeTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      codeTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const lang = tab.dataset.lang;
      const snippet = codeSnippets[lang];
      if (snippet && codeContent && codeFilename) {
        codeContent.textContent = snippet.code;
        codeFilename.textContent = snippet.filename;
      }
    });
  });


  // ─── SMOOTH SCROLL FOR ANCHOR LINKS ───
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const targetId = anchor.getAttribute('href');
      if (!targetId || targetId === '#') return;

      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        if (window.parsaShowView) {
          window.parsaShowView('home');
        }
        setTimeout(() => {
          targetEl.scrollIntoView({ behavior: 'smooth' });
        }, 50);
      }
    });
  });

  // ─── LITHOS CURSOR SPOTLIGHT REVEAL ───
  const SPOTLIGHT_R = 260;
  const lithosCanvas = document.getElementById('lithosCanvas');
  const lithosReveal = document.getElementById('lithosRevealLayer');

  if (lithosCanvas && lithosReveal) {
    let mouseX = -999, mouseY = -999;
    let smoothX = -999, smoothY = -999;
    const ctx = lithosCanvas.getContext('2d');

    function resizeCanvas() {
      lithosCanvas.width = window.innerWidth;
      lithosCanvas.height = window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas, { passive: true });

    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    }, { passive: true });

    function renderSpotlight() {
      if (mouseX !== -999 && mouseY !== -999) {
        if (smoothX === -999) {
          smoothX = mouseX;
          smoothY = mouseY;
        } else {
          smoothX += (mouseX - smoothX) * 0.1;
          smoothY += (mouseY - smoothY) * 0.1;
        }

        ctx.clearRect(0, 0, lithosCanvas.width, lithosCanvas.height);
        const grad = ctx.createRadialGradient(smoothX, smoothY, 0, smoothX, smoothY, SPOTLIGHT_R);
        grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
        grad.addColorStop(0.4, 'rgba(255, 255, 255, 1)');
        grad.addColorStop(0.6, 'rgba(255, 255, 255, 0.75)');
        grad.addColorStop(0.75, 'rgba(255, 255, 255, 0.4)');
        grad.addColorStop(0.88, 'rgba(255, 255, 255, 0.12)');
        grad.addColorStop(1, 'rgba(255, 255, 255, 0)');

        ctx.beginPath();
        ctx.arc(smoothX, smoothY, SPOTLIGHT_R, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();

        const maskUrl = lithosCanvas.toDataURL();
        lithosReveal.style.maskImage = `url(${maskUrl})`;
        lithosReveal.style.webkitMaskImage = `url(${maskUrl})`;
        lithosReveal.style.maskSize = '100% 100%';
        lithosReveal.style.webkitMaskSize = '100% 100%';
      }
      requestAnimationFrame(renderSpotlight);
    }
    requestAnimationFrame(renderSpotlight);
  }

  // ─── HERO VIDEO BACKGROUND FADE CONTROLLER ───
  (function setupHeroVideo() {
    const video = document.getElementById('heroBgVideo');
    if (!video) return;

    let animFrameId = null;
    let fadingOut = false;
    let fadingIn = false;

    function cancelRunningAnimation() {
      if (animFrameId !== null) {
        cancelAnimationFrame(animFrameId);
        animFrameId = null;
      }
    }

    function getOpacity() {
      const computedOpacity = video.style.opacity;
      if (computedOpacity === '' || computedOpacity === undefined) return 0;
      const parsed = parseFloat(computedOpacity);
      return isNaN(parsed) ? 0 : parsed;
    }

    function fadeIn(duration) {
      duration = duration || 250;
      cancelRunningAnimation();
      fadingIn = true;
      fadingOut = false;

      const startOpacity = getOpacity();
      const startTime = performance.now();

      function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentOpacity = startOpacity + (1 - startOpacity) * progress;
        video.style.opacity = currentOpacity.toString();

        if (progress < 1) {
          animFrameId = requestAnimationFrame(step);
        } else {
          fadingIn = false;
          animFrameId = null;
        }
      }
      animFrameId = requestAnimationFrame(step);
    }

    function fadeOut(duration, onComplete) {
      duration = duration || 250;
      cancelRunningAnimation();
      fadingOut = true;
      fadingIn = false;

      const startOpacity = getOpacity();
      const startTime = performance.now();

      function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentOpacity = startOpacity * (1 - progress);
        video.style.opacity = currentOpacity.toString();

        if (progress < 1) {
          animFrameId = requestAnimationFrame(step);
        } else {
          fadingOut = false;
          animFrameId = null;
          if (onComplete) onComplete();
        }
      }
      animFrameId = requestAnimationFrame(step);
    }

    video.addEventListener('timeupdate', function () {
      if (!video.duration) return;
      const remaining = video.duration - video.currentTime;
      if (remaining <= 0.55 && !fadingOut && !fadingIn) {
        fadeOut(250);
      }
    });

    video.addEventListener('ended', function () {
      cancelRunningAnimation();
      video.style.opacity = '0';
      fadingOut = false;
      fadingIn = false;
      setTimeout(function () {
        video.currentTime = 0;
        const playPromise = video.play();
        if (playPromise !== undefined) {
          playPromise.then(function () {
            fadeIn(250);
          }).catch(function () {});
        }
      }, 100);
    });

    video.addEventListener('loadeddata', function () {
      video.style.opacity = '0';
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.then(function () {
          fadeIn(250);
        }).catch(function () {});
      }
    });

    video.style.opacity = '0';
    if (video.readyState >= 2) {
      video.style.opacity = '0';
      video.play().then(function () {
        fadeIn(250);
      }).catch(function () {});
    }
  })();

  // ─── ENTERPRISE DEMO MODAL CONTROLLER ───
  (function setupDemoModal() {
    const demoModal = document.getElementById('demoModal');
    const btnCloseModal = document.getElementById('btnCloseModal');
    const btnDoneDemo = document.getElementById('btnDoneDemo');
    const demoForm = document.getElementById('demoForm');
    const demoSuccessState = document.getElementById('demoSuccessState');

    function openModal() {
      if (!demoModal) return;
      demoModal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      if (demoForm) demoForm.classList.remove('hidden');
      if (demoSuccessState) demoSuccessState.classList.add('hidden');
    }

    function closeModal() {
      if (!demoModal) return;
      demoModal.classList.add('hidden');
      document.body.style.overflow = '';
    }

    window.openParsaDemoModal = openModal;

    document.querySelectorAll('[data-open-demo="true"], a[href="#demoModal"], #btnBookDemo').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        openModal();
      });
    });

    if (btnCloseModal) btnCloseModal.addEventListener('click', closeModal);
    if (btnDoneDemo) btnDoneDemo.addEventListener('click', closeModal);

    if (demoModal) {
      demoModal.addEventListener('click', (e) => {
        if (e.target === demoModal) {
          closeModal();
        }
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && demoModal && !demoModal.classList.contains('hidden')) {
        closeModal();
      }
    });

    if (demoForm) {
      demoForm.addEventListener('submit', (e) => {
        e.preventDefault();
        demoForm.classList.add('hidden');
        if (demoSuccessState) demoSuccessState.classList.remove('hidden');
      });
    }
  })();

  // ─── SEARCH INPUT PLUS MENU & WORKSPACE CONTEXT LOGIC ───
  (function () {
    const btnPlusMenu = document.getElementById('btnPlusMenu');
    const plusMenuPopover = document.getElementById('plusMenuPopover');
    const btnAttachTrigger = document.getElementById('btnAttachTrigger');
    const heroFileInput = document.getElementById('heroFileInput');
    const heroFolderInput = document.getElementById('heroFolderInput');
    const menuOptFolder = document.getElementById('menuOptFolder');
    const menuOptDocument = document.getElementById('menuOptDocument');
    const menuOptWorkspace = document.getElementById('menuOptWorkspace');
    const wsBadgeState = document.getElementById('wsBadgeState');
    const heroAttachmentChips = document.getElementById('heroAttachmentChips');
    const heroQueryInput = document.getElementById('heroQueryInput');

    let attachments = [];
    let isWsActive = false;

    if (!btnPlusMenu || !plusMenuPopover) return;

    // Toggle Plus Menu Popover
    btnPlusMenu.addEventListener('click', (e) => {
      e.stopPropagation();
      plusMenuPopover.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
      if (plusMenuPopover && !plusMenuPopover.classList.contains('hidden')) {
        if (!plusMenuPopover.contains(e.target) && !btnPlusMenu.contains(e.target)) {
          plusMenuPopover.classList.add('hidden');
        }
      }
    });

    if (btnAttachTrigger && heroFileInput) {
      btnAttachTrigger.addEventListener('click', () => {
        heroFileInput.click();
      });
    }

    if (menuOptFolder && heroFolderInput) {
      menuOptFolder.addEventListener('click', () => {
        plusMenuPopover.classList.add('hidden');
        heroFolderInput.click();
      });
    }

    if (menuOptDocument && heroFileInput) {
      menuOptDocument.addEventListener('click', () => {
        plusMenuPopover.classList.add('hidden');
        heroFileInput.click();
      });
    }

    if (menuOptWorkspace) {
      menuOptWorkspace.addEventListener('click', () => {
        plusMenuPopover.classList.add('hidden');
        isWsActive = !isWsActive;

        if (isWsActive) {
          if (wsBadgeState) wsBadgeState.classList.remove('hidden');
          menuOptWorkspace.classList.add('active');
          if (!attachments.some(a => a.id === 'ws-context')) {
            attachments.push({
              id: 'ws-context',
              name: 'Workspace Context (/idp-platform)',
              type: 'workspace'
            });
          }
          if (heroQueryInput) {
            heroQueryInput.placeholder = "Ask using active workspace context or paste schema...";
          }
        } else {
          if (wsBadgeState) wsBadgeState.classList.add('hidden');
          menuOptWorkspace.classList.remove('active');
          attachments = attachments.filter(a => a.id !== 'ws-context');
          if (heroQueryInput) {
            heroQueryInput.placeholder = "Ask anything about your document or paste schema...";
          }
        }
        renderChips();
      });
    }

    if (heroFileInput) {
      heroFileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          Array.from(e.target.files).forEach((file, idx) => {
            attachments.push({
              id: 'doc-' + Date.now() + '-' + idx,
              name: file.name,
              type: 'document'
            });
          });
          renderChips();
        }
      });
    }

    if (heroFolderInput) {
      heroFolderInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          const files = Array.from(e.target.files);
          const firstPath = files[0].webkitRelativePath || '';
          const folderName = firstPath.split('/')[0] || 'Selected Folder';
          attachments.push({
            id: 'folder-' + Date.now(),
            name: folderName + ' (' + files.length + ' files)',
            type: 'folder'
          });
          renderChips();
        }
      });
    }

    function renderChips() {
      if (!heroAttachmentChips) return;

      if (attachments.length === 0) {
        heroAttachmentChips.style.display = 'none';
        heroAttachmentChips.innerHTML = '';
        return;
      }

      heroAttachmentChips.style.display = 'flex';
      heroAttachmentChips.innerHTML = attachments.map(item => {
        const chipClass = item.type === 'workspace' ? 'chip-workspace' : (item.type === 'folder' ? 'chip-folder' : 'chip-document');
        const iconSvg = item.type === 'workspace'
          ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'
          : (item.type === 'folder'
            ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>'
            : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>');

        return `
          <div class="chip-item ${chipClass}">
            ${iconSvg}
            <span>${escapeHtml(item.name)}</span>
            <button type="button" class="chip-remove-btn" data-remove-id="${item.id}" title="Remove context">✕</button>
          </div>
        `;
      }).join('');

      heroAttachmentChips.querySelectorAll('.chip-remove-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const remId = e.currentTarget.getAttribute('data-remove-id');
          if (remId === 'ws-context') {
            isWsActive = false;
            if (wsBadgeState) wsBadgeState.classList.add('hidden');
            if (menuOptWorkspace) menuOptWorkspace.classList.remove('active');
            if (heroQueryInput) {
              heroQueryInput.placeholder = "Ask anything about your document or paste schema...";
            }
          }
          attachments = attachments.filter(a => a.id !== remId);
          renderChips();
        });
      });
    }

      function escapeHtml(str) {
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      }

      // ─── SUBMIT SEARCH & LAUNCH AI STUDIO ───
      function submitSearchToStudio(queryText = '') {
        const query = (queryText || (heroQueryInput ? heroQueryInput.value : '')).trim();
        
        // Switch to AI Studio
        if (typeof window.parsaShowView === 'function') {
          window.parsaShowView('studio');
        }

        // Forward query to AI Studio tester prompt or search filter
        setTimeout(() => {
          const testerPromptInput = document.getElementById('testerPromptInput');
          const searchChunksInput = document.getElementById('searchChunksInput');

          if (query) {
            if (testerPromptInput) {
              testerPromptInput.value = query;
            }
            if (searchChunksInput) {
              searchChunksInput.value = query;
              // Trigger search filter
              searchChunksInput.dispatchEvent(new Event('input', { bubbles: true }));
            }

            // If user attached custom files, notify
            if (attachments.length > 0) {
              const toastMsg = document.createElement('div');
              toastMsg.className = 'key-vault-toast';
              toastMsg.textContent = `⚡ Attached ${attachments.length} document context item(s). Running Unlimited-OCR 3B-MoE...`;
              document.body.appendChild(toastMsg);
              setTimeout(() => toastMsg.classList.add('visible'), 20);
              setTimeout(() => {
                toastMsg.classList.remove('visible');
                setTimeout(() => toastMsg.remove(), 300);
              }, 3200);
            }
          }
        }, 120);
      }

      const heroSearchForm = document.getElementById('heroSearchForm');
      if (heroSearchForm) {
        heroSearchForm.addEventListener('submit', (e) => {
          e.preventDefault();
          submitSearchToStudio();
        });
      }

      const btnHeroSearchSubmit = document.getElementById('btnHeroSearchSubmit');
      if (btnHeroSearchSubmit) {
        btnHeroSearchSubmit.addEventListener('click', (e) => {
          e.preventDefault();
          submitSearchToStudio();
        });
      }

      // ─── HERO PROMPT CHIPS INTERACTION ───
      document.querySelectorAll('.hero-prompt-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const preset = chip.getAttribute('data-preset');
          const query = chip.getAttribute('data-query');

          // Load corresponding preset in app.js if available
          if (preset && typeof window.parsaLoadPreset === 'function') {
            window.parsaLoadPreset(preset);
          }

          submitSearchToStudio(query);
        });
      });

      // ─── UPGRADE CREDITS MODAL ───
      const upgradeModal = document.getElementById('upgradeCreditsModal');
      const btnHeroUpgradeCredits = document.getElementById('btnHeroUpgradeCredits');
      const btnCloseUpgradeModal = document.getElementById('btnCloseUpgradeModal');
      const btnUpgradeOpenDemo = document.getElementById('btnUpgradeOpenDemo');

      if (btnHeroUpgradeCredits && upgradeModal) {
        btnHeroUpgradeCredits.addEventListener('click', () => {
          upgradeModal.classList.remove('hidden');
        });
      }

      if (btnCloseUpgradeModal && upgradeModal) {
        btnCloseUpgradeModal.addEventListener('click', () => {
          upgradeModal.classList.add('hidden');
        });
      }

      if (btnUpgradeOpenDemo && upgradeModal) {
        btnUpgradeOpenDemo.addEventListener('click', () => {
          upgradeModal.classList.add('hidden');
          if (typeof window.openParsaDemoModal === 'function') {
            window.openParsaDemoModal();
          }
        });
      }

      if (upgradeModal) {
        upgradeModal.addEventListener('click', (e) => {
          if (e.target === upgradeModal) upgradeModal.classList.add('hidden');
        });
      }
    })();

  })();




