[![CI build](https://github.com/HurricanGame/Hurrican/actions/workflows/build.yml/badge.svg)](https://github.com/HurricanGame/Hurrican/actions/workflows/build.yml)

A fork of Hurrican, freeware jump and shoot game created by Poke53280, with SDL2 enabled by default, support for libopenmpt and CRT simulation.
Also uses XDG compliant data/config paths on UNIX.
Additional userlevels from http://turricanforever.de included.

Original code by Eiswuxe (Poke53280) [[Winterworks](https://www.winterworks.de/project/hurrican/)]  
Further work by [Pickle136](https://sourceforge.net/projects/hurrican/), Stefan Schmidt ([thrimbor](https://github.com/thrimbor/Hurrican)) and Leandro Nini ([drfiemost](https://github.com/drfiemost/Hurrican))  
CRT simulation partially based on [CRT effect - Shadertoy, Unity](https://luka712.github.io/2018/07/21/CRT-effect-Shadertoy-Unity/) article from luka712's blog

![screenshot](https://github.com/HurricanGame/Hurrican/wiki/images/level1.png)

---

### Dependencies

The code depends on SDL2 (or the old deprecated SDL) with the image and mixer components, and libepoxy.
Optionally libopenmpt can be used for the music in place of the standard from SDL_mixer (see below).
A compiler with c++17 support is required.

### Building

The code can be built using cmake (tested on Linux and MinGW)

    git clone --recurse-submodules https://github.com/HurricanGame/Hurrican.git
    cd Hurrican/Hurrican
    mkdir build && cd build
    cmake -DCMAKE_BUILD_TYPE=Release ..
    cmake --build .

Building for PI 5

    sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libepoxy-dev libglm-dev
    git clone --recurse-submodules git@github.com:fruit-bat/HurricanGame.git
    cd HurricanGame/Hurrican
    mkdir build && cd build
    cmake -DCMAKE_BUILD_TYPE=Release -DRENDERER=GL2  ..
    cmake --build .
    cd ..
    ./build/hurrican -NV --colorbleed

The Pi 5 delivers a smooth 400fps and the graphics look good. Frame-sync is not working properly and results in a 30fps display; advice appreciated!

Building on Ubuntu 24.04

Install the same packages as above, then point cmake at the system SDL2 library explicitly:

    cd HurricanGame/Hurrican
    mkdir build && cd build
    SDL2_LIBRARIES="/lib/x86_64-linux-gnu/libSDL2-2.0.so.0" cmake -DCMAKE_BUILD_TYPE=Release -DRENDERER=GL2 ..
    cmake --build .



The following build options are available:

Predefined platforms
* -DPLATFORM=<RPI|GCW|RDU|RDU2|PANDORA> : Compile for the specified platform, setting the correct options

OpenGL Options
* -DRENDERER=GL1          : Use the OpenGL 1.X code (fixed pipline)
* -DRENDERER=GLES1        : Use the OpenGL 1.X code with ES compatible
* -DRENDERER=GL2          : Use the OpenGL 2.0 code (programable pipline) [this is the default if not specified]
* -DRENDERER=GLES2        : Use the OpenGL 2.0 code with ES compatible
* -DRENDERER=GL3          : Use the OpenGL 3.0 code (programable pipline)
* -DRENDERER=GLES3        : Use the OpenGL 3.0 code with ES compatible
* -DFBO=ON                : Add FBO support, allow screen to be scaled to arbitrary dimensions, available only with GL2 or GL3 and enabled by default
* -DDEFAULT_SCREENBPP=<16|24|32> : Set the default screen depth, 32 if not specified

Sound
* -DOPENMPT=ON            : Use the libopenmpt code for music (SDL2_mixer uses libmodplug while SDL_mixer uses the lower quality mikmod engine)

Generic
* -DFAST_RANDOM=OFF             : Use standard C random function in place of the fast [LCG](https://en.wikipedia.org/wiki/Linear_congruential_generator)
* -DFAST_TRIG=ON                : Use fast approximation for trigonometric functions
* -DDISABLE_EXCEPTIONS=ON       : Disable exception handling to reduce binary size
* -DUSE_PRECOMPILED_HEADERS=ON  : Enable pre-compiled headers for better compile time

Debug
* -DDISABLE_MEMPOOLING=ON : Bypass pooled memory manager
* -DCMAKE_BUILD_TYPE=<Asan|Ubsan>: Enable the Address or Undefined Behaviour Sanitizer

### Running

To launch Hurrican, go back under the Hurrican folder

    cd ..
    ./build/hurrican

To see the available command line options use the `--help` argument

    ./build/hurrican --help

or check online at https://github.com/HurricanGame/Hurrican/wiki/Help

### Default controls

The default keyboard layout avoids Ctrl and Alt, because Ctrl+Alt+Arrow is a window-manager shortcut
(workspace switching) on many Linux desktops and was being intercepted during play.

| Action        | Player 1    | Player 2      |
|---------------|-------------|---------------|
| Left / Right  | A / D       | Left / Right  |
| Look up       | W           | Up            |
| Duck          | S           | Down          |
| Jump          | Space       | Numpad 0      |
| Fire          | Right Shift | Numpad 1      |
| Beam          | Enter       | Numpad 2      |
| Powerline     | Left Shift  | Numpad 3      |
| Grenade       | E           | Numpad 4      |
| Smartbomb     | R           | Numpad 5      |
| Weapon cycle  | Q           | Numpad 6      |

Defaults only apply when there is no saved configuration. If you played an earlier version, use the
reset-to-defaults option in the controls menu, or delete `~/.config/hurrican/Hurrican.cfg`.

### High-resolution mode

The game logic works in 640x480, and by default every frame is drawn into a 640x480 buffer that is then
stretched to the screen. With `--renderscale` the buffer is made larger (the game still positions
everything in 640x480 terms), so rotated and scaled sprites, smooth movement and effects are drawn
at the higher resolution:

    ./build/hurrican --renderscale 2        # fullscreen, rendered at 1280x960
    ./build/hurrican -W --renderscale 2     # 1280x960 window

Valid values are 1 to 4 (default 1). This needs the GL2 or GL3 renderer with FBO support (the default);
if the larger buffer can't be created the game falls back to 1.

#### High-resolution textures

When the render scale is above 1, textures are loaded from `data/textures/hd/` if a copy exists there,
falling back to the original in `data/textures/`. The folder isn't part of the repository; generate it
with the upscaling script (needs Python 3 with Pillow and NumPy, e.g. `sudo apt-get install python3-pil python3-numpy`):

    cd HurricanGame/Hurrican
    tools/upscale_textures.py

This writes 2x copies of all textures (about 120 MB, a couple of minutes). By default it uses Lanczos
resizing, which smooths jagged edges but can't add detail. For better results pass an AI upscaler such
as [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan); `{in}`, `{out}` and `{scale}`
are substituted:

    tools/upscale_textures.py --force --command "realesrgan-ncnn-vulkan -i {in} -o {out} -s 4 -t 64 -n realesrgan-x4plus -m /path/to/realesrgan/models"

`realesrgan-x4plus` suits Hurrican's pre-rendered art best; `realesr-animevideov3` is much faster but softer.
`-s 4` is required by the x4plus models (the script resizes the result down to 2x). On integrated GPUs keep
`-t 64` (tile size): larger tiles can exceed the kernel's GPU timeout, causing a GPU reset and black output,
which the script now reports as a failure.

Other options: `--scale N` for a different factor (match it to `--renderscale`), `--src`/`--dst` for
other folders, and `--force` to overwrite existing files. Transparency is preserved, and level tilesets
are upscaled tile by tile so neighbouring tiles on the sheet don't bleed into each other's edges.

e.g.
```
cd ~/Downloads
wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip
unzip realesrgan-ncnn-vulkan-20220424-ubuntu.zip -d realesrgan
chmod +x realesrgan/realesrgan-ncnn-vulkan
```
then
```
cd ~/HurricanGame/Hurrican
RE=~/Downloads/realesrgan
tools/upscale_textures.py --force --command "$RE/realesrgan-ncnn-vulkan -i {in} -o {out} -s 4 -t 64 -n realesrgan-x4plus -m $RE/models"
```
