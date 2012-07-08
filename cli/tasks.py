from celery.task import task

from image_builder.imagebuilder import ImageBuilder

@task
def build(buildconfig, kickstart = None):

    build = ImageBuilder(buildconfig, kickstart)
    status = build.build()

    #TODO: email notification

    return
