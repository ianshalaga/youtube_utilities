const LOOP = 20;

const particles = document.getElementById("particles");
const gears = document.getElementById("gears");
const svg = document.getElementById("magic-circle");

const PARTICLE_COUNT = 120;

const particleObjects = [];

/*--------------------------
CREAR PARTÍCULAS
--------------------------*/

for (let i = 0; i < PARTICLE_COUNT; i++) {

    const p = document.createElement("div");

    p.className = "particle";

    particles.appendChild(p);

    particleObjects.push({

        element: p,

        phase: i / PARTICLE_COUNT

    });

}

/*--------------------------
ENGRANAJES
--------------------------*/

function createGear(size, x, y) {

    const g = document.createElement("div");

    g.className = "gear";

    g.style.width = size + "px";
    g.style.height = size + "px";

    g.style.left = x + "px";
    g.style.top = y + "px";

    gears.appendChild(g);

    return g;

}

const gearA = createGear(320, 180, 180);
const gearB = createGear(220, 1450, 620);
const gearC = createGear(160, 1450, 120);

/*--------------------------
TIEMPO
--------------------------*/

const start = performance.now();

function getTime() {

    if (window.renderTime !== undefined) {

        return window.renderTime;

    }

    return (performance.now() - start) / 1000;

}

/*--------------------------
RENDER
--------------------------*/

function render() {

    const elapsed = getTime();

    const t = (elapsed % LOOP) / LOOP;

    const angle = t * 360;

    svg.style.transform =
        `translate(-50%,-50%) rotate(${angle}deg)`;

    gearA.style.transform =
        `rotate(${angle * 0.7}deg)`;

    gearB.style.transform =
        `rotate(${-angle}deg)`;

    gearC.style.transform =
        `rotate(${angle * 1.8}deg)`;

    particleObjects.forEach(p => {

        const tt = (t + p.phase) % 1;

        const x = 1920 * tt;

        const y =
            540 +
            Math.sin(tt * Math.PI * 6) * 260;

        p.element.style.left = x + "px";

        p.element.style.top = y + "px";

        p.element.style.opacity =
            0.25 + 0.75 * Math.sin(tt * Math.PI);

    });

}

/*--------------------------
ANIMACIÓN EN TIEMPO REAL
--------------------------*/

function animationLoop() {

    render();

    requestAnimationFrame(animationLoop);

}

/*--------------------------
INICIO
--------------------------*/

if (window.renderTime === undefined) {

    animationLoop();

}

window.render = render;