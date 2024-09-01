import kivy

if kivy.platform == 'android':
    from .android import Serial
else:
    from .linux import Serial
