''' Tests delegation to the appropriate
build method '''

from mock import MagicMock
from image_builder.imagebuilder import Worker

def delegation(iso_type):

    worker_real = Worker('')

    # get the stubs
    worker_real.build_bootiso = MagicMock(return_value = None)
    worker_real.build_dvd = MagicMock(return_value = None)
    worker_real.build_live = MagicMock(return_value = None)

    if iso_type == 'boot':
        worker_real.build_bootiso()
        worker_real.build_bootiso.assert_called_with()

    if iso_type == 'dvd':
        worker_real.build_dvd()
        worker_real.build_dvd.assert_called_with()

    if iso_type == 'boot':
        worker_real.build_live()
        worker_real.build_live.assert_called_with()
    
    return

def test_delegation():
    iso_types=['boot', 'dvd', 'live']

    for iso_type in iso_types:
        delegation(iso_type)
    
    return
    
