from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.AIS import AIS_Shape
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopoDS import topods_Face
from OCC.Core.TopLoc import TopLoc_Location  
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.STEPConstruct import stepconstruct
from OCC.Core.TCollection import TCollection_HAsciiString
from OCC.Extend.DataExchange import read_step_file
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.Graphic3d import Graphic3d_NameOfTextureEnv
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
from OCC.Core.Prs3d import Prs3d_Drawer
from OCC.Core.V3d import V3d_SpotLight, V3d_XnegYnegZpos
from OCC.Core.gp import gp_Vec, gp_Pnt

import sys

def viewer_raytracing(display):
    """Set the viewer to raytracing mode."""
    # create one spotlight
    spot_light = V3d_SpotLight(
        gp_Pnt(-100, -100, 500), V3d_XnegYnegZpos, Quantity_Color(Quantity_NOC_WHITE)
    )
    ## display the spotlight in rasterized mode
    display.Viewer.AddLight(spot_light)
    display.View.SetLightOn()
    # display.SetRasterizationMode()
    display.SetRaytracingMode(depth=3)
    
def viewer_rasterization(display):
    """Set the viewer to rasterization mode."""
    display.SetRasterizationMode()
    display.View.SetLightOff()


def list_face(shape):   # Extracts all face elements from a given 3D shape.
    '''
    input
        shape: TopoDS_Shape
    output
        fset: {TopoDS_Face}
    '''
    """
    fset = set()
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        s = exp.Current()
        exp.Next()
        face = topods.Face(s)
        fset.add(face)
    return list(fset)
    """
    topo = TopologyExplorer(shape)

    return list(topo.faces())

def save_shape(shape, step_path, label_map):
    """
    Saves the given shape to a STEP file at 'step_path' with face labels from 'label_map'.
    """
    try:
        print(f"Saving: {step_path}")
        shape_with_fid_to_step(step_path, shape, label_map)
        print(f"Successfully saved: {step_path}")
    except Exception as e:
        print(f"Error saving STEP file: {str(e)}")

def shape_with_fid_to_step(filename, shape, id_map):
    """Save shape to a STEP file format.

    :param filename: Name to save shape as.
    :param shape: Shape to be saved.
    :param id_map: Variable mapping labels to faces in shape.
    """
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)

    finderp = writer.WS().TransferWriter().FinderProcess()
    faces = list_face(shape) # a list of TopoDS_Face objects
    loc = TopLoc_Location() 

    for face in faces:
        item = stepconstruct.FindEntity(finderp, face, loc)
        if item is None:
            print(f"Warning: Could not find step entities for face {face}")
            continue
        
        # Ensure that id_map[hash(face)] exists and is not a tuple
        face_hash = hash(face)
        if face_hash in id_map and isinstance(id_map[face_hash], str):
            face_label = id_map[face_hash]
            item.SetName(TCollection_HAsciiString(str(face_label)))
            # remove face_hash from id_map
            del id_map[face_hash]
    
    if not id_map:
        for face_hash in id_map.keys() and id_map[face_hash] is not None:
            print(f"Warning: No step entities found for face with hash {face_hash}")
    
    writer.Write(filename)
