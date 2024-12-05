## python library, base on 3.11
from enum import Enum
import shutil
from typing import Optional, Union, Self, Callable, Any, Generator
import os
import uuid
import time
import math
import json
from pathlib import Path
from dataclasses import dataclass, field
from pprint import pp
## c4d library
import c4d
from c4d.gui import GeDialog, C4DGadget, TreeViewCustomGui, GeUserArea
from c4d import BaseContainer, gui, documents
from mxutils import CheckType

#=============================================
# Plugin Config
#=============================================

PLUGINPATH, PLUGINNAME = os.path.split(__file__)
PLUGINNAME = os.path.splitext(PLUGINNAME)[0]
RES_PATH = os.path.join(PLUGINPATH, "res")

DATA_FOLDER = os.path.join(PLUGINPATH, "Learning Data")
METADATA_PATH = os.path.join(PLUGINPATH, "Learning Data", "metadata.json")

PLUGINID: int = 1064433
ID_MSG_REMOVE_STEP = 1064434
ID_MSG_NEW_STEP = 1064436
ID_MSG_DATA_CHANGED = 1064451
ID_MSG_DATA_RELOAD = 1064471

PLUGINHELP: str = f"{PLUGINNAME}: Create and edit Learning Source for Cinema 4D Learning Pannel."
TITLE: str = f"{PLUGINNAME}"

#=============================================
# Constants
#=============================================
LSD_CLICK_COUNTER : float = 0

MENU_LAYOUT_OFF = 1056325
MENU_LAYOUT_ON = 465001796

CMD_LEARNING_PANNEL = 1064034
CMD_LEARNING_HANDLER = 1064212

ICON_DELETE = 12109
ICON_CREATE = 202586
ICON_EIDT = 1028160
ICON_SAVE = 12098

ICON_ROUND_RIGHT = 1021103
ICON_QUAD_RIGHT = 1021131
ICON_BOOK_MARK = 465001121
ICON_MENU = 13746
ICON_FOLDER = 12676
ICON_STEP = 450000058
ICON_LSD = 450000059

TEXT_COLOR_DARK = c4d.Vector(0.25)
TEXT_COLOR_GREY = c4d.Vector(0.45)
BG_DARK = c4d.Vector(0.13)

DEBUG_MODE = False

class ManagerId(Enum):
    """
    The ID of the Manager.
    has #id and #description attributes.
    """

    ARNOLD_IPR: int = (1032195, "Arnold IPR Manager")
    ARNOLD_SHADER_NETWORK: int = (1033989, "Arnold Shader Network Manager")
    ATTRIBUTE_MANAGER: int = (1000468, "Attribute Manager")
    CONSOLE: int = (10214, "Console")

    ASSET_BROWSER: int = (1054225, "Asset Browser")
    OBJECT_MANAGER: int = (100004709, "Object Manager")
    PICTURE_VIEWER: int = (430000700, "Picture Viewer")

    CORONA_NODE_MANAGER: int = (1040908, "Corona Node Manager")
    LAYER_MANAGER: int = (100004704, "Layer Manager")
    MATERIAL_MANAGER: int = (1500410, "Material Manager")
    NODEEDITOR_MANAGER: int = (465002211, "Node Editor")

    PROJECT_ASSET_INSPECTOR : int = (1029486, "Project Asset Inspector")
    TIMELINE_MANAGER: int = (465001516, "Timeline Manager")
    XPPRESSO_MANAGER: int = (1001148, "Xpresso Manager")
    TAKE_MANAGER: int = (431000053, "Take Manager")
    RENDER_QUEUE: int = (465003500, "Render Queue")
    RENDER_SETTING: int = (12161, "Render Setting")
    VIEWPORT: int = (59000, "Viewport")

    def __init__(self, id: int, description: str):
        self.id: int = id
        self.description: str = description

class WindowPlacement(Enum):
    """
    The placement string of the window.
    has #id and #description attributes.
    """

    CENTER: str = (100, "CENTER")

    BOTTOM_LEFT: str = (101, "BOTTOM_LEFT")
    BOTTOM_RIGHT: str = (102, "BOTTOM_RIGHT")
    BOTTOM_CENTER: str = (103, "BOTTOM_CENTER")

    TOP_LEFT: str = (104, "TOP_LEFT")
    TOP_RIGHT: str = (105, "TOP_RIGHT")
    TOP_CENTER: str = (106, "TOP_CENTER")

    def __init__(self, id: int, description: str):
        self.id: int = id
        self.description: str = description

def find_value_by_id(enum_class, target_id):
    """
    Find the value of the enum by the id.
    """
    for member in enum_class:
        if int(member.id) == int(target_id):
            return member
    return None

#=============================================
# File Methods
#=============================================

def read_json(source_path: str) -> str:
    if not os.path.exists(source_path):
        raise RuntimeError(f"{source_path} not exists")
    with open(source_path, 'r', encoding='UTF-8') as file:
        return json.load(file)

def write_json(source_path: str, data) -> None:
    if not os.path.exists((dir:=os.path.dirname(source_path))):
        os.makedirs(dir)
    with open(source_path, 'w', encoding='UTF-8') as file:
        json.dump(data, file, sort_keys=True, indent=4, separators=(',', ':'), ensure_ascii=False)

#=============================================
# Custom GUI helper methods@boghma4d.gui (https://www.boghma.com/)
#=============================================

def get_bitmap_from(source: Union[str,int,c4d.bitmaps.BaseBitmap], resourceFolder: str = None, default_resource: int = 1023411) -> c4d.bitmaps.BaseBitmap:

    if isinstance(source, c4d.bitmaps.BaseBitmap):
        bmp = source
    if isinstance(source, str):
        ext_list = [".jpg", ".png", ".tif", ".tiff", ".tga", ".hdr", ".exr"] 
        bmp = c4d.bitmaps.BaseBitmap()
        for ext in ext_list: #遍历所有后缀名
            if resourceFolder:
                bpath = os.path.join(resourceFolder, source + ext)
            else:
                filePath, _ = os.path.split(__file__)
                bpath = os.path.join(filePath, 'res', 'icons',source + ext)
                if not os.path.exists(bpath):
                    bpath = os.path.join(filePath, 'res', 'icon',source + ext)
                
                result, isMovie = bmp.InitWith(bpath)
                if result == c4d.IMAGERESULT_OK: 
                    return bmp
    elif isinstance(source, int):
        bmp = c4d.bitmaps.InitResourceBitmap(source)
        if bmp:
            return bmp
        else:
            bmp = c4d.bitmaps.InitResourceBitmap(default_resource)
            return bmp
    return bmp

def add_custom_button(host: c4d.gui.GeDialog, BTN_id: int, name:str="", layout_flag: int = c4d.BFH_SCALEFIT|c4d.BFV_SCALEFIT, size: Union[tuple,int]=(16,16),
                    image: Union[c4d.bitmaps.BaseBitmap,int,str]= 18161, image2: Union[c4d.bitmaps.BaseBitmap,int,str]= None, is_btm: bool=True, tool_tips: str=None, no_fading: bool=False) -> c4d.gui.BitmapButtonCustomGui:
    
    # BITMAPBUTTON_BUTTON
    settings = c4d.BaseContainer()
    settings[c4d.BITMAPBUTTON_BUTTON] = is_btm
    settings[c4d.BITMAPBUTTON_STRING] = name
    settings[c4d.BITMAPBUTTON_BORDER] = False
    settings[c4d.BITMAPBUTTON_DISABLE_FADING] = no_fading
    settings[c4d.BITMAPBUTTON_ICONID1] = None
    settings[c4d.BITMAPBUTTON_ICONID2] = None
    settings[c4d.BITMAPBUTTON_TOGGLE] = True
    if tool_tips:
        settings[c4d.BITMAPBUTTON_TOOLTIP] = tool_tips
    if size:
        if isinstance(size, tuple):
            settings[c4d.BITMAPBUTTON_FORCE_SIZE] = size[0]
            settings[c4d.BITMAPBUTTON_FORCE_SIZE_Y] = size[1]
        elif isinstance(size, int):
            settings[c4d.BITMAPBUTTON_FORCE_SIZE] = size
            settings[c4d.BITMAPBUTTON_FORCE_SIZE_Y] = size
        else:
            raise TypeError("size must be int or tuple")
    else:
        settings[c4d.BITMAPBUTTON_FORCE_SIZE] = 16
        settings[c4d.BITMAPBUTTON_FORCE_SIZE_Y] = 16
            
    btm: c4d.gui.BitmapButtonCustomGui = host.AddCustomGui(BTN_id, c4d.CUSTOMGUI_BITMAPBUTTON, name, layout_flag, 0, 0, settings)
    bmp = get_bitmap_from(image)
    btm.SetImage(bmp)
    if image2:
        bmp2 = get_bitmap_from(image2)
        btm.SetImage(bmp2, secondstate=True)
    return btm

#=============================================
# Custom TreeView GUI @boghma.easy_tree (https://www.boghma.com/)
#=============================================

class Signal:
    """Simplified version of the Signal class in pyqt"""

    def __init__(self, *args_types, **kwargs_types):
        self._slots = []

    def connect(self, slot:Callable):
        """ Connect the slot function to the signal.
            The method will be called when the signal emit
        """
        if slot not in self._slots:
            self._slots.append(slot)

    def disconnect(self, slot:Callable):
        """Disconnect the slot function from the signal."""
        if slot in self._slots:
            self._slots.remove(slot)

    def emit(self, *args, **kwargs):
        """ call all connected slot functions with the passed parameters （*args, **kwargs.）
        """
        for slot in self._slots:
            slot(*args, **kwargs)

class BaseHierarchy:
    """ A general hierarchy class
        use to determine the parent-child relationship between instances.
    """
    def __init__(self):
        self._parent:"BaseHierarchy" = None 
        self._children: list = [] 

    # Hierarchy Navigation Methods
    def get_children(self) -> list["BaseHierarchy"]:
        return self._children

    def get_down(self) -> "BaseHierarchy":
        if self._children:
            return self._children[0]

    def get_downlast(self) -> "BaseHierarchy":
        if self._children:
            return self._children[-1]

    def get_next(self) -> "BaseHierarchy":
        if self._parent and self._parent._children:
            index = self._parent._children.index(self)
            if index+1 != len(self._parent._children):
                return self._parent._children[index+1]

    def get_pred(self) -> "BaseHierarchy":
        if self._parent and self._parent._children:
            index = self._parent._children.index(self)
            if index != 0:
                return self._parent._children[index-1]

    def get_up(self) -> "BaseHierarchy":
        return self._parent

    # Insertion Methods
    def insert_after(self, obj:"BaseHierarchy") -> bool:
        if obj and obj._parent and obj != self:
            index = obj._parent._children.index(obj)
            obj._parent._children.insert(index+1, self)
            self._parent = obj._parent
            return True
        else:
            return False

    def insert_before(self, obj:"BaseHierarchy") -> bool:
        if obj and obj._parent and obj != self:
            index = obj._parent._children.index(obj)
            obj._parent._children.insert(index, self)
            self._parent = obj._parent
            return True
        else:
            return False
        
    def insert_under(self, obj:"BaseHierarchy") -> bool:
        if obj and obj != self:
            obj._children.insert(0, self)
            self._parent = obj
            return True
        else:
            return False
    def insert_underlast(self, obj:"BaseHierarchy") -> bool:
        if obj and obj != self:
            obj._children.append(self)
            self._parent = obj
            return True
        else:
            return False

    # advance
    def iter_all_children(self) -> Generator:
        for objx in self._children:
            yield objx
            for objx2 in objx.iter_all_children():
                yield objx2
    
    def remove(self) -> bool:
        parent = self.get_up()
        if parent:
            self._parent = None 
            parent.get_children().remove(self)
            return True

        return False

    def remove_all_children(self) -> None:
        for obj in reversed(self._children):
            obj.remove()

