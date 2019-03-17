"""Functions for pulling data primarily from the EIA's Form 860."""

import sqlalchemy as sa
import pandas as pd

import pudl
import pudl.constants as pc
import pudl.models.entities

# Shorthand for easier table referecnes:
pt = pudl.models.entities.PUDLBase.metadata.tables


def utilities_eia(start_date=None, end_date=None, testing=False):
    """Pull all fields from the EIA860 Utilities table."""
    pudl_engine = pudl.init.connect_db(testing=testing)
    # grab the entity table
    utils_eia_tbl = pt['utilities_entity_eia']
    utils_eia_select = sa.sql.select([utils_eia_tbl])
    utils_eia_df = pd.read_sql(utils_eia_select, pudl_engine)

    # grab the annual eia entity table
    utils_an_eia_tbl = pt['utilities_annual_eia']
    utils_an_eia_select = sa.sql.select([utils_an_eia_tbl])

    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        utils_an_eia_select = utils_an_eia_select.where(
            utils_an_eia_tbl.c.report_date >= start_date
        )
    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        utils_an_eia_select = utils_an_eia_select.where(
            utils_an_eia_tbl.c.report_date <= end_date
        )
    utils_an_eia_df = pd.read_sql(utils_an_eia_select, pudl_engine)

    # grab the glue table for the utility_id_pudl
    utils_g_eia_tbl = pt['utilities_eia']
    utils_g_eia_select = sa.sql.select([
        utils_g_eia_tbl.c.utility_id_eia,
        utils_g_eia_tbl.c.utility_id_pudl,
    ])
    utils_g_eia_df = pd.read_sql(utils_g_eia_select, pudl_engine)

    out_df = pd.merge(utils_eia_df, utils_an_eia_df,
                      how='left', on=['utility_id_eia', ])
    out_df = pd.merge(out_df, utils_g_eia_df,
                      how='left', on=['utility_id_eia', ])

    out_df = out_df.drop(['id'], axis=1)
    first_cols = [
        'report_date',
        'utility_id_eia',
        'utility_id_pudl',
        'utility_name',
    ]

    out_df = pudl.helpers.organize_cols(out_df, first_cols)
    out_df = pudl.helpers.extend_annual(
        out_df, start_date=start_date, end_date=end_date)
    return out_df


def plants_eia(start_date=None, end_date=None, testing=False):
    """Pull all fields from the EIA Plants tables."""
    pudl_engine = pudl.init.connect_db(testing=testing)

    # grab the entity table
    plants_eia_tbl = pt['plants_entity_eia']
    plants_eia_select = sa.sql.select([plants_eia_tbl])
    plants_eia_df = pd.read_sql(plants_eia_select, pudl_engine)

    # grab the annual table select
    plants_an_eia_tbl = pt['plants_annual_eia']
    plants_an_eia_select = sa.sql.select([plants_an_eia_tbl])
    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        plants_an_eia_select = plants_an_eia_select.where(
            plants_an_eia_tbl.c.report_date >= start_date
        )
    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        plants_an_eia_select = plants_an_eia_select.where(
            plants_an_eia_tbl.c.report_date <= end_date
        )
    plants_an_eia_df = pd.read_sql(plants_an_eia_select, pudl_engine)
    plants_an_eia_df['report_date'] = \
        pd.to_datetime(plants_an_eia_df['report_date'])

    # plant glue table
    plants_g_eia_tbl = pt['plants_eia']
    plants_g_eia_select = sa.sql.select([
        plants_g_eia_tbl.c.plant_id_eia,
        plants_g_eia_tbl.c.plant_id_pudl,
    ])
    plants_g_eia_df = pd.read_sql(plants_g_eia_select, pudl_engine)

    out_df = pd.merge(plants_eia_df, plants_an_eia_df,
                      how='left', on=['plant_id_eia', ])

    out_df = pd.merge(out_df, plants_g_eia_df,
                      how='left', on=['plant_id_eia', ])

    utils_eia_tbl = pt['utilities_eia']
    utils_eia_select = sa.sql.select([
        utils_eia_tbl.c.utility_id_eia,
        utils_eia_tbl.c.utility_id_pudl,
    ])
    utils_eia_df = pd.read_sql(utils_eia_select, pudl_engine)

    out_df = pd.merge(out_df, utils_eia_df,
                      how='left', on=['utility_id_eia', ])
    return out_df


