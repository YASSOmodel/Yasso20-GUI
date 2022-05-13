from enable.component_editor import ComponentEditor
from pyface.image_resource import ImageResource

from traitsui.menu import (
    RevertAction,
    CloseAction,
    UndoAction,
    RedoAction,
    NoButtons,
    MenuBar,
    Menu,
)
from traitsui.api import (
    TextEditor,
    spring,
    HGroup,
    VGroup,
    Group,
    Label,
    Item,
    View,
)

from utils.table_editors import (
    monthly_climate_te,
    yearly_climate_te,
    timed_litter_te,
    co2_yield_te,
    c_stock_te,
    litter_te,
    change_te,
)


app_ir = ImageResource("../yasso.ico")
ui_view = View(
        VGroup(
            HGroup(
                Item('new_data_file_event', show_label=False, ),
                Item('open_data_file_event', show_label=False, ),
                Item('save_data_file_event', show_label=False, ),
                Item('save_as_file_event', show_label=False, ),
                Item('data_file', style='readonly', show_label=False, ),
            ),
            HGroup(
                Item('all_data', show_label=False, style='custom',
                     has_focus=True, editor=TextEditor(),
                     width=300, height=300)
            ),
            label='All data',
        ),
        VGroup(
            HGroup(
                Item('parameter_set', width=-145),
                Item('leaching', width=-45,
                     label='Leaching parameter',
                     visible_when='initial_mode!="steady state"'),
                show_border=True,

            ),
            VGroup(
                HGroup(
                    Item(name='initial_mode', style='custom',
                         label='Initial state:', emphasized=True,
                         ),
                ),
                Item('initial_litter',
                     visible_when='initial_mode=="non zero"',
                     show_label=False, editor=litter_te,
                     width=790, height=75,
                     ),
            ),
            VGroup(
                HGroup(
                    Item('litter_mode', style='custom',
                         label='Soil carbon input:', emphasized=True
                         )
                ),
                HGroup(
                    Item('constant_litter',
                         visible_when='litter_mode=="constant yearly"',
                         show_label=False, editor=litter_te, springy=False,
                         width=-790, height=-75
                         ),
                    Item('monthly_litter',
                         visible_when='litter_mode=="monthly"',
                         show_label=False, editor=timed_litter_te, springy=False,
                         width=-790, height=-75
                         ),
                    Item('yearly_litter',
                         visible_when='litter_mode=="yearly"',
                         show_label=False, editor=timed_litter_te, springy=False,
                         width=-790, height=-75
                         ),
                ),
                HGroup(
                    Item('area_change',
                         visible_when='litter_mode=="yearly" or litter_mode=="monthly"',
                         show_label=False, editor=change_te, springy=False,
                         width=-150, height=-75
                         ),
                    spring,
                ),
            ),
            VGroup(
                HGroup(
                    Item('climate_mode', style='custom',
                         label='Climate:', emphasized=True,
                         ),
                ),
                HGroup(
                    Item('monthly_climate', show_label=False,
                         visible_when='climate_mode=="monthly"',
                         editor=monthly_climate_te, width=200, height=75
                         ),
                    Item('yearly_climate', show_label=False,
                         visible_when='climate_mode=="yearly"',
                         editor=yearly_climate_te, width=200, height=75
                         ),
                    VGroup(
                        Item('object.constant_climate.mean_temperature',
                             style='readonly', ),
                        Item('object.constant_climate.annual_rainfall',
                             style='readonly', ),
                        # Item('object.constant_climate.variation_amplitude',
                        #      style='readonly', ),
                        show_border=True,
                        visible_when='climate_mode=="constant yearly"'
                    ),
                ),
            ),
            label='Data to use',
        ),
        VGroup(
            Group(
                HGroup(
                    Item('sample_size', width=-45,
                         ),
                    Item('simulation_length', width=-45,
                         label='Number of timesteps',
                         ),
                    Item('timestep_length', width=-45,
                         style='readonly'),
                    Item('duration_unit', style='custom',
                         show_label=False, ),
                ),
                HGroup(
                    Item('woody_size_limit', width=-45,
                         ),
                    Item('modelrun_event', show_label=False),
                ),
                show_border=True
            ),
            HGroup(
                Item('result_type', style='custom', label='Show',
                     emphasized=True, ),
                Item('save_result_event', show_label=False, ),
                Item('save_moment_event', show_label=False, ),
            ),
            HGroup(
                Item('presentation_type', style='custom', label='As',
                     emphasized=True, ),
                Item('chart_type', style='custom', label='Chart type',
                     visible_when='presentation_type=="chart"'),
            ),
            HGroup(
                Item('c_stock', visible_when='result_type=="C stock" and \
                      presentation_type=="array"', show_label=False,
                     editor=c_stock_te,  # width=600
                     ),
                Item('c_change', visible_when='result_type=="C change" and \
                      presentation_type=="array"', show_label=False,
                     editor=c_stock_te, ),
                Item('co2_yield', visible_when='result_type=="CO2 production" ' \
                                               'and presentation_type=="array"', show_label=False,
                     editor=co2_yield_te, ),
                Item('stock_plots', editor=ComponentEditor(),
                     show_label=False,
                     visible_when='result_type=="C stock" and \
                                  presentation_type=="chart"', ),
                Item('change_plots', editor=ComponentEditor(),
                     show_label=False,
                     visible_when='result_type=="C change" and \
                                  presentation_type=="chart"', ),
                Item('co2_plot', editor=ComponentEditor(),
                     show_label=False,
                     visible_when='result_type=="CO2 production" and \
                                  presentation_type=="chart"', ),
            ),
            label='Model run',
        ),
        VGroup(
            Label(label='Yasso soil carbon model', emphasized=True),
            Label(label="<placeholder>", id="about_text"),
            label='About',
        ),
        title='Yasso',
        id='simosol.yasso15',
        dock='horizontal',
        width=800,
        height=600,
        resizable=True,
        scrollable=False,
        buttons=NoButtons,
        icon=app_ir,
        menubar=MenuBar(
            Menu(CloseAction, name='File'),
            Menu(UndoAction, RedoAction, RevertAction, name='Edit'),
        ),
        help=False,
    )