class TreeItem(BaseHierarchy):

    P_TYPE_TEXT = "text"
    P_TYPE_BITMAP = "bitmap"
    P_TYPE_CHECK = "check"
    P_TYPE_SLIDER = "slider"
    P_TYPE_CONTEXT_MENU = "context_menu"
    P_TYPE_DROPDOWN = "dropdown"

    def __init__(self):
        super().__init__()
        self._uid = uuid.uuid4()  # 
        self._tree :Tree=None
        self._meta :dict= {}
        self._selected :bool = False
        self._selectable :bool = True
        self._opened :bool = True
        self._property_data :list[dict] = []

    def get_uid(self) -> uuid.UUID:
        return self._uid

    def get_tree(self) -> "Tree":
        if not self._tree:
            parent = self.get_up()
            if parent:
                self._tree = parent.get_tree()
            else:
                return 
        return self._tree

    def set_meta(self, key:str, value:any):
        self._meta[key] = value
    
    def get_meta(self, key:str):
        return self._meta[key]

    def has_meta(self, key:str):
        return key in self._meta
    
    def create_child(self) -> "TreeItem":
        item = TreeItem()
        item.insert_underlast(self)
        return item
    
    def is_selectable(self) -> bool:
        return self._selectable
    
    def set_selectable(self, value:bool):
        self._selectable = value

    def is_selected(self) -> bool:
        return self._selected
    
    def set_selected(self, value:bool):
        self._selected = value

    def is_opened(self) -> bool:
        return self._opened
    
    def set_opened(self, value:bool):
        self._opened = value

    ### property_data
    def set_property_data(self, column:int, type:str, value):
        for data in self._property_data:
            if data["column"] == column and data["type"] == type:
                data["value"] = value
                return 
        new_data = {"column":column, "type":type, "value":value}
        self._property_data.append(new_data)
        
    def get_property_data(self):
        return self._property_data
    
    def get_property_data_value(self, column:int, type:str):
        for data in self._property_data:
            if data["column"] == column and data["type"] == type:
                return data["value"]

    def has_property_data_type(self, column:int, type:str):
        for data in self._property_data:
            if data["column"] == column and data["type"] == type:
                return True

    def set_text(self, column:int, value:str):
        self.set_property_data(column, self.P_TYPE_TEXT, value)

    def get_text(self, column:int) -> str:
        return self.get_property_data_value(column, self.P_TYPE_TEXT)

    def set_bitmap(self, column:int, value:Union[c4d.bitmaps.BaseBitmap,list]):
        self.set_property_data(column, self.P_TYPE_BITMAP, value)

    def get_bitmap(self, column:int):
        return self.get_property_data_value(column, self.P_TYPE_BITMAP)
    
    def set_check(self, column:int, value:bool):
        self.set_property_data(column, self.P_TYPE_CHECK, value)

    def get_check(self, column:int):
        return self.get_property_data_value(column, self.P_TYPE_CHECK)

    def set_slider(self, column:int, value, 
                                        minValue=None,
                                        maxValue=None,
                                        minNominalValue=None,
                                        maxNominalValue=None,
                                        increment=None,
                                        floatFormat=None,
                                        state=None,
                                        unit=None,
                                        finalValue=None
                                        ):
        
        data = {}
        data["value"] = value
        data["minValue"] = minValue
        data["maxValue"] = maxValue
        data["minNominalValue"] = minNominalValue
        data["maxNominalValue"] = maxNominalValue
        data["increment"] = increment
        data["floatFormat"] = floatFormat
        data["state"] = state
        data["unit"] = unit
        data["finalValue"] = finalValue

        prev_data = self.get_slider(column)
        if not prev_data:
            prev_data = data
        else:
            for key in data:
                if data[key] is None or key not in prev_data:
                    continue 
                prev_data[key] = data[key]
            prev_data["value"] = data["value"]
        self.set_property_data(column, self.P_TYPE_SLIDER, prev_data)

    def get_slider(self, column:int):
        return self.get_property_data_value(column, self.P_TYPE_SLIDER)

    def get_context_menu(self, column:int):
        if self.has_property_data_type(column, self.P_TYPE_CONTEXT_MENU):
            return self.get_property_data_value(column, self.P_TYPE_CONTEXT_MENU)
        if self.has_property_data_type(-1, self.P_TYPE_CONTEXT_MENU):
            return self.get_property_data_value(-1, self.P_TYPE_CONTEXT_MENU)
    
    def set_context_menu(self, column:int, value:c4d.BaseContainer):
        """ set column -1 if you want all column has same context menu"""
        self.set_property_data(column, self.P_TYPE_CONTEXT_MENU, value)

    def set_dropdown(self, column:int, entry:int, 
                                        menu:c4d.BaseContainer=None,
                                        state:int=None,
                                        ):
        data = {}
        data["entry"] = entry
        data["menu"] = menu
        data["state"] = state

        prev_data = self.get_dropdown(column)
        if not prev_data:
            prev_data = data
        else:
            for key in data:
                if data[key] is None or key not in prev_data:
                    continue 
                prev_data[key] = data[key]
        
        self.set_property_data(column, self.P_TYPE_DROPDOWN, prev_data)
        
    def get_dropdown(self, column:int):
        return self.get_property_data_value(column, self.P_TYPE_DROPDOWN)

@dataclass
class TreeUserData:
    line_height :int = 20
    column_width :dict = field(default_factory=dict)
    draw_item_space_x :int = 8
    draw_bitmap_margin :int = 2
    color_item_normal :c4d.Vector = field(default_factory=c4d.Vector)
    color_item_selected :c4d.Vector= field(default_factory=c4d.Vector)
    color_background_normal :c4d.Vector= field(default_factory=c4d.Vector)
    color_background_alternate :c4d.Vector= field(default_factory=c4d.Vector)
    color_background_selected :c4d.Vector= field(default_factory=c4d.Vector)
    drag_enable :bool = False
    drag_insert_type :int = c4d.INSERT_BEFORE | c4d.INSERT_AFTER | c4d.INSERT_UNDER
    empty_text :str = "Empty"

class TreeHeaderList:

    def __init__(self) -> None:
        self.header_list:list = []

    def __len__(self):
        return len(self.header_list)

    def clear(self):
        self.header_list = []

    def append_header(self, name:str, type:int=None) -> int:
        """ return current index of header"""
        if type is None:
            type = c4d.LV_USERTREE if not self.header_list else c4d.LV_USER
        self.header_list.append([name, type])
        return len(self.header_list)-1

    def add_usertree(self, name:str) -> int:
        return self.append_header(name, c4d.LV_USERTREE)
    
    def add_user(self, name:str) -> int:
        return self.append_header(name, c4d.LV_USER)
    
    def add_checkbox(self, name:str) -> int:
        return self.append_header(name, c4d.LV_CHECKBOX)

    def add_checkbox_user(self, name:str) -> int:
        return self.append_header(name, c4d.LV_CHECKBOXUSER)

    def add_slider(self, name:str) -> int:
        return self.append_header(name, c4d.LV_SLIDER)

    def add_dropdown(self, name:str) -> int:
        return self.append_header(name, c4d.LV_DROPDOWN)

    def get_header_index(self, name:str) -> int:
        """
        return -1 if not find name
        note: always return first find index when headerlist has multiple same name
        """
        for index, header in enumerate(self.header_list):
            if name == header[0]:
                return index
        return -1

def ClickCounter(break_time: float = 0.1) -> bool:
    global LSD_CLICK_COUNTER
    if (c_time := time.perf_counter()) - LSD_CLICK_COUNTER > break_time:
        LSD_CLICK_COUNTER = c_time
        return True
    return False

