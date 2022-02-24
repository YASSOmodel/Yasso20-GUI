FONT_ARIAL = 'Arial 9'
FONT_COURIER = 'Courier 10'

APP_INFO = """
For detailed information, including a user's manual, see:
http://www.syke.fi/projects/yasso

Inside the program help is available by clicking the label texts.
Program wiki is at https://github.com/JariLiski/Yasso15

Yasso15 model by Finnish Environment Institute (SYKE, www.environment.fi)
User interface by Simosol Oy (www.simosol.fi)

The program is distributed under the GNU Lesser General Public License (LGPL)
The source code is available at https://github.com/JariLiski/Yasso15
"""

DATA_STRING = """
# THE CHANGES YOU MAKE HERE HAVE ONLY EFFECT AFTER YOU SAVE THE CHANGES
#
# commented out rows begin with the # character
# numbers must be whitespace separated (space or tab)
# decimal separator is ., no thousands separator
#
[Initial state]
# Data as value pairs, mean and standard deviation, except for the size of
# woody litter mean only
# Mass as unit of mass, chemical composition as percentages of the total mass,
# size of woody litter as diameter in cm
# Data: mass, acid hydrolyzable, water soluble, ethanol soluble, non-soluble,
# humus, size of woody litter (diameter in cm)

[Constant soil carbon input]
# Data as value pairs, mean and standard deviation, except for the size of
# woody litter mean only
# Mass as unit of mass, chemical composition as percentages of the total mass,
# size of woody litter as diameter in cm
# Data: mass, acid hydrolyzable, water soluble, ethanol soluble, non-soluble,
# humus, size of woody litter (diameter in cm)

[Monthly soil carbon input]
# Data as value pairs, mean and standard deviation, except for the size of
# woody litter mean only
# Mass as unit of mass, chemical composition as percentages of the total mass,
# size of woody litter as diameter in cm
# Data: month, mass, acid hydrolyzable, water soluble, ethanol soluble,
# non-soluble, humus, size of woody litter (diameter in cm)

[Yearly soil carbon input]
# Data as value pairs, mean and standard deviation, except for the size of
# woody litter mean only
# Mass as unit of mass, chemical composition as percentages of the total mass,
# size of woody litter as diameter in cm
# Data: year, mass, acid hydrolyzable, water soluble,
# ethanol soluble, non-soluble, humus, size of woody litter (diameter in cm)

[Relative area change]
# Timestep, relative change in area

[Constant climate]
# Data: mean temperature, precipitation, amplitude of monthly mean temperature
# variation

[Yearly climate]
# Data: timestep, mean temperature, precipitation

[Monthly climate]
# Data: timestep, mean temperature, precipitation
"""
