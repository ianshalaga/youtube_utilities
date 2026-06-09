class OverlayTimer {

    constructor(display) {

        this.display = display
        this.time = 0
        this.running = false
        this.interval = null
        this.splits = []

    }

    format() {

        let h = Math.floor(this.time / 3600)
        let m = Math.floor((this.time % 3600) / 60)
        let s = this.time % 60

        return (
            String(h).padStart(2, '0') + ":" +
            String(m).padStart(2, '0') + ":" +
            String(s).padStart(2, '0')
        )

    }

    update() {

        this.time++
        this.display.textContent = this.format()

    }

    start() {

        if (this.running) return

        this.running = true
        this.interval = setInterval(() => this.update(), 1000)

    }

    pause() {

        this.running = false
        clearInterval(this.interval)

    }

    reset() {

        this.pause()
        this.time = 0
        this.display.textContent = "00:00:00"
        this.splits = []

    }

    split() {

        this.splits.push(this.time)
        spawnPaw()

    }

}

const timer = new OverlayTimer(
    document.getElementById("timer")
)

timer.start()

window.overlayTimer = timer

function spawnPaw() {

    const layer = document.getElementById("paw-layer")

    const paw = document.createElement("div")
    paw.className = "paw"
    paw.textContent = "🐾"

    paw.style.left = (Math.random() * 80 + 10) + "%"

    layer.appendChild(paw)

    setTimeout(() => paw.remove(), 1500)

}