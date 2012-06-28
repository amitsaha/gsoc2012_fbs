''' Tests delegation to the prep_siderepo
method '''

from mock import MagicMock
from image_builder.imagebuilder import Worker

def create_siderepo(workdir, arch, nvr, bid):

    worker_real=Worker('')

    # get the stubs
    worker_real.prep_siderepo = MagicMock(return_value = ' __str__')
    worker_real.get_nvr = MagicMock(return_value = []) 

    rpms_nvr = []
    if nvr:
        for rpm in nvr.split(';'):
            rpms_nvr.append(rpm)

    bids = []        
    if bid:
        for rpm in bid.split(';'):
            bids.extend(str(rpm))
            
    rpms_bid = worker_real.get_nvr(bids, arch)
    rpms_nvr.extend(rpms_bid)
    
    # prepare side repository
    rpms = rpms_nvr

    if rpms:
        worker_real.prep_siderepo(workdir, rpms, arch)

    if bid:
        worker_real.get_nvr.assert_called_with(bids, arch)
    if rpms:
        worker_real.prep_siderepo.assert_called_with(workdir, rpms, arch)

    return

def test_create_siderepo():
    archs=['i686','x86_64']

    for arch in archs:
        nvr='foo;bar'
        bid='baz;bazz'
        create_siderepo([], arch, nvr, bid)

        nvr='foo;bar'
        bid=''
        create_siderepo([], arch, nvr, bid)

        nvr=''
        bid='foo;bar'
        create_siderepo([], arch, nvr, bid)

        nvr=''
        bid=''
        create_siderepo([], arch, nvr, bid)
    
    return
        
        
    
