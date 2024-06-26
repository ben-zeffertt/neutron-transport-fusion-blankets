
import numpy as np
import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
# import time

# %% Neutron Transport Class & Functions


class Neutron:
    def __init__(self, speed, material='vacuum', initial_position=(0, 0, 0)):
        self.path = [initial_position]  # Initialize with position at origin
        self.status = 0  # Initialize as in range of simulation
        # Initialize moving in x direction
        self.direction = {'theta': np.pi / 2, 'phi': 0}
        self.speed = speed  # Mean free paths per second
        self.material = material  # Material the neutron is in

    def scatter(self):
        # Randomize theta and phi when scattered
        self.direction['theta'] = np.arccos(1 - 2 * np.random.uniform())
        self.direction['phi'] = 2 * np.pi * np.random.uniform()

    def move(self, record_lambda=None):
        # Calculate new position based on current direction and speed
        if record_lambda is None:  # If in vacuum
            x = self.path[-1][0] + self.speed * \
                np.sin(self.direction['theta']) * np.cos(self.direction['phi'])
            y = self.path[-1][1] + self.speed * \
                np.sin(self.direction['theta']) * np.sin(self.direction['phi'])
            z = self.path[-1][2] + self.speed * np.cos(self.direction['theta'])
        else:  # If not in vacuum
            x = self.path[-1][0] + self.speed * np.sin(self.direction['theta']) * np.cos(
                self.direction['phi']) * (-record_lambda * np.log(np.random.uniform()))
            y = self.path[-1][1] + self.speed * np.sin(self.direction['theta']) * np.sin(
                self.direction['phi']) * (-record_lambda * np.log(np.random.uniform()))
            z = self.path[-1][2] + self.speed * \
                np.cos(self.direction['theta']) * \
                (-record_lambda * np.log(np.random.uniform()))
        self.path.append((x, y, z))

    def absorb(self):
        # Set status to absorbed
        self.status = 3

    def transmit(self):
        # Set status to transmitted
        self.status = 1

    def reflect(self):
        # Set status to reflected
        self.status = 2

    def in_blanket(self):
        # Set status to in blanket
        self.status = 4


