class AFKOverlay {

    constructor() {

        this.running = false

    }

    start() {

        if (this.running) return

        this.running = true
        this.loop()

    }

    loop() {

        if (!this.running) return

        spawnParticle()

        requestAnimationFrame(() => this.loop())

    }

    stop() {
        this.running = false
    }

}

const afk = new AFKOverlay()
afk.start()

window.afkOverlay = afk

/* PARTICLES */

function spawnParticle() {

    const container = document.getElementById("global-particles")

    const p = document.createElement("div")
    p.className = "particle"

    /* POSICIÓN INICIAL ALEATORIA */
    p.style.left = Math.random() * 1920 + "px"
    p.style.top = "1080px"

    /* DESTINO ALEATORIO */
    const endX = Math.random() * 1920
    const duration = 3000 + Math.random() * 2000

    p.animate([
        {
            transform: "translate(0,0)",
            opacity: 0
        },
        {
            opacity: 1
        },
        {
            transform: `translate(${endX - parseFloat(p.style.left)}px,-1200px)`,
            opacity: 0
        }
    ], {
        duration: duration,
        easing: "ease-out"
    })

    container.appendChild(p)

    setTimeout(() => p.remove(), duration)

}