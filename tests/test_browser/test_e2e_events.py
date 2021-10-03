# from ui4 import Button
# from ui4 import Label
#
#
# def test_button_on_top_of_a_button(get_app, views, driver, expect):
#     def setup(root):
#         views.button1 = Button(text='Click me 1', dock=root.center, was_clicked = False)
#         views.button2 = Button(text='Click me 2', dock=views.button1.center, was_clicked = False)
#
#         @views.button1
#         def on_click(view):
#             view.was_clicked = True
#
#         @views.button2
#         def on_click(view):
#             view.was_clicked = True
#
#     with get_app(setup):
#         driver.find_element_by_id(views.button2.id).click()
#         assert expect(lambda: views.button2.was_clicked)
#         assert expect(lambda: not views.button1.was_clicked)
#
#
# def test_label_on_top_of_button(get_app, views, driver, expect):
#
#     def setup(root):
#         views.button = Button(text='Click me 1', dock=root.center, was_clicked=False)
#         views.label = Label(
#             text='See me',
#             parent=views.button,
#             width=views.button.width,
#             height=views.button.height,
#             text_color='black',
#             background_color='white',
#         )
#
#         @views.button
#         def on_click(view):
#             view.was_clicked = True
#
#     with get_app(setup):
#         driver.find_element_by_id(views.label.id).click()
#         assert expect(lambda: views.button.was_clicked)
