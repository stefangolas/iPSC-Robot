# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 17:32:19 2021

@author: stefa
"""

from labkey.api_wrapper import APIWrapper
from labkey.query import Pagination, QueryFilter


print("Create a server context")
labkey_server = "aics.corp.alleninstitute.org"
project_name = "AICS"  # Project folder name
context_path = "labkey"
api = APIWrapper(labkey_server, project_name, context_path, use_ssl=False)
schema = "microscopy"
table = "HamiltonWorklist"

filters = [
    QueryFilter("PlateBatch", "60_20211206_Seed", QueryFilter.Types.EQUAL),
]

result = api.query.select_rows(schema, table, filter_array=filters)

barcodes = [x['Barcode'] for x in result['rows']]

def get_uniques(dblist):
    unique_items = []
    for item in dblist:
        if item not in unique_items:
            unique_items.append(item)
    return unique_items

unique_barcodes = get_uniques(barcodes)

worklist = []

for bc in unique_barcodes:
    bc_filter = [
        QueryFilter("Barcode", bc, QueryFilter.Types.EQUAL),
        ]

    plate_type = api.query.select_rows(schema, table, filter_array=bc_filter)['rows'][0]['PlateGeometry']
    worklist.append({'barcode':bc, 'plate_type':plate_type})
