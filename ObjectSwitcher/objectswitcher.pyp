# Author: safina3d
# Url: https://safina3d.blogspot.com
# Repo: https://github.com/safina3d/c4d-object-switcher

import os
import c4d
from c4d import gui, documents, plugins

PLUGIN_ID = 1027124

ID_BTN_REFRESH = 20000
ID_BTN_APPLY = 20001
ID_CHKBOX_ON_OFF = 30000
ID_CMBOX_OBJECT_LIST = 40000
ID_CMBOX_VISIBILITY_EDITOR = 50000
ID_CMBOX_VISIBILITY_RENDER = 60000


class Helper:

    @staticmethod
    def get_next_object(current_object):
        """ Return the next object in the hierarchy """
        if current_object.GetDown():
            return current_object.GetDown()
        while not current_object.GetNext() and current_object.GetUp():
            current_object = current_object.GetUp()
        return current_object.GetNext()

    @staticmethod
    def get_objects_map():
        """ Return map of all objects, keys values are object type ids, and values are array of objects """
        doc = documents.GetActiveDocument()
        objects_map = {}
        current_object = doc.GetFirstObject()
        while current_object:
            object_type = current_object.GetType()
            if object_type in objects_map:
                objects_map[object_type].append(current_object)
            else:
                objects_map[object_type] = []
                objects_map[object_type].append(current_object)
            current_object = Helper.get_next_object(current_object)
        return objects_map


class ObjectSwitecherGUI(gui.GeDialog):

    def __init__(self):
        self.objects_map = Helper.get_objects_map()

    def CreateLayout(self):
        self.SetTitle("ObjectSwitcher")
        self.GroupBegin(1000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT)
        self.GroupBorderSpace(3, 5, 3, 5)
        self.AddComboBox(ID_CMBOX_OBJECT_LIST, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT)
        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)
        self.AddComboBox(ID_CMBOX_VISIBILITY_EDITOR, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT)
        self.AddChild(ID_CMBOX_VISIBILITY_EDITOR, 50003, "Editor : Default")
        self.AddChild(ID_CMBOX_VISIBILITY_EDITOR, 50001, "Editor : Visible")
        self.AddChild(ID_CMBOX_VISIBILITY_EDITOR, 50002, "Editor : Hidden")
        self.AddComboBox(ID_CMBOX_VISIBILITY_RENDER, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT)
        self.AddChild(ID_CMBOX_VISIBILITY_RENDER, 60003, "Renderer : Default")
        self.AddChild(ID_CMBOX_VISIBILITY_RENDER, 60001, "Renderer : Visible")
        self.AddChild(ID_CMBOX_VISIBILITY_RENDER, 60002, "Renderer : Hidden")
        self.AddCheckbox(ID_CHKBOX_ON_OFF, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 0, 0, name="Enable")
        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)
        self.AddButton(ID_BTN_APPLY, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 0, 0, "Apply")
        self.GroupEnd()
        return True

    def InitValues(self):
        self.SetLong(ID_CMBOX_VISIBILITY_EDITOR, 50003)
        self.SetLong(ID_CMBOX_VISIBILITY_RENDER, 60003)
        self.SetBool(ID_CHKBOX_ON_OFF, True)
        if len(self.objects_map) > 0:
            self.SetLong(ID_CMBOX_OBJECT_LIST, self.objects_map.keys()[0])
        return True

    def Command(self, id, msg):
        if id == ID_BTN_APPLY:
            selected_id = self.GetLong(ID_CMBOX_OBJECT_LIST)
            for obj in self.objects_map[selected_id]:
                obj[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = self.GetBool(ID_CHKBOX_ON_OFF)
                obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = self.GetLong(ID_CMBOX_VISIBILITY_EDITOR) - 50001
                obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = self.GetLong(ID_CMBOX_VISIBILITY_RENDER) - 60001
        c4d.EventAdd()
        return True

    def Message(self, msg, result):
        if msg.GetId() == c4d.BFM_GOTFOCUS:
            self.objects_map = Helper.get_objects_map()
            self.FreeChildren(ID_CMBOX_OBJECT_LIST)
            for object_id, objects_list in self.objects_map.iteritems():
                self.AddChild(
                    ID_CMBOX_OBJECT_LIST,
                    object_id,
                    "%s ( %s )" % (c4d.GetObjectName(object_id), len(objects_list))
                )
            if len(self.objects_map) > 0:
                self.SetLong(ID_CMBOX_OBJECT_LIST, self.objects_map.keys()[0])
            self.LayoutChanged(ID_CMBOX_OBJECT_LIST)
        return gui.GeDialog.Message(self, msg, result)


class ObjectSwitcher(plugins.CommandData):

    dialog = None

    def Execute(self, doc):
        if self.dialog is None:
            self.dialog = ObjectSwitecherGUI()
        return self.dialog.Open(c4d.DLG_TYPE_ASYNC, PLUGIN_ID)

    def RestoreLayout(self, secret):
        if self.dialog is None:
            self.dialog = ObjectSwitecherGUI()
        return self.dialog.Restore(PLUGIN_ID, secret)


if __name__ == "__main__":
    _path, _file_name = os.path.split(__file__)
    icon = c4d.bitmaps.BaseBitmap()
    icon.InitWith(os.path.join(_path, 'res', 'objectswitcher.png'))
    plugins.RegisterCommandPlugin(PLUGIN_ID, "ObjectSwitcher+", 0, icon, "Object Enabler/Disabler.", ObjectSwitcher())
