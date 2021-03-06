"""
Genome, genetic map and demographic model definitions for humans.
"""
import math

import msprime

import stdpopsim.models as models
import stdpopsim.genomes as genomes
import stdpopsim.genetic_maps as genetic_maps


###########################################################
#
# Genetic maps
#
###########################################################


class HapmapII_GRCh37(genetic_maps.GeneticMap):
    """
    The Phase II HapMap Genetic map (lifted over to GRCh37) used in
    1000 Genomes. Please see the `README
    <ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/working/20110106_recombination_hotspots/README_hapmapII_GRCh37_map>`_
    for more details.
    """
    url = (
        "http://ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/working/"
        "20110106_recombination_hotspots/"
        "HapmapII_GRCh37_RecombinationHotspots.tar.gz")
    file_pattern = "genetic_map_GRCh37_{name}.txt"


genetic_maps.register_genetic_map(HapmapII_GRCh37())


###########################################################
#
# Genome definition
#
###########################################################

# List of chromosomes. Data for length information based on GRCh38,
# https://www.ncbi.nlm.nih.gov/grc/human/data

# FIXME: add mean mutation and recombination rate data to this table.
_chromosome_data = """\
chr1   248956422
chr2   242193529
chr3   198295559
chr4   190214555
chr5   181538259
chr6   170805979
chr7   159345973
chr8   145138636
chr9   138394717
chr10  133797422
chr11  135086622
chr12  133275309
chr13  114364328
chr14  107043718
chr15  101991189
chr16  90338345
chr17  83257441
chr18  80373285
chr19  58617616
chr20  64444167
chr21  46709983
chr22  50818468
chrX   156040895
chrY   57227415
"""

_chromosomes = []
for line in _chromosome_data.splitlines():
    name, length = line.split()[:2]
    _chromosomes.append(genomes.Chromosome(
        name=name, length=int(length),
        mean_mutation_rate=1e-8,  # WRONG!,
        mean_recombination_rate=1e-8))  # WRONG!


#: :class:`stdpopsim.Genome` definition for humans. Chromosome length data is
#: based on `GRCh38 <https://www.ncbi.nlm.nih.gov/grc/human/data>`_.
genome = genomes.Genome(
    species="homo_sapiens",
    chromosomes=_chromosomes,
    default_genetic_map=HapmapII_GRCh37.name)


###########################################################
#
# Demographic models
#
###########################################################


class GutenkunstThreePopOutOfAfrica(models.Model):
    """
    The three population Out-of-Africa model from Gutenkunst et al.

    .. todo:: document this model, including the original publications
        and clear information about what the different population indexes
        mean.

    """

    def __init__(self):
        super().__init__()
        # First we set out the maximum likelihood values of the various parameters
        # given in Table 1.
        N_A = 7300
        N_B = 2100
        N_AF = 12300
        N_EU0 = 1000
        N_AS0 = 510
        # Times are provided in years, so we convert into generations.
        generation_time = 25
        T_AF = 220e3 / generation_time
        T_B = 140e3 / generation_time
        T_EU_AS = 21.2e3 / generation_time
        # We need to work out the starting (diploid) population sizes based on
        # the growth rates provided for these two populations
        r_EU = 0.004
        r_AS = 0.0055
        N_EU = N_EU0 / math.exp(-r_EU * T_EU_AS)
        N_AS = N_AS0 / math.exp(-r_AS * T_EU_AS)
        # Migration rates during the various epochs.
        m_AF_B = 25e-5
        m_AF_EU = 3e-5
        m_AF_AS = 1.9e-5
        m_EU_AS = 9.6e-5
        # Population IDs correspond to their indexes in the population
        # configuration array. Therefore, we have 0=YRI, 1=CEU and 2=CHB
        # initially.
        self.population_configurations = [
            msprime.PopulationConfiguration(initial_size=N_AF),
            msprime.PopulationConfiguration(initial_size=N_EU, growth_rate=r_EU),
            msprime.PopulationConfiguration(initial_size=N_AS, growth_rate=r_AS)
        ]
        self.migration_matrix = [
            [      0, m_AF_EU, m_AF_AS],  # noqa
            [m_AF_EU,       0, m_EU_AS],  # noqa
            [m_AF_AS, m_EU_AS,       0],  # noqa
        ]
        self.demographic_events = [
            # CEU and CHB merge into B with rate changes at T_EU_AS
            msprime.MassMigration(
                time=T_EU_AS, source=2, destination=1, proportion=1.0),
            msprime.MigrationRateChange(time=T_EU_AS, rate=0),
            msprime.MigrationRateChange(
                time=T_EU_AS, rate=m_AF_B, matrix_index=(0, 1)),
            msprime.MigrationRateChange(
                time=T_EU_AS, rate=m_AF_B, matrix_index=(1, 0)),
            msprime.PopulationParametersChange(
                time=T_EU_AS, initial_size=N_B, growth_rate=0, population_id=1),
            # Population B merges into YRI at T_B
            msprime.MassMigration(
                time=T_B, source=1, destination=0, proportion=1.0),
            # Size changes to N_A at T_AF
            msprime.PopulationParametersChange(
                time=T_AF, initial_size=N_A, population_id=0)
        ]


class TennessenEuropean(models.Model):
    """
    The model is derived from the Tennesen et al.
    `analysis <https://doi.org/10.1126/science.1219240>`_  of the jSFS from
    European Americans and African Americans.

    .. todo:: document this model, including the original publications
        and clear information about what the different population indexes
        mean.

    """
    def __init__(self):
        super().__init__()
        # Population sizes
        N_A = 7310
        N_AF = 14474
        N_B = 1861
        N_EU1 = 9475
        # Times
        generation_time = 25
        T_AF = 148000 / generation_time
        T_B = 51000 / generation_time
        T_EU0 = 23000 / generation_time
        T_EU1 = 5115 / generation_time
        # Rates and Present Ne
        r_EU0 = 0.00307
        r_EU1 = 0.0195
        N_EU = N_EU1 / math.exp(-r_EU1 * T_EU1)
        self.population_configurations = [
            msprime.PopulationConfiguration(initial_size=N_EU, growth_rate=r_EU1)
        ]
        self.demographic_events = [
            msprime.PopulationParametersChange(
                time=T_EU1, initial_size=N_EU1, growth_rate=r_EU0, population_id=0),
            msprime.PopulationParametersChange(
                time=T_EU0, initial_size=N_B, growth_rate=0, population_id=0),
            msprime.PopulationParametersChange(
                time=T_B, initial_size=N_AF, growth_rate=0, population_id=0),
            msprime.PopulationParametersChange(
                time=T_AF, initial_size=N_A, growth_rate=0, population_id=0)
        ]