def plants_utils_eia860(start_date=None, end_date=None, testing=False):
    """
    Create a dataframe of plant and utility IDs and names from EIA.

    Returns a pandas dataframe with the following columns:
    - report_date (in which data was reported)
    - plant_name (from EIA entity)
    - plant_id_eia (from EIA entity)
    - plant_id_pudl
    - utility_id_eia (from EIA860)
    - utility_name (from EIA860)
    - utility_id_pudl

    Note: EIA 860 data has only been integrated for 2011-2016. If earlier or
          later years are requested, they will be filled in with data from the
          first or last years.
    """
    # Contains the one-to-one mapping of EIA plants to their operators, but
    # we only have the 860 data integrated for 2011 forward right now.
    plants_eia = plants_eia860(start_date=start_date,
                               end_date=end_date,
                               testing=testing)
    utils_eia = utilities_eia(start_date=start_date,
                              end_date=end_date,
                              testing=testing)

    # to avoid duplicate columns on the merge...
    plants_eia = plants_eia.drop(['utility_id_pudl', 'utility_name', 'city',
                                  'state', 'zip_code', 'street_address'],
                                 axis=1)
    out_df = pd.merge(plants_eia, utils_eia,
                      how='left', on=['report_date', 'utility_id_eia'])

    cols_to_keep = ['report_date',
                    'plant_id_eia',
                    'plant_name',
                    'plant_id_pudl',
                    'utility_id_eia',
                    'utility_name',
                    'utility_id_pudl']

    out_df = out_df[cols_to_keep]
    out_df = out_df.dropna()
    out_df.plant_id_pudl = out_df.plant_id_pudl.astype(int)
    out_df.utility_id_pudl = out_df.utility_id_pudl.astype(int)
    return out_df


def generators_eia860(start_date=None, end_date=None, testing=False):
    """
    Pull all fields reported in the generators_eia860 table.

    Merge in other useful fields including the latitude & longitude of the
    plant that the generators are part of, canonical plant & operator names and
    the PUDL IDs of the plant and operator, for merging with other PUDL data
    sources.

    Fill in data for adjacent years if requested, but never fill in earlier
    than the earliest working year of data for EIA923, and never add more than
    one year on after the reported data (since there should at most be a one
    year lag between EIA923 and EIA860 reporting)

    Args:
        start_date (date): the earliest EIA 860 data to retrieve or synthesize
        end_date (date): the latest EIA 860 data to retrieve or synthesize
        testing (bool): Connect to the live PUDL DB or the testing DB?

    Returns:
        A pandas dataframe.

    """
    pudl_engine = pudl.init.connect_db(testing=testing)
    # Almost all the info we need will come from here.
    gens_eia860_tbl = pt['generators_eia860']
    gens_eia860_select = sa.sql.select([gens_eia860_tbl, ])
    # To get the Lat/Lon coordinates
    plants_entity_eia_tbl = pt['plants_entity_eia']
    plants_entity_eia_select = sa.sql.select([
        # plants_eia860_tbl.c.report_date, # remove?
        plants_entity_eia_tbl.c.plant_id_eia,
        plants_entity_eia_tbl.c.plant_name,
        plants_entity_eia_tbl.c.latitude,
        plants_entity_eia_tbl.c.longitude,
        plants_entity_eia_tbl.c.state,
        plants_entity_eia_tbl.c.balancing_authority_code,
        plants_entity_eia_tbl.c.balancing_authority_name,
        plants_entity_eia_tbl.c.iso_rto_name,
        plants_entity_eia_tbl.c.iso_rto_code,
    ])

    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        # We don't want to get too crazy with the date extensions...
        # start_date shouldn't go back before the earliest working year of
        # EIA 923
        eia923_start_date = \
            pd.to_datetime('{}-01-01'.format(
                min(pc.working_years['eia923'])))
        if start_date < eia923_start_date:
            raise AssertionError(f"""
EIA 860 generators start_date ({start_date}) is before the
earliest EIA 923 data is available ({eia923_start_date}).
That's too much backfilling.""")
        gens_eia860_select = gens_eia860_select.where(
            gens_eia860_tbl.c.report_date >= start_date
        )

    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        # end_date shouldn't be more than one year ahead of the most recent
        # year for which we have EIA 860 data:
        eia860_end_date = \
            pd.to_datetime('{}-12-31'.format(
                max(pc.working_years['eia860'])))
        if end_date > eia860_end_date + pd.DateOffset(years=1):
            raise AssertionError(f"""
EIA 860 end_date ({end_date}) is more than a year after the
most recent EIA 860 data available ({eia860_end_date}).
That's too much forward filling.""")
        gens_eia860_select = gens_eia860_select.where(
            gens_eia860_tbl.c.report_date <= end_date
        )

    gens_eia860 = pd.read_sql(gens_eia860_select, pudl_engine)
    # Canonical sources for these fields are elsewhere. We will merge them in.
    gens_eia860 = gens_eia860.drop(['utility_id_eia',
                                    'utility_name'], axis=1)
    plants_entity_eia_df = pd.read_sql(plants_entity_eia_select, pudl_engine)
    out_df = pd.merge(gens_eia860, plants_entity_eia_df,
                      how='left', on=['plant_id_eia'])
    out_df.report_date = pd.to_datetime(out_df.report_date)

    # Bring in some generic plant & utility information:
    pu_eia = plants_utils_eia860(start_date=start_date,
                                 end_date=end_date,
                                 testing=testing)
    out_df = pd.merge(out_df, pu_eia,
                      on=['report_date', 'plant_id_eia', 'plant_name'])

    # Drop a few extraneous fields...
    cols_to_drop = ['id', ]
    out_df = out_df.drop(cols_to_drop, axis=1)

    # In order to be able to differentiate betweet single and multi-fuel
    # plants, we need to count how many different simple energy sources there
    # are associated with plant's generators. This allows us to do the simple
    # lumping of an entire plant's fuel & generation if its primary fuels
    # are homogeneous, and split out fuel & generation by fuel if it is
    # hetereogeneous.
    ft_count = out_df[['plant_id_eia', 'fuel_type_code_pudl', 'report_date']].\
        drop_duplicates().groupby(['plant_id_eia', 'report_date']).count()
    ft_count = ft_count.reset_index()
    ft_count = ft_count.rename(
        columns={'fuel_type_code_pudl': 'fuel_type_count'})
    out_df = pd.merge(out_df, ft_count, how='left',
                      on=['plant_id_eia', 'report_date'])

    first_cols = [
        'report_date',
        'plant_id_eia',
        'plant_id_pudl',
        'plant_name',
        'utility_id_eia',
        'utility_id_pudl',
        'utility_name',
        'generator_id',
    ]

    # Re-arrange the columns for easier readability:
    out_df = pudl.helpers.organize_cols(out_df, first_cols)
    out_df = pudl.helpers.extend_annual(
        out_df, start_date=start_date, end_date=end_date)
    out_df = out_df.sort_values(['report_date',
                                 'plant_id_eia',
                                 'generator_id'])

    return out_df