def simulate_neutron_flux_store(materials, proportions, number_density, scattering_cross_sections, absorption_cross_sections,
                                num_iterations=300, neutron_number=10, breeder_lims=(100, 200),
                                finite_space_lims=(0, 300), y_lims=(-50, 50), z_lims=(-50, 50), velocity=1):
    '''
    This function simulates a flux of neutrons from one direction for a certain number of iterations.

    Parameters:
    materials: List of materials in the breeder blanket.
    proportions: Proportions of the materials in the breeder blanket.
    number_density: Number density of the material.
    scattering_cross_sections: Scattering cross sections of the materials.
    absorption_cross_sections: Absorption cross sections of the materials.
    num_iterations: The number of iterations for which the simulation should run.
    neutron_number: The number of neutrons to start with (default is 10).
    breeder_lims: The x limits of the breeder region (default is (100, 200)).
    finite_space_lims: The x limits of the simulation space (default is (0, 300)).
    y_lims: The y limits of the region (default is (-50, 50)).
    z_lims: The z limits of the region (default is (-50, 50)).
    velocity: The velocity of the neutrons in the x direction (default is 1).

    Returns:
    number_absorbed, number_transmitted, number_reflected, number_in_blanket, paths: The number of neutrons absorbed,
    transmitted, reflected, in blanket, and the paths of all neutrons.
    '''
    # Initialize the neutrons in vacuum
    neutrons = [Neutron(velocity) for _ in range(neutron_number)]

    neutrons = [  # Initialise Neutron Flux randomly across the x=0 plane
        Neutron(
            velocity,
            initial_position=(
                0,
                np.random.uniform(
                    *
                    y_lims),
                np.random.uniform(
                    *
                    z_lims))) for _ in range(neutron_number)]

    num_transmitted = 0
    num_absorbed = 0
    num_reflected = 0
    num_in_blanket = 0
    # Initialize the dictionary for absorbed materials
    absorbed_materials = {material: 0 for material in materials}

    for _ in range(num_iterations):
        for neutron in neutrons:
            if neutron.status == 0:  # Only move neutrons that are still in the loop
                if neutron.material != 'vacuum':
                    # Calculate the mean free path and absorption probability for the current
                    # material
                    record_lambda = 1 / \
                        (number_density *
                         absorption_cross_sections[neutron.material])
                else:
                    record_lambda = None
                neutron.move(record_lambda)
                x, y, z = neutron.path[-1]
                if ((x > breeder_lims[0]) and (x < breeder_lims[1]) and
                    (y > y_lims[0]) and (y < y_lims[1]) and
                        (z > z_lims[0]) and (z < z_lims[1])):
                    # Randomly choose a material for the neutron based on the proportions
                    neutron.material = np.random.choice(
                        materials, p=proportions)
                    if neutron.material != 'vacuum':
                        # Calculate the mean free path and absorption probability for the current
                        # material
                        record_lambda = 1 / \
                            (number_density *
                             absorption_cross_sections[neutron.material])
                        prob_a = absorption_cross_sections[neutron.material] * \
                            number_density
                        prob_s = scattering_cross_sections[neutron.material] * \
                            number_density
                        if np.random.uniform() < prob_a:
                            neutron.absorb()
                            # Increment the count for the material
                            absorbed_materials[neutron.material] += 1
                            num_absorbed += 1
                        elif np.random.uniform() < prob_s:
                            neutron.scatter()
                if ((x > breeder_lims[1])  # if beyond blanket: "Transmitted"
                    and ((y < y_lims[0]) or (y > y_lims[1]) or  # Out of fiducial range conditions
                         (z < z_lims[0]) or (z > z_lims[1]) or (x > finite_space_lims[1]))):
                    neutron.transmit()
                    num_transmitted += 1
                elif ((x < breeder_lims[0])  # if before blanket: "Reflected"
                      and ((y < y_lims[0]) or (y > y_lims[1]) or  # Out of fiducial range conditions
                           (z < z_lims[0]) or (z > z_lims[1]) or (x < finite_space_lims[0]))):
                    neutron.reflect()
                    num_reflected += 1
                elif ((x > breeder_lims[0]) and (x < breeder_lims[1])  # if still "in blanket"
                      and ((y < y_lims[0]) or (y > y_lims[1]) or  # Out of fiducial range conditions
                           (z < z_lims[0]) or (z > z_lims[1]))):
                    neutron.in_blanket()
                    num_in_blanket += 1

    # Extract the paths from the neutrons
    paths = [neutron.path for neutron in neutrons]

    return num_absorbed, num_transmitted, num_reflected, num_in_blanket, paths, absorbed_materials


""" ~Ben Zeffertt
I didn't want to edit your code so I've just made my own 'copy' function. 
it is used to plot the various output numbers against time.
it will also be used to find the time variation of the numbers so that a rate
of tritium production can be found. 
"""


