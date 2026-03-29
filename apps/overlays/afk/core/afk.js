class AFKOverlay {

    constructor(duration = 5000) {

        this.duration = duration
        this.running = false

    }

    start() {

        if (this.running) return

        this.running = true
        this.loop()

    }

    loop() {

        if (!this.running) return

        this.animateCycle()

        setTimeout(() => {
            this.loop()
        }, this.duration)

    }

    animateCycle() {

        const hg = document.getElementById("hourglass")

        hg.classList.remove("flip")
        void hg.offsetWidth
        hg.classList.add("flip")

        spawnParticles()

    }

    stop() {

        this.running = false

    }

}

const afk = new AFKOverlay(5000)

afk.start()

window.afkOverlay = afk

/* PARTICLES */

function spawnParticles() {

    const container = document.getElementById("particles")

    for (let i = 0; i < 6; i++) {

        const p = document.createElement("div")
        p.className = "particle"

        p.style.left = Math.random() * 100 + "%"
        p.style.animationDelay = Math.random() + "s"

        container.appendChild(p)

        setTimeout(() => p.remove(), 2000)

    }

}