# override 
class Tree(c4d.gui.TreeViewFunctions):
    
    def __init__(self, dlg:GeDialog, id:int, flag=c4d.BFH_SCALEFIT|c4d.BFV_SCALEFIT, minw=0, minh=0, customdata:c4d.BaseContainer=None,
                                                                                        border = None,
                                                                                        outside_drop:bool=None,
                                                                                        hide_lines:bool=None,
                                                                                        ctrl_drag:bool=None,
                                                                                        no_multiselect:bool=None,
                                                                                        has_header:bool=True,
                                                                                        resize_header:bool=True,
                                                                                        move_column:bool=None,
                                                                                        fixed_layout:bool=True,
                                                                                        noautocolumns:bool=True,
                                                                                        no_open_ctrlclk:bool=True,
                                                                                        alt_drag:bool=None,
                                                                                        no_back_delete:bool=True,
                                                                                        no_delete:bool=True,
                                                                                        alternate_bg:bool=True,
                                                                                        cursorkeys:bool=None,
                                                                                        noenterrename:bool=True,
                                                                                        no_verticalscroll:bool=None,
                                                                                        addrow:bool=None,
                                                                                        resizable:bool=None
                                                                                        ):
        super().__init__()
        
        self._dlg :GeDialog= None
        self._id :int= None
        if customdata == None:
            customdata = c4d.BaseContainer()
            #Border type
            if border != None:
                customdata.SetLong(c4d.TREEVIEW_BORDER,border)
            #True if an object may be dropped under all the objects in the tree view.
            if outside_drop != None:
                customdata.SetBool(c4d.TREEVIEW_OUTSIDE_DROP,outside_drop)
            #True if no lines should be drawn.
            if hide_lines != None:
                customdata.SetBool(c4d.TREEVIEW_HIDE_LINES,hide_lines)
            #True if item may be duplicated by Ctrl + Drag.
            if ctrl_drag != None:
                customdata.SetBool(c4d.TREEVIEW_CTRL_DRAG,ctrl_drag)
            #True if no multiple selection is allowed.
            if no_multiselect != None:
                customdata.SetBool(c4d.TREEVIEW_NO_MULTISELECT,no_multiselect)
            #True if the tree view may have a header line.
            if has_header != None:
                customdata.SetBool(c4d.TREEVIEW_HAS_HEADER,has_header)
            #True if the column width can be changed by the user.
            #如果改成True 可以通过鼠标拖动的方式来修改columns的宽度
            if resize_header != None:
                customdata.SetBool(c4d.TREEVIEW_RESIZE_HEADER,resize_header)
            #True if the user can move the columns.
            #如果改成True 可以通过鼠标拖动的方式来修改columns的前后顺序
            if move_column != None:
                customdata.SetBool(c4d.TREEVIEW_MOVE_COLUMN,move_column)
            #True if all lines have the same height.
            if fixed_layout != None:
                customdata.SetBool(c4d.TREEVIEW_FIXED_LAYOUT,fixed_layout)
            #True if only the first line is asked for the columns width, resulting in a huge speedup.
            if noautocolumns != None:
                customdata.SetBool(c4d.TREEVIEW_NOAUTOCOLUMNS,noautocolumns)
            #True if it is not allowed to open the complete tree with Ctrl + Click.
            if no_open_ctrlclk != None:
                customdata.SetBool(c4d.TREEVIEW_NO_OPEN_CTRLCLK,no_open_ctrlclk)
            #True if Alt should be used instead of Ctrl for drag and drop; implies item may be duplicated by Alt + Drag.
            if alt_drag != None:
                customdata.SetBool(c4d.TREEVIEW_ALT_DRAG,alt_drag)
            #Disable “delete pressed” messages if backspace was hit.
            if no_back_delete != None:
                customdata.SetBool(c4d.TREEVIEW_NO_BACK_DELETE,no_back_delete)
            #Disable Delete Message Callback completely for backspace and delete.
            if no_delete != None:
                customdata.SetBool(c4d.TREEVIEW_NO_DELETE,no_delete)
            #Alternate background per line.
            if alternate_bg != None:
                customdata.SetBool(c4d.TREEVIEW_ALTERNATE_BG,alternate_bg)
            #True if cursor keys should be processed. 
            # Note: The focus item has to be set to None if it is deleted and this flag is set.
            if cursorkeys != None:
                customdata.SetBool(c4d.TREEVIEW_CURSORKEYS, cursorkeys)
            #Suppresses the rename popup when the user presses enter.
            if noenterrename != None:
                customdata.SetBool(c4d.TREEVIEW_NOENTERRENAME,noenterrename)
            #True to disable vertical scrolling and show the full list.
            if no_verticalscroll != None:
                customdata.SetBool(c4d.TREEVIEW_NO_VERTICALSCROLL, no_verticalscroll)
            #Show an add new column row at the bottom of the list.
            if addrow != None:
                customdata.SetBool(c4d.TREEVIEW_ADDROW, addrow)
            #The treeview is resizable from the bottom edge.
            if resizable != None:
                customdata.SetBool(c4d.TREEVIEW_RESIZABLE, resizable)
        
        self._tvcg :TreeViewCustomGui= dlg.AddCustomGui(id, c4d.CUSTOMGUI_TREEVIEW, "", flag, minw, minh, customdata)
        self._root:TreeItem = None
        self._header_list:TreeHeaderList = TreeHeaderList()
        self._userdata:TreeUserData = TreeUserData( line_height=20,
                                                    column_width={"0":150},
                                                    draw_item_space_x = 8,
                                                    draw_bitmap_margin = 2,
                                                    color_item_normal=c4d.COLOR_TEXT, 
                                                    color_item_selected=c4d.COLOR_TEXT_SELECTED,
                                                    color_background_normal=c4d.COLOR_BG_DARK2,
                                                    color_background_alternate=c4d.COLOR_BG_DARK1,
                                                    color_background_selected=c4d.COLOR_BG_HIGHLIGHT,
                                                    drag_enable=False,
                                                    drag_insert_type=c4d.INSERT_BEFORE | c4d.INSERT_AFTER | c4d.INSERT_UNDER,
                                                    empty_text="TreeView is Empty",
                                                    )

        self._prev_selection = []
        self.__drag_obj = None
        self.init_signals()

    def init_signals(self):
        self.selection_changed:Signal = Signal()
        self.double_clicked:Signal = Signal("tree_item:TreeItem, column:int, mouseinfo")
        self.context_menu_called:Signal = Signal("tree_item:TreeItem, column:int, lCommand")
        self.check_changed:Signal = Signal("tree_item:TreeItem, column:int, bCheck, bcMsg")
        self.slider_changed:Signal = Signal("tree_item:TreeItem, column:int, value, finalValue")
        self.dropdown_changed:Signal = Signal("tree_item:TreeItem, column:int, entry")
        self.hierarchy_changed:Signal = Signal("tree_item:TreeItem")
        self.open_changed:Signal = Signal("tree_item:TreeItem")
        
    @property
    def userdata(self) -> TreeUserData:
        return self._userdata
    
    @property
    def header_list(self) -> TreeHeaderList:
        return self._header_list

    def set_header_list(self, header_list:TreeHeaderList):
        self._header_list = header_list
        self.update_header_list()
    
    def update_header_list(self):
        header_list = self._header_list
        layout_container = c4d.BaseContainer()
        for index, header in enumerate(header_list.header_list):
            layout_container[index] = header[1]
        self._tvcg.SetLayout(len(header_list), layout_container)
        for index, header in enumerate(header_list.header_list):
            self._tvcg.SetHeaderText(index, header[0]) 
        self._tvcg.Refresh()  

    def create_item(self, parent:TreeItem=None):
        item = TreeItem()
        if not parent and not self.get_root():
            self.set_root(item)
        if not parent:
            parent = self.get_root()
        item.insert_underlast(parent)
        return item
    
    def get_root(self) -> "TreeItem":
        return self._root

    def set_root(self, root:TreeItem):
        if root:
            root._tree = self
        self._root = root
        self._tvcg.SetRoot(root, functions=self, userdata=self._userdata)
        self._tvcg.Refresh()      

    def refresh(self):
        self._tvcg.Refresh()      
    
    def layout_changed(self):
        self._tvcg.LayoutChanged()

    def clear(self):
        self.set_root(None)
        self.refresh()

    def deselect_all(self):
        if not self._root:
            return 
        for tree_item in self._root.iter_all_children():
            tree_item.set_selected(False)
    
    def get_selected_items(self) -> list["TreeItem"]:
        if not self.get_root():
            return 
        listx = []
        for item in self.get_root().iter_all_children():
            if item.is_selected():
                listx.append(item)
        return listx
    
    ####################################################### tv functions
    
    def GetFirst(self, root:"TreeItem", userdata:TreeUserData):
        if root:
            return root.get_down()

    def GetDown(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        return obj.get_down()

    def GetNext(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        return obj.get_next()
         
    def GetPred(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        return obj.get_pred()

    def GetBackgroundColor(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", line, col):
        if not obj:
            return
        if obj.is_selected():
            col = userdata.color_background_selected
        else:
            if line%2==0:
                col = userdata.color_background_normal
            else:
                col = userdata.color_background_alternate
        return col
    
    def GetHeaderColumnWidth(self, root:"TreeItem", userdata:TreeUserData, col, area):
        if str(col) in userdata.column_width:
            return userdata.column_width[str(col)]
        else:
            return 40

    def GetLineHeight(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", col, area):
        return userdata.line_height

    def DrawCell(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", col, drawinfo, bgColor):
        ua :c4d.gui.GeUserArea= drawinfo["frame"]
        xpos = drawinfo["xpos"]
        ypos = drawinfo["ypos"] #
        default_width = drawinfo["width"]
        default_height = drawinfo["height"]-1
        ua.DrawSetPen(bgColor)
        ua.DrawRectangle(xpos, ypos, xpos+default_width, ypos+default_height)
        gap = userdata.draw_item_space_x
        margin = userdata.draw_bitmap_margin

        if not obj:
            return 
        for property in obj.get_property_data():
            value = property["value"]
            if property["column"] != col:
                continue
            if property["type"] == TreeItem.P_TYPE_TEXT:
                if obj.is_selected():
                    text_color = userdata.color_item_selected
                else:
                    text_color = userdata.color_item_normal
                ua.DrawSetTextCol(text_color, bgColor)
                ua.DrawText(value, int(xpos), int(ypos+1))
                text_width = ua.DrawGetTextWidth(value)
                xpos += text_width + gap

            elif property["type"] == TreeItem.P_TYPE_BITMAP:
                if isinstance(value, c4d.bitmaps.BaseBitmap):
                    draw_icon = value
                elif isinstance(value, list):
                    check = obj.is_opened()
                    if obj.has_property_data_type(col, TreeItem.P_TYPE_CHECK):
                        check = obj.get_property_data_value(col, TreeItem.P_TYPE_CHECK)
                    if check:
                        draw_icon = value[1]
                    else:
                        draw_icon = value[0]
                else:
                    print("draw_icon type not valid")
                    continue
                w = draw_icon.GetBw()
                h = draw_icon.GetBh()
                res = w/float(h)
                img_h = default_height - margin*2
                img_w = img_h*res
                ua.DrawSetPen(bgColor)
                #ua.DrawRectangle(xpos, ypos, xpos+default_height, ypos+default_height)
                ua.DrawBitmap(draw_icon,
                                int(xpos+margin), int(ypos+margin), int(img_w), int(img_h), 
                                0, 0, int(w), int(h), 
                                c4d.BMP_ALLOWALPHA 
                                )
                xpos += img_w + gap
        
    def IsSelectable(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        return obj.is_selectable()

    def IsSelected(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        return obj.is_selected()
           
    def Select(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", mode):
        if mode == c4d.SELECTION_ADD:
            obj.set_selected(True)
        elif mode == c4d.SELECTION_SUB:
            obj.set_selected(False)
        elif mode == c4d.SELECTION_NEW:
            self.deselect_all()
            obj.set_selected(True)
                
    def IsOpened(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        return obj.is_opened()

    def Open(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", opened):
        obj.set_opened(opened)
        self.open_changed.emit(obj)

    def IsChecked(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", lColumn):
        check = obj.get_check(lColumn)
        if check is None:
            return c4d.LV_CHECKBOX_HIDE
        if check:
            return c4d.LV_CHECKBOX_CHECKED | c4d.LV_CHECKBOX_ENABLED
        else:
            return c4d.LV_CHECKBOX_ENABLED
    
    def SetCheck(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", lColumn, bCheck, bcMsg):
        check = obj.get_check(lColumn)
        if check != bCheck:
            obj.set_check(lColumn, bCheck)
            self.check_changed.emit(obj, lColumn, bCheck, bcMsg)

    def SetFloatValue(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", lColumn, value, finalValue):
        obj.set_slider(lColumn, value, finalValue=finalValue)
        self.slider_changed.emit(obj, lColumn, value, finalValue)

    def GetFloatValue(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", lColumn, sliderInfo):
        data = obj.get_slider(lColumn)
        if not data:
            sliderInfo["state"] = c4d.LV_CHECKBOX_HIDE
            return 
        for key in data:
            if data[key] is None or key not in sliderInfo:
                continue 
            sliderInfo[key] = data[key]
        sliderInfo["value"] = data["value"]

    def SetDropDownMenu(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", lColumn, entry):
        obj.set_dropdown(lColumn, entry)
        self.dropdown_changed.emit(obj, lColumn, entry)
        
    def GetDropDownMenu(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", lColumn, menuInfo):
        data = obj.get_dropdown(lColumn)
        if not data:
            menuInfo["state"] = c4d.LV_CHECKBOX_HIDE
            return 
        menuInfo["entry"] = data["entry"]
        data["menu"].CopyTo(menuInfo["menu"], 0)
        menuInfo["state"] = data["state"]
        
    def EmptyText(self, root:"TreeItem", userdata:TreeUserData):
        return userdata.empty_text
    
    def GetDragType(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        if not userdata.drag_enable:
            return c4d.NOTOK
        return c4d.DRAGTYPE_ATOMARRAY 

    def GenerateDragArray(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        self.__drag_obj = obj
        return []

    def SetDragObject(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        pass

    def DragStart(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem"):
        return c4d.TREEVIEW_DRAGSTART_ALLOW | c4d.TREEVIEW_DRAGSTART_SELECT

    def AcceptDragObject(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", dragtype, dragobject):
        return userdata.drag_insert_type, False

    def InsertObject(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", dragtype, dragobject, insertmode, bCopy):
        """
        Called when a drag is dropped on the TreeView.
        """
        if not self.__drag_obj:
            return 
        drag_object = self.__drag_obj
        if obj == drag_object:
            return 
        for child in drag_object.iter_all_children():
            if obj == child:
                return 
        drag_object.remove()
        if insertmode == c4d.INSERT_AFTER:
            drag_object.insert_after(obj)
        elif insertmode == c4d.INSERT_BEFORE:
            drag_object.insert_before(obj)
        elif insertmode == c4d.INSERT_UNDER:
            drag_object.insert_under(obj)
        else:
            return 
        self.hierarchy_changed.emit(drag_object)
        return

    def CreateContextMenu(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", lColumn, bc):
        #The added menu entry IDs must be larger than c4d.ID_TREEVIEW_FIRST_NEW_ID.
        #bc[c4d.ID_TREEVIEW_FIRST_NEW_ID+1] ="ContextMenu 1"
        bc.FlushAll()
        if not obj:
            obj = root
        if not obj:
            return 
        obc = obj.get_context_menu(lColumn)
        if obc:
            obc.CopyTo(bc, c4d.COPYFLAGS_NONE)
        
    def ContextMenuCall(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", lColumn, lCommand):
        self.context_menu_called.emit(obj, lColumn, lCommand)
        return True
    
    def DoubleClick(self, root:"TreeItem", userdata:TreeUserData, obj:"TreeItem", col, mouseinfo):
        # 如果想保留原有的双击功能（比如重命名）返回 False
        self.double_clicked.emit(obj, col, mouseinfo)
        return True 

    def SelectionChanged(self, root:"TreeItem", userdata:TreeUserData):
        items = self.get_selected_items()
        if self._prev_selection != items:
            self._prev_selection = items
            self.selection_changed.emit()

    ####################################################### custom functions
    def MouseDown(self, root: TreeItem, userdata, obj: TreeItem, col, mouseinfo, rightButton):
        # print(root, userdata, obj, col, mouseinfo,rightButton)
        if not obj:
            if not ClickCounter(0.1):
                # print("double click")
                c4d.SpecialEventAdd(ID_MSG_NEW_STEP)
                return False
        return False

#=============================================
# Data Management
#=============================================

@dataclass
class StepData:
    """The data of a step in a Learning Source."""

    description: str = ""
    media: str = ""
    window_placement: str = "CENTER"
    command_id_shortcut: str = ""
    ui_event: str = ""
    ui_manager_highlight: str = ""
    ui_command_bubble: str = ""

    def to_dict(self) -> dict:
        """Convert the StepData data to a dictionary."""
        return {
            "description": self.description,
            "media": self.media,
            "window_placement": self.window_placement,
            "command_id_shortcut": self.command_id_shortcut,
            "ui_event": self.ui_event,
            "ui_manager_highlight": self.ui_manager_highlight,
            "ui_command_bubble": self.ui_command_bubble
        }

@dataclass
class LearningSourceData:
    """The data of a basic Lreaning Source from a JSON file."""

    tutorial_title: str = ""
    author: str = "Maxon"
    duration_minutes: int =  5
    welcome_media: str = "intro.mp4"
    welcome_description: str = "This is a quick breakdown of important parts of the <b>Cinema 4D interface.</b>"
    complete_media: str = "intro.mp4"
    complete_description: str = "You're now ready to dive deeper into Cinema 4D."
    steps: list = field(default_factory=list)

    def __post_init__(self) -> None:
        self.result: dict = {
            "tutorial_title" : self.tutorial_title,
            "author" : self.author,
            "duration_minutes" : self.duration_minutes,
            "welcome_media" : self.welcome_media,
            "welcome_description" : self.welcome_description,
            "complete_media" : self.complete_media,
            "complete_description" : self.complete_description,
            "steps" : self.steps
        }

    def add_step(self, description: str="", media: str="", window_placement: str="CENTER", command_id_shortcut: str="",
                    ui_event: str="", ui_manager_highlight: str="", ui_command_bubble: str="") -> dict:
        """Add a step to the list of steps."""

        step = dict()
        step["description"] = description
        step["media"] = media
        step["window_placement"] = window_placement
        step["command_id_shortcut"] = command_id_shortcut
        step["ui_event"] = ui_event
        step["ui_manager_highlight"] = ui_manager_highlight
        step["ui_command_bubble"] = ui_command_bubble
        self.steps.append(step)
        return step
    
    def get_step(self, step_index: int) -> dict:
        """Get a step from the list of steps."""
        if step_index < len(self.steps):
            return self.steps[step_index]
        else:
            return {}

    def update_step(self, step_index: int, step_data: StepData|dict) -> None:
        """Update a step in the list of steps."""
        if step_index < len(self.steps):
            if isinstance(step_data, StepData):
                self.steps[step_index] = step_data.to_dict()
            elif isinstance(step_data, dict):
                self.steps[step_index] = step_data
        else:
            raise IndexError("Step index out of range.")

    def remove_step(self, step_index: int) -> None:
        """Remove a step from the list of steps."""
        if step_index < len(self.steps):
            self.steps.pop(step_index)
        else:
            raise IndexError("Step index out of range.")

    def clear_steps(self) -> None:
        """Clear the list of steps."""
        self.steps.clear()

    def get_step_count(self) -> int:
        """Get the number of steps in the list of steps."""
        return len(self.steps)
    
    def swap_step_order(self, step_index_1: int, step_index_2: int) -> None:
        """Swap the order of two steps in the list of steps."""
        try:
            self.steps[step_index_1], self.steps[step_index_2] = self.steps[step_index_2], self.steps[step_index_1]
        except IndexError:
            raise IndexError("Step index out of range.")
        except:
            raise RuntimeError("Failed to swap steps.")

    def save_to_file(self, file_path: str) -> None:
        """Save the Lreaning Source data to a file."""
        write_json(file_path, self.result)

    @staticmethod
    def load_from_file(file_path: str) -> "LearningSourceData":
        """Load the Lreaning Source data from a file."""
        data: dict = read_json(file_path)
        result: dict = {
                "tutorial_title" : data.get("tutorial_title", ""),
                "author" : data.get("author", "Maxon"),
                "duration_minutes" : data.get("duration_minutes", 5),
                "welcome_media" : data.get("welcome_media", "intro.mp4"),
                "welcome_description" : data.get("welcome_description", "This is a quick breakdown of important parts of the <b>Cinema 4D interface.</b>"),
                "complete_media" : data.get("complete_media", "intro.mp4"),
                "complete_description" : data.get("complete_description", "You're now ready to dive deeper into Cinema 4D."),
                "steps" : data.get("steps", [])
            }
        return LearningSourceData(**result)

@dataclass
class LearningSourceFolder:
    """The Learning Source folder."""

    path: str = ""

    def __post_init__(self) -> None:
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"File not found: {self.path}")
        if not os.path.isdir(self.path):
            raise NotADirectoryError(f"Not a directory: {self.path}")
        
    def is_valid(self) -> bool:
        """Check if the Learning Source is valid."""
        self.tut_path: str = os.path.join(self.path, "tut")
        self.json_path: str = os.path.join(self.tut_path, "tutorial.json")
        if os.path.exists(self.json_path) and os.path.isfile(self.json_path):
            return True
        return False

@dataclass
class MetaDataItem:
    """The DataItem class."""

    title: str
    
    category: str = field(default="Uncategorized", repr=False)
    tags: list|str = field(default="", repr=False)

    def __post_init__(self) -> None:
        self.folder_path = os.path.join(DATA_FOLDER, self.title)
        self.tut_path: str = os.path.join(self.folder_path, "tut")
        self.json_path: str = os.path.join(self.tut_path, "tutorial.json")

    def __str__(self) -> str:
        return f"{self.title}"

    def get_learning_source_item(self) -> LearningSourceData:
        """Get the Learning Data data."""
        if os.path.exists(self.json_path):
            return LearningSourceData.load_from_file(self.json_path)
    
    def to_dict(self) -> dict:
        """Convert the DataItem data to a dictionary."""
        return {
            "title": self.title,
            "category": self.category,
            "tags" : self.tags
        }
    
    @staticmethod
    def from_dict(data: dict) -> Self:
        """Load the DataItem data from a dictionary."""
        return MetaDataItem(title=data.get("title", ""),
                            category=data.get("category", "Uncategorized"),
                            tags=data.get("tags", []))

    def tags_string_from_list(self) -> str:
        """Get the tags as a string."""
        if isinstance(self.tags, list) and len(self.tags) > 0:
            return ", ".join(self.tags)
        else:
            return ""

    def tags_list_from_string(self, tags_string: str) -> list:
        """Get the tags as a list from a string."""
        if "," in tags_string:
            return tags_string.split(",")
        else:
            return []

    def replace_with(self, new_item: Self|dict) -> None:
        """Replace the current item with a new item."""
        if isinstance(new_item, dict):
            new_item = MetaDataItem.from_dict(new_item)
        self.title = new_item.title
        self.category = new_item.category
        self.tags = new_item.tags
        self.folder_path = new_item.folder_path
        #self.json_path = new_item.json_path

@dataclass
class DataManager:
    """This class manages the tutorial json data with a metadata.
    """

    name: str = "metadata.json"

    def __post_init__(self) -> None:
        self.root_path: str = os.path.join(PLUGINPATH, "Learning Data")
        self.path: str = os.path.join(self.root_path, self.name)
        self.data_items: list[MetaDataItem] = []
        self.reload()
        self.categories: list[str] = self.get_categories()
        self.tags: list[str] = self.get_tags()

    def get_categories(self) -> list[str]:
        """Get the list of categories."""
        categories = [item.category for item in self.data_items]
        categories = list(set(categories))
        categories.sort()
        return categories

    def get_tags(self) -> list[str]:
        """Get the list of tags."""
        tags: list[str] = []
        for item in self.data_items:
            if isinstance(item.tags, list):
                tags.extend(item.tags)
            elif isinstance(item.tags, str):
                if item.tags:
                    tags.append(item.tags)
        tags = list(set(tags))
        tags.sort()
        return tags

    def __repr__(self) -> str:
        return f"DataManager contains {len(self.data_items)} data items."
    
    def save_data(self) -> None:
        """Save the data to a file."""
        write_json(self.path, [item.to_dict() for item in self.data_items])
        if DEBUG_MODE:
            print(f"Data saved to {self.path}")

    def update_all(self) -> None:
        """Update all the data."""

        all_items = []
        for folder_path in os.listdir(self.root_path):
            if os.path.isdir(folder:=os.path.join(self.root_path, folder_path)):
                ls = LearningSourceFolder(folder)
                if ls.is_valid():
                    all_items.append(folder_path)
        meta_items = [str(item) for item in self.data_items if item.title]

        for i in list(set(all_items)^set(meta_items)):
            data_item = MetaDataItem(title=i)
            lsd = LearningSourceData.load_from_file(data_item.json_path)
            self.add_item(data_item, lsd)
        self.save_data()

    def update(self, item: MetaDataItem, lsd: LearningSourceData) -> None:
        """Update the data."""
        lsd.save_to_file(item.json_path)
        self.save_data()
        self.reload()

    def reload(self) -> None:
        """Load the data from a file."""
        self.data_items.clear()
        datas: list[dict] = read_json(self.path)
        for value in datas:
            self.data_items.append(MetaDataItem(title=value.get("title", ""), 
                                            category=value.get("category", ""),
                                            tags=value.get("tags", [])))
        
    def add_item(self, item: MetaDataItem, lsd: LearningSourceData=None, update: bool=False) -> None:
        if not isinstance(item, MetaDataItem):
            raise TypeError("item must be of type DataItem.")
        
        self.data_items.append(item)
        if not isinstance(lsd, LearningSourceData):
            lsd = LearningSourceData(tutorial_title=item.title)

        if update:
            self.update(item, lsd)

    def get_index_by_title(self, title: str) -> int:
        for index, item in enumerate(self.data_items):
            if item.title == title:
                return index
        return -1

    def get_item_by_title(self, title: str) -> MetaDataItem:
        for item in self.data_items:
            if item.title == title:
                return item
        return None

    def get_lsd_by_title(self, title: str) -> LearningSourceData:
        for _, item in enumerate(self.data_items):
            if item.title == title:
                return LearningSourceData.load_from_file(item.json_path)

    def replace_item(self, old_title: str, new_item: MetaDataItem) -> None:
        index = self.get_index_by_title(old_title)
        if 0 <= index < len(self.data_items):
            self.data_items[index].replace_with(new_item)

    def remove_item(self, name: str) -> None:
        meta_names = [str(item) for item in self.data_items if item.title]
        if name in meta_names:
            index = self.get_index_by_title(name)
            if 0 <= index < len(self.data_items):
                del self.data_items[index]

    def find_by_category(self, category: str) -> list[MetaDataItem]:
        if category == "All":
            return self.data_items
        return [item for item in self.data_items if item.category == category]

    def find_by_title(self, title: str) -> list[MetaDataItem]:
        if title == "All":
            return self.data_items
        return [item for item in self.data_items if item.title == title]

    def find_by_tag(self, tag: str) -> list[MetaDataItem]:
        if tag == "All":
            return self.data_items
        return [item for item in self.data_items if tag in item.tags]

#=============================================
# Dialog
#=============================================

def wrap_icon(source: int) -> str:
    return "&i" + str(source) + "&"

class ItemCallBacks:

    def __init__(self, tree_item: TreeItem, dataItem: MetaDataItem, lsd: LearningSourceData, index: int) -> None:
        self.tree_item: TreeItem = tree_item
        self.dataItem: MetaDataItem = dataItem
        self.lsd: LearningSourceData = lsd
        self.index: int = index

        step = self.lsd.get_step(self.index)
        self.description: str = step.get("description","")
        self.media: str = step.get("mdeia","")
        self.window_placement: str = step.get("window_placement","CENTER")
        self.command_id_shortcut: str = step.get("command_id_shortcut","")
        self.ui_event: str = step.get("ui_event","")
        self.ui_manager_highlight: str = step.get("ui_manager_highlight","")
        self.ui_command_bubble: str = step.get("ui_command_bubble","")

        self.init_values()

    def init_values(self):
        self.tree_item.set_bitmap(0, c4d.bitmaps.InitResourceBitmap(ICON_STEP))
        self.tree_item.set_text(0, f"  Step {self.index+1}")

        bc = c4d.BaseContainer()
        bc[c4d.ID_TREEVIEW_FIRST_NEW_ID+1] = wrap_icon(ICON_DELETE) + "Delete Current Step"
        self.tree_item.set_context_menu(-1, bc)

    def update_values(self):
        self.init_values()

    def context_menu_called(self,column, lCommand):
        if lCommand == c4d.ID_TREEVIEW_FIRST_NEW_ID + 1 :
            if gui.QuestionDialog("Are you sure you want to delete this step?"):
                self.lsd.remove_step(self.index)
                self.lsd.save_to_file(self.dataItem.json_path)
                c4d.SpecialEventAdd(ID_MSG_REMOVE_STEP)

@dataclass
class Entry:
    """The Entry class, used for the search bar of quick tab."""
    entryId: int
    entryName: str
    selectionState: bool

@dataclass
class ImageArea(GeUserArea):

    path: str = os.path.join(RES_PATH, "bmp", "default_preview.png")

    def __post_init__(self) -> None:
        if os.path.exists(self.path):
            bmp: c4d.bitmaps.BaseBitmap = c4d.bitmaps.BaseBitmap()
            result, isMovie = bmp.InitWith(self.path)
            if result == c4d.IMAGERESULT_OK:
                if isMovie:
                    self.type: str = "movie"
                else:
                    self.type: str = "image"
                self._bitmap: c4d.bitmaps.BaseBitmap = bmp
                self.height: int = self._bitmap.GetBh()
                self.width: int = self._bitmap.GetBw()
                self.size: int = self.get_size(self.path)
                self.name: str = os.path.basename(self.path)

    def convert_size(self, size_bytes) -> str :
        if size_bytes <= 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = '%.1f' % (size_bytes / p)
        res = "%s %s" % (s, size_name[i])
        return res

    def get_size(self, filepath) -> str :
        if os.path.exists(filepath):
            return self.convert_size(os.path.getsize(filepath))
        return ""

    @staticmethod
    def scaleImage(path: str, w: int) -> c4d.bitmaps.BaseBitmap:
        bmp = c4d.bitmaps.BaseBitmap()
        result, ismovie = bmp.InitWith(path)
        if result == c4d.IMAGERESULT_OK: 
            if bmp.GetBw() < w:
                return None
            h = int((bmp.GetBh()/float(bmp.GetBw()))*w)
            dst = c4d.bitmaps.BaseBitmap()
            dst.Init(w, h, depth=16, flags=c4d.INITBITMAPFLAGS_0)
            bmp.ScaleBicubic(dst, 0, 0, bmp.GetBw()-1, bmp.GetBh()-1, 0, 0, dst.GetBw()-1, dst.GetBh()-1)
            return dst

    def DrawMsg(self, x1, y1, x2, y2, msg: BaseContainer) -> None:
        self.OffScreenOn()
        self.SetClippingRegion(x1, y1, x2, y2)
        bmp: c4d.bitmaps.BaseBitmap = ImageArea.scaleImage(self.path, 480)
        self.DrawBitmap(bmp,
                        x1, y1, x2, y2,
                        0, 0, bmp.GetBw(), bmp.GetBh(),
                        mode=c4d.BMP_NORMAL)

    def GetMinSize(self) -> tuple[int,int]:
        return 480, 270

class LSD_Setup_Dialog(GeDialog):
    """Setup Dialog class."""
    ID_EMPTY: int = 50
    ID_TXT: int = 1000

    ID_GROUP_MAIN: int = 1001
    ID_GROUP_CREATE: int = 1002
    ID_GROUP_WELCOME: int = 1003
    ID_GROUP_COMPLETE: int = 1004
    ID_GROUP_CATEGORY: int = 1005
    ID_GROUP_TAGS: int = 1006
    ID_GROUP_BTN: int = 1007

    ID_TITLE: int = 2000
    ID_AUTHOR: int = 2001
    ID_DURATION: int = 2002
    ID_WELCOME_MEDIA: int = 2003
    ID_WELCOME_DESCRIPTION: int = 2004
    ID_COMPLETE_MEDIA: int = 2005
    ID_COMPLETE_DESCRIPTION: int = 2006
    ID_STEP_COUNT: int = 2007
    ID_CATEGORY: int = 2008
    ID_TAGS: int = 2009
    ID_CATEGORY_HELPER: int = 2010
    ID_TAGS_HELPER: int = 2011

    ID_BTN_WELCOME_MEDIA: int = 3000
    ID_BTN_COMPLETE_MEDIA: int = 3001
    ID_BTN_OK: int = 3002
    ID_BTN_CANCEL: int = 3003

    def __init__(self, source_data: LearningSourceData = None, data_item: MetaDataItem = None) -> None:
        self.source_data: LearningSourceData|None = source_data
        self.data_item: MetaDataItem|None = data_item
        self.edit_mode: bool = True if self.source_data is not None else False
        if self.edit_mode:
            self.title: str = "Learning Source Editor"
        else:
            self.title: str = "Learning Source Creator"
        self.data_manager: DataManager = None

    def init_helper(self) -> str:
        
        self.FreeChildren(self.ID_CATEGORY_HELPER)
        for nid, item in enumerate(self.data_manager.categories, start=100):
            self.AddChild(self.ID_CATEGORY_HELPER, nid, f"&i12676&{item}")

        self.FreeChildren(self.ID_TAGS_HELPER)
        for nid, item in enumerate(self.data_manager.tags, start=100):
            self.AddChild(self.ID_TAGS_HELPER, nid, f"&i12676&{item}")

    def CreateLayout(self):
        """This Method is called automatically when Cinema 4D Create the Layout (display) of the Dialog."""

        self.SetTitle(self.title)

        if self.GroupBegin(self.ID_GROUP_MAIN, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=2, rows=0):

            self.GroupBorderNoTitle(c4d.BORDER_GROUP_IN)
            self.GroupBorderSpace(8,8,8,8)

            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Category", initw=200)
            if self.GroupBegin(self.ID_GROUP_COMPLETE, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=3, rows=0):
                
                self.AddEditText(self.ID_CATEGORY, flags=c4d.BFH_SCALEFIT)
                self.AddPopupButton(self.ID_CATEGORY_HELPER, flags=c4d.BFH_RIGHT)
            self.GroupEnd()

            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Tags", initw=200)
            if self.GroupBegin(self.ID_GROUP_COMPLETE, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=3, rows=0):
                self.AddEditText(self.ID_TAGS, flags=c4d.BFH_SCALEFIT)
                self.AddPopupButton(self.ID_TAGS_HELPER, flags=c4d.BFH_RIGHT)
            self.GroupEnd()

            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Title", initw=200)
            self.AddEditText(self.ID_TITLE, flags=c4d.BFH_SCALEFIT)

            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Author", initw=200)
            self.AddEditText(self.ID_AUTHOR, flags=c4d.BFH_SCALEFIT)

            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Duration", initw=200)
            self.AddEditText(self.ID_DURATION, flags=c4d.BFH_SCALEFIT)

            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Welcome Media", initw=200)
            if self.GroupBegin(self.ID_GROUP_COMPLETE, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=3, rows=0):
                
                self.AddEditText(self.ID_WELCOME_MEDIA, flags=c4d.BFH_SCALEFIT)
                add_custom_button(self,self.ID_BTN_WELCOME_MEDIA, layout_flag=c4d.BFH_LEFT | c4d.BFV_SCALEFIT, size=(20,20), image=1027025, tool_tips="Browse Media")
            self.GroupEnd()
            
            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Welcome Text", initw=200)
            self.AddEditText(self.ID_WELCOME_DESCRIPTION, flags=c4d.BFH_SCALEFIT)

            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Complete Media", initw=200)
            if self.GroupBegin(self.ID_GROUP_WELCOME, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=3, rows=0):
                self.AddEditText(self.ID_COMPLETE_MEDIA, flags=c4d.BFH_SCALEFIT)
                add_custom_button(self,self.ID_BTN_COMPLETE_MEDIA, layout_flag=c4d.BFH_LEFT | c4d.BFV_SCALEFIT, size=(20,20), image=1027025, tool_tips="Browse Media")
            self.GroupEnd()

            self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Complete Text", initw=200)
            self.AddEditText(self.ID_COMPLETE_DESCRIPTION, flags=c4d.BFH_SCALEFIT)

            if not self.edit_mode:
                self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Setps Count", initw=200)
                self.AddEditNumberArrows(self.ID_STEP_COUNT, flags=c4d.BFH_SCALEFIT)

        self.GroupEnd()

        if self.GroupBegin(self.ID_GROUP_BTN, c4d.BFH_RIGHT | c4d.BFV_SCALEFIT, cols=2, rows=0):
            self.AddButton(self.ID_BTN_OK, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, name="OK")
            self.AddButton(self.ID_BTN_CANCEL, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, name="Cancel")
        self.GroupEnd()
        return True
    
    def InitValues(self) -> bool:
        self.data_manager: DataManager = DataManager()
        self.init_helper()

        if not self.edit_mode:
            self.SetString(self.ID_CATEGORY, "Category Name Here", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetString(self.ID_TAGS, "Tag1, Tag2, Tag3", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetString(self.ID_TITLE, "Your Title Here", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetString(self.ID_AUTHOR, "Creator Name Here", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetString(self.ID_DURATION, "Duration Time in Minutes(Int)", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetString(self.ID_WELCOME_MEDIA, "Welcome Media File Path", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetString(self.ID_WELCOME_DESCRIPTION, "Welcome Description Here", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetString(self.ID_COMPLETE_MEDIA, "Complete Media File Path", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetString(self.ID_COMPLETE_DESCRIPTION, "Complete Description Here", flags=c4d.EDITTEXT_HELPTEXT)
            self.SetInt32(self.ID_STEP_COUNT, 1)
        else:
            self.SetString(self.ID_CATEGORY, self.data_item.category)
            self.SetString(self.ID_TAGS, ", ".join(self.data_item.tags))
            self.SetString(self.ID_TITLE, self.source_data.tutorial_title)
            self.SetString(self.ID_AUTHOR, self.source_data.author)
            self.SetString(self.ID_DURATION, str(self.source_data.duration_minutes))
            self.SetFilename(self.ID_WELCOME_MEDIA, self.source_data.welcome_media)
            self.SetString(self.ID_WELCOME_DESCRIPTION, self.source_data.welcome_description)
            self.SetFilename(self.ID_COMPLETE_MEDIA, self.source_data.complete_media)
            self.SetString(self.ID_COMPLETE_DESCRIPTION, self.source_data.complete_description)
        return True
    
    def browse_media(self, cid: int) -> None:
        """Opens a file browser to select a media file."""
        file_path = c4d.storage.LoadDialog(title="Select a media file", flags=c4d.FILESELECT_LOAD, type=c4d.FILESELECTTYPE_ANYTHING)
        if file_path:
            self.SetFilename(cid, file_path)

    def Command(self, id: int, msg: c4d.BaseContainer) -> bool:
        if id == self.ID_BTN_WELCOME_MEDIA:
            self.browse_media(self.ID_WELCOME_MEDIA)

        elif id == self.ID_BTN_COMPLETE_MEDIA:
            self.browse_media(self.ID_COMPLETE_MEDIA)

        elif id == self.ID_BTN_OK:
            if not self.edit_mode:
                # lsd
                lsd: LearningSourceData = LearningSourceData(
                    tutorial_title=self.GetString(self.ID_TITLE),
                    author=self.GetString(self.ID_AUTHOR),
                    duration_minutes=int(self.GetString(self.ID_DURATION)) if self.GetString(self.ID_DURATION).isdigit() else 0,
                    welcome_media=self.GetFilename(self.ID_WELCOME_MEDIA),
                    welcome_description=self.GetString(self.ID_WELCOME_DESCRIPTION),
                    complete_media=self.GetFilename(self.ID_COMPLETE_MEDIA),
                    complete_description=self.GetString(self.ID_COMPLETE_DESCRIPTION)
                )
                for _ in range(self.GetInt32(self.ID_STEP_COUNT)):
                    lsd.add_step()

                # data item
                data_item = MetaDataItem(
                    title=self.GetString(self.ID_TITLE), 
                    category=self.GetString(self.ID_CATEGORY), 
                    tags=self.GetString(self.ID_TAGS).split(",") if "," in self.GetString(self.ID_TAGS) else [])

                # data manager
                data_manager = DataManager()
                data_manager.add_item(item=data_item, lsd=lsd)
                lsd.save_to_file(data_item.json_path)
                data_manager.save_data()
                c4d.SpecialEventAdd(ID_MSG_DATA_RELOAD)
            else:
                lsd: LearningSourceData = LearningSourceData(
                    tutorial_title=self.GetString(self.ID_TITLE),
                    author=self.GetString(self.ID_AUTHOR),
                    duration_minutes=int(self.GetString(self.ID_DURATION)) if self.GetString(self.ID_DURATION).isdigit() else 0,
                    welcome_media=self.GetFilename(self.ID_WELCOME_MEDIA),
                    welcome_description=self.GetString(self.ID_WELCOME_DESCRIPTION),
                    complete_media=self.GetFilename(self.ID_COMPLETE_MEDIA),
                    complete_description=self.GetString(self.ID_COMPLETE_DESCRIPTION),
                    steps = self.source_data.steps
                )
                lsd.save_to_file(self.data_item.json_path)
                # data item
                data_item = MetaDataItem(
                    title=self.GetString(self.ID_TITLE), 
                    category=self.GetString(self.ID_CATEGORY), 
                    tags=self.GetString(self.ID_TAGS).split(",") if "," in self.GetString(self.ID_TAGS) else [],
                    folder_path=os.path.join(DATA_FOLDER,self.GetString(self.ID_TITLE)))
                # data manager
                data_manager = DataManager()
                data_manager.replace_item(self.GetString(self.ID_TITLE),data_item)

                data_manager.save_data()

                c4d.SpecialEventAdd(ID_MSG_DATA_CHANGED)
            self.Close()

        elif id == self.ID_BTN_CANCEL:
            self.Close()

        elif id == self.ID_CATEGORY_HELPER:
            self.SetString(self.ID_CATEGORY, self.data_manager.categories[(self.GetInt32(self.ID_CATEGORY_HELPER)-100)])

        elif id == self.ID_TAGS_HELPER:
            tags = self.GetString(self.ID_TAGS)
            new_tags = self.data_manager.tags[(self.GetInt32(self.ID_TAGS_HELPER)-100)]
            if not tags:
                tags += f"{new_tags}"
            if new_tags not in tags:
                tags += f",{new_tags}"
            self.SetString(self.ID_TAGS, tags)
        return True

    @staticmethod
    def show_dialog(source_data: LearningSourceData = None, data_item: MetaDataItem = None) -> None:
        """Static method to show the dialog."""
        dialog = LSD_Setup_Dialog(source_data, data_item)
        dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=500, defaulth=400,xpos=-3, ypos=-3)

class DescriptionDialog(GeDialog):

    # Group IDs
    ID_GROUP_MAIN: int = 1000
    ID_GROUP_1: int = 1001
    ID_DESCRIPTION: int = 1002
    ID_BTN_OK: int = 1003
    ID_BTN_CANCEL: int = 1004

    def __init__(self, description: str=""):
        super().__init__()
        self.description = description

    def CreateLayout(self):
        """This Method is called automatically when Cinema 4D Create the Layout (display) of the Dialog."""

        self.SetTitle("Description Editor")

        if self.GroupBegin(self.ID_GROUP_MAIN, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0):

            self.GroupBorderNoTitle(c4d.BORDER_GROUP_IN)
            self.GroupBorderSpace(8,8,8,8)

            self.AddMultiLineEditText(self.ID_DESCRIPTION, flags=c4d.BFH_SCALEFIT|c4d.BFV_SCALEFIT, initw=500, inith=200, style=c4d.DR_MULTILINE_WORDWRAP|c4d.DR_MULTILINE_NO_BORDER)

            if self.GroupBegin(self.ID_GROUP_1, c4d.BFH_CENTER | c4d.BFV_SCALEFIT, cols=2, rows=0):
                self.AddButton(self.ID_BTN_OK, flags=c4d.BFH_CENTER | c4d.BFV_BOTTOM, name="OK")
                self.AddButton(self.ID_BTN_CANCEL, flags=c4d.BFH_CENTER | c4d.BFV_BOTTOM, name="Cancel")
            self.GroupEnd()

        self.GroupEnd()
        return True

    def InitValues(self) -> bool:
        self.SetString(self.ID_DESCRIPTION, self.description)
        return True

    def Command(self, id: int, msg: c4d.BaseContainer) -> bool:
        if id == self.ID_BTN_OK:
            self.description = self.GetString(self.ID_DESCRIPTION)
            self.Close()
        elif id == self.ID_BTN_CANCEL:
            self.Close()
        return True
    
    @staticmethod
    def show_dialog(data_item: MetaDataItem) -> str:
        """Static method to show the dialog."""
        dialog = DescriptionDialog(data_item)
        dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=500, defaulth=400)
        return dialog.description

class MetaManagerDialog(GeDialog):
    
    START: int = 100
    GROUPS: int = 5
    TEXT: int = 1
    BUTTON: int = 2

    ID_Group_Main: int = 1000
    ID_GROUP_DYNAMIC: int = 1001
    
    def __init__(self):
        super().__init__()

    
    def add_item(self, index: int, item: str) -> None:

        if self.GroupBegin(self.START + index * self.GROUPS, c4d.BFH_SCALEFIT |c4d.BFV_SCALEFIT, 3, 0, ""):
            self.GroupBorderSpace(20, 4, 20, 4)

            self.AddStaticText(self.START + index, c4d.BFH_LEFT, 0, 0,str(index) + " : ",c4d.BORDER_WITH_TITLE_BOLD)
            self.AddStaticText(self.START + index + self.TEXT, c4d.BFH_SCALEFIT, 0, 0,item)
            add_custom_button(self,self.START + index + self.BUTTON, layout_flag=c4d.BFH_RIGHT | c4d.BFV_CENTER,size=(16,16), image=13957,no_fading=False)

        self.GroupEnd()     
    
    def CreateLayout(self):

        self.SetTitle("MetaData Manager")

        if self.GroupBegin(self.ID_Group_Main, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0, title=""):
            
            self.GroupBorderNoTitle(c4d.BORDER_THIN_INb)
            self.GroupBorderSpace(4, 4, 4, 4)
            self.GroupSpace(4, 4)

            if self.GroupBegin(self.ID_GROUP_DYNAMIC, c4d.BFH_CENTER | c4d.BFV_SCALEFIT, cols=1, rows=0, title='', groupflags=0, initw=200, inith=0):
                self.GroupSpace(4, 4)
                pass
            self.GroupEnd()
                
        return True

    def RefreshItems(self) -> None:
        self.LayoutFlushGroup(self.ID_GROUP_DYNAMIC)
        for index,item in enumerate(self.items):
            self.add_item(index,item)
        self.LayoutChanged(self.ID_GROUP_DYNAMIC)

    def InitValues(self) -> bool:
        self.data_manager = DataManager()
        self.data_manager.reload()
        self.items: list[str] = [str(item) for item in self.data_manager.data_items]
        self.RefreshItems()
        return super().InitValues()

    def Command(self, id: int, msg: BaseContainer) -> bool:

        id_index = id - self.START - self.BUTTON
        item = self.items[id_index]
        self.items.remove(item)
        self.data_manager.remove_item(item)
        self.data_manager.save_data()
        self.RefreshItems()
        c4d.SpecialEventAdd(ID_MSG_DATA_RELOAD)
        
        return super().Command(id, msg)
  
    @staticmethod
    def show_dialog():
        global  fav_dlg
        fav_dlg = MetaManagerDialog()
        fav_dlg.Open(c4d.DLG_TYPE_MODAL, pluginid=0, xpos=- 1, ypos=- 1, defaultw=320, defaulth=0, subid=0)

class LearningCreatorDialog(GeDialog):

    # Group IDs
    ID_GROUP_MAIN: int = 1000
    ID_GROUP_LEFT_BAR: int = 1001
    ID_GROUP_RIGHT_BAR: int = 1002
    ID_GROUP_SETUP: int = 1003
    ID_GROUP_TREEVIEW: int = 1004
    ID_GROUP_STEP_INFO: int = 1005
    ID_GROUP_STEP_PREVIEW: int = 1006
    ID_GROUP_LSD_INFO: int = 1007
    ID_GROUP_SUB_1: int = 1008
    ID_GROUP_SUB_2: int = 1009
    ID_GROUP_SUB_3: int = 1010
    ID_GROUP_SUB_4: int = 1011
    ID_GROUP_SUB_5: int = 1012
    ID_GROUP_SUB_6: int = 1013
    ID_GROUP_SUB_7: int = 1014
    ID_GROUP_SUB_8: int = 1015
    ID_GROUP_SUB_9: int = 1016
    ID_GROUP_SUB_10: int = 1017
    ID_GROUP_SUB_11: int = 1018
    ID_GROUP_SUB_12: int = 1019
    ID_GROUP_SUB_13: int = 1020
    ID_GROUP_SUB_14: int = 1021
    ID_GROUP_SUB_15: int = 1022
    ID_GROUP_SUB_16: int = 1023
    ID_GROUP_SWITCH_SHORTCUT: int = 1024

    # Setup IDs
    ID_CATEGORY: int = 2000
    ID_TITLE: int = 2001
    ID_SETUP_BTN: int = 2002
    ID_NEW_ITEM_BTN: int = 2003
    ID_QUICKTAB_BAR: int = 2004
    ID_EDIT_LSD_BTN: int = 2005
    ID_SAVE_LSD_BTN: int = 2006
    ID_REMOVE_STEP_BTN: int = 2007

    # Treeview IDs
    ID_TREEVIEW: int = 3000

    # LSD Info IDs
    ID_LSD_TITLE: int = 3001
    ID_LSD_AUTHOR: int = 3002
    ID_LSD_DURATION: int = 3003
    ID_LSD_WELCOME_MEDIA: int = 3004
    ID_LSD_WELCOME_TEXT: int = 3005
    ID_LSD_COMPLETE_MEDIA: int = 3006
    ID_LSD_COMPLETE_TEXT: int = 3007
    ID_LSD_WELCOME_BTN: int = 3008
    ID_LSD_COMPLETE_BTN: int = 3009
    ID_STEP_MEDIA_BTN: int = 3010
    ID_LSD_SHORTCUT_SWIRCH: int = 3011
    # Data Item
    ID_DATA_ITEM_CATEGORY: int = 3012
    ID_DATA_ITEM_TAGS: int = 3013

    # Step Info IDs
    ID_STEP_DESCRIPTION: int = 4000
    ID_STEP_MEDIA: int = 4001
    ID_STEP_WINDOW_PLACEMENT: int = 4002
    ID_STEP_EVENTS: int = 4003
    ID_STEP_CMD_SHORTCUT: int = 4004
    ID_STEP_MANAGER_HIGHLIGHT: int = 4005
    ID_STEP_CMD_BUBBLE: int = 4006
    ID_STEP_MANAGER_HELPER: int = 4007
    ID_STEP_EVENT_HELPER: int = 4008
    ID_STEP_PLACMENT_HELPER: int = 4009
    ID_STEP_LOCALIZE_FILE: int = 4010
    ID_STEP_CMD_MANAGER: int = 4011
    ID_STEP_SAVE_DESCRIPTION: int = 4012
    ID_STEP_RESTROE_DESCRIPTION: int = 4013
    ID_STEP_EDIT_DESCRIPTION: int = 4014

    # Step Preview IDs
    ID_STEP_PREVIEW: int = 5000
    ID_STEP_NAME: int = 5001
    ID_STEP_PATH: int = 5002
    ID_STEP_SIZE: int = 5003
    ID_PREVIEW_SUB_DLG: int = 5004

    ID_GROUP_PALETTE: int = 200

    # Text IDs
    ID_TXT: int = 6000

    # Menu
    ID_MENU_PRECIEW: int = 7000
    ID_IMAGE_AREA: int = 7001
    ID_MENU_OPEN: int = 7002
    ID_MENU_SAVE_PANNEL: int = 7003
    ID_MENU_PANNEL_HANDLER: int = 7004
    ID_MENU_UPDATE: int = 7005
    ID_MENU_MANAGE: int = 7006

    # Info
    ID_INFO_MEDIA: int = 8000
    ID_INFO_WINDOWS_PLACEMENT: int = 8001
    ID_INFO_EVENTS: int = 8002
    ID_INFO_CMD_SHORTCUT: int = 8003
    ID_INFO_MANAGER_HIGHLIGHT: int = 8004
    ID_INFO_CMD_BUBBLE: int = 8005

    ## Core Override Methods
    def __init__(self) -> None:
        super().__init__()
        self.border_space: tuple[int] = [4, 4, 4, 4]
        self.tree: Tree = None
        self.weights_saved: bool = False
        self.weights: BaseContainer = c4d.BaseContainer()
        # quick tab
        self.tab_element = ["All","Categoty", "Tag"]
        self.entries: list[Entry] = []
        self.entriesHash: int = 0
        self.data_manager: DataManager = None
        self.show_preview: bool = True
        # data
        self._categorys: list[str] = []
        self._tags: list[str] = []
        # self properties
        self.title: str = "Learning Source Creator"

    def CreateLayout(self) -> bool:
        
        self.SetTitle(self.title)

        if self.MenuFlushAll():
            if self.MenuSubBegin("File"):
                self.MenuAddString(self.ID_MENU_UPDATE, "Update metadata")
                self.MenuAddString(self.ID_MENU_MANAGE, "Manage metadata")
                self.MenuAddSeparator()
                self.MenuAddString(self.ID_MENU_OPEN, "Open Data Folder")
            self.MenuSubEnd()
            if self.MenuSubBegin("Functions"):
                self.MenuAddCommand(CMD_LEARNING_PANNEL)
                self.MenuAddCommand(CMD_LEARNING_HANDLER)
            self.MenuSubEnd()
        self.MenuFinished()
        
        if self.GroupBegin(self.ID_GROUP_MAIN, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=2, rows=1, groupflags=c4d.BFV_GRIDGROUP_ALLOW_WEIGHTS):
            self.GroupBorderSpace(*self.border_space)
            self.GroupBorderNoTitle(c4d.BORDER_GROUP_IN)

            ## Left
            if self.GroupBegin(self.ID_GROUP_LEFT_BAR, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0):
                self.GroupBorderNoTitle(c4d.BORDER_GROUP_IN)
                self.GroupBorderSpace(*self.border_space)
                ## Filter
                if self.GroupBegin(self.ID_GROUP_SETUP, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=2, rows=0):
                    self.GroupBorderNoTitle(c4d.BORDER_THIN_IN)
                    self.GroupBorderSpace(*self.border_space)

                    self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Filter",  initw=200)
                    self._quickTab = self._add_quicktab_element()
                    self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="KeyWords", initw=200)
                    self.filter_combobox = self.AddComboBox(self.ID_CATEGORY, c4d.BFH_SCALEFIT , initw=120, inith=0, specialalign=False, allowfiltering=False)
                    self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Title", initw=200)
                    self.porject = self.AddComboBox(self.ID_TITLE, c4d.BFH_SCALEFIT , initw=120, inith=0, specialalign=False, allowfiltering=False)
                    
                self.GroupEnd()

                self.AddSeparatorH(2,c4d.BFH_SCALEFIT)

                ## Buttons
                if self.GroupBegin(self.ID_GROUP_SUB_13, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=2):
                    self.GroupBorderSpace(*self.border_space)

                    self.AddStaticText(self.ID_TXT, c4d.BFH_SCALEFIT, name="Learning Source", initw=200)
                    self.AddButton(self.ID_SETUP_BTN, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, name="Create")
                    self.AddButton(self.ID_EDIT_LSD_BTN, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, name="Edit")

                    self.AddStaticText(self.ID_TXT, c4d.BFH_SCALEFIT, name="Steps", initw=200)
                    # self.AddStaticText(self.ID_TXT, c4d.BFH_SCALEFIT)
                    self.AddButton(self.ID_NEW_ITEM_BTN, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, name="Create")
                    self.AddButton(self.ID_REMOVE_STEP_BTN, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, name="Remove")

                self.GroupEnd()

                self.AddSeparatorH(2,c4d.BFH_SCALEFIT)

                if self.ScrollGroupBegin(self.ID_GROUP_TREEVIEW, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, c4d.SCROLLGROUP_HORIZ | c4d.SCROLLGROUP_VERT):
                    self.GroupBorderNoTitle(c4d.BORDER_THIN_IN)
                    self.GroupBorderSpace(*self.border_space)
                    self.tree = Tree(self, self.ID_TREEVIEW, noenterrename=True, outside_drop=False, no_delete=False, no_verticalscroll=False, has_header=False,no_multiselect=True)
                self.GroupEnd()             

            self.GroupEnd() 
            
            ## Right
            if self.GroupBegin(self.ID_GROUP_RIGHT_BAR, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0):
                self.GroupBorderNoTitle(c4d.BORDER_GROUP_IN)
                self.GroupBorderSpace(8,8,8,8)

                if self.GroupBegin(self.ID_GROUP_STEP_INFO, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0):
                    # self.GroupBorderNoTitle(c4d.BORDER_ACTIVE_4)
                    self.GroupBorderNoTitle(c4d.BORDER_THIN_IN)
                    self.GroupBorderSpace(8,8,8,8)

                    ## description
                    if self.GroupBegin(self.ID_GROUP_SUB_3, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=4, rows=0):
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Description", initw=200)
                        self.AddMultiLineEditText(self.ID_STEP_DESCRIPTION, flags=c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, inith=160,initw=200,
                                                  style=c4d.DR_MULTILINE_WORDWRAP|c4d.DR_MULTILINE_NO_BORDER|c4d.DR_MULTILINE_READONLY)
                        add_custom_button(self,self.ID_STEP_EDIT_DESCRIPTION, layout_flag=c4d.BFH_LEFT | c4d.BFV_TOP, size=(20,20), image=ICON_EIDT, tool_tips="Edit Description")
                    self.GroupEnd()

                    ## media
                    if self.GroupBegin(self.ID_GROUP_SUB_4, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=4, rows=0):
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Media", initw=200)
                        self.AddEditText(self.ID_STEP_MEDIA, flags=c4d.BFH_SCALEFIT)
                        add_custom_button(self,self.ID_STEP_MEDIA_BTN, layout_flag=c4d.BFH_LEFT | c4d.BFV_SCALEFIT, size=(20,20), image=1027025, tool_tips="Browse Media")
                        add_custom_button(self,self.ID_STEP_LOCALIZE_FILE, layout_flag=c4d.BFH_LEFT | c4d.BFV_SCALEFIT, size=(20,20), image=1050522, tool_tips="Localize Media")
                    self.GroupEnd()

                    ## window placement
                    if self.GroupBegin(self.ID_GROUP_SUB_5, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=0):
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Window Placement", initw=200)
                        self.AddEditText(self.ID_STEP_WINDOW_PLACEMENT, flags=c4d.BFH_SCALEFIT)
                        self.AddPopupButton(self.ID_STEP_PLACMENT_HELPER, flags=c4d.BFH_RIGHT)
                    self.GroupEnd()

                    ## ui events
                    if self.GroupBegin(self.ID_GROUP_SUB_6, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=0):
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="UI Events", initw=200)
                        self.AddEditText(self.ID_STEP_EVENTS, flags=c4d.BFH_SCALEFIT)
                        self.AddPopupButton(self.ID_STEP_EVENT_HELPER, flags=c4d.BFH_RIGHT)
                    self.GroupEnd()

                    ## cmd shortcut
                    if self.GroupBegin(self.ID_GROUP_SUB_7, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=0):
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Command Shortcut", initw=200)
                        if self.GroupBegin(self.ID_GROUP_SWITCH_SHORTCUT, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=0):
                            self.AddEditText(self.ID_STEP_CMD_SHORTCUT, flags=c4d.BFH_SCALEFIT)
                        self.GroupEnd()
                        self.AddCheckbox(self.ID_LSD_SHORTCUT_SWIRCH, c4d.BFH_RIGHT,0,0,"Shortcut Input")
                    self.GroupEnd()

                    ## manager highlight
                    if self.GroupBegin(self.ID_GROUP_SUB_8, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=0):
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Manager Highlight", initw=200)
                        self.AddEditText(self.ID_STEP_MANAGER_HIGHLIGHT, flags=c4d.BFH_SCALEFIT)
                        self.AddPopupButton(self.ID_STEP_MANAGER_HELPER, flags=c4d.BFH_RIGHT)
                    self.GroupEnd()

                    ## cmd bubble
                    if self.GroupBegin(self.ID_GROUP_SUB_9, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=0):
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT, name="Command Bubble", initw=200)
                        self.AddEditText(self.ID_STEP_CMD_BUBBLE, flags=c4d.BFH_SCALEFIT)
                        add_custom_button(self,self.ID_STEP_CMD_MANAGER, layout_flag=c4d.BFH_LEFT | c4d.BFV_SCALEFIT, size=(20,20), image=300000186, tool_tips="Open Command Manager")
                    self.GroupEnd()

                self.GroupEnd()

                self.AddSeparatorH(2,c4d.BFH_SCALEFIT)

                ## Preivew
                if self.GroupBegin(self.ID_GROUP_STEP_PREVIEW,  c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=3, rows=0):
                    ...
                self.GroupEnd()
            
            self.GroupEnd()

        self.GroupEnd()

        return True

    def InitValues(self) -> bool:
        ## data manager
        self.data_manager = DataManager()
        self.data_manager.reload()
        ## temp data
        self._categorys = self.data_manager.categories
        self._tags = self.data_manager.tags
        self.init_combobox()
        self.init_project()
        self.SetBool(self.ID_LSD_SHORTCUT_SWIRCH, False)
        self.init_helper_drop()
        ## GroupWeightsLoad
        if not self.weights_saved:
            self.weights.SetInt32(c4d.GROUPWEIGHTS_PERCENT_W_CNT, 2)     
            self.weights.SetFloat(c4d.GROUPWEIGHTS_PERCENT_W_VAL+0, 30.0)
            self.weights.SetFloat(c4d.GROUPWEIGHTS_PERCENT_W_VAL+1, 70.0)
            self.weights_saved = True
        self.GroupWeightsLoad(self.ID_GROUP_MAIN, self.weights)
        ## Tree
        self.tree.init_signals()
        self.tree.selection_changed.connect(self.on_tree_selection_changed)
        self.tree.context_menu_called.connect(self.on_tree_context_menu_called)
        self.init_tree()
        self.on_tree_selection_changed()
        return super().InitValues()
    
    def Command(self, id: int, msg: BaseContainer) -> bool:
        ## menu
        if id == self.ID_MENU_OPEN:
            c4d.storage.ShowInFinder(self.data_manager.root_path, True)
        elif id == self.ID_MENU_UPDATE:
            self.data_manager.update_all()
            self.InitValues()
        elif id == self.ID_MENU_MANAGE:
            MetaManagerDialog.show_dialog()

        ## project
        elif id == self.ID_QUICKTAB_BAR and self._quickTab:
            for entry in self.entries:
                entry.selectionState = self._quickTab.IsSelected(entry.entryId)
            
            newSelectionState = hash(str(self.entries))
            if newSelectionState != self.entriesHash:
                self.entriesHash = newSelectionState
                self.init_combobox()
                self.init_project()
                self.redraw_tree()
                self.on_tree_selection_changed()

        elif id == self.ID_CATEGORY:
            self.init_project()
            self.redraw_tree()
            self.on_tree_selection_changed()

        elif id == self.ID_TITLE:
            self.redraw_tree()
            self.on_tree_selection_changed()

        ## button : lsd
        elif id == self.ID_SETUP_BTN:
            LSD_Setup_Dialog.show_dialog()

        elif id == self.ID_EDIT_LSD_BTN:
            data_item: MetaDataItem = self.get_active_project()
            lsd: LearningSourceData =  data_item.get_learning_source_item()
            LSD_Setup_Dialog.show_dialog(lsd, data_item)

        ## button : step
        elif id == self.ID_REMOVE_STEP_BTN:
            if gui.QuestionDialog("Are you sure you want to delete this step?"):
                data_item: MetaDataItem = self.get_active_project()
                lsd: LearningSourceData =  data_item.get_learning_source_item()
                lsd.remove_step(self.get_active_index())
                lsd.save_to_file(data_item.json_path)
                c4d.SpecialEventAdd(ID_MSG_REMOVE_STEP)

        elif id == self.ID_NEW_ITEM_BTN:
            data_item: MetaDataItem = self.get_active_project()
            lsd: LearningSourceData =  data_item.get_learning_source_item()
            lsd.add_step()
            lsd.save_to_file(data_item.json_path)
            self.redraw_tree()
            self.on_tree_selection_changed()

        # Editor: lsd
        elif id == self.ID_STEP_EDIT_DESCRIPTION:
            txt = DescriptionDialog.show_dialog(self.GetString(self.ID_STEP_DESCRIPTION))
            if txt:
                self.SetString(self.ID_STEP_DESCRIPTION, txt)
                self.save_lsd()
                self.redraw_step()

        elif id in [self.ID_STEP_CMD_SHORTCUT, self.ID_STEP_CMD_BUBBLE]:
            self.save_lsd()
            self.redraw_step()

        elif id == self.ID_LSD_SHORTCUT_SWIRCH:
            text: str = self.GetString(self.ID_STEP_CMD_SHORTCUT)

            self.LayoutFlushGroup(self.ID_GROUP_SWITCH_SHORTCUT)
            self.GroupBegin(self.ID_GROUP_SWITCH_SHORTCUT, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=0)

            if self.GetBool(self.ID_LSD_SHORTCUT_SWIRCH):                
                self.AddEditShortcut(self.ID_STEP_CMD_SHORTCUT, flags=c4d.BFH_SCALEFIT)

            else:
                self.AddEditText(self.ID_STEP_CMD_SHORTCUT, flags=c4d.BFH_SCALEFIT)
            self.SetString(self.ID_STEP_CMD_SHORTCUT, text)
            self.LayoutChanged(self.ID_GROUP_SWITCH_SHORTCUT)
            self.save_lsd()
            self.redraw_step()
            
        elif id == self.ID_STEP_MANAGER_HELPER:
            self.SetString(self.ID_STEP_MANAGER_HIGHLIGHT, self.GetInt32(self.ID_STEP_MANAGER_HELPER))
            self.save_lsd()
            self.redraw_step()

        elif id == self.ID_STEP_EVENT_HELPER:
            self.SetString(self.ID_STEP_EVENTS, self.GetInt32(self.ID_STEP_EVENT_HELPER))
            self.save_lsd()
            self.redraw_step()

        elif id == self.ID_STEP_PLACMENT_HELPER:
            text = find_value_by_id(WindowPlacement, self.GetInt32(self.ID_STEP_PLACMENT_HELPER))
            self.SetString(self.ID_STEP_WINDOW_PLACEMENT, text.description)
            self.save_lsd()
            self.redraw_step()

        elif id == self.ID_STEP_CMD_MANAGER:
            c4d.CallCommand(300000186)

        elif id == self.ID_STEP_MEDIA_BTN:
            file_path = c4d.storage.LoadDialog(title="Select a media file", flags=c4d.FILESELECT_LOAD, type=c4d.FILESELECTTYPE_ANYTHING)
            if file_path:
                self.SetFilename(self.ID_STEP_MEDIA, file_path)

        elif id == self.ID_STEP_LOCALIZE_FILE:
            path = self.GetFilename(self.ID_STEP_MEDIA)
            dirpath = os.path.dirname(self.get_active_project().json_path)
            exist: bool = False
            for file in os.listdir(dirpath):
                if file == os.path.basename(path):
                    exist = True
                    break
            if path:
                if os.path.isabs(path):
                    if not exist:
                        shutil.copy(path, os.path.join(dirpath, os.path.basename(path)))
                self.SetString(self.ID_STEP_MEDIA, os.path.basename(path))
                self.save_lsd()
                self.redraw_step()

        return True

    def DestroyWindow(self) -> None:
        pass

    def CoreMessage(self, id: int, msg: c4d.BaseContainer) -> c4d.BaseContainer:
        if id == ID_MSG_REMOVE_STEP:
            self.redraw_tree()
            self.on_tree_selection_changed()

        if id == ID_MSG_NEW_STEP:
            data_item: MetaDataItem = self.get_active_project()
            lsd: LearningSourceData =  data_item.get_learning_source_item()
            lsd.add_step()
            lsd.save_to_file(data_item.json_path)
            self.redraw_tree()
            self.on_tree_selection_changed()

        if id == ID_MSG_DATA_CHANGED:
            self.data_manager.reload()
            self.redraw_step()  
            self.redraw_preview()    

        if id == ID_MSG_DATA_RELOAD:
            self.data_manager.reload()
            self.InitValues()
            
        return super().CoreMessage(id, msg)

    def get_ui_step(self) -> StepData:
        setp = StepData(description=self.GetString(self.ID_STEP_DESCRIPTION).replace('\r', ''),
                        media=self.GetFilename(self.ID_STEP_MEDIA),
                        window_placement=self.GetString(self.ID_STEP_WINDOW_PLACEMENT),
                        command_id_shortcut=self.GetString(self.ID_STEP_CMD_SHORTCUT),
                        ui_event=self.GetString(self.ID_STEP_EVENTS),
                        ui_manager_highlight=self.GetString(self.ID_STEP_MANAGER_HIGHLIGHT),
                        ui_command_bubble=self.GetString(self.ID_STEP_CMD_BUBBLE))
        return setp

    def get_ui_dataItem(self) -> MetaDataItem:
        data_item: MetaDataItem = MetaDataItem(
            title=self.GetString(self.ID_LSD_TITLE),
            category=self._categorys[self.GetLong(self.ID_DATA_ITEM_CATEGORY)],
            tags=self._tags[self.GetLong(self.ID_DATA_ITEM_TAGS)])

        pp(data_item.to_dict())

    def get_active_tab(self) -> int:
        index = 0        
        for index, txt in enumerate(self.tab_element):
            if self._quickTab.IsSelected(index):
                return index
        return index

    def get_active_project(self) -> MetaDataItem:
        match self.get_active_tab():
            case 0:
                return self.data_manager.data_items[self.GetLong(self.porject)]
            case 1:
                filter_text = self._categorys[self.GetLong(self.filter_combobox)]
                return self.data_manager.find_by_category(filter_text)[self.GetLong(self.porject)]
            case 2:
                filter_text = self._tags[self.GetLong(self.filter_combobox)]
                return self.data_manager.find_by_tag(filter_text)[self.GetLong(self.porject)]
            case _:
                gui.MessageDialog("Error: Invalid Tab Selected")
                return self.data_manager.data_items[0]

    def get_active_index(self) -> int:
        if len(self.tree.get_selected_items()) == 1:
            active_item: ItemCallBacks = self.tree.get_selected_items()[0].get_meta("call_back")
            return active_item.index
        return 0

    def get_active_step(self) -> dict:
        seleced_items = self.tree.get_selected_items()
        if seleced_items:
            active_item: ItemCallBacks = self.tree.get_selected_items()[0].get_meta("call_back")
            lsd: LearningSourceData = active_item.lsd
            step: dict = lsd.steps[active_item.index]
        else:
            data_item = self.get_active_project()
            lsd: LearningSourceData = data_item.get_learning_source_item()
            step: dict = lsd.steps[0]
        return step
    
    ## init data
    def init_combobox(self):
        self.FreeChildren(self.filter_combobox)
        self.Enable(self.filter_combobox, True)
        match self.get_active_tab():
            case 0:
                self.AddChild(self.filter_combobox, 0, f"{wrap_icon(ICON_FOLDER)}{'All Items'}")
                self.SetLong(self.filter_combobox, 0)
                self.Enable(self.filter_combobox, False)
            case 1:
                for index, item in enumerate(self._categorys):
                    self.AddChild(self.filter_combobox, index, f"{wrap_icon(ICON_MENU)}{item}")
                self.SetLong(self.filter_combobox, 0)
            case 2:
                for index, item in enumerate(self._tags):
                    self.AddChild(self.filter_combobox, index, f"{wrap_icon(ICON_BOOK_MARK)}{item}")
                self.SetLong(self.filter_combobox, 0)

    def init_project(self):
        self.FreeChildren(self.porject)
        match self.get_active_tab():
            case 0:
                name_list = [name.title for name in self.data_manager.data_items]
                for index, item in enumerate(name_list):
                    self.AddChild(self.porject, index, f"{wrap_icon(ICON_LSD)}{item}")
                self.SetLong(self.porject, len(name_list)-1)    
            case 1:
                filter_text = self._categorys[self.GetLong(self.filter_combobox)]
                name_list = [name.title for name in self.data_manager.find_by_category(filter_text)]
                for index, item in enumerate(name_list):
                    self.AddChild(self.porject, index, f"{wrap_icon(ICON_LSD)}{item}")
                self.SetLong(self.porject, len(name_list)-1)
            case 2:
                filter_text = self._tags[self.GetLong(self.filter_combobox)]
                name_list = [name.title for name in self.data_manager.find_by_tag(filter_text)]
                for index, item in enumerate(name_list):
                    self.AddChild(self.porject, index, f"{wrap_icon(ICON_LSD)}{item}")
                self.SetLong(self.porject, len(name_list)-1)

    def init_helper_drop(self):
        self.FreeChildren(self.ID_STEP_MANAGER_HELPER)
        for item in ManagerId:
            self.AddChild(self.ID_STEP_MANAGER_HELPER, item.id, f"&i12676&{item.description}")

        self.FreeChildren(self.ID_STEP_EVENT_HELPER)
        for item in ManagerId:
            self.AddChild(self.ID_STEP_EVENT_HELPER, item.id, f"&i12676&{item.description}")

        self.FreeChildren(self.ID_STEP_PLACMENT_HELPER)
        for item in WindowPlacement:
            self.AddChild(self.ID_STEP_PLACMENT_HELPER, item.id, f"&i12676&{item.description}")
    
    def init_tree(self):
        ## Header
        header_list = self.tree.header_list
        header_list.clear()
        header_list.add_user("Name")
        self.tree.update_header_list()
        ## Userdata
        self.tree.userdata.drag_enable = True
        self.tree.userdata.draw_item_space_x = 2
        self.tree.userdata.draw_bitmap_margin = 2
        self.tree.userdata.empty_text = ''
        self.tree.userdata.column_width = {"0":300}
        # self.tree.userdata.line_height = 40
        self.tree.userdata.color_background_normal = c4d.COLOR_BG_DARK1
        self.tree.userdata.color_background_alternate = c4d.COLOR_BG
        self.tree.userdata.color_background_selected = c4d.COLOR_BG_DARK2
        self.tree.userdata.empty_text = ''
        ## Root
        self.tree.clear()
        root = self.tree.create_item()
        ## Create LSD Tree
        self.create_lsd_tree(root)
        self.redraw_preview()
        ## ReDraw
        self.tree.layout_changed()
        self.LayoutChanged(self.ID_TREEVIEW)

    ## refresh data
    def redraw_preview(self):
        if self.show_preview:
            self.LayoutFlushGroup(self.ID_GROUP_STEP_PREVIEW)
            if self.GroupBegin(self.ID_GROUP_STEP_PREVIEW,  c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=3, rows=0):

                ## image preview
                step = self.get_active_step()
                if self.GroupBegin(self.ID_GROUP_SUB_15,  c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=0, rows=2):

                    if self.GroupBegin(self.ID_GROUP_SUB_16,  c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=0, rows=1):
                        # self.GroupBorderNoTitle(c4d.BORDER_ACTIVE_3)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Media Preview", borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                    self.GroupEnd()

                    if self.GroupBegin(self.ID_GROUP_SUB_10,  c4d.BFH_SCALEFIT | c4d.BFV_CENTER):
                        self.GroupBorderSpace(8,8,8,8)
                        self.GroupBorderNoTitle(c4d.BORDER_THIN_INb)

                        dirpath = os.path.dirname(self.get_active_project().json_path)
                        path = step.get("media","")

                        if path:
                            if not os.path.isabs(path):
                                image_path = os.path.join(dirpath, os.path.basename(path))
                            else:
                                image_path = path
                            # print(f"{image_path= }")
                            if os.path.exists(image_path) and os.path.isfile(image_path):
                                self._imageArea: ImageArea = ImageArea(image_path)
                        else:
                            self._imageArea: ImageArea = ImageArea()

                        self.AddUserArea(self.ID_IMAGE_AREA, c4d.BFH_LEFT | c4d.BFV_TOP)
                        self.AttachUserArea(self._imageArea, self.ID_IMAGE_AREA)

                    self.GroupEnd()
                self.GroupEnd()

                self.AddSeparatorV(2,c4d.BFV_SCALEFIT)

                if self.GroupBegin(self.ID_GROUP_SUB_12,  c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=0, rows=2):

                    if self.GroupBegin(self.ID_GROUP_SUB_14,  c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=0, rows=1):
                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Data Preview", borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                    self.GroupEnd()

                    if self.GroupBegin(self.ID_GROUP_SUB_11,  c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=2, rows=0):
                        self.GroupBorderSpace(8,8,8,8)
                        self.GroupBorderNoTitle(c4d.BORDER_THIN_IN)
                        
                        data_item = self.get_active_project()
                        lsd = self.get_active_project().get_learning_source_item()

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Title", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name= lsd.tutorial_title)

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Author", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name= lsd.author)

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Category", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=data_item.category)

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Tags", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=data_item.tags_string_from_list())

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Media", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name= os.path.basename(self.GetString(self.ID_STEP_MEDIA)))

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Media Resolution", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=f"{self._imageArea.width} x {self._imageArea.height}")

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Media Size", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=self._imageArea.size)

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Window Placement", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=self.GetString(self.ID_STEP_WINDOW_PLACEMENT))

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="UI Event", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=self.GetString(self.ID_STEP_EVENTS))

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Command Shortcut", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=self.GetString(self.ID_STEP_CMD_SHORTCUT))

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Manager Highlight", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=self.GetString(self.ID_STEP_MANAGER_HIGHLIGHT))

                        self.AddStaticText(self.ID_TXT, c4d.BFH_CENTER|c4d.BFV_CENTER, name="Command Bubble", initw=200, inith=12,borderstyle=c4d.BORDER_WITH_TITLE_BOLD)
                        self.AddStaticText(self.ID_TXT, c4d.BFH_LEFT|c4d.BFV_CENTER, name=self.GetString(self.ID_STEP_CMD_BUBBLE))

                    self.GroupEnd()
                self.GroupEnd()

            self.GroupEnd()
            self.SetDefaultColor(self.ID_GROUP_SUB_14, c4d.COLOR_BG, BG_DARK)
            self.SetDefaultColor(self.ID_GROUP_SUB_16, c4d.COLOR_BG, BG_DARK)

            self.LayoutChanged(self.ID_GROUP_STEP_PREVIEW)

    def redraw_tree(self):
        ## Root
        self.tree.clear()
        root = self.tree.create_item()
        ## Create LSD Tree
        self.create_lsd_tree(root)
        self.redraw_preview()
        ## ReDraw
        self.tree.layout_changed()
        self.LayoutChanged(self.ID_TREEVIEW)

    def redraw_step(self) -> None:
        if len(self.tree.get_selected_items()) == 1:
            active_item: ItemCallBacks = self.tree.get_selected_items()[0].get_meta("call_back")
            data_item: MetaDataItem = active_item.dataItem
            lsd: LearningSourceData = data_item.get_learning_source_item()
            step: dict = lsd.steps[active_item.index]
        else:
            data_item = self.get_active_project()
            lsd: LearningSourceData = data_item.get_learning_source_item()
            step: dict = lsd.steps[0]

        self.SetString(self.ID_STEP_DESCRIPTION, step.get("description",""))
        self.SetString(self.ID_STEP_MEDIA, step.get("media",""))
        self.SetString(self.ID_STEP_WINDOW_PLACEMENT, step.get("window_placement",""))
        self.SetString(self.ID_STEP_EVENTS, step.get("ui_event",""))
        self.SetString(self.ID_STEP_CMD_SHORTCUT, step.get("command_id_shortcut",""))
        self.SetString(self.ID_STEP_MANAGER_HIGHLIGHT, step.get("ui_manager_highlight",""))
        self.SetString(self.ID_STEP_CMD_BUBBLE, step.get("ui_command_bubble",""))

    def save_lsd(self) -> None:
        data_item = self.get_active_project()
        lsd: LearningSourceData = data_item.get_learning_source_item()
        lsd.update_step(self.get_active_index(), self.get_ui_step())
        lsd.save_to_file(data_item.json_path)
        print(f"save lsd {data_item.title} to {data_item.json_path}")
        self.data_manager.reload()

    ## gui
    def create_lsd_tree(self, root: TreeItem) -> None:
        data_item = self.get_active_project()
        lsd: LearningSourceData = data_item.get_learning_source_item()
        for i in range(len(lsd.steps)):
            tree_item: TreeItem  = root.create_child()
            tree_item.set_meta("call_back", ItemCallBacks(tree_item, data_item, lsd, i))

    def _add_quicktab_element(self) -> gui.QuickTabCustomGui:
        # Creates a QuickTab Custom Gui
        bc = c4d.BaseContainer()
        bc.SetBool(c4d.QUICKTAB_BAR, False)
        bc.SetBool(c4d.QUICKTAB_SHOWSINGLE, True)
        bc.SetBool(c4d.QUICKTAB_NOMULTISELECT, True)
        quickTab: gui.QuickTabCustomGui = self.AddCustomGui(self.ID_QUICKTAB_BAR, c4d.CUSTOMGUI_QUICKTAB, '',
                                           c4d.BFH_SCALEFIT | c4d.BFV_TOP, 0, 0, bc)
        
        if self.entries == []:
            for index, element in enumerate(self.tab_element):
                if index == 0:     
                    self.entries.append(Entry(index, element, True))
                else:
                    self.entries.append(Entry(index, element, False))
                
        self.entriesHash = hash(str(self.entries))
        
        for entry in self.entries:
            quickTab.AppendString(entry.entryId, entry.entryName, entry.selectionState)
        return quickTab

    ## on signals : those are called when the user interacts with the gui
    def on_tree_selection_changed(self):
        self.redraw_step()
        self.redraw_preview()

    def on_tree_context_menu_called(self, tree_item:TreeItem, column:int, lCommand):
        tree_item.get_meta("call_back").context_menu_called(column, lCommand)

    ## unused

#=============================================
# CommandData
#=============================================
class LearningCreatorCommand(c4d.plugins.CommandData):

    def __init__(self) -> None:
        self.dialog: Optional[gui.GeDialog] = None

    def GetDialog(self) -> c4d.gui.GeDialog:
        if self.dialog is None:            
            self.dialog = LearningCreatorDialog()
        return self.dialog

    def Execute(self, doc: documents.BaseDocument) -> bool:        
        dlg: c4d.gui.GeDialog = self.GetDialog()
        if dlg.IsOpen() and not dlg.GetFolding():
            dlg.SetFolding(True)
        else:
            self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, pluginid=int(PLUGINID), defaulth=720, defaultw=1280, xpos=-3, ypos=-3)

        return True

    def RestoreLayout(self, sec_ref) -> bool:
        return self.GetDialog().Restore(pluginid=PLUGINID, secret=sec_ref)

    def GetState(self, doc: c4d.documents.BaseDocument) -> int:
        result: int = c4d.CMD_ENABLED
        dlg: c4d.gui.GeDialog = self.GetDialog()
        if dlg.IsOpen() and not dlg.GetFolding():
            result |= c4d.CMD_VALUE
        return result

    @staticmethod
    def Register() -> None:
        """Registers the plugin hook.
        """
        icon_path = os.path.join(PLUGINPATH, "res", "icons", "icon.png")
        icon = c4d.bitmaps.BaseBitmap()
        icon.InitWith(icon_path)
        c4d.plugins.RegisterCommandPlugin(id = PLUGINID,
                                        str = PLUGINNAME,
                                        info = 0,
                                        icon = icon,
                                        help = PLUGINHELP,
                                        dat = LearningCreatorCommand())

if __name__ == '__main__':
    if c4d.GetC4DVersion() >= 2025100:
        LearningCreatorCommand.Register()
    else:
        print("Learning Source Creator requires Cinema 4D R2025.1.0 or later.")

"""
- Learning Source Creator
    - Learning Data
        - Your Project Name
            - tut
                - tutorial.json (title name should be the same as the folder name(Your Project Name))
        - metadata.json
    - ...
"""