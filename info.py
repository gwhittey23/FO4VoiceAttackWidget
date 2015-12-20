from widgets import widgets
from .FO4VAWidget import FO4VaWidget

# Holds meta-information about the widgets
class ModuleInfo(widgets.ModuleInfoBase):
    LABEL = 'FO4VAServer' # Unique widget label
    NAME = 'Fallout 4 VoiceAttack widget' # Human readable name
    # Factory function that returns a (or a list of) widget instance
    #   handle ... handle representing the widget ()
    #   parent ... QtWidget parent
    @staticmethod
    def createWidgets(handle, parent):
        return FO4VaWidget(handle, parent)

