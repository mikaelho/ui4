ui4 - Python UI library

Create cross-platform UIs easily in Python.

![Python tests](https://github.com/mikaelho/ui4/actions/workflows/ui4.yaml/badge.svg) ![Javascript tests](https://github.com/mikaelho/ui4/actions/workflows/ui4-js.yaml/badge.svg)

Roadmap
-------

- [x] Anchor minmax, portrait/landscape, high/wide
- [x] Event loop basics
- [x] JS tests
- [x] Run and serve
- [ ] Grid/flow
- [ ] Basic demo
- [ ] Widget demo
- [ ] UI tester
- [ ] Sound
- [ ] Deployment story
- [ ] Authentication support
- [ ] Thread safety
- [ ] FastAPI backend
- [ ] WebSocket/SSE

Widget coverage
---------------

- [x] View
- [x] Button
- [x] Textfield
- [x] Table
- [x] Switch
- [ ] Form
- [ ] Image
- [ ] Card
- [ ] Navigator
- [x] Slider

Small features
--------------

- [x] Release opposite anchor if needed
- [x] scrollable
- [x] Event loop - wait, direction, iterations
- [ ] Dark mode
- [ ] Event loop - yield wait
- [ ] Event loop - pause, play
- [ ] Textfield immediate change
- [ ] clip_to_bounds
- [ ] yield fetch
- [ ] Gradients
- [ ] Transforms
- [ ] introduce
- [x] release is dirty


Similar projects
----------------

* JustPy - https://justpy.io
* PyWebIO - https://pywebio.readthedocs.io/en/latest/
* PyEverywhere - https://github.com/kollivier/pyeverywhere

Development installation notes
------------------------------

- Selenium/ChromeDriver on Mac
  - brew install chromedriver

- Selenium/Safari on Mac
  - `safaridriver --enable` needs to be run once
    - In Safari, Develop > Allow Remote Automation
    - Start `safaridriver -p 0` and stop it to verify operation
  
To explore
---------------------

- mkdocs
- mktestdocs