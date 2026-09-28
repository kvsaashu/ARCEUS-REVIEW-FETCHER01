/**
 * ARCEUS REVIEW FETCHER — 3D WebGL Scene & Visual Engine
 * Powered by Three.js (r128)
 * 
 * Features:
 * - Rotating Arceus Polyhedral Core Crystal (Gold & Cyber-Cyan/Emerald)
 * - Orbital Celestial Energy Rings
 * - Infinite 3D Starfield & Particle Dust with Z-Depth
 * - Smooth Mouse Parallax & Dynamic Lighting
 * - Battery-conscious Visibility Lifecycle & 3D Toggle
 */

(function () {
  'use strict';

  // State
  let is3dEnabled = localStorage.getItem('arceus_3d_mode') !== 'false';
  let scene, camera, renderer;
  let heroGroup, outerCrystal, innerCore, ring1, ring2, particlesMesh;
  let mouseX = 0, mouseY = 0;
  let targetRotationX = 0, targetRotationY = 0;
  let targetCameraX = 0, targetCameraY = 0;
  let animFrameId = null;
  let isTabVisible = true;

  const canvas = document.getElementById('bg3dCanvas');
  if (!canvas) return;

  // Check WebGL availability
  function isWebGLAvailable() {
    try {
      const testCanvas = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl')));
    } catch (e) {
      return false;
    }
  }

  if (!window.THREE || !isWebGLAvailable()) {
    console.warn('[Arceus 3D] WebGL or Three.js not available. Running in 2D mode.');
    if (canvas) canvas.style.display = 'none';
    return;
  }

  function initScene() {
    // 1. Scene & Camera
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x06090e, 0.0018);

    const width = window.innerWidth;
    const height = window.innerHeight;
    camera = new THREE.PerspectiveCamera(45, width / height, 1, 2000);
    camera.position.z = 700;

    // 2. Renderer
    renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, window.innerWidth < 768 ? 1.5 : 2));
    renderer.setSize(width, height);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    // Primary Golden Light (top-right)
    const goldLight = new THREE.PointLight(0xf59e0b, 2.8, 1200);
    goldLight.position.set(300, 300, 400);
    scene.add(goldLight);

    // Cyber Cyan Accent Light (bottom-left)
    const cyanLight = new THREE.PointLight(0x06b6d4, 2.2, 1000);
    cyanLight.position.set(-350, -250, 300);
    scene.add(cyanLight);

    // Emerald Rim Light (back-top)
    const emeraldLight = new THREE.DirectionalLight(0x10b981, 1.2);
    emeraldLight.position.set(0, 400, -300);
    scene.add(emeraldLight);

    // 4. Arceus Hero Core Object (Parent Group)
    heroGroup = new THREE.Group();
    // Position slightly to the right side so it frames the dashboard gracefully
    heroGroup.position.set(width > 1200 ? 320 : 0, 0, 0);
    scene.add(heroGroup);

    // A. Outer Golden Faceted Crystal (Icosahedron)
    const outerGeo = new THREE.IcosahedronGeometry(90, 0);
    const outerMat = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      metalness: 0.85,
      roughness: 0.18,
      wireframe: false,
      transparent: true,
      opacity: 0.72,
      envMapIntensity: 1.0
    });
    outerCrystal = new THREE.Mesh(outerGeo, outerMat);
    heroGroup.add(outerCrystal);

    // Golden Wireframe Cage Overlay
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0xfef3c7,
      wireframe: true,
      transparent: true,
      opacity: 0.35
    });
    const wireMesh = new THREE.Mesh(outerGeo, wireMat);
    wireMesh.scale.set(1.02, 1.02, 1.02);
    outerCrystal.add(wireMesh);

    // B. Inner Glowing Energy Core (Octahedron)
    const innerGeo = new THREE.OctahedronGeometry(45, 0);
    const innerMat = new THREE.MeshStandardMaterial({
      color: 0x06b6d4,
      emissive: 0x0891b2,
      emissiveIntensity: 0.6,
      metalness: 0.3,
      roughness: 0.1,
      transparent: true,
      opacity: 0.85
    });
    innerCore = new THREE.Mesh(innerGeo, innerMat);
    heroGroup.add(innerCore);

    // C. Orbital Celestial Energy Ring 1 (Gold)
    const ring1Geo = new THREE.TorusGeometry(150, 2.2, 16, 100);
    const ring1Mat = new THREE.MeshStandardMaterial({
      color: 0xfbbf24,
      metalness: 0.9,
      roughness: 0.1,
      emissive: 0xd97706,
      emissiveIntensity: 0.3
    });
    ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
    ring1.rotation.x = Math.PI / 3;
    ring1.rotation.y = Math.PI / 6;
    heroGroup.add(ring1);

    // D. Orbital Celestial Energy Ring 2 (Cyan/Emerald)
    const ring2Geo = new THREE.TorusGeometry(185, 1.6, 16, 100);
    const ring2Mat = new THREE.MeshStandardMaterial({
      color: 0x34d399,
      metalness: 0.8,
      roughness: 0.2,
      emissive: 0x059669,
      emissiveIntensity: 0.25
    });
    ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2.rotation.x = -Math.PI / 4;
    ring2.rotation.z = Math.PI / 4;
    heroGroup.add(ring2);

    // 5. 3D Particle Cloud / Cyber Starfield (1200 Particles)
    const particleCount = 1200;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const colorGold = new THREE.Color(0xf59e0b);
    const colorCyan = new THREE.Color(0x06b6d4);
    const colorEmerald = new THREE.Color(0x10b981);
    const colorWhite = new THREE.Color(0xf8fafc);

    for (let i = 0; i < particleCount; i++) {
      // Spread across 3D space with deep Z
      positions[i * 3] = (Math.random() - 0.5) * 2200;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 1600;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 1200;

      // Color distribution: gold (40%), cyan (30%), emerald (15%), white (15%)
      const rand = Math.random();
      let col = colorGold;
      if (rand > 0.85) col = colorWhite;
      else if (rand > 0.7) col = colorEmerald;
      else if (rand > 0.4) col = colorCyan;

      colors[i * 3] = col.r;
      colors[i * 3 + 1] = col.g;
      colors[i * 3 + 2] = col.b;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Particle Material
    const particleMat = new THREE.PointsMaterial({
      size: 3.2,
      vertexColors: true,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending
    });

    particlesMesh = new THREE.Points(particleGeo, particleMat);
    scene.add(particlesMesh);

    // Initial positioning
    updateCanvasSize();
  }

  function updateCanvasSize() {
    if (!renderer || !camera) return;
    const width = window.innerWidth;
    const height = window.innerHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, width < 768 ? 1.5 : 2));
    renderer.setSize(width, height);

    // Adjust hero position for responsiveness
    if (heroGroup) {
      if (width < 768) {
        // Mobile: center and scale down slightly
        heroGroup.position.set(0, 50, -100);
        heroGroup.scale.set(0.7, 0.7, 0.7);
      } else if (width < 1200) {
        // Tablet / Small Laptop
        heroGroup.position.set(160, 0, 0);
        heroGroup.scale.set(0.85, 0.85, 0.85);
      } else {
        // Desktop
        heroGroup.position.set(360, 20, 0);
        heroGroup.scale.set(1.0, 1.0, 1.0);
      }
    }
  }

  // Animation Loop with Smooth Interpolation (lerp)
  let clock = new THREE.Clock();

  function animate() {
    if (!is3dEnabled || !isTabVisible) {
      animFrameId = null;
      return;
    }

    animFrameId = requestAnimationFrame(animate);

    const delta = clock.getDelta();
    const elapsedTime = clock.getElapsedTime();

    // 1. Crystal Rotations
    if (outerCrystal) {
      outerCrystal.rotation.x += delta * 0.28;
      outerCrystal.rotation.y += delta * 0.42;
    }

    // Inner core counter-rotates and breathes gently
    if (innerCore) {
      innerCore.rotation.x -= delta * 0.5;
      innerCore.rotation.z += delta * 0.35;
      const breathe = 1 + Math.sin(elapsedTime * 2.5) * 0.08;
      innerCore.scale.set(breathe, breathe, breathe);
    }

    // Rings rotation
    if (ring1) {
      ring1.rotation.z += delta * 0.3;
      ring1.rotation.x += delta * 0.15;
    }
    if (ring2) {
      ring2.rotation.z -= delta * 0.22;
      ring2.rotation.y += delta * 0.2;
    }

    // 2. Slow particle cloud drift
    if (particlesMesh) {
      particlesMesh.rotation.y = elapsedTime * 0.025;
      particlesMesh.rotation.x = Math.sin(elapsedTime * 0.015) * 0.1;
    }

    // 3. Mouse Parallax Reaction (Camera & Hero Sway)
    targetCameraX = mouseX * 80;
    targetCameraY = mouseY * 60;
    camera.position.x += (targetCameraX - camera.position.x) * 0.05;
    camera.position.y += (-targetCameraY - camera.position.y) * 0.05;
    camera.lookAt(0, 0, 0);

    // Hero tilts slightly towards cursor
    if (heroGroup) {
      targetRotationX = mouseY * 0.35;
      targetRotationY = mouseX * 0.45;
      heroGroup.rotation.x += (targetRotationX - heroGroup.rotation.x) * 0.06;
      heroGroup.rotation.y += (targetRotationY - heroGroup.rotation.y) * 0.06;
    }

    renderer.render(scene, camera);
  }

  // Mouse / Pointer Parallax Listeners
  window.addEventListener('mousemove', (e) => {
    // Normalized between -1 and 1
    mouseX = (e.clientX / window.innerWidth) * 2 - 1;
    mouseY = (e.clientY / window.innerHeight) * 2 - 1;
  }, { passive: true });

  // Touch Parallax for Mobile Devices
  window.addEventListener('touchmove', (e) => {
    if (e.touches.length > 0) {
      const touch = e.touches[0];
      mouseX = (touch.clientX / window.innerWidth) * 2 - 1;
      mouseY = (touch.clientY / window.innerHeight) * 2 - 1;
    }
  }, { passive: true });

  // Window Resize
  window.addEventListener('resize', updateCanvasSize);

  // Tab Visibility (Pause loop when tab hidden to save CPU/GPU)
  document.addEventListener('visibilitychange', () => {
    isTabVisible = !document.hidden;
    if (isTabVisible && is3dEnabled && !animFrameId) {
      clock.start();
      animate();
    }
  });

  // Start 3D Engine
  initScene();
  if (is3dEnabled) {
    animate();
  } else {
    canvas.style.opacity = '0';
  }

  // ==========================================================================
  // 3D CARD TILT & DYNAMIC SPECULAR GLARE PHYSICS
  // ==========================================================================
  const activeTiltCards = new Set();

  function initCardTilt(card, options = {}) {
    if (!card || card._tiltInitialized) return;
    card._tiltInitialized = true;
    activeTiltCards.add(card);

    const maxTilt = options.maxTilt !== undefined ? options.maxTilt : 9;
    const scale = options.scale !== undefined ? options.scale : 1.018;
    const perspective = options.perspective !== undefined ? options.perspective : 1000;

    card.classList.add('tilt-card');

    // Create glare overlay if not present
    let glare = card.querySelector(':scope > .card-glare');
    if (!glare) {
      glare = document.createElement('div');
      glare.className = 'card-glare';
      card.appendChild(glare);
    }

    let isHovered = false;
    let rafId = null;
    let currentRotateX = 0, currentRotateY = 0;
    let targetRotateX = 0, targetRotateY = 0;

    function renderTilt() {
      if (!isHovered && Math.abs(currentRotateX) < 0.05 && Math.abs(currentRotateY) < 0.05) {
        card.style.transform = '';
        card.style.removeProperty('--glare-opacity');
        rafId = null;
        return;
      }

      currentRotateX += (targetRotateX - currentRotateX) * 0.16;
      currentRotateY += (targetRotateY - currentRotateY) * 0.16;

      if (is3dEnabled) {
        const curScale = isHovered ? scale : 1;
        card.style.transform = `perspective(${perspective}px) rotateX(${currentRotateX.toFixed(2)}deg) rotateY(${currentRotateY.toFixed(2)}deg) scale3d(${curScale}, ${curScale}, ${curScale})`;
      } else {
        card.style.transform = '';
      }

      rafId = requestAnimationFrame(renderTilt);
    }

    card.addEventListener('pointerenter', (e) => {
      if (!is3dEnabled || (e.pointerType && e.pointerType !== 'mouse')) return;
      isHovered = true;
      card.style.transition = 'none';
      card.style.setProperty('--glare-opacity', '0.65');
      if (!rafId) rafId = requestAnimationFrame(renderTilt);
    });

    card.addEventListener('pointermove', (e) => {
      if (!is3dEnabled || (e.pointerType && e.pointerType !== 'mouse')) return;
      const rect = card.getBoundingClientRect();
      if (!rect.width || !rect.height) return;

      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const normX = (x / rect.width) * 2 - 1;
      const normY = (y / rect.height) * 2 - 1;

      targetRotateX = -normY * maxTilt;
      targetRotateY = normX * maxTilt;

      card.style.setProperty('--glare-x', `${x.toFixed(1)}px`);
      card.style.setProperty('--glare-y', `${y.toFixed(1)}px`);

      if (!rafId) rafId = requestAnimationFrame(renderTilt);
    });

    card.addEventListener('pointerleave', () => {
      isHovered = false;
      targetRotateX = 0;
      targetRotateY = 0;
      card.style.transition = 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease';
      card.style.setProperty('--glare-opacity', '0');
    });
  }

  function attachTiltToAllCards() {
    const cards = document.querySelectorAll(
      '.metric-card, .sidebar-panel, .target-banner, .batch-summary-card, .batch-target-card, .feed-toolbar, .modal-card, .review-card, .brand'
    );
    cards.forEach((card) => {
      const isSidebar = card.classList.contains('sidebar-panel');
      const isBrand = card.classList.contains('brand');
      const isReview = card.classList.contains('review-card');
      initCardTilt(card, {
        maxTilt: isSidebar ? 4 : isBrand ? 7 : isReview ? 9 : 11,
        scale: isSidebar ? 1.006 : 1.018
      });
    });
  }

  function resetAllCardTilts() {
    activeTiltCards.forEach((card) => {
      card.style.transform = '';
      card.style.setProperty('--glare-opacity', '0');
    });
  }

  // Expose Global 3D Mode Toggle for UI
  window.toggle3dMode = function () {
    is3dEnabled = !is3dEnabled;
    localStorage.setItem('arceus_3d_mode', is3dEnabled ? 'true' : 'false');

    const toggleBtn = document.getElementById('toggle3dBtn');
    if (toggleBtn) {
      toggleBtn.innerHTML = is3dEnabled ? '✨ 3D Mode: ON' : '🌑 3D Mode: OFF';
      toggleBtn.classList.toggle('active', is3dEnabled);
    }

    if (canvas) {
      canvas.style.transition = 'opacity 0.5s ease';
      canvas.style.opacity = is3dEnabled ? '0.85' : '0';
    }

    if (!is3dEnabled) {
      resetAllCardTilts();
    } else {
      attachTiltToAllCards();
      if (!animFrameId) {
        clock.start();
        animate();
      }
    }
  };

  // Expose init hook for dynamic components
  window.initArceus3DTilt = attachTiltToAllCards;

  // Sync Toggle Button state on DOM ready & attach Tilt
  document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle3dBtn');
    if (toggleBtn) {
      toggleBtn.innerHTML = is3dEnabled ? '✨ 3D Mode: ON' : '🌑 3D Mode: OFF';
      toggleBtn.classList.toggle('active', is3dEnabled);
      toggleBtn.addEventListener('click', window.toggle3dMode);
    }

    // Attach 3D tilt to cards
    attachTiltToAllCards();

    // Observe dynamic additions (reviews, batch cards, modals)
    const observer = new MutationObserver(() => {
      attachTiltToAllCards();
    });

    const reviewsFeed = document.getElementById('reviewsFeed');
    if (reviewsFeed) observer.observe(reviewsFeed, { childList: true, subtree: true });

    const batchPanel = document.getElementById('batchPanel');
    if (batchPanel) observer.observe(batchPanel, { childList: true, subtree: true });
  });

  console.log('[Arceus 3D] WebGL Background & 3D Card Tilt Engine initialized successfully 💎');
})();

