"""
  author  : Safina3D
  description: Enable/Disable/Modify the visibility of one or more objects with a single click
  version : 1.1.0
  website : https://safina3d.blogspot.com
  Repo: https://github.com/safina3d/c4d-object-switcher
"""

import os
import c4d
from c4d import gui, documents, plugins


class Constants:
    PLUGIN_ID = 1027124
    PLUGIN_NAME = "ObjectSwitcher+"

    ID_BTN_APPLY = 2000
    ID_CHKBOX_ON_OFF = 2001

    # Editor
    ID_CBX_VISIBILITY_EDITOR = 2002
    ID_CBX_VISIBILITY_EDITOR_ON = 2003
    ID_CBX_VISIBILITY_EDITOR_OFF = 2004
    ID_CBX_VISIBILITY_EDITOR_DEFAULT = 2005

    # RENDER
    ID_CBX_VISIBILITY_RENDER = 2006
    ID_CBX_VISIBILITY_RENDER_ON = 2007
    ID_CBX_VISIBILITY_RENDER_OFF = 2008
    ID_CBX_VISIBILITY_RENDER_DEFAULT = 2009

    ID_CBX_OBJECT_LIST = 3000


class Helper:

    @staticmethod
    def iterate_hierarchy(op: c4d.BaseObject):
        """ Loop through all objects """
        while op:
            yield op
            if op.GetDown():
                op = op.GetDown()
                continue
            while not op.GetNext() and op.GetUp():
                op = op.GetUp()
            op = op.GetNext()

    @staticmethod
    def get_objects_map():
        """ Return map of all objects, keys values are object type ids, and values are array of objects """
        doc = documents.GetActiveDocument()
        objects_map = {}
        first_object = doc.GetFirstObject()
        for obj in Helper.iterate_hierarchy(first_object):
            object_type = obj.GetType()
            if object_type not in objects_map:
                objects_map[object_type] = []

            objects_map[object_type].append(obj)

        return objects_map


