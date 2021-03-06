#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from __future__ import with_statement

import y07, y15, y20
import numpy
import math
from utils import loader

from datetime import date
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import random
import stats
from pyface.api import ProgressDialog
from traitsui.message import error

# the order in which data comes in (defined by list index) and in which
# it should passed to the model (defined in the tuple)
VALUESPEC = [('mass', None), ('acid', 0), ('water', 1), ('ethanol', 2),
             ('non_soluble', 3), ('humus', 4)]
STARTDATE = date(2, 1, 1)
STEADY_STATE_TIMESTEP = 10000.
# constants for the model parameters
PARAM_SAMPLES = 10000



class ModelRunner(object):
    """
    This class is responsible for calling the actual Yasso07 modeldata.
    It converts the data in the UI into the form that can be passed
    to the model
    """

    def __init__(self, parfile):
        """
        Constructor.
        """
        self.temp_list = []
        self.param_set = []
        self._param_file_shape = None
        with open(parfile) as f:
            for line in f:
                line_split = line.split()
                self.param_set.append([float(v.strip()) for v in line_split])
                if line.strip():
                    self._param_file_shape = len(line_split)

    def is_usable_parameter_file(self):
        """Returns True, if the parameter file has a suitable number of
        parameters that can be used."""
        return self._param_file_shape == 35

    def compute_steady_state(self, modeldata):
        """
        Solves the steady state for the system given the constant infall
        """
        self.simulation = False
        self.md = modeldata
        self.steady_state = numpy.empty(shape=(0, 6), dtype=numpy.float32)
        self.timemap = defaultdict(list)
        self.area_timemap = defaultdict(list)
        samplesize = self.md.sample_size
        timesteps = 1
        self.timestep_length = STEADY_STATE_TIMESTEP
        self.curr_yr_ind = 0
        self.curr_month_ind = 0
        self.ml_run = True
        self.infall = {}
        self.initial_mode = 'zero'
        timemsg = None
        for j in range(samplesize):
            self.draw = True
            self._predict_steady_state(j)
            self.ml_run = False
        self._steadystate2initial()
        return self.ss_result

    def run_model(self, modeldata):
        self.simulation = True
        self.md = modeldata
        self.c_stock = numpy.empty(shape=(0, 10), dtype=numpy.float32)
        self.c_change = numpy.empty(shape=(0, 10), dtype=numpy.float32)
        self.co2_yield = numpy.empty(shape=(0, 3), dtype=numpy.float32)
        self.timemap = defaultdict(list)
        self.area_timemap = defaultdict(list)
        samplesize = self.md.sample_size
        msg = "Simulating %d samples for %d timesteps" % (samplesize,
                                                          self.md.simulation_length)
        progress = ProgressDialog(title="Simulation", message=msg,
                                  max=samplesize, show_time=True,
                                  can_cancel=True)
        progress.open()
        timesteps = self.md.simulation_length
        self.timestep_length = self.md.timestep_length
        self.ml_run = True
        self.infall = {}
        self.initial_mode = self.md.initial_mode
        if self.initial_mode == 'steady state':
            self.initial_def = self.md.steady_state
        else:
            self.initial_def = self.md.initial_litter
        timemsg = None
        for j in range(samplesize):
            (cont, skip) = progress.update(j)
            if not cont or skip:
                break
            self.draw = True
            self.curr_yr_ind = 0
            self.curr_month_ind = 0
            for k in range(timesteps):
                self._predict_timestep(j, k)
            self.ml_run = False
        self._fill_moment_results()
        progress.update(samplesize)
        if timemsg is not None:
            error(timemsg, title='Error handling timesteps',
                  buttons=['OK'])
        return self.c_stock, self.c_change, self.co2_yield

    def _add_c_stock_result(self, sample, timestep, sc, endstate):
        """
        Adds model result to the C stock

        res -- model results augmented with timestep, iteration and
               sizeclass data
        """
        cs = self.c_stock
        # if sizeclass is non-zero, all the components are added together
        # to get the mass of wood
        if sc >= self.md.woody_size_limit:
            totalom = endstate.sum()
            woody = totalom
            nonwoody = 0.0
        else:
            totalom = endstate.sum()
            woody = 0.0
            nonwoody = totalom
        res = numpy.concatenate(([float(sample), float(timestep), totalom,
                                  woody, nonwoody], endstate))
        res.shape = (1, 10)
        # find out whether there are already results for this timestep and
        # iteration
        criterium = (cs[:, 0] == res[0, 0]) & (cs[:, 1] == res[0, 1])
        target = numpy.where(criterium)[0]
        if len(target) == 0:
            self.c_stock = numpy.append(cs, res, axis=0)
        else:
            # if there are, add the new results to the existing ones
            self.c_stock[target[0], 2:] = numpy.add(cs[target[0], 2:], res[0, 2:])

    def _add_steady_state_result(self, sc, endstate):
        """
        Adds model result to the C stock

        res -- model results augmented with timestep, iteration and
               sizeclass data
        """
        res = numpy.concatenate(([float(sc)], endstate))
        res.shape = (1, 6)
        self.steady_state = numpy.append(self.steady_state, res, axis=0)

    def _calculate_c_change(self, s, ts):
        """
        The change of mass per component during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cc = self.c_change
        cs = self.c_stock
        criterium = (cs[:, 0] == s) & (cs[:, 1] == ts)
        nowtarget = numpy.where(criterium)[0]
        criterium = (cs[:, 0] == s) & (cs[:, 1] == ts - 1)
        prevtarget = numpy.where(criterium)[0]
        if len(nowtarget) > 0 and len(prevtarget) > 0:
            stepinf = numpy.array([[s, ts, 0., 0., 0., 0., 0., 0., 0., 0.]],
                                  dtype=numpy.float32)
            self.c_change = numpy.append(cc, stepinf, axis=0)
            self.c_change[-1, 2:] = cs[nowtarget, 2:] - cs[prevtarget, 2:]

    def _calculate_co2_yield(self, s, ts):
        """
        The yield of CO2 during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cs = self.c_stock
        cy = self.co2_yield
        stepinf = numpy.array([[s, ts, 0.]], dtype=numpy.float32)
        self.co2_yield = numpy.append(cy, stepinf, axis=0)
        # total organic matter at index 3
        criterium = (cs[:, 0] == s) & (cs[:, 1] == ts)
        rowind = numpy.where(criterium)[0]
        if len(rowind) > 0:
            atend = cs[rowind[0], 2]
            co2_as_c = self.ts_initial + self.ts_infall - atend
            self.co2_yield[-1, 2] = co2_as_c

    def _construct_climate(self, timestep):
        """
        From the different ui options, creates a unified climate description
        (type, duration, temperature, rainfall, amplitude)
        """
        cl = {}
        now, end = self._get_now_and_end(timestep)
        if now == -1:
            return -1
        if self.simulation:
            # if self.md.duration_unit == 'month':
            #     cl['duration'] = self.md.timestep_length / 12.
            # if self.md.duration_unit == 'year':
            cl['duration'] = self.md.timestep_length
        else:
            # cl['duration'] = STEADY_STATE_TIMESTEP
            cl['duration'] = self.md.timestep_length
        if self.md.climate_mode == 'constant yearly':
            cl['rain'] = self.md.constant_climate.annual_rainfall
            cl['temp'] = self.md.constant_climate.mean_temperature
            # cl['amplitude'] = self.md.constant_climate.variation_amplitude
        elif self.md.climate_mode == 'monthly':
            cl = self._construct_monthly_climate(cl, now, end)
        elif self.md.climate_mode == 'yearly':
            cl = self._construct_yearly_climate(cl, now, end)
        return cl

    def _construct_monthly_climate(self, cl, now, end):
        """
        Summarizes the monthly climate data into rain, temp and amplitude
        given the start and end dates

        cl -- climate dictionary
        now -- start date
        end -- end date
        """
        # how many months should we aggregate
        if self.simulation:
            # if self.md.duration_unit == 'month':
            #     months = range(self.md.timestep_length)
            # else:
            months = range(12 * self.md.timestep_length)
        else:
            # use the first year for steady state computation
            months = range(12)
        rain = 0.0
        # temp = 0.0
        # maxtemp = 0.0
        # mintemp = 0.0
        maxind = len(self.md.monthly_climate) - 1
        self.temp_list = list()

        if self.curr_month_ind > maxind:
            self.curr_month_ind = 0
        mtemp = self.md.monthly_climate[self.curr_month_ind].temperature
        self.temp_list = [mtemp for i in range(12)]

        # if mtemp < mintemp:`
        #     mintemp = mtemp
        # if mtemp > maxtemp:
        #     maxtemp = mtemp

        # monthly rain converted into yearly rain
        rain += 12 * self.md.monthly_climate[self.curr_month_ind].rainfall
        self.curr_month_ind += 1

        cl['rain'] = rain
        cl['temp'] = self.temp_list
        # cl['amplitude'] = (maxtemp - mintemp) / 2.0

        return cl

    def _construct_yearly_climate(self, cl, now, end):
        """
        Summarizes the yearly climate data into rain, temp and amplitude
        given the start and end dates. Rotates the yearly
        climate definition round if shorter than the simulation length.

        cl -- climate dictionary
        now -- start date
        end -- end year
        """
        if self.simulation:
            years = range(now.year, end.year + 1)
            if len(years) > 1:
                # the ordinals of days within the year
                lastord = float(date(now.year, 12, 31).timetuple()[7])
                noword = float(now.timetuple()[7])
                firstyearweight = (lastord - noword) / lastord
                lastord = float(date(end.year, 12, 31).timetuple()[7])
                endord = float(end.timetuple()[7])
                lastyearweight = endord / lastord
        else:
            # for steady state computation year 0 or 1 used
            years = [0]
            firstyearweight = 1.0
            lastyearweight = 1.0
            self.curr_yr_ind = 0
        rain = 0.0
        temp = 0.0
        ampl = 0.0
        addyear = True
        if len(years) == 1:
            firstyearweight = 1.0
            if now.year == end.year and not (end.month == 12 and end.day == 31):
                addyear = False
        maxind = len(self.md.yearly_climate) - 1
        for ind in range(len(years)):
            if self.curr_yr_ind > maxind:
                self.curr_yr_ind = 0
            cy = self.md.yearly_climate[self.curr_yr_ind]
            if self.simulation and cy.timestep == 0:
                # timestep 0 is used only for steady state calculation
                self.curr_yr_ind += 1
                if self.curr_yr_ind <= maxind:
                    cy = self.md.yearly_climate[self.curr_yr_ind]
            if ind == 0:
                weight = firstyearweight
                passedzero = False
            elif ind == len(years) - 1:
                weight = lastyearweight
            else:
                weight = 1.0
            temp += weight * cy.mean_temperature
            rain += weight * cy.annual_rainfall
            # ampl += weight * cy.variation_amplitude
            if addyear:
                self.curr_yr_ind += 1

            attrs = [attr for attr in cy.__dict__.items()]
            self.temp_list = [value[1] for value in attrs if 'mean_temperature_' in value[0]]

        # backs one year back, if the last weight was less than 1
        if weight < 1.0 and addyear:
            self.curr_yr_ind -= 1
            if self.curr_yr_ind < 0:
                self.curr_yr_ind = len(self.md.yearly_climate) - 1

        # for year in self.md.yearly_climate:
        #     if len(self.temp_list) < cl.get('duration'):
        #         self.temp_list.append(year.mean_temperature)
        #     else:
        #         break

        cl['temp'] = self.temp_list
        cl['rain'] = rain / len(years)
        # cl['amplitude'] = ampl / len(years)
        return cl

    def __create_input(self, timestep):
        """
        Sums up the non-woody initial states and inputs into a single
        initial state and input. Matches the woody inital states and
        inputs by size class.
        """
        self.litter = {}
        if timestep == 0:
            self.initial = {}
            if self.initial_mode != 'zero':
                self._define_components(self.initial_def, self.initial)
        if self.md.litter_mode == 'constant yearly':
            self._define_components(self.md.constant_litter, self.litter)
        elif self.md.litter_mode == 'zero':
            # Not setting litter to anything. Will be rectified in
            # _fill_input
            pass
        else:
            timeind = self._map_timestep2timeind(timestep)
            if self.md.litter_mode == 'monthly':
                infdata = self.md.monthly_litter
            elif self.md.litter_mode == 'yearly':
                infdata = self.md.yearly_litter
            self._define_components(infdata, self.litter, tsind=timeind)
        self._fill_input()

    def _define_components(self, fromme, tome, tsind=None):
        """
        Adds the component specification to list to be passed to the model

        fromme -- the component specification from the ui
        tome -- the list on its way to the model
        tsind -- indices if the components are taken from a timeseries
        """
        sizeclasses = defaultdict(list)
        if tsind is None:
            for i in range(len(fromme)):
                sizeclasses[fromme[i].size_class].append(i)
        else:
            for i in tsind:
                sizeclasses[fromme[i].size_class].append(i)
        for sc in sizeclasses:
            m, m_std, a, a_std, w, w_std = (0., 0., 0., 0., 0., 0.)
            e, e_std, n, n_std, h, h_std = (0., 0., 0., 0., 0., 0.)
            for ind in sizeclasses[sc]:
                litter = fromme[ind]
                mass = litter.mass
                m += mass
                a += mass * litter.acid
                w += mass * litter.water
                e += mass * litter.ethanol
                n += mass * litter.non_soluble
                h += mass * litter.humus
                m_std += mass * litter.mass_std
                a_std += mass * litter.acid_std
                w_std += mass * litter.water_std
                e_std += mass * litter.ethanol_std
                n_std += mass * litter.non_soluble_std
                h_std += mass * litter.humus_std
            if m > 0.:
                tome[sc] = [m, m_std / m, a / m, a_std / m, w / m, w_std / m,
                            e / m, e_std / m, n / m, n_std / m,
                            h / m, h_std / m]
            else:
                tome[sc] = [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]

    def _draw_from_distr(self, values, pairs, randomize):
        """
        Draw a sample from the normal distribution based on the mean and std
        pairs

        values -- a vector containing mean and standard deviation pairs
        pairs -- how many pairs the vector contains
        randomize -- boolean for really drawing a random sample instead of
                  using the maximum likelihood values
        """
        # sample size one less than pairs specification as pairs contain
        # the total mass and component percentages. These are transformed
        # into component masses
        sample = [None for i in range(len(pairs) - 1)]
        for i in range(len(pairs)):
            vs = pairs[i]
            mean = values[2 * i]
            std = values[2 * i + 1]
            if std > 0.0 and randomize:
                samplemean = random.gauss(mean, std)
            else:
                samplemean = mean
            if vs[0] == 'mass':
                samplemass = samplemean
                remainingmass = samplemean
            elif vs[0] != 'water':
                compmass = samplemass * samplemean
                sample[vs[1]] = compmass
                remainingmass -= compmass
            elif vs[0] == 'water':
                waterind = i
        sample[pairs[waterind][1]] = remainingmass
        return sample

    def _endstate2initial(self, sizeclass, endstate, timestep):
        """
        Transfers the endstate masses to the initial state description of
        masses and percentages with standard deviations. Std set to zero.
        Also scales the total mass with the relative area change if defined.
        """
        mass = endstate.sum()

        # Avoid division by 0 or negative masses.
        mass_sum = mass if mass > 0 else 1

        acid = endstate[0] / mass_sum
        water = endstate[1] / mass_sum
        ethanol = endstate[2] / mass_sum
        nonsoluble = endstate[3] / mass_sum
        humus = endstate[4] / mass_sum

        # area change scaling
        if self.md.litter_mode in ('monthly', 'yearly'):
            for listind in self.area_timemap[timestep]:
                change = self.md.area_change[listind]
                mass = mass * (1. + change.rel_change)
        self.initial[sizeclass] = [mass, 0., acid, 0., water, 0., ethanol, 0.,
                                   nonsoluble, 0., humus, 0.]

    def _fill_input(self):
        """
        Makes sure that both the initial state and litter input have the same
        size classes
        """
        for sc in self.initial:
            if sc not in self.litter:
                self.litter[sc] = [0., 0., 0., 0., 0., 0.,
                                   0., 0., 0., 0., 0., 0.]
        for sc in self.litter:
            if sc not in self.initial:
                self.initial[sc] = [0., 0., 0., 0., 0., 0.,
                                    0., 0., 0., 0., 0., 0.]

    def _fill_moment_results(self):
        """
        Fills the result arrays used for storing the calculated moments
         common format: time, mean, mode, var, skewness, kurtosis,
                        95% confidence lower limit, 95% upper limit
        """
        toprocess = [('stock_tom', self.c_stock, 2),
                     ('stock_woody', self.c_stock, 3),
                     ('stock_non_woody', self.c_stock, 4),
                     ('stock_acid', self.c_stock, 5),
                     ('stock_water', self.c_stock, 6),
                     ('stock_ethanol', self.c_stock, 7),
                     ('stock_non_soluble', self.c_stock, 8),
                     ('stock_humus', self.c_stock, 9),
                     ('change_tom', self.c_change, 2),
                     ('change_woody', self.c_change, 3),
                     ('change_non_woody', self.c_change, 4),
                     ('change_acid', self.c_change, 5),
                     ('change_water', self.c_change, 6),
                     ('change_ethanol', self.c_change, 7),
                     ('change_non_soluble', self.c_change, 8),
                     ('change_humus', self.c_change, 9),
                     ('co2', self.co2_yield, 2)]
        for (resto, dataarr, dataind) in toprocess:
            # filter time steps
            ts = numpy.unique(dataarr[:, 1])
            # extract data for the timestep
            for timestep in ts:
                ind = numpy.where(dataarr[:, 1] == timestep)
                mean = stats.mean(dataarr[ind[0], dataind])
                mode_res = stats.mode(dataarr[ind[0], dataind])
                mode = mode_res[0]
                var = stats.var(dataarr[ind[0], dataind])
                skew = stats.skew(dataarr[ind[0], dataind])
                kurtosis = stats.kurtosis(dataarr[ind[0], dataind])
                if var > 0.0:
                    sd2 = 2 * math.sqrt(var)
                else:
                    sd2 = var
                res = [[timestep, mean, mode[0], var, skew, kurtosis,
                        mean - sd2, mean + sd2]]
                if resto == 'stock_tom':
                    self.md.stock_tom = numpy.append(self.md.stock_tom,
                                                     res, axis=0)
                elif resto == 'stock_woody':
                    self.md.stock_woody = numpy.append(self.md.stock_woody,
                                                       res, axis=0)
                elif resto == 'stock_non_woody':
                    self.md.stock_non_woody = numpy.append(
                        self.md.stock_non_woody, res, axis=0
                    )
                elif resto == 'stock_acid':
                    self.md.stock_acid = numpy.append(self.md.stock_acid,
                                                      res, axis=0)
                elif resto == 'stock_water':
                    self.md.stock_water = numpy.append(self.md.stock_water,
                                                       res, axis=0)
                elif resto == 'stock_ethanol':
                    self.md.stock_ethanol = numpy.append(self.md.stock_ethanol,
                                                         res, axis=0)
                elif resto == 'stock_non_soluble':
                    self.md.stock_non_soluble = numpy.append(
                        self.md.stock_non_soluble, res, axis=0)
                elif resto == 'stock_humus':
                    self.md.stock_humus = numpy.append(self.md.stock_humus,
                                                       res, axis=0)
                elif resto == 'change_tom':
                    self.md.change_tom = numpy.append(self.md.change_tom,
                                                      res, axis=0)
                elif resto == 'change_woody':
                    self.md.change_woody = numpy.append(self.md.change_woody,
                                                        res, axis=0)
                elif resto == 'change_non_woody':
                    self.md.change_non_woody = numpy.append(
                        self.md.change_non_woody, res, axis=0
                    )
                elif resto == 'change_acid':
                    self.md.change_acid = numpy.append(self.md.change_acid,
                                                       res, axis=0)
                elif resto == 'change_water':
                    self.md.change_water = numpy.append(self.md.change_water,
                                                        res, axis=0)
                elif resto == 'change_ethanol':
                    self.md.change_ethanol = numpy.append(
                        self.md.change_ethanol, res, axis=0)
                elif resto == 'change_non_soluble':
                    self.md.change_non_soluble = numpy.append(
                        self.md.change_non_soluble, res, axis=0)
                elif resto == 'change_humus':
                    self.md.change_humus = numpy.append(self.md.change_humus,
                                                        res, axis=0)
                elif resto == 'co2':
                    self.md.co2 = numpy.append(self.md.co2, res, axis=0)

    def _get_now_and_end(self, timestep):
        """
        Uses a fixed simulation start date for calculating the value date
        for each timestep and its end date
        """
        rd = relativedelta
        start = STARTDATE
        if self.simulation:
            tslength = self.md.timestep_length
        else:
            tslength = 1
        try:
            # if self.md.duration_unit == 'month':
            #     now = start + rd(months=timestep * tslength)
            #     end = now + rd(months=tslength)
            # elif self.md.duration_unit == 'year':
            now = start + rd(years=timestep * tslength)
            end = now + rd(years=tslength) - rd(days=1)
        except ValueError:
            now = -1
            end = -1
        return now, end

    def _map_timestep2timeind(self, timestep):
        """
        Convert the timestep index to the nearest time defined in the litter
        timeseries array

        timestep -- ordinal number of the simulation run timestep
        """
        if not self.simulation and timestep not in self.timemap:
            # for steady state computation include year 0 or first 12 months
            if self.md.litter_mode == 'monthly':
                incl = range(1, 13)
                infall = self.md.monthly_litter
            elif self.md.litter_mode == 'yearly':
                incl = [0]
                infall = self.md.yearly_litter
            elif self.md.litter_mode == 'zero':
                infall = []
            for ind in range(len(infall)):
                if infall[ind].timestep in incl:
                    self.timemap[timestep].append(ind)
            if timestep not in self.timemap and self.md.litter_mode == 'yearly':
                # if no year 0 specification, use the one for year 1
                for ind in range(len(infall)):
                    if infall[ind].timestep == 1:
                        self.timemap[timestep].append(ind)
        if self.simulation and timestep not in self.timemap:
            # now for the simulation run
            now, end = self._get_now_and_end(timestep)
            # if self.md.duration_unit == 'month':
            #     dur = relativedelta(months=self.md.timestep_length)
            # elif self.md.duration_unit == 'year':
            dur = relativedelta(years=self.md.timestep_length)
            end = now + dur - relativedelta(days=1)
            if self.md.litter_mode == 'monthly':
                inputdur = relativedelta(months=1)
                infall = self.md.monthly_litter
            elif self.md.litter_mode == 'yearly':
                inputdur = relativedelta(years=1)
                infall = self.md.yearly_litter
            elif self.md.litter_mode == 'zero':
                inputdur = relativedelta(years=1)
                infall = self.md.zero_litter
            # the first mont/year will have index number 1, hence deduce 1 m/y
            start = STARTDATE - inputdur
            for ind in range(len(infall)):
                incl = self._test4inclusion(ind, infall, now, start, end)
                if incl:
                    self.timemap[timestep].append(ind)
            # check for possible area reductions to be mapped
            areachange = self.md.area_change
            for ind in range(len(areachange)):
                incl = self._test4inclusion(ind, areachange, now, start, end)
                if incl:
                    self.area_timemap[timestep].append(ind)
        if timestep not in self.timemap:
            self.timemap[timestep] = []
        if timestep not in self.area_timemap:
            self.area_timemap[timestep] = []
        return self.timemap[timestep]

    def _test4inclusion(self, ind, dataarray, now, start, end):
        relamount = int(dataarray[ind].timestep)
        if self.md.litter_mode == 'monthly':
            inputdate = start + relativedelta(months=relamount)
        else:
            inputdate = start + relativedelta(years=relamount)
        if inputdate >= now and inputdate <= end:
            return True
        else:
            return False

    def _predict(self, sc, initial, litter, climate, steady_state=False):
        """
        Processes the input data before calling the model and then
        runs the model

        sc -- non-woody / size of the woody material modelled
        initial -- system state at the beginning of the timestep
        litter -- litter input for the timestep
        climate -- climate conditions for the timestep
        draw -- should the values be drawn from the distribution or not
        """
        # model parameters
        if self.ml_run:
            # maximum likelihood estimates for the model parameters
            self.param = self.param_set[0]
        elif self.draw:
            which = random.randint(1, PARAM_SAMPLES - 1)
            self.param = self.param_set[which]
        # and mean values for the initial state and input
        if self.ml_run:
            initial = self._draw_from_distr(initial, VALUESPEC, False)
            self.infall[sc] = self._draw_from_distr(litter, VALUESPEC, False)
        elif self.draw:
            initial = self._draw_from_distr(initial, VALUESPEC, True)
            self.infall[sc] = self._draw_from_distr(litter, VALUESPEC, True)
        else:
            # initial values drawn randomly only for the "draw" run
            # i.e. for the first run after maximum likelihood run
            initial = self._draw_from_distr(initial, VALUESPEC, False)
            self.infall[sc] = self._draw_from_distr(litter, VALUESPEC, True)
        # climate
        na = numpy.array
        f32 = numpy.float32
        par = na(self.param, dtype=f32)
        if self.md.climate_mode == 'monthly':
            dur = 1/12
        else:
            dur = 1
        init = na(initial, dtype=f32)
        # convert input to yearly input in all cases
        # if not self.simulation or self.md.litter_mode == 'constant yearly':
        inf = na(self.infall[sc], dtype=f32)
        # else:
        #     inf = na(self.infall[sc], dtype=f32) / 12

        temp = na(climate.get('temp'), dtype=f32)
        rain = climate.get('rain')

        # If we're using steady state as original state,
        # the leach parameters are not allowed to be set.
        leach = self.md.leach_parameter
        if self._param_file_shape == 35:
            if self.md.parameter_set == 'Yasso07':
                endstate = y07.yasso.mod5c(
                    par, dur, temp, rain, init, inf, sc, leach, steady_state
                )
            elif self.md.parameter_set == 'Yasso15':
                endstate = y15.yasso.mod5c(
                    par, dur, temp, rain, init, inf, sc, leach, steady_state
                )
            elif self.md.parameter_set == 'Yasso20':
                endstate = y20.yasso20.mod5c20(
                    par, dur, temp, rain, init, inf, sc, leach, steady_state
                )

            loader.load_parameters(param=self.param,
                                   dur=dur,
                                   climate=climate.get('temp'),
                                   rain=rain,
                                   inf=self.infall[sc],
                                   sc=sc,
                                   leach=leach,
                                   steady_state=steady_state
                                   )

        else:
            raise Exception("Invalid number of parameters in parameter file.")

        self.ts_initial += sum(initial)
        self.ts_infall += sum(self.infall[sc])
        return init, endstate.copy()

    def _predict_timestep(self, sample, timestep):
        """
        Loops over all the size classes for the given sample and timestep
        """
        climate = self._construct_climate(timestep)
        if climate == -1:
            timemsg = "Simulation extends too far into the future." \
                      " Couldn't allocate inputs to all timesteps"
            return
        self.ts_initial = 0.0
        self.ts_infall = 0.0
        self.__create_input(timestep)

        for sizeclass in self.initial:
            initial, endstate = self._predict(sizeclass,
                                              self.initial[sizeclass],
                                              self.litter[sizeclass], climate)
            if timestep == 0:
                self._add_c_stock_result(sample, timestep, sizeclass, initial)
            self._add_c_stock_result(sample, timestep + 1, sizeclass, endstate)
            self._endstate2initial(sizeclass, endstate, timestep)
            self.draw = False
        self._calculate_c_change(sample, timestep + 1)
        self._calculate_co2_yield(sample, timestep + 1)

    def _predict_steady_state(self, sample):
        """
        Makes a single prediction for the steady state for each sizeclass
        """
        climate = self._construct_climate(0)
        self.ts_initial = 0.0
        self.ts_infall = 0.0
        self.__create_input(0)
        for sizeclass in self.initial:
            initial, endstate = self._predict(sizeclass,
                                              self.initial[sizeclass],
                                              self.litter[sizeclass], climate,
                                              steady_state=True)
            self._add_steady_state_result(sizeclass, endstate)
            self.draw = False

    def _steadystate2initial(self):
        """
        Transfers the endstate masses to the initial state description of
        masses and percentages with standard deviations. Std set to zero.
        """
        self.ss_result = []
        ss = self.steady_state
        sizeclasses = numpy.unique(ss[:, 0])
        for sc in sizeclasses:
            criterium = (ss[:, 0] == sc)
            target = numpy.where(criterium)[0]
            div = len(target)
            masses = [ss[t, 1:].sum() for t in target]
            mass_sum = sum(masses)
            m = mass_sum / div
            m_std = self._std(masses)
            acids = ss[target, 1] / masses
            a = acids.sum() / div
            a_std = self._std(acids)
            waters = ss[target, 2] / masses
            w = waters.sum() / div
            w_std = self._std(waters)
            ethanols = ss[target, 3] / masses
            e = ethanols.sum() / div
            e_std = self._std(ethanols)
            nonsolubles = ss[target, 4] / masses
            n = nonsolubles.sum() / div
            n_std = self._std(nonsolubles)
            humuses = ss[target, 5] / masses
            h = humuses.sum() / div
            h_std = self._std(humuses)
            self.ss_result.append([m, m_std, a, a_std, w, w_std,
                                   e, e_std, n, n_std, h, h_std, sc])

    def _std(self, data):
        """
        Computes the standard deviation
        """
        var = stats.var(data)
        if var > 0.0:
            sd = math.sqrt(var)
        else:
            sd = 0.0
        return sd
