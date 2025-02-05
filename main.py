import tkinter as tk

# ------------------------------------------
# Class Node: Represents a node (rectangle or diamond)
# ------------------------------------------
class Node:
    def __init__(self, canvas, node_id, x, y, text="Node", shape="rectangle", fill="#FFFFFF"):
        self.canvas = canvas
        self.id = node_id
        self.x = x
        self.y = y
        self.text = text
        self.shape = shape
        self.fill = fill
        if self.shape == "rectangle":
            self.width = 100
            self.height = 50
        elif self.shape == "diamond":
            self.width = 100
            self.height = 60
        self.item = None
        self.text_item = None
        self.draw()

    def draw(self):
        if self.shape == "rectangle":
            self.item = self.canvas.create_rectangle(
                self.x, self.y, self.x + self.width, self.y + self.height,
                fill=self.fill, outline="black", width=2
            )
            self.text_item = self.canvas.create_text(
                self.x + self.width/2, self.y + self.height/2,
                text=self.text, font=("Arial", 10)
            )
        elif self.shape == "diamond":
            cx = self.x + self.width/2
            cy = self.y + self.height/2
            points = [cx, self.y, self.x + self.width, cy, cx, self.y + self.height, self.x, cy]
            self.item = self.canvas.create_polygon(
                points, fill=self.fill, outline="black", width=2
            )
            self.text_item = self.canvas.create_text(cx, cy, text=self.text, font=("Arial", 10))

    def update_position(self, new_x, new_y):
        self.x = new_x
        self.y = new_y
        if self.shape == "rectangle":
            self.canvas.coords(self.item, self.x, self.y, self.x + self.width, self.y + self.height)
            self.canvas.coords(self.text_item, self.x + self.width/2, self.y + self.height/2)
        elif self.shape == "diamond":
            cx = self.x + self.width/2
            cy = self.y + self.height/2
            points = [cx, self.y, self.x + self.width, cy, cx, self.y + self.height, self.x, cy]
            self.canvas.coords(self.item, *points)
            self.canvas.coords(self.text_item, cx, cy)

    def update_text(self, new_text):
        self.text = new_text
        self.canvas.itemconfig(self.text_item, text=new_text)

    def update_color(self, new_color):
        self.fill = new_color
        self.canvas.itemconfig(self.item, fill=new_color)

    def highlight(self, flag=True):
        if flag:
            self.canvas.itemconfig(self.item, outline="red", width=3)
        else:
            self.canvas.itemconfig(self.item, outline="black", width=2)

    def contains_point(self, x, y):
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def get_center(self):
        return (self.x + self.width/2, self.y + self.height/2)


# ------------------------------------------
# Class Edge: Represents the connection (arrow) between two nodes
# ------------------------------------------
class Edge:
    def __init__(self, canvas, source, target, label=""):
        self.canvas = canvas
        self.source = source
        self.target = target
        self.label = label
        self.line_item = None
        self.label_item = None
        self.draw()

    def draw(self):
        sx, sy = self.source.get_center()
        tx, ty = self.target.get_center()
        self.line_item = self.canvas.create_line(sx, sy, tx, ty, arrow=tk.LAST, width=2)
        if self.label:
            mx = (sx + tx) / 2
            my = (sy + ty) / 2
            self.label_item = self.canvas.create_text(mx, my, text=self.label, fill="blue")

    def update_position(self):
        sx, sy = self.source.get_center()
        tx, ty = self.target.get_center()
        self.canvas.coords(self.line_item, sx, sy, tx, ty)
        if self.label_item:
            mx = (sx + tx) / 2
            my = (sy + ty) / 2
            self.canvas.coords(self.label_item, mx, my)


