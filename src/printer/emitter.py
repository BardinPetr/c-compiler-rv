class Emitter:

    def __init__(self):
        self.data = []

    def emit(self, cmd, *args):
        self.data.append(f"{cmd} {', '.join(str(i) for i in args)}")

    def emit_label(self, text):
        self.data.append(f"{text}:")

    def emit_section(self, name):
        self.emit(".section", f".{name}")

    def get(self) -> str:
        return '\n'.join(self.data) + "\n"

