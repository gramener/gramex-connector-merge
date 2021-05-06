import gramex.cache
import gramex.data
import pandas as pd
import sqlalchemy as sa


def merge(configpath):
    conf = gramex.cache.open(configpath)
    # All columns beginning with target: define target parameters
    # e.g. target:url, target:table, etc
    targetcols = [c for c in conf.columns if c.startswith('target:') and not c.endswith(':column')]
    # All columns beginning with source: define source parameters
    # e.g. source:url, source:table, etc
    sourcecols = [c for c in conf.columns if c.startswith('source:') and not c.endswith(':column')]
    # Transform columns
    for target, targetframe in conf.groupby(targetcols):
        # Append results from each source into an array of dataframe
        result = []
        # Transform all source columns
        for source, sourceframe in targetframe.groupby(sourcecols):
            # Load the data
            source_args = {key.split(':')[1]: val for key, val in zip(sourcecols, source)}
            data = gramex.data.filter(**source_args)
            # Pick relevant columns
            data = data[sourceframe['source:column'].values]
            for index, row in sourceframe.iterrows():
                if row['source:column'] not in data.columns:
                    continue
                if pd.notnull(row['default']):
                    data[row['source:column']].fillna(row['default'], inplace=True)
                if pd.notnull(row['target:column']):
                    data.rename(columns={row['source:column']: row['target:column']}, inplace=True)
            result.append(data)
        # Save into target column
        result = pd.concat(result, sort=False)
        target_args = {key.split(':')[1]: val for key, val in zip(targetcols, target)}
        con = sa.create_engine(f'sqlite:///{target_args["url"]}')
        result.to_sql(target_args['table'], con, if_exists='replace', index=False)
    return {'merged': conf[targetcols].drop_duplicates()}