# ------------------------------------------
# Class DiagramEditor: Manages the interface and editor logic
# ------------------------------------------
class DiagramEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Mermaid Diagram Editor")
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right panel: instructions are shown initially.
        self.toolbar = tk.Frame(root, padx=5, pady=5)
        self.toolbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.instructions_label = tk.Label(self.toolbar, text=(
            "Instructions:\n"
            "- Right-click on the canvas to create a node.\n"
            "  (Rectangle or Diamond based on the context menu).\n"
            "- Once created, the node is ready for editing:\n"
            "  type directly on it.\n"
            "- The right panel shows a color palette\n"
            "  to change its color.\n"
            "- Double-click on a node to initiate connection mode:\n"
            "  then click on another node to create an arrow.\n"
            "- Clicking outside a node hides the editor\n"
            "  and palette, revealing the instructions again."
        ), justify="left")
        self.instructions_label.pack(pady=10)

        # Buttons to show and copy the code.
        self.btn_show_code = tk.Button(self.toolbar, text="Show Code", command=self.generate_mermaid)
        self.btn_show_code.pack(pady=5)
        self.btn_copy_code = tk.Button(self.toolbar, text="Copy Code", command=self.copy_mermaid_to_clipboard)
        self.btn_copy_code.pack(pady=5)

        # Variables for in-place editing and palette.
        self.current_edit_node = None  # Currently edited node.
        self.text_editor = None          # Entry widget embedded in the canvas.
        self.editor_window_id = None     # ID of the widget in the canvas.
        self.palette_panel = None        # Color palette panel in the toolbar.

        # Context menu to create nodes.
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Rectangle", command=lambda: self.create_node_at("rectangle"))
        self.context_menu.add_command(label="Diamond", command=lambda: self.create_node_at("diamond"))

        self.nodes = {}    # Dictionary of nodes (id -> Node).
        self.edges = []    # List of connections (Edge).
        self.node_counter = 0
        self.arrow_source = None  # Source node for connection.

        self.dragging_node = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.drag_threshold = 5

        # Bind events to the canvas.
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)

    def get_new_node_id(self):
        if self.node_counter < 26:
            node_id = chr(65 + self.node_counter)
        else:
            node_id = "N" + str(self.node_counter)
        self.node_counter += 1
        return node_id

    def on_right_click(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        self.context_menu_x = event.x
        self.context_menu_y = event.y

    def create_node_at(self, shape):
        x = self.context_menu_x
        y = self.context_menu_y
        node_id = self.get_new_node_id()
        new_node = Node(self.canvas, node_id, x, y, text="Node", shape=shape, fill="#FFFFFF")
        self.nodes[node_id] = new_node
        # Activate in-place editing immediately.
        self.start_editing_node(new_node)

    def start_editing_node(self, node):
        if self.current_edit_node and self.current_edit_node != node:
            self.stop_editing()
        self.current_edit_node = node
        if self.text_editor:
            self.text_editor.focus_set()
            self.text_editor.select_range(0, tk.END)
            return
        self.text_editor = tk.Entry(self.canvas, bd=0, relief="flat", highlightthickness=0,
                                      justify="center", font=("Arial", 10), bg="white")
        self.text_editor.insert(0, node.text)
        self.text_editor.select_range(0, tk.END)
        cx, cy = node.get_center()
        self.editor_window_id = self.canvas.create_window(cx, cy, window=self.text_editor)
        self.text_editor.focus_set()
        self.text_editor.bind("<KeyRelease>", lambda event: node.update_text(self.text_editor.get()))
        self.text_editor.bind("<Return>", self.finish_editing)
        self.text_editor.bind("<FocusOut>", self.finish_editing)
        self.show_palette_panel()
        if self.arrow_source:
            self.arrow_source.highlight(False)
            self.arrow_source = None

    def finish_editing(self, event=None):
        if self.current_edit_node and self.text_editor:
            new_text = self.text_editor.get()
            self.current_edit_node.update_text(new_text)
        self.remove_text_editor()
        self.hide_palette_panel()
        self.current_edit_node = None

    def remove_text_editor(self):
        if self.text_editor:
            self.canvas.delete(self.editor_window_id)
            self.text_editor.destroy()
            self.text_editor = None
            self.editor_window_id = None

    def show_palette_panel(self):
        self.instructions_label.pack_forget()
        if self.palette_panel:
            self.palette_panel.destroy()
        self.palette_panel = tk.Frame(self.toolbar)
        tk.Label(self.palette_panel, text="Choose color:", font=("Arial", 10, "bold")).pack(pady=5)
        colors = [
            ("Red", "#FF0000"),
            ("Green", "#00FF00"),
            ("Blue", "#0000FF"),
            ("Yellow", "#FFFF00"),
            ("Orange", "#FFA500"),
            ("Black", "#000000"),
            ("White", "#FFFFFF")
        ]
        for name, hex_color in colors:
            btn = tk.Button(self.palette_panel, bg=hex_color, width=4,
                            command=lambda c=hex_color: self.change_color(c))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        self.palette_panel.pack(pady=10)

    def hide_palette_panel(self):
        if self.palette_panel:
            self.palette_panel.destroy()
            self.palette_panel = None
        self.instructions_label.pack(pady=10)

    def change_color(self, new_color):
        if self.current_edit_node:
            self.current_edit_node.update_color(new_color)

    def on_left_click(self, event):
        if self.arrow_source:
            node = self.get_node_at(event.x, event.y)
            if node and node != self.arrow_source:
                new_edge = Edge(self.canvas, self.arrow_source, node)
                self.edges.append(new_edge)
                self.arrow_source.highlight(False)
                self.arrow_source = None
            return
        node = self.get_node_at(event.x, event.y)
        if node:
            self.start_editing_node(node)
            self.dragging_node = node
            self.drag_offset_x = event.x - node.x
            self.drag_offset_y = event.y - node.y
        else:
            self.stop_editing()

    def on_double_click(self, event):
        node = self.get_node_at(event.x, event.y)
        if node:
            self.stop_editing()
            self.arrow_source = node
            node.highlight(True)

    def on_drag(self, event):
        if self.dragging_node:
            new_x = event.x - self.drag_offset_x
            new_y = event.y - self.drag_offset_y
            self.dragging_node.update_position(new_x, new_y)
            if self.current_edit_node == self.dragging_node and self.text_editor:
                cx, cy = self.dragging_node.get_center()
                self.canvas.coords(self.editor_window_id, cx, cy)
            for edge in self.edges:
                if edge.source == self.dragging_node or edge.target == self.dragging_node:
                    edge.update_position()

    def on_release(self, event):
        self.dragging_node = None

    def get_node_at(self, x, y):
        for node in self.nodes.values():
            if node.contains_point(x, y):
                return node
        return None

    def stop_editing(self):
        self.remove_text_editor()
        self.hide_palette_panel()
        self.current_edit_node = None

    def get_mermaid_code(self):
        lines = []
        lines.append("```mermaid")
        lines.append("graph TD;")
        for node in self.nodes.values():
            if node.shape == "rectangle":
                lines.append(f"    {node.id}[{node.text}];")
            elif node.shape == "diamond":
                lines.append(f"    {node.id}{{{node.text}}};")
            else:
                lines.append(f"    {node.id}[{node.text}];")
        for edge in self.edges:
            if edge.label:
                lines.append(f"    {edge.source.id} -- {edge.label} --> {edge.target.id};")
            else:
                lines.append(f"    {edge.source.id} --> {edge.target.id};")
        predefined = {
            "#1e90ff": ("blue", "#1E90FF"),
            "#ff4500": ("red", "#FF4500"),
            "#32cd32": ("green", "#32CD32"),
            "#ffff00": ("yellow", "#FFFF00"),
            "#ffa500": ("orange", "#FFA500")
        }
        color_classes = {}
        for node in self.nodes.values():
            color = node.fill.lower()
            if color in predefined:
                class_name = predefined[color][0]
            else:
                if color not in color_classes:
                    class_name = "color" + str(len(color_classes) + 1)
                else:
                    class_name = color_classes[color]
            color_classes[color] = class_name
        for color, class_name in color_classes.items():
            lines.append(f"    classDef {class_name} fill:{color},stroke:#000,stroke-width:2px;")
        groups = {}
        for node in self.nodes.values():
            color = node.fill.lower()
            class_name = color_classes[color]
            groups.setdefault(class_name, []).append(node.id)
        for class_name, node_ids in groups.items():
            lines.append(f"    class {','.join(node_ids)} {class_name};")
        lines.append("```")
        return "\n".join(lines)

    def generate_mermaid(self):
        code_str = self.get_mermaid_code()
        top = tk.Toplevel(self.root)
        top.title("Mermaid Code")
        text_widget = tk.Text(top, wrap="word")
        text_widget.insert("1.0", code_str)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True)
        top.lift()
        top.focus_force()

    def copy_mermaid_to_clipboard(self):
        code_str = self.get_mermaid_code()
        self.root.clipboard_clear()
        self.root.clipboard_append(code_str)
        if not hasattr(self, "status_label"):
            self.status_label = tk.Label(self.toolbar, text="", fg="green", font=("Arial", 10))
            self.status_label.pack(pady=5)
        self.status_label.config(text="Code copied to clipboard")
        self.root.after(2000, lambda: self.status_label.config(text=""))


if __name__ == "__main__":
    root = tk.Tk()
    app = DiagramEditor(root)
    root.mainloop()