def simulate_neutron_flux_store_tracking(materials, proportions, number_density, scattering_cross_sections, absorption_cross_sections,
                                         num_iterations=300, neutron_number=10, breeder_lims=(100, 200),
                                         finite_space_lims=(0, 300), y_lims=(-50, 50), z_lims=(-50, 50), velocity=1):

    neutrons = [Neutron(velocity, initial_position=(0, np.random.uniform(
        *y_lims), np.random.uniform(*z_lims))) for _ in range(neutron_number)]

    outcomes_tracking = {'num_absorbed': [], 'num_transmitted': [
    ], 'num_reflected': [], 'num_in_blanket': [], 'time': []}
    absorbed_materials_tracking = {material: [] for material in materials}
    absorbed_materials_tracking['time'] = []

    num_transmitted = 0
    num_absorbed = 0
    num_reflected = 0
    num_in_blanket = 0
    absorbed_materials = {material: 0 for material in materials}

    for iteration in range(num_iterations):
        for neutron in neutrons:
            if neutron.status == 0:  # Only move neutrons that are still in the loop
                if neutron.material != 'vacuum':
                    # Calculate the mean free path and absorption probability for the current
                    # material
                    record_lambda = 1 / \
                        (number_density *
                         absorption_cross_sections[neutron.material])
                else:
                    record_lambda = None
                neutron.move(record_lambda)
                x, y, z = neutron.path[-1]
                if ((x > breeder_lims[0]) and (x < breeder_lims[1]) and
                    (y > y_lims[0]) and (y < y_lims[1]) and
                        (z > z_lims[0]) and (z < z_lims[1])):
                    # Randomly choose a material for the neutron based on the proportions
                    neutron.material = np.random.choice(
                        materials, p=proportions)
                    if neutron.material != 'vacuum':
                        # Calculate the mean free path and absorption probability for the current
                        # material
                        record_lambda = 1 / \
                            (number_density *
                             absorption_cross_sections[neutron.material])
                        prob_a = absorption_cross_sections[neutron.material] * \
                            number_density
                        prob_s = scattering_cross_sections[neutron.material] * \
                            number_density
                        if np.random.uniform() < prob_a:
                            neutron.absorb()
                            # Increment the count for the material
                            absorbed_materials[neutron.material] += 1
                            num_absorbed += 1
                        elif np.random.uniform() < prob_s:
                            neutron.scatter()
                if ((x > breeder_lims[1])  # if beyond blanket: "Transmitted"
                    and ((y < y_lims[0]) or (y > y_lims[1]) or  # Out of fiducial range conditions
                         (z < z_lims[0]) or (z > z_lims[1]) or (x > finite_space_lims[1]))):
                    neutron.transmit()
                    num_transmitted += 1
                elif ((x < breeder_lims[0])  # if before blanket: "Reflected"
                      and ((y < y_lims[0]) or (y > y_lims[1]) or  # Out of fiducial range conditions
                           (z < z_lims[0]) or (z > z_lims[1]) or (x < finite_space_lims[0]))):
                    neutron.reflect()
                    num_reflected += 1
                elif ((x > breeder_lims[0]) and (x < breeder_lims[1])  # if still "in blanket"
                      and ((y < y_lims[0]) or (y > y_lims[1]) or  # Out of fiducial range conditions
                           (z < z_lims[0]) or (z > z_lims[1]))):
                    neutron.in_blanket()
                    num_in_blanket += 1

        # After processing all neutrons for this iteration, record the current counts.
        outcomes_tracking['num_absorbed'].append(num_absorbed)
        outcomes_tracking['num_transmitted'].append(num_transmitted)
        outcomes_tracking['num_reflected'].append(num_reflected)
        outcomes_tracking['num_in_blanket'].append(num_in_blanket)
        outcomes_tracking['time'].append(iteration)

        for material in materials:
            absorbed_materials_tracking[material].append(
                absorbed_materials[material])
        absorbed_materials_tracking['time'].append(iteration)

    return outcomes_tracking, absorbed_materials_tracking


def calculate_tritium_production_rate(absorbed_materials_tracking):
    lithium6_rates = [absorbed_materials_tracking['Lithium-6'][i] - absorbed_materials_tracking['Lithium-6'][i - 1]
                      for i in range(1, len(absorbed_materials_tracking['Lithium-6']))]
    lithium7_rates = [absorbed_materials_tracking['Lithium-7'][i] - absorbed_materials_tracking['Lithium-7'][i - 1]
                      for i in range(1, len(absorbed_materials_tracking['Lithium-7']))]
    tritium_rates = [li6 + li7 for li6,
                     li7 in zip(lithium6_rates, lithium7_rates)]
    tritium_cumulative = np.cumsum(tritium_rates).tolist()

    # Insert a zero at the beginning of rates lists to align with the time steps
    lithium6_rates.insert(0, 0)
    lithium7_rates.insert(0, 0)
    tritium_rates.insert(0, 0)

    return lithium6_rates, lithium7_rates, tritium_rates, tritium_cumulative


