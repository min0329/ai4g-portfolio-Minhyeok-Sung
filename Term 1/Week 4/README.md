# Term 1 - Week 4: Strings, Text & Files

---

## 1. Homework & workshop assignments -> [`homework/`](homework/)

**What was the assignment?**

**What did I hand in?**
_List the files, or link to them. Notebook exports, screenshots, scripts._

**What did I find difficult, and how did I solve it?**

### Checklist
- [ ] My workshop / homework files are in `homework/`
- [ ] Everything runs without errors, or I explained what does not and why

---


## 2. Hackathon prototype -> [`hackathon/`](hackathon/)

> Your tool and your SDG for this hackathon are announced at the **start of Friday's class**.
> Write them down here once you know them.

**Project title:** Amsterdam's Plastic Pollution -  A 25 second Climate Warning

**My pair partner:** Allan Hassan

**Tool we had to use:** ComfyUI

**SDG we had to address:** SDG 13.3 (Improving education and awareness-rasing about climate change.)

**What problem does it solve, and for whom?**
This project is aimed at people who live in Amsterdam, those who travel there daily, and the city’s policymakers who don’t realize how much plastic ends up as waste. Research from the AMS Institute and Wageningen University shows that about 3.7 plastic items fall into the IJ River every minute. That adds up to roughly 16 metric tons (about 1.9 million pieces) of plastic spilling into Amsterdam’s waterways each year. The film uses strong visuals to highlight this hidden environmental problem.
[AMS Institute, 2025]( https://www.ams-institute.org/news/amsterdams-plastic-soup-whats-polluting-our-waterways/ )


**What did you build?**
We made a 25 second short film made up of seven scenes. It starts with a clean, historic Amsterdam canal and then shows a movie‑style disaster where plastic waste piles up and overtakes the city. Anyone can look at our full ComfyUI workflow files (JSON), use the given seed and settings to recreate each frame and clip, and watch the finished video in MP4 format.

**Link to the live thing (if any):**
[Youtube](https://youtu.be/J9YZVRBtmEk) <br>
Workflow "image generation" `Week 4/hackathon/json_files/image(s)_generation.json` <br>
Workflow "images to video" Json file located in: `Week 4/hackathon/json_files/images_to_single_video.json`

**How do I run it?**
To reproduce or run this video generation pipeline in ComfyUI, follow these steps:
- Prerequisites & Hardware:
    - GPU's 16gb vram or more
    - 32 gb of system ram or more
    - At least 30gb of free space on your machine
    - Software ComfyUI installed with LTX-Video nodes and KJNodes (for transitions).
    - python installed
    - A virtual environment is created within comfyUI directory using the command:
    ```bash
    python -m venv venv
    ``` 

- Required Models:
    - Download and place the LTX-Video model weights into your ComfyUI models/diffusion_models/ directory.
    - Ensure standard VAE and text encoder models are placed in their respective ComfyUI directories.

- Loading the Workflow:
    - Launch ComfyUI.
    - Drag and drop the provided project workflow JSON files into two workflows inside the ComfyUI canvas to load the node structure.
        - Workflow 1: "image generation" `Week 4/hackathon/json_files/image(s)_generation.json` <br>
        - Workflow 2: "images to video" Json file located in: `Week 4/hackathon/json_files/images_to_single_video.json`
        > [!NOTE] You will find the used positive and negative prompts in this file `Week 4/hackathon/generation_prompts/image_generation.md`.

- Generating the Assets:
    - Start with the text-to-image workflow to generate the 7 base scene frames (representing the narrative progression from pristine Amsterdam canals to the climate disaster warning).
    - Save the generated frames sequentially into your project directory.
    > [!NOTE] We are generating the initial images in a seperate workflow due the limitation on development hardware. In the next workflow we will use this images as a startup point.

- Running Image-to-Video (I2V):
    - Switch to the LTX-Video I2V workflow nodes.
    - Feed each static scene image into the LTXVImgToVideo node, setting strength to ~0.70 and cfg to ~5.0 for dynamic motion control.
    - Input the corresponding descriptive positive/negative prompt for each scene (detailing camera movements like drone ascents and rolling destruction).
    > [!NOTE] You will find the used positive and negative prompts in this file `Week 4/hackathon/generation_prompts/video_generation.md`.

- Inside the load Audio node (Last third node) import the following audio track `Week 4/hackathon/music_track/leberch-strings-piano-249680.mp3`

- If you have followed all steps right so far, it will take you about 20 to 40 minutes to complete the video generation

**Alternativly** You can also the generated video directly by clicking this [link](https://youtu.be/J9YZVRBtmEk)


**Who did what?**
- Allan: Handled the conceptual problem definition, ComfyUI node setup, prompt engineering for all 7 scenes, image-to-video generation, and final video assembly.
- Min: Brainstormed the video idea with Allan, and worked on the statistical research on problem of plastic pollution and finding relevant sources. Worked on presentation slides.

**Ethical reflection - what are the risks of your tool? Who could it harm?**
AI‑made climate pictures can be very strong, but they can also trick people by turning real places into made up, scary scenes a huge ball of trash rolling over old canal houses. Our film uses these pictures as a symbol, not as real footage of something that actually happened, but some viewers might still think the dramatic AI images are a real prediction. To prevent this, we can mark the work in the README as “AI‑generated conceptual art.” and in the video.

### Checklist
- [ ] Prototype code (or export / workflow file) is in `hackathon/`
- [ ] This week's slides are in `hackathon/`
- [ ] The prototype actually runs, and I wrote down how to run it
- [ ] Ethical reflection written above

---

## 3. Presentation -> [`presentation/`](presentation/)

*Only fill this in for the week your group was selected to present. You need at least **one** of these across the whole term.*

- [ ] My group presented in this week
- [ ] Slides are in `presentation/`
- [ ] Proof of the live demo is in `presentation/` (recording, screenshots, or link)

**How did it go? What would I do differently next time?**

---

## 4. Reflection

**What is the most important thing I learned this week?**

**Where does this connect to "AI for Good"?**
_One concrete link to ethics, sustainability or social impact._
