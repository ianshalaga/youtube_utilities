const WIDTH = 1920;
const HEIGHT = 1080;

const LOOP = 20;
const COUNT = 450;

const container = document.getElementById("particles");

const particles = [];

for (let i = 0; i < COUNT; i++) {

    const p = document.createElement("div");

    p.className = "particle";

    container.appendChild(p);

    particles.push({

        element: p,

        phase: Math.random(),

        x0: Math.random() * WIDTH,

        scale: 0.3 + Math.random() * 1.2,

        amplitude: 40 + Math.random() * 140,

        frequency: 0.5 + Math.random() * 2.5,

        drift: Math.random() * Math.PI * 2,

        speed: 0.8 + Math.random() * 0.4

    });

}

const start = performance.now();

function getTime() {

    if (window.renderTime !== undefined)
        return window.renderTime;

    return (performance.now() - start) / 1000;

}

function flowX(tt, p) {

    return (

        Math.sin(
            tt * Math.PI * 2 * p.frequency +
            p.drift
        ) * p.amplitude +

        Math.sin(
            tt * Math.PI * 6 +
            p.drift * 0.7
        ) * 35 +

        Math.cos(
            tt * Math.PI * 10 +
            p.drift * 1.8
        ) * 18

    );

}

function render() {

    const t = (getTime() % LOOP) / LOOP;

    particles.forEach(p => {

        const tt = (t * p.speed + p.phase) % 1;

        const x = (
            p.x0 +
            flowX(tt, p) +
            WIDTH
        ) % WIDTH;

        const y =
            tt * (HEIGHT + 120) -
            60 +
            Math.sin(
                tt * Math.PI * 8 +
                p.drift
            ) * 12;

        const opacity =
            0.35 +
            0.65 *
            Math.sin(
                tt * Math.PI
            );

        const scale =
            p.scale *
            (
                0.8 +
                0.2 *
                Math.sin(
                    tt * Math.PI * 2 +
                    p.drift
                )
            );

        p.element.style.left =

            ((x + WIDTH) % WIDTH) +

            "px";

        p.element.style.top =

            y +

            "px";

        p.element.style.opacity = opacity;

        p.element.style.transform =
            `translate(-50%, -50%) scale(${scale})`;

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