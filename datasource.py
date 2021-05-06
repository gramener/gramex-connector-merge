import gramex.cache
import gramex.data
import pandas as pd


def merge(configpath):
    config = gramex.cache.open(configpath)
    # All columns beginning with target: define target parameters
    # e.g. target:url
    targetcols = 'target:url'
    # All columns beginning with source: define source parameters
    # e.g. source:url, source:table, etc
    sourcecols = [col for col in config.columns if col.startswith('source:')]
    # Transform columns
    for target, targetframe in config.groupby(targetcols):
        # Append results from each source into an array of dataframe
        result = []
        # Transform all source columns
        for source, sourceframe in targetframe.groupby(sourcecols):
            # Load the data
            source_args = {key.split(':')[1]: val for key, val in zip(sourcecols, source)}
            data = gramex.data.filter(**source_args)
            # Pick relevant columns
            data = data[sourceframe['column'].values]
            for index, row in sourceframe.iterrows():
                if row['column'] not in data.columns:
                    continue
                if pd.notnull(row['default']):
                    data[row['column']].fillna(row['default'], inplace=True)
                if pd.notnull(row['target']):
                    data.rename(columns={row['column']: row['target']}, inplace=True)
            result.append(data)
        # Save into target column
        result = pd.concat(result, sort=False)
        gramex.cache.save(result, target, callback='csv', index=False)
    return {'merged': config[targetcols].drop_duplicates()}
