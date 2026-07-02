const LOOP = 20;

const particles = document.getElementById("particles");
const gears = document.getElementById("gears");
const svg = document.getElementById("magic-circle");

const STAR_COUNT = 180;

const stars = [];

for (let i = 0; i < STAR_COUNT; i++) {

    const s = document.createElement("div");

    s.className = "particle";

    particles.appendChild(s);

    stars.push({

        element: s,

        phase: i / STAR_COUNT,

        lane: i % 7

    });

}

function createRing(size, x, y) {

    const ring = document.createElement("div");

    ring.className = "gear";

    ring.style.width = size + "px";
    ring.style.height = size + "px";

    ring.style.left = x + "px";
    ring.style.top = y + "px";

    ring.style.borderRadius = "50%";
    ring.style.border = "10px solid #FFD34A";
    ring.style.boxShadow =
        "0 0 20px #FFD34A";

    gears.appendChild(ring);

    return ring;

}

const ringA = createRing(240, 220, 140);
const ringB = createRing(170, 1470, 180);
const ringC = createRing(300, 1360, 620);

const start = performance.now();

function getTime() {

    if (window.renderTime !== undefined)

        return window.renderTime;

    return (performance.now() - start) / 1000;

}

function render() {

    const elapsed = getTime();

    const t = (elapsed % LOOP) / LOOP;

    const angle = t * 360;

    svg.style.transform =
        `translate(-50%,-50%) rotate(${-angle * .15}deg)`;

    ringA.style.transform =
        `rotate(${angle}deg)`;

    ringB.style.transform =
        `rotate(${-angle * 1.5}deg)`;

    ringC.style.transform =
        `rotate(${angle * .6}deg)`;

    stars.forEach(star => {

        const tt = (t + star.phase) % 1;

        const x = -120 + tt * 2160;

        const y =

            120 +

            star.lane * 140 +

            Math.sin(tt * Math.PI * 2 + star.lane) * 40;

        const scale =

            .4 +

            .8 * Math.sin(tt * Math.PI);

        star.element.style.left = x + "px";

        star.element.style.top = y + "px";

        star.element.style.transform =

            `scale(${scale})`;

        star.element.style.opacity =

            .3 +

            .7 * Math.sin(tt * Math.PI);

    });

}

function animationLoop() {

    render();

    requestAnimationFrame(animationLoop);

}

if (window.renderTime === undefined) {

    animationLoop();

}

window.render = render;