from csv_conversion import convert_to_peaks
import matplotlib.pyplot as plt
from   dlsAnalyzer       import *

if __name__ == "__main__":
    # convert data to peaks
    convert_to_peaks("CleanedEMDSignal.csv")
    # Initialize plots
    plt.rcParams['figure.figsize'] = [10, 5]

    # Start dls analyzer
    print("Initializing DLS...")
    dls               = dlsAnalyzer()
    l                 = dls.loadExperiment("subsets.csv","test")
    d                 = dls.experimentsOri["test"] 

    d.lambda0         = 635                #  Laser wavelength in nanometers
    d.scatteringAngle = 90 / 180 * np.pi  #  Angle of detection in radians
    d.getQ()                               #  Calculate the Bragg wave vector
    d.createFittingS_space(0.09,1e6,200)   #  Discretize the decay rate space we will use for the fitting
    d.setAutocorrelationData()   

    # Estimate the intercept of the second order autocorrelation curves
    print("Estimating beta and correlation...")
    d.getBetaEstimate()   
    # Compute  the first order autocorrelation curves
    # Due to errors in measurement, same values can't be computed (negative sqrt)
    d.getG1correlation() 

    # Calculate DLS data
    print("Calculating DLS results...")
    d.getInitialEstimates()
    d.getInitialEstimatesManyAlpha()
    d.getOptimalAlphaLcurve()
    d.getInitialEstimatesOptimalAlphaLcurve()
    d.getInitialEstimatesManyAlpha()

    # Find fitting curve to represent data
    print("Calculating correlation prediction...")
    d.predictAutocorrelationCurves()
    # Plot fitted data
    plt.xscale("log")
    plt.plot(d.time,d.autocorrelationPredicted[:,0],'red')
    plt.plot(d.time,d.autocorrelation[:,0],'bo',markersize=1)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Second order autocorrelation")
    plt.show()

    # Calculate and plot the results
    plt.xscale("log")
    vals = []
    data_range = [0, 200]

    for data_set in range( len(d.autocorrelation[0])):
        max1 = np.where(d.contributionsGuess[data_set] == max(d.contributionsGuess[data_set][data_range[0]:data_range[1]]))
        dia = int(d.hrs[max1].item()) * 2
        vals.append(dia)
        plt.plot(d.hrs[data_range[0]:data_range[1]],d.contributionsGuess[data_set][data_range[0]:data_range[1]], label=('Data Set ' + str(data_set) + " d = " + str(dia)))
        
    plt.xlabel("Hydrodynamic radius (nm)")
    plt.ylabel("Relative contribution")
    plt.title("Average particle diameter = " + str(np.average(vals)))
    plt.legend()
    plt.show()