class ObjectSwitecherGUI(gui.GeDialog):

    def __init__(self):
        super().__init__()
        self.object_dict = Helper.get_objects_map()

    def CreateLayout(self):
        self.SetTitle(Constants.PLUGIN_NAME)
        self.GroupBegin(1000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT)
        self.GroupBorderSpace(5, 5, 5, 5)
        self.AddComboBox(Constants.ID_CBX_OBJECT_LIST, c4d.BFH_SCALEFIT)
        # self.AddSeparatorV(0)

        # Editor
        self.AddComboBox(Constants.ID_CBX_VISIBILITY_EDITOR, c4d.BFH_SCALEFIT)
        self.AddChild(Constants.ID_CBX_VISIBILITY_EDITOR, Constants.ID_CBX_VISIBILITY_EDITOR_DEFAULT, "Editor : Default")
        self.AddChild(Constants.ID_CBX_VISIBILITY_EDITOR, Constants.ID_CBX_VISIBILITY_EDITOR_ON,      "Editor   : Visible")
        self.AddChild(Constants.ID_CBX_VISIBILITY_EDITOR, Constants.ID_CBX_VISIBILITY_EDITOR_OFF, "Editor : Hidden")

        # Render
        self.AddComboBox(Constants.ID_CBX_VISIBILITY_RENDER, c4d.BFH_SCALEFIT)
        self.AddChild(Constants.ID_CBX_VISIBILITY_RENDER, Constants.ID_CBX_VISIBILITY_RENDER_DEFAULT, "Renderer : Default")
        self.AddChild(Constants.ID_CBX_VISIBILITY_RENDER, Constants.ID_CBX_VISIBILITY_RENDER_ON, "Renderer : Visible")
        self.AddChild(Constants.ID_CBX_VISIBILITY_RENDER, Constants.ID_CBX_VISIBILITY_RENDER_OFF, "Renderer : Hidden")

        # self.AddSeparatorV(0)
        self.AddCheckbox(Constants.ID_CHKBOX_ON_OFF, c4d.BFH_SCALEFIT, 0, 0, name="Enable")
        # self.AddSeparatorV(0)
        self.AddButton(Constants.ID_BTN_APPLY, c4d.BFH_SCALEFIT, 0, 0, "Apply")

        self.GroupEnd()
        return True

    def InitValues(self):
        self.SetLong(Constants.ID_CBX_VISIBILITY_EDITOR, Constants.ID_CBX_VISIBILITY_EDITOR_DEFAULT)
        self.SetLong(Constants.ID_CBX_VISIBILITY_RENDER, Constants.ID_CBX_VISIBILITY_RENDER_DEFAULT)
        self.SetBool(Constants.ID_CHKBOX_ON_OFF, True)
        if len(self.object_dict) > 0:
            self.SetLong(Constants.ID_CBX_OBJECT_LIST, list(self.object_dict)[0])
        return True

    def Command(self, id, msg):
        if id == Constants.ID_BTN_APPLY:
            selected_id = self.GetLong(Constants.ID_CBX_OBJECT_LIST)
            for obj in self.object_dict[selected_id]:
                obj[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = self.GetBool(Constants.ID_CHKBOX_ON_OFF)
                obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = self._get_combo_box_value(Constants.ID_CBX_VISIBILITY_EDITOR)
                obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = self._get_combo_box_value(Constants.ID_CBX_VISIBILITY_RENDER)

        c4d.EventAdd()
        return True

    def Message(self, msg, result):
        if msg.GetId() == c4d.BFM_GOTFOCUS:
            self.object_dict = Helper.get_objects_map()
            self.FreeChildren(Constants.ID_CBX_OBJECT_LIST)
            has_objects = len(self.object_dict) > 0
            if has_objects:
                for object_id, objects_list in self.object_dict.items():
                    self.AddChild(
                        Constants.ID_CBX_OBJECT_LIST,
                        object_id,
                        f"&i{object_id}& {c4d.GetObjectName(object_id)} ( {len(objects_list)} )"
                    )

                self.SetLong(Constants.ID_CBX_OBJECT_LIST, list(self.object_dict)[0])
            self.LayoutChanged(Constants.ID_CBX_OBJECT_LIST)
            self._update_gui_state(has_objects)

        return gui.GeDialog.Message(self, msg, result)

    def CoreMessage(self, id, msg):
        if id == c4d.EVMSG_CHANGE:
            has_objects = len(self.object_dict) > 0
            self._update_gui_state(has_objects)

        return True

    def _update_gui_state(self, state):
        self.Enable(Constants.ID_BTN_APPLY, state)
        self.Enable(Constants.ID_CHKBOX_ON_OFF, state)
        self.Enable(Constants.ID_CBX_VISIBILITY_EDITOR, state)
        self.Enable(Constants.ID_CBX_VISIBILITY_RENDER, state)
        self.Enable(Constants.ID_CBX_OBJECT_LIST, state)

    def _get_combo_box_value(self, cbx_id):
        return self.GetLong(cbx_id) - (cbx_id + 1)


class ObjectSwitcher(plugins.CommandData):

    dialog = None

    def Execute(self, doc):
        if self.dialog is None:
            self.dialog = ObjectSwitecherGUI()
        return self.dialog.Open(c4d.DLG_TYPE_ASYNC, Constants.PLUGIN_ID)

    def RestoreLayout(self, secret):
        if self.dialog is None:
            self.dialog = ObjectSwitecherGUI()
        return self.dialog.Restore(Constants.PLUGIN_ID, secret)


if __name__ == "__main__":
    _path, _file_name = os.path.split(__file__)
    icon = c4d.bitmaps.BaseBitmap()
    icon.InitWith(os.path.join(_path, 'res', 'objectswitcher.png'))
    plugins.RegisterCommandPlugin(Constants.PLUGIN_ID, Constants.PLUGIN_NAME, 0, icon, "Object Enabler/Disabler.", ObjectSwitcher())
