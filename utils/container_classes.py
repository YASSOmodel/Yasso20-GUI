from traits.api import (
    HasTraits,
    Float,
    Range,
    Int,
)


class LitterComponent(HasTraits):
    mass = Float()
    mass_std = Float()
    acid = Range(low=0.0, high=100.0)
    acid_std = Float()
    water = Range(low=0.0, high=100.0)
    water_std = Float()
    ethanol = Range(low=0.0, high=100.0)
    ethanol_std = Float()
    non_soluble = Range(low=0.0, high=100.0)
    non_soluble_std = Float()
    humus = Range(low=0.0, high=100.0)
    humus_std = Float()
    size_class = Float(default=0.0)


class TimedLitterComponent(HasTraits):
    timestep = Int()
    mass = Float()
    mass_std = Float()
    acid = Range(low=0.0, high=100.0)
    acid_std = Float()
    water = Range(low=0.0, high=100.0)
    water_std = Float()
    ethanol = Range(low=0.0, high=100.0)
    ethanol_std = Float()
    non_soluble = Range(low=0.0, high=100.0)
    non_soluble_std = Float()
    humus = Range(low=0.0, high=100.0)
    humus_std = Float()
    size_class = Float(default_value=0.0)


class AreaChange(HasTraits):
    timestep = Int()
    rel_change = Float()


class YearlyClimate(HasTraits):
    timestep = Int()
    mean_temperature_1 = Float()
    mean_temperature_2 = Float()
    mean_temperature_3 = Float()
    mean_temperature_4 = Float()
    mean_temperature_5 = Float()
    mean_temperature_6 = Float()
    mean_temperature_7 = Float()
    mean_temperature_8 = Float()
    mean_temperature_9 = Float()
    mean_temperature_10 = Float()
    mean_temperature_11 = Float()
    mean_temperature_12 = Float()
    mean_temperature = Float()
    annual_rainfall = Float()
    # variation_amplitude = Float()


class MonthlyClimate(HasTraits):
    month = Int()
    temperature = Float()
    rainfall = Float()
