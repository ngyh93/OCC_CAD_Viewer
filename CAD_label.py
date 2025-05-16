from OCC.Display.backend import load_backend
load_backend("pyqt5")  # Use "qt-pyside2" if you're using PySide

from OCC.Display.qtDisplay import qtViewer3d
from OCC.Display.OCCViewer import get_color_from_name
from OCC.Core.AIS import AIS_Shape
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_EDGE
from OCC.Core.TopoDS import topods_Face, topods
from OCC.Core.TopLoc import TopLoc_Location  
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.STEPConstruct import stepconstruct
from OCC.Core.TCollection import TCollection_HAsciiString
from OCC.Extend.DataExchange import read_step_file
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.Graphic3d import Graphic3d_MaterialAspect, Graphic3d_NameOfTextureEnv, Graphic3d_NameOfMaterial
from OCC.Core.V3d import V3d_TypeOfVisualization
from OCC.Core.Quantity import (
    Quantity_Color,
    Quantity_NameOfColor,
    Quantity_NOC_ALICEBLUE,
    Quantity_NOC_ANTIQUEWHITE,
    Quantity_NOC_YELLOW, 
    Quantity_TOC_RGB,
    Quantity_NOC_WHITE,
)

from PyQt5 import QtCore, uic, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog, QWidget, QVBoxLayout, QSizePolicy, QPushButton, QMdiSubWindow

import sys
from Utils.occ_utils_addon import save_shape,  viewer_raytracing, viewer_rasterization, list_face

class OCCViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("MainWindow.ui", self)

        # UI Elements
        self.mdi_area = self.findChild(QtWidgets.QMdiArea, "mdiArea")

        # File Menu actions
        self.new_doc_actionBtn = self.findChild(QtWidgets.QAction, "newDocument")
        self.import_step_action = self.findChild(QtWidgets.QAction, "importStep")
        self.export_step_action = self.findChild(QtWidgets.QAction, "exportStep")

        # Selection Menu actions
        self.body_selection_action = self.findChild(QtWidgets.QAction, "selectBody")
        self.face_selection_action = self.findChild(QtWidgets.QAction, "selectFace")
        self.edge_selection_action = self.findChild(QtWidgets.QAction, "selectEdge")
        self.vertex_selection_action = self.findChild(QtWidgets.QAction, "selectVertex")

        # View Menu actions
        self.front_view_action = self.findChild(QtWidgets.QAction, "actionFront")
        self.back_view_action = self.findChild(QtWidgets.QAction, "actionBack")
        self.left_view_action = self.findChild(QtWidgets.QAction, "actionLeft")
        self.right_view_action = self.findChild(QtWidgets.QAction, "actionRight")
        self.top_view_action = self.findChild(QtWidgets.QAction, "actionTop")
        self.bottom_view_action = self.findChild(QtWidgets.QAction, "actionBottom")
        self.isometric_action = self.findChild(QtWidgets.QAction, "actionIsometric")

        self.orthographic_action = self.findChild(QtWidgets.QAction, "actionOrthographic")
        self.perspective_action = self.findChild(QtWidgets.QAction, "actionPerspective")
        
        self.shaded_action = self.findChild(QtWidgets.QAction, "actionShaded")
        self.wireframe_action = self.findChild(QtWidgets.QAction, "actionWireframe")

        self.raytracing_action = self.findChild(QtWidgets.QAction, "actionRaytracing")
        self.rasterization_action = self.findChild(QtWidgets.QAction, "actionRasterization")

        # Label Menu actions
        self.label_face_action = self.findChild(QtWidgets.QAction, "labelFace")

        self.console = self.findChild(QtWidgets.QTextEdit, "output_text")

        # Intialize all signals
        self.connect_signals()

        # Parameters
        self.active_shape = None
        self.active_viewer = None
        self.active_sub = None

        self.selected_faces = {} # dictionary of selected faces {hash(face): TopDS_Face}
        self.highlight_selected_faces = {} # dictionary of highlighted faces {hash(face): AIS_Shape}. 
        self.face_map = {} # dictionary of face labels {hash(face): label}
        self.color_labeled_faces = {} # dictionary of labeled faces {hash(face): AIS_Shape}
        self.ais_shape = {} # dictionary of AIS_Shape objects {subwindow name: ais_shape}

        self.face_list = [] # list of faces in the shape

        self._mouse_down_time = None


        # Set up model and view
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Shape Hierarchy"])
        self.tree_view = self.findChild(QtWidgets.QTreeView, "treeView")
        self.tree_view.setModel(self.tree_model)
        # self.tree_view.expandAll()

    def connect_signals(self):
        """Connect UI signals to their handlers"""
        # Connect the mdi area to the subwindow activated signal
        self.mdi_area.subWindowActivated.connect(self.on_subwindow_activated)

        # connect file menu buttons
        self.new_doc_actionBtn.triggered.connect(self.create_new_document)
        self.import_step_action.triggered.connect(self.import_step_to_active)
        self.export_step_action.triggered.connect(self.export_step_file_with_label)

        # connect selection menu buttons
        self.body_selection_action.triggered.connect(self.body_selection)
        self.face_selection_action.triggered.connect(self.face_selection)
        self.edge_selection_action.triggered.connect(self.edge_selection)
        self.vertex_selection_action.triggered.connect(self.vertex_selection)

        # connect view menu buttons
        self.front_view_action.triggered.connect(self.front_view)
        self.back_view_action.triggered.connect(self.back_view)
        self.left_view_action.triggered.connect(self.left_view)
        self.right_view_action.triggered.connect(self.right_view)
        self.top_view_action.triggered.connect(self.top_view)
        self.bottom_view_action.triggered.connect(self.bottom_view)
        self.isometric_action.triggered.connect(self.iso_view)

        self.orthographic_action.triggered.connect(self.orthographic_view)
        self.perspective_action.triggered.connect(self.perspective_view)
        
        self.shaded_action.triggered.connect(self.shaded_on)
        self.wireframe_action.triggered.connect(self.wireframe_on)

        self.raytracing_action.triggered.connect(self.raytracing_on)
        self.rasterization_action.triggered.connect(self.rasterization_on)
        
        # connect label menu buttons
        self.label_face_action.triggered.connect(self.label_face)

        self.console.setReadOnly(True)
        self.console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def on_subwindow_activated(self, subwindow):
        if subwindow and self.active_sub and subwindow.windowTitle() != self.active_sub.windowTitle():
            self.clear_face_selection()

            self.active_sub = subwindow
            if subwindow.widget() is not None:
                self.active_viewer = subwindow.widget()
                self.active_shape = self.active_viewer.shape
                print("Change active viewer and shape")
            else:
                self.active_viewer = None
                self.active_shape = None
                print("No viewer in subwindow")
            print("Subwindow activated:", self.active_sub.windowTitle())
            self.console.append("Subwindow activated: " + subwindow.windowTitle())
        elif subwindow and self.active_sub and subwindow.windowTitle() == self.active_sub.windowTitle():
            pass # Do nothing if the same subwindow is activated again
        elif subwindow and not self.active_sub:
            self.active_sub = subwindow
            print("SubWindow activated:", self.active_sub.windowTitle())
        elif subwindow is None:
            self.reset_all()
            print("No subwindow is active")
    def iso_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.View_Iso()
    def front_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.View_Front()
    def back_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.View_Rear()
    def left_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.View_Left()
    def right_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.View_Right()
    def top_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.View_Top()
    def bottom_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.View_Bottom()
    def orthographic_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.SetOrthographicProjection()
            self.active_viewer._display.Context.UpdateCurrentViewer()
    def perspective_view(self):
        if self.active_viewer is not None:
            self.active_viewer._display.SetPerspectiveProjection()
            self.active_viewer._display.Context.UpdateCurrentViewer()

    def face_selection(self):
        self.clear_face_selection()
        
        # ais_shape = self.ais_shape[self.active_sub.windowTitle()]
        # self.active_viewer._display.Context.Deactivate(ais_shape)
        # self.active_viewer._display.Context.Activate(ais_shape, 4, True)  # Mode 4 = Face selection
        self.active_viewer._display.SetSelectionModeFace()  

    def edge_selection(self):
        self.clear_face_selection()
        # ais_shape = self.ais_shape[self.active_sub.windowTitle()]
        # self.active_viewer._display.Context.Deactivate(ais_shape)
        # self.active_viewer._display.Context.Activate(ais_shape, 2, True)  # Mode 4 = Face selection
        self.active_viewer._display.SetSelectionModeEdge()  
    
    def vertex_selection(self):
        self.clear_face_selection()
        self.active_viewer._display.SetSelectionModeVertex()
    
    def body_selection(self):
        self.clear_face_selection()
        self.active_viewer._display.SetSelectionModeShape()

    def create_new_document(self):
        sub = QMdiSubWindow()
        # sub.setWidget(viewer_widget)
        sub.setAttribute(Qt.WA_DeleteOnClose)
        sub.setWindowTitle("New Document")

        self.mdi_area.addSubWindow(sub)
        sub.showMaximized()
        self.mdi_area.setActiveSubWindow(sub)
        self.console.append("🗂️ New document created.")

    def populate_shape_tree(self, shape):
        solid_explorer = TopExp_Explorer(shape, TopAbs_SOLID)
        solid_idx = 0
        while solid_explorer.More():
            solid = topods.Solid(solid_explorer.Current())
            solid_item = QStandardItem(f"Solid {solid_idx}")
            self.tree_model.appendRow(solid_item)

            # Explore faces in solid
            face_explorer = TopExp_Explorer(solid, TopAbs_FACE)
            face_idx = 0
            while face_explorer.More():
                face = topods.Face(face_explorer.Current())
                face_item = QStandardItem(f"  Face {face_idx}")
                solid_item.appendRow(face_item)

                # Explore edges in face
                edge_explorer = TopExp_Explorer(face, TopAbs_EDGE)
                edge_idx = 0
                while edge_explorer.More():
                    edge = topods.Edge(edge_explorer.Current())
                    edge_item = QStandardItem(f"    Edge {edge_idx}")
                    face_item.appendRow(edge_item)

                    edge_explorer.Next()
                    edge_idx += 1

                face_explorer.Next()
                face_idx += 1

            solid_explorer.Next()
            solid_idx += 1

    def import_step_to_active(self):
        """Import a STEP file and display it in the viewer"""
        self.active_sub = self.mdi_area.activeSubWindow()

        if self.active_sub is None:
            self.console.append("⚠️ No active subwindow.")
            print ("⚠️ No active subwindow.")
            return
        
        # Prompt for file path
        path, _ = QFileDialog.getOpenFileName(None, "Open STEP file", "", "STEP Files (*.step *.stp)")
        if not path:
            sys.exit()
        
        # retreive file name and set document name on subwindow
        shape_name = path.split("/")[-1].split(".")[0]
        self.active_sub.setWindowTitle(shape_name + " - Document")

        # load step in pythonocc-core asTopoDS_Shape
        shape = read_step_file(path)
        self.active_shape = shape
        self.face_list = list_face(shape)  # Extract all faces from the shape

        # Populate tree
        self.populate_shape_tree(shape)

        # Setup viewer
        viewer = qtViewer3d()
        viewer.InitDriver()
        viewer.installEventFilter(self)
        viewer.resize(self.active_sub.size().width(), self.active_sub.size().height())
        self.active_sub.setWidget(viewer)
        self.active_viewer = viewer
        self.active_viewer.shape = shape  # Store shape for export use
        # self.active_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # retrieve display, view and context
        display = self.active_viewer._display
        view = self.active_viewer._display.View

        # display edit
        display.display_triedron()
        # display.hide_triedron()

        # Set the viewer background color and texture
        display.set_bg_gradient_color(
            Quantity_Color(Quantity_NameOfColor.Quantity_NOC_LIGHTSKYBLUE1),
            Quantity_Color(Quantity_NameOfColor.Quantity_NOC_ANTIQUEWHITE),
            2
        )
        display.Repaint()
        # display.default_drawer.SetFaceBoundaryDraw(False)

        # display the shape
        self.display_shape_with_wire()
        self.orthographic_view
        display.View_Iso()
        display.FitAll()

        # connect callbacks
        # display.register_select_callback(self.on_face_selected)
        display.register_select_callback(self._handle_selection)

        print(f"✅ Shape {shape_name} loaded.")
        self.console.append(f"✅ {shape_name} part loaded.")

    def display_shape_with_wire(self):
        display = self.active_viewer._display

        ais_shaded = AIS_Shape(self.active_viewer.shape)
        # Shaded view
        material = Graphic3d_MaterialAspect(Graphic3d_NameOfMaterial.Graphic3d_NOM_PLASTIC)
        ais_shaded.SetMaterial(material)
        ais_shaded.SetColor(Quantity_Color(0.8, 0.8, 0.8, Quantity_TOC_RGB))  # light gray
        ais_shaded.SetDisplayMode(1)  # 1 = shaded
        display.Context.Display(ais_shaded, True)
        self.ais_shape[self.active_sub.windowTitle()] = ais_shaded  # Store AIS_Shape for later use

        ais_wire = AIS_Shape(self.active_viewer.shape)
        # Wireframe overlay for edges
        ais_wire.SetDisplayMode(0)  # 0 = wireframe
        ais_wire.SetColor(Quantity_Color(0.0, 0.0, 0.0, Quantity_TOC_RGB))  # black
        ais_wire.SetWidth(2.0)  # thicker edges
        display.Context.Display(ais_wire, True)


    def shaded_on(self):
        """Shaded view"""
        display = self.active_viewer._display
        display.Context.DisplayAll(True)
        # display.SetModeShaded()
        print("Shaded mode activated.")
        self.console.append("Shaded mode activated.")


    def wireframe_on(self):
        """Wireframe view"""
        ais_shape = self.ais_shape[self.active_sub.windowTitle()]
        display = self.active_viewer._display
        display.Context.Erase(ais_shape, True)
        # display.SetModeWireFrame()
        print("Wireframe mode activated.")
        self.console.append("Wireframe mode activated.")

    def highlight_face(self, face):
        """
        Highlights a face in the OCC viewer by coloring and displaying it.
        
        :param viewer: qtViewer3d instance.
        :param face: TopoDS_Face to be highlighted.
        """
        ais_face = AIS_Shape(face)
        self.highlight_selected_faces[hash(face)] = ais_face
        color = Quantity_Color(Quantity_NOC_YELLOW)  # Proper wrapper
        self.active_viewer._display.Context.SetDisplayMode(ais_face, 1, True)
        self.active_viewer._display.Context.SetColor(ais_face, color, False)
        self.active_viewer._display.Context.Display(ais_face, True)
        # self.active_viewer._display.Context.UpdateCurrentViewer()

    def clear_face_selection(self):
        for ais_face in self.highlight_selected_faces.values():
            self.active_viewer._display.Context.Erase(ais_face, True)
            self.active_viewer._display.Context.Remove(ais_face, True)
            # self.active_viewer._display.Context.UpdateCurrentViewer()
        self.selected_faces.clear()
        self.highlight_selected_faces.clear()
        self.console.append("⚠️ Selection cleared.")
        print("⚠️ Selection cleared.")

    def on_face_selected(self, shapes, x=None, y=None):
        for face in shapes:
            if face.ShapeType() == TopAbs_FACE:
                face_hash = hash(face)
                if face_hash not in self.selected_faces:
                    self.highlight_face(face)
                    self.selected_faces[face_hash] = face
                    if face_hash not in self.face_map:
                        print(f"✅ Face {face_hash} selected.")
                        self.console.append(f"✅ Face '{face_hash}' selected.")
                    else:
                        print(f"✅ Face {self.face_map[face_hash]} selected.")
                        self.console.append(f"✅ Face '{self.face_map[face_hash]}' selected.")
    
    def deselect_face(self, shapes):
        """Deselects a face in the OCC viewer by removing its highlight."""
        for face in shapes:
            if face.ShapeType() == TopAbs_FACE:
                face_hash = hash(face)
                if face_hash in self.selected_faces:
                    self.active_viewer._display.Context.Erase(self.highlight_selected_faces[face_hash], True)
                    self.active_viewer._display.Context.Remove(self.highlight_selected_faces[face_hash], True)
                    # self.active_viewer._display.Context.UpdateCurrentViewer()
                    del self.selected_faces[face_hash]
                    del self.highlight_selected_faces[face_hash]
                    if face_hash not in self.face_map:
                        print(f"❌ Face {face_hash} deselected.")
                        self.console.append(f"❌ Face {face_hash} deselected.")
                    else:
                        print(f"❌ Face '{self.face_map[face_hash]}' deselected.")
                        self.console.append(f"❌ Face '{self.face_map[face_hash]}' deselected.")

    def label_face(self):
        # prompt for label using a dropdown list
        # dropdown_list = ["Optical"]
        dropdown_list = ["Hole", "Slot", "Pocket", "Passage", "Stock", "Groove", "Step", "Chamfer", "Fillet", "Wall", 'Wall + Hole']
        label, ok = QInputDialog.getItem(None, "Label Face", "Select label for selected face:", dropdown_list, 0, False)
        if not ok or not label:
            return
        for hash_face, face in self.selected_faces.items():
            self.face_map[hash_face] = str(label)
            self.highlight_labeled_faces(face, str(label))
        print("✅ Face labeled.")
        self.console.append("✅ Face labeled.")
        self.clear_face_selection()
        # print(self.face_map)
    
    def highlight_labeled_faces(self,face, label):
        """
        Color the labeled faces in the viewer.
        """
        ais_face = AIS_Shape(face)
        self.color_labeled_faces[hash(face)] = ais_face

        if label == "Hole":
            color = Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB)   # Red
        elif label == "Slot":
            color = Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB)   # Green
        elif label == "Pocket":
            color = Quantity_Color(0.0, 0.0, 1.0, Quantity_TOC_RGB)   # Blue
        elif label == "Passage":
            color = Quantity_Color(1.0, 0.0, 1.0, Quantity_TOC_RGB)   # Magenta
        elif label == "Stock":
            color = Quantity_Color(0.0, 1.0, 1.0, Quantity_TOC_RGB)   # Cyan
        elif label == "Groove":
            color = Quantity_Color(1.0, 0.5, 0.0, Quantity_TOC_RGB)   # Orange
        elif label == "Step":
            color = Quantity_Color(0.6, 0.2, 0.8, Quantity_TOC_RGB)   # Purple
        elif label == "Chamfer":
            color = Quantity_Color(0.3, 0.7, 0.5, Quantity_TOC_RGB)   # Teal-green
        elif label == "Fillet":
            color = Quantity_Color(0.7, 0.3, 0.3, Quantity_TOC_RGB)   # Brownish-red
        elif label == "Wall":
            color = Quantity_Color(0.3, 0.3, 0.7, Quantity_TOC_RGB)   # Deep blue
        elif label == 'Wall + Hole':
            color = Quantity_Color(0.4, 0.6, 0.2, Quantity_TOC_RGB)   # Olive-green
        elif label == 'Optical':
            color = Quantity_Color(0.6, 0.4, 0.2, Quantity_TOC_RGB)   # Dark tan

        self.active_viewer._display.Context.SetDisplayMode(ais_face, 1, True)
        self.active_viewer._display.Context.SetColor(ais_face, color, False)
        self.active_viewer._display.Context.Display(ais_face, True)


    def export_step_file_with_label(self):
        """
        Label the selected face and export the shape to a STEP file.
        """

        # Prompt for save path
        path, _ = QFileDialog.getSaveFileName(None, "Save STEP file", "", "STEP Files (*.step *.stp)")
        if not path:
            return
        face_map_copy = self.face_map.copy()
        save_shape(self.active_shape, path, face_map_copy)

    def raytracing_on(self):
        viewer_raytracing(self.active_viewer._display)
        print("Raytracing mode activated.")
        self.console.append("Raytracing mode activated.")

    def rasterization_on(self):
        viewer_rasterization(self.active_viewer._display)
        print("Rasterization mode activated.")
        self.console.append("Rasterization mode activated.")

    def keyPressEvent(self, event):
        """Handle key press events"""
        # ESC key to clear selection
        if event.key() == Qt.Key_Escape:
            self.clear_face_selection()
        # Ctrl + C to close
        elif event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            print("Closing application.")
            self.close()  # This will trigger closeEvent


    def _handle_selection(self, picked_shapes, x=None, y=None):
        if not picked_shapes or self._mouse_down_time is None:
            return

        elapsed = self._mouse_down_time.msecsTo(QtCore.QTime.currentTime())
        # print(elapsed)
        if elapsed >= 250:
            # Long press: treat as rotate/pan, do nothing
            print("Ignored selection due to long press")
            return

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers & QtCore.Qt.ControlModifier:
            self.deselect_face(picked_shapes)
        else:
            self.on_face_selected(picked_shapes)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
            self._mouse_down_time = QtCore.QTime.currentTime()
        return super().eventFilter(obj, event)

    def reset_all(self):
        """Reset all parameters and clear the viewer"""
        self.active_shape = None
        self.active_viewer = None
        self.active_sub = None
        self.selected_faces.clear()
        self.highlight_selected_faces.clear()
        self.face_map.clear()
        self.console.clear()
        self.console.append("🔄 All parameters reset.")

    def closeEvent(self, event):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    # Main layout window to hold viewer and export button
    main_window = OCCViewer()
    main_window.show()
    
    sys.exit(app.exec_())