def boiler_generator_assn_eia860(start_date=None, end_date=None,
                                 testing=False):
    """Pull all fields from the EIA 860 boiler generator association table."""
    pudl_engine = pudl.init.connect_db(testing=testing)
    bga_eia860_tbl = pt['boiler_generator_assn_eia860']
    bga_eia860_select = sa.sql.select([bga_eia860_tbl])

    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        bga_eia860_select = bga_eia860_select.where(
            bga_eia860_tbl.c.report_date >= start_date
        )
    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        bga_eia860_select = bga_eia860_select.where(
            bga_eia860_tbl.c.report_date <= end_date
        )
    bga_eia860_df = pd.read_sql(bga_eia860_select, pudl_engine)
    out_df = pudl.helpers.extend_annual(bga_eia860_df,
                                        start_date=start_date, end_date=end_date)
    return out_df


def ownership_eia860(start_date=None, end_date=None, testing=False):
    """
    Pull a useful set of fields related to ownership_eia860 table.

    Args:
    -----
        start_date (date): date of the earliest data to retrieve
        end_date (date): date of the latest data to retrieve
        testing (bool): True if we're connecting to the pudl_test DB, False
            if we're connecting to the live PUDL DB. False by default.
    Returns:
    --------
        out_df (pandas dataframe)

    """
    pudl_engine = pudl.init.connect_db(testing=testing)
    o_eia860_tbl = pt['ownership_eia860']
    o_eia860_select = sa.sql.select([o_eia860_tbl, ])
    o_df = pd.read_sql(o_eia860_select, pudl_engine)

    pu_eia = plants_utils_eia860(start_date=start_date,
                                 end_date=end_date,
                                 testing=testing)
    pu_eia = pu_eia[['plant_id_eia', 'plant_id_pudl', 'plant_name',
                     'utility_id_pudl', 'report_date']]

    o_df['report_date'] = pd.to_datetime(o_df.report_date)
    out_df = pd.merge(o_df, pu_eia,
                      how='left', on=['report_date', 'plant_id_eia'])

    out_df = out_df.drop(['id'], axis=1)

    out_df = out_df.dropna(subset=[
        'plant_id_eia',
        'plant_id_pudl',
        'utility_id_eia',
        'utility_id_pudl',
        'generator_id',
        'owner_utility_id_eia',
    ])

    first_cols = [
        'report_date',
        'plant_id_eia',
        'plant_id_pudl',
        'plant_name',
        'utility_id_eia',
        'utility_id_pudl',
        'utility_name',
        'generator_id',
        'owner_utility_id_eia',
        'owner_name',
    ]

    # Re-arrange the columns for easier readability:
    out_df = pudl.helpers.organize_cols(out_df, first_cols)
    out_df['plant_id_pudl'] = out_df.plant_id_pudl.astype(int)
    out_df['utility_id_pudl'] = out_df.utility_id_pudl.astype(int)
    out_df = pudl.helpers.extend_annual(
        out_df, start_date=start_date, end_date=end_date)

    return out_df