# %% Plotting Functions


def plot_simulation_results(outcomes_tracking, absorbed_materials_tracking):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plotting outcome counts
    ax.plot(outcomes_tracking['time'],
            outcomes_tracking['num_absorbed'], label='Absorbed')
    ax.plot(outcomes_tracking['time'],
            outcomes_tracking['num_transmitted'], label='Transmitted')
    ax.plot(outcomes_tracking['time'],
            outcomes_tracking['num_reflected'], label='Reflected')
    ax.plot(outcomes_tracking['time'],
            outcomes_tracking['num_in_blanket'], label='In Blanket')

    # Plotting absorbed material counts
    for material in absorbed_materials_tracking.keys():
        if material != 'time':
            ax.plot(absorbed_materials_tracking['time'],
                    absorbed_materials_tracking[material], label=f'Absorbed in {material}')

    ax.set_xlabel('Iteration (Time)')
    ax.set_ylabel('Count')
    ax.set_title('Neutron Outcomes Over Time')
    ax.legend()
    plt.show()


def plot_tritium_rates(lithium6_rates, lithium7_rates, tritium_rates, tritium_cumulative, time):
    # PLOT THE TRITIUM RATE OF PRODUCTION FROM Li6 and Li7 AND CUMULATIVE

    plt.figure(figsize=(14, 7))

    # Plot the rates of absorption for Lithium-6 and Lithium-7
    plt.plot(time, lithium6_rates,
             label='Lithium-6 Tritium Production Rate', marker='o')
    plt.plot(time, lithium7_rates,
             label='Lithium-7 Tritium Production Rate', marker='x')

    # Plot the rate of tritium production
    plt.plot(time, tritium_rates,
             label='Total Tritium Production Rate', marker='^')

    # Plot the cumulative tritium production
    plt.plot(time[1:], tritium_cumulative,
             label='Cumulative Tritium Production', linestyle='--')

    # Adding titles and labels
    plt.title('Tritium Production and Lithium Absorption Rates Over Time')
    plt.xlabel('Time (Iterations)')
    plt.ylabel('log(Number)')
    plt.legend()
    plt.yscale('log')
    plt.grid(True)
    plt.show()


def plot_neutron_paths(paths, x_lims=(0, 300), y_lims=(-100, 100), z_lims=(-100, 100),
                       breeder_lims=(100, 200), n=1):
    '''
    This function plots the path of each neutron.

    Parameters:
    paths: A list of paths of each neutron. Each path is a list of (x, y, z) coordinates.
    x_lims: The x limits of the region with finite mean free path (default is (5, 15)).
    y_lims: The y limits of the region (default is (-100, 100)).
    z_lims: The z limits of the region (default is (-100, 100)).
    n: The function will plot every nth point to reduce load (default is 1).
    '''

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    colors = plt.cm.jet(np.linspace(0, 1, len(paths)))  # Create a color map

    # Add a shaded region to indicate the finite mean free path region
    for z in np.linspace(z_lims[0], z_lims[1], 100):  # Adjust the range as needed
        ax.add_collection3d(plt.fill_between(np.linspace(breeder_lims[0], breeder_lims[1], 10), y_lims[0],
                            y_lims[1], color='grey', alpha=0.01), zs=z, zdir='z')

    for i, path in enumerate(paths):
        if i % n == 0:  # Plot every nth path
            x, y, z = zip(*path)  # Unzip the coordinates
            # Use line plot and color-code each path
            ax.plot(x, y, z, color=colors[i])

    # Set the limits of the x, y, and z axes
    ax.set_xlim(x_lims)  # Set x limits
    ax.set_ylim(y_lims)  # Set y limits
    ax.set_zlim(z_lims)  # Set z limits

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')


