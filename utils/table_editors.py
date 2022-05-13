from traitsui.tabular_adapter import TabularAdapter
from traitsui.api import TabularEditor

from utils.constants import FONT_ARIAL, FONT_COURIER
from utils.container_classes import (
    TimedLitterComponent,
    LitterComponent,
    MonthlyClimate,
    YearlyClimate,
    AreaChange,
)


class MonthlyClimateAdapter(TabularAdapter):
    columns = [
        ('month', 'month'), ('temperature', 'temperature'),
        ('rainfall', 'rainfall')
    ]
    font = FONT_ARIAL
    default_value = MonthlyClimate()


class YearlyClimateAdapter(TabularAdapter):
    columns = [
        ('timestep', 'timestep'),
        ('mean temp 1', 'mean_temperature_1'),
        ('mean temp 2', 'mean_temperature_2'),
        ('mean temp 3', 'mean_temperature_3'),
        ('mean temp 4', 'mean_temperature_4'),
        ('mean temp 5', 'mean_temperature_5'),
        ('mean temp 6', 'mean_temperature_6'),
        ('mean temp 7', 'mean_temperature_7'),
        ('mean temp 8', 'mean_temperature_8'),
        ('mean temp 9', 'mean_temperature_9'),
        ('mean temp 10', 'mean_temperature_10'),
        ('mean temp 11', 'mean_temperature_11'),
        ('mean temp 12', 'mean_temperature_12'),
        ('annual rainfall', 'annual_rainfall'),
        # ('temp variation amplitude', 'variation_amplitude')
    ]
    font = FONT_ARIAL
    default_value = YearlyClimate()


class LitterAdapter(TabularAdapter):
    columns = [
        ('mass', 'mass'),
        ('mass std', 'mass_std'), ('A', 'acid'),
        ('A std', 'acid_std'), ('W', 'water'),
        ('W std', 'water_std'), ('E', 'ethanol'),
        ('E std', 'ethanol_std'), ('N', 'non_soluble'),
        ('N std', 'non_soluble_std'), ('H', 'humus'),
        ('H std', 'humus_std'), ('size class', 'size_class')
    ]
    font = FONT_ARIAL
    acid_width = 50
    acid_std_width = 50
    default_value = LitterComponent()


class ChangeAdapter(TabularAdapter):
    columns = [
        ('timestep', 'timestep'),
        ('relative change in area', 'rel_change')
    ]
    font = FONT_ARIAL
    default_value = AreaChange()


class TimedLitterAdapter(TabularAdapter):
    columns = [
        ('timestep', 'timestep'), ('mass', 'mass'),
        ('mass std', 'mass_std'), ('A', 'acid'),
        ('A std', 'acid_std'), ('W', 'water'),
        ('W std', 'water_std'), ('E', 'ethanol'),
        ('E std', 'ethanol_std'), ('N', 'non_soluble'),
        ('N std', 'non_soluble_std'), ('H', 'humus'),
        ('H std', 'humus_std'), ('size class', 'size_class')
    ]
    font = FONT_ARIAL
    acid_width = 50
    acid_std_width = 50
    default_value = TimedLitterComponent()


class CStockAdapter(TabularAdapter):
    columns = [
        ('sample', 0), ('time step', 1), ('total om', 2),
        ('woody om', 3), ('non-woody om', 4), ('acid', 5),
        ('water', 6), ('ethanol', 7), ('non soluble', 8), ('humus', 9)
    ]
    font = FONT_COURIER
    alignment = 'right'
    format = '%.4f'


class CO2YieldAdapter(TabularAdapter):
    columns = [('sample', 0), ('time step', 1), ('CO2 production', 2)]
    font = FONT_COURIER
    alignment = 'right'
    format = '%.4f'


monthly_climate_te = TabularEditor(adapter=MonthlyClimateAdapter(), editable=False)
yearly_climate_te = TabularEditor(adapter=YearlyClimateAdapter(), editable=False)
timed_litter_te = TabularEditor(adapter=TimedLitterAdapter(), editable=False)
litter_te = TabularEditor(adapter=LitterAdapter(), editable=False)
change_te = TabularEditor(adapter=ChangeAdapter(), editable=False)
co2_yield_te = TabularEditor(adapter=CO2YieldAdapter())
c_stock_te = TabularEditor(adapter=CStockAdapter())
