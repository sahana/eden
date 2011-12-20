from ..graphics.shapes import Line

class RegressionLine (Line):
    def __init__ (self, xdata, ydata, xbounds, ybounds):
        from rpy2.robjects import RFormula
        from rpy2 import rinterface as R

        R.initr ()
        R.globalEnv['x'] = R.FloatSexpVector (xdata)
        R.globalEnv['y'] = R.FloatSexpVector (ydata)
        formula = RFormula ('y ~ x')
        rLine = R.globalEnv.get ('lm')(formula)
        slope = rLine[0][1]
        intercept = rLine[0][0]

        y1 = slope * xbounds[0] + intercept
        y2 = slope * xbounds[1] + intercept

        p1 = (xbounds[0], y1)
        p2 = (xbounds[1], y2)

        Line.__init__ (self, point1 = p1, point2 = p2)