def plot_pie_charts(num_reflected, num_transmitted, num_in_blanket, absorbed_materials):
    """
    This function generates a pie chart for the reflection, transmission, and absorption processes
    for a single material.

    Parameters:
    num_reflected: The number of neutrons reflected.
    num_transmitted: The number of neutrons transmitted.
    num_in_blanket: The number of neutrons in the blanket.
    absorbed_materials: A dictionary with the number of neutrons absorbed in each material.

    Returns:
    None. The function generates a pie chart.
    """
    import matplotlib.pyplot as plt

    processes = ['Reflection', 'Transmission', 'In Blanket'] + \
        list(absorbed_materials.keys())
    counts = [num_reflected, num_transmitted, num_in_blanket] + \
        list(absorbed_materials.values())
    explode = (0.05,) * len(processes)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=processes, explode=explode, autopct='%1.0f%%')


# %% Main


def main():
    # Define the proprotions of material that exist within the breeder blanket
    materials = ['Lead', 'Lithium-6', 'Lithium-7']
    # NB THE PROPROTIONS HAVE TO MATCH TO THE MATERIALS ABOVE
    proportions = [0.8, 0.1, 0.1]
    # Nuclear absorption cross section of the material
    cross_section_absorptions = {'Lead': 0.2,
                                 'Lithium-6': 0.2, 'Lithium-7': 0.2}
    # Nuclear scattering cross section of the material
    cross_section_scatterings = {'Lead': 0.1,
                                 'Lithium-6': 0.1, 'Lithium-7': 0.1}
    number_density = 0.2  # Number density of the material
    number_iterations = 50  # The time for which the simulation should run
    neutron_number_set = 2500  # The number of starting neutrons
    # The x values of where the breeder material begins and ends
    breeder_lims_set = (0, 1200)
    # NB these are the boundary conditions for the
    xlims_set = (-50, breeder_lims_set[1] + 100)
    # simulation, can adjust as you wish.
    ylims_set = (-50, 50)
    zlims_set = (-50, 50)

    # Call the simulate_neutron_flux function
    num_absorbed, num_transmitted, num_reflected, num_in_blanket, paths, absorbed_materials = \
        simulate_neutron_flux_store(materials, proportions, number_density, cross_section_scatterings,
                                    cross_section_absorptions,
                                    number_iterations, neutron_number_set, breeder_lims_set,
                                    finite_space_lims=xlims_set, y_lims=ylims_set, z_lims=zlims_set,
                                    velocity=1)

    # Absorbed is when a neutron has reacted with the blanket material
    print(f"Number of Neutrons Absorbed: {num_absorbed}")
    # Transmitted is when a neutron has left the simulation boundaries after passing through
    # the blanket
    print(f"Number of Neutrons Transmitted: {num_transmitted}")
    # Reflected is when a neutron has left the simulation boundaries in front of the blanket
    print(f"Number of Neutrons Reflected: {num_reflected}")
    # "in blanket" refers to when a neutron has left the simulation while within the blanket
    # for approximation reasons we will ignore these ones
    print(f"Number of Neutrons in Blanket: {num_in_blanket}")

    # Call the plot_pie_charts function
    plot_pie_charts(num_reflected, num_transmitted,
                    num_in_blanket, absorbed_materials)

    # Call the plot_neutron_paths function
    plot_neutron_paths(paths, x_lims=xlims_set, y_lims=ylims_set,
                       z_lims=zlims_set, breeder_lims=breeder_lims_set, n=5)
    # Note "n" makes it so only "n" of the neutron paths are plotted. This increased to reduce
    # plotting load.

    plt.show()

    # PLOT THE SIMULATION RESULTS AGAINST TIME
    outcomes_tracking, absorbed_materials_tracking = simulate_neutron_flux_store_tracking(
        materials, proportions, number_density, cross_section_scatterings,
        cross_section_absorptions, number_iterations, neutron_number_set, breeder_lims_set,
        finite_space_lims=xlims_set, y_lims=ylims_set, z_lims=zlims_set, velocity=1)

    # Call the plotting function for tracking results
    plot_simulation_results(outcomes_tracking, absorbed_materials_tracking)

    # PLOT THE TRITIUM RATE OF PRODUCTION FROM Li6 and Li7 AND CUMULATIVE

    lithium6_rates, lithium7_rates, tritium_rates, tritium_cumulative = calculate_tritium_production_rate(
        absorbed_materials_tracking)
    time = absorbed_materials_tracking['time']

    plot_tritium_rates(lithium6_rates, lithium7_rates,
                       tritium_rates, tritium_cumulative, time)

    # find the peak in the total neutron absorption against thickness

    max_thickness = 2000
    steps = 250
    thicknesses = np.linspace(1, max_thickness, steps)
    counts_array = []
    counts_per_thickness_array = []

    processes = ['Reflection', 'Transmission',
                 'In Blanket', 'Lead', 'Lithium-6', 'Lithium-7']

    for thickness in thicknesses:
        breeder_lims_set = (0, thickness)

        num_absorbed, num_transmitted, num_reflected, num_in_blanket, paths, absorbed_materials = \
            simulate_neutron_flux_store(materials, proportions, number_density, cross_section_scatterings,
                                        cross_section_absorptions,
                                        number_iterations, neutron_number_set, breeder_lims_set,
                                        finite_space_lims=xlims_set, y_lims=ylims_set, z_lims=zlims_set,
                                        velocity=1)

        counts = [num_reflected, num_transmitted, num_in_blanket] + \
            list(absorbed_materials.values())

        counts_array.append(counts)

        counts_per_thickness = counts / thickness

        counts_per_thickness_array.append(counts_per_thickness)

    reflection_counts = [row[0] for row in counts_array]
    transmission_counts = [row[1] for row in counts_array]
    in_blanket_counts = [row[2] for row in counts_array]
    lead_counts = [row[3] for row in counts_array]
    lithium6_counts = [row[4] for row in counts_array]
    lithium7_counts = [row[5] for row in counts_array]

    reflection_counts_per_thickness = [row[0]
                                       for row in counts_per_thickness_array]
    transmission_counts_per_thickness = [row[1]
                                         for row in counts_per_thickness_array]
    in_blanket_counts_per_thickness = [row[2]
                                       for row in counts_per_thickness_array]
    lead_counts_per_thickness = [row[3] for row in counts_per_thickness_array]
    lithium6_counts_per_thickness = [row[4]
                                     for row in counts_per_thickness_array]
    lithium7_counts_per_thickness = [row[5]
                                     for row in counts_per_thickness_array]

    plt.plot(thicknesses, lithium6_counts, label='lithium 6')
    plt.plot(thicknesses, lithium7_counts, label='lithium 7')
    plt.legend()
    plt.title('lithium counts against thickness')
    plt.xlabel('thickness')
    plt.ylabel('total counts')
    plt.show()

    argmax6 = np.argmax(lithium6_counts_per_thickness)
    argmax7 = np.argmax(lithium7_counts_per_thickness)

    plt.plot(thicknesses, lithium6_counts_per_thickness, label='lithium 6')
    plt.scatter(thicknesses[argmax6], lithium6_counts_per_thickness[argmax6],
                label='maximum for li6', c='blue')
    plt.plot(thicknesses, lithium7_counts_per_thickness, label='lithium 7')
    plt.scatter(thicknesses[argmax7], lithium7_counts_per_thickness[argmax7],
                label='maximum for li7', c='orange')

    plt.legend()
    plt.title('lithium counts per thickness (lift density?) against thickness')
    plt.xlabel('thickness')
    plt.ylabel('total counts per unit thickness')
    plt.show()


if __name__ == "__main__":
    main()


'''

notes from call : 
    
neutron absorption against thickness 

lift density is total neutron absorption against thickness 

could do an optimisation of 

'''


if __name__ == "__main__":
    main()
