from furious import context

from ripl.core.aggregation.client import twitter


def aggregate():
    """Kick off the trend aggregation process."""

    locations = twitter.get_locations_with_trends()

    with context.new() as ctx:
        for location_chunk in _chunk(locations):
            ctx.add(target=aggregate_for_locations, args=(location_chunk,))


def aggregate_for_locations(locations):
    """Collect trend data for the given locations, specified as WOEIDs."""
    # TODO
    print locations


def _chunk(the_list, chunk_size=5):
    """Chunk the_list into multiple lists of size chunk_size."""

    for i in xrange(0, len(the_list), chunk_size):
        yield the_list[i:i + chunk_size]

