const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");

const WIDTH = 1920;
const HEIGHT = 1080;

const FPS = 60;
const DURATION = 20;

const TOTAL_FRAMES = FPS * DURATION;

const OUTPUT_DIR = path.join(
    __dirname,
    "guilty_gear"
);

(async () => {

    if (!fs.existsSync(OUTPUT_DIR)) {

        fs.mkdirSync(
            OUTPUT_DIR,
            {
                recursive: true
            }
        );

    }

    const browser = await puppeteer.launch({

        headless: true,

        defaultViewport: {

            width: WIDTH,
            height: HEIGHT

        }

    });

    const page = await browser.newPage();

    await page.goto(

        "http://localhost:8080/applications/overlays/backgrounds/guilty_gear/index.html",

        {

            waitUntil: "networkidle0"

        }

    );

    console.log();

    console.log("==========");

    console.log("RENDER");

    console.log("==========");

    console.log();

    for (let frame = 0; frame < TOTAL_FRAMES; frame++) {

        const seconds = frame / FPS;

        await page.evaluate((time) => {

            window.renderTime = time;

            render();

        }, seconds);

        const filename =
            "frame_" +
            String(frame).padStart(4, "0") +
            ".png";

        await page.screenshot({

            path: path.join(
                OUTPUT_DIR,
                filename
            )

        });

        process.stdout.write(

            "\rFrame " +

            (frame + 1) +

            " / " +

            TOTAL_FRAMES

        );

    }

    console.log();

    console.log();

    console.log("Render finalizado.");

    await browser.close();

})();