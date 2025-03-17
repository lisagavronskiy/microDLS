from data_processing.csv_conversion import convert_to_peaks
import matplotlib.pyplot as plt
import pandas as pd
from data_processing.dlsAnalyzer import *

def post_processing():
    # convert data to peaks
    convert_to_peaks("data_output.csv")
    # Initialize plots
    # plt.rcParams['figure.figsize'] = [10, 5]

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

    df_corr = pd.DataFrame({
    "Time": d.time,
    "Autocorrelation Predicted": d.autocorrelationPredicted[:, 0],
    "Autocorrelation Actual": d.autocorrelation[:, 0]
    })
    df_corr.to_csv("autocorrelation_data.csv", index=False)
    # Plot fitted data
    # plt.xscale("log")
    # plt.plot(d.time,d.autocorrelationPredicted[:,0],'red')
    # plt.plot(d.time,d.autocorrelation[:,0],'bo',markersize=1)
    # plt.xlabel("Time (seconds)")
    # plt.ylabel("Second order autocorrelation")
    # plt.show()

    # Calculate and plot the results
    # plt.xscale("log")

    # Define the data range and radius range
    data_range = [0, 100]
    radius_range = d.hrs[data_range[0]:data_range[1]]

    # Initialize an empty list to store rows
    rows = []

    # Prepare the header with the initial columns
    header = ['Radius (nm)']

    # Add new columns for each dataset's intensity and diameter
    for data_set in range(len(d.autocorrelation[0])):
        header.append(f'Contribution {data_set + 1}')
        header.append(f'Diameter {data_set + 1} (nm)')

    # Loop through each data point in the range
    for i in range(len(radius_range)):
        row = [radius_range[i]]  # Start with the radius value for each row
        
        # Loop through each dataset and gather contributions and diameters
        for data_set in range(len(d.autocorrelation[0])):
            contributions_range = d.contributionsGuess[data_set][data_range[0]:data_range[1]]
            
            try:
                # Find the maximum contribution and calculate diameter
                max1 = np.where(d.contributionsGuess[data_set] == np.max(d.contributionsGuess[data_set][data_range[0]:data_range[1]]))
                dia = int(d.hrs[max1].item()) * 2
            except:
                dia = None

            # Add intensity and diameter for the current dataset
            row.append(contributions_range[i])
            row.append(dia)
        
        # Add the row to the list of rows
        rows.append(row)

    # Convert to DataFrame
    df_results = pd.DataFrame(rows, columns=header)

    # Save to CSV
    df_results.to_csv("results.csv", index=False)

        
        # plt.plot(d.hrs[data_range[0]:data_range[1]],d.contributionsGuess[data_set][data_range[0]:data_range[1]], label=('Data Set ' + str(data_set) + " d = " + str(dia)))
        
    # plt.xlabel("Hydrodynamic radius (nm)")
    # plt.ylabel("Relative contribution")
    # plt.title("Average particle diameter = " + str(np.average(vals)))
    # plt.legend()
    # plt.show()
