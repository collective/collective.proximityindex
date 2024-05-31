# -*- coding: utf-8 -*-
"""Distance calculation functions.

This module is possibly too narrowly conceived. If we have other
location-related code with no complex dependencies, it could also
go in here, and the module could be renamed appropriately.
"""
import logging
import math
from App.special_dtml import DTMLFile
from Products.PluginIndexes.interfaces import ISortIndex
from Products.PluginIndexes.common.UnIndex import UnIndex
from zope.interface import implementer
from ZODB.POSException import ConflictError
from zope.globalrequest import getRequest


logger = logging.getLogger(__name__)

AVG_EARTH_RADIUS_KM = 6371.0088


def distanceInDegrees(origin, destination):
    """Euclidean distance

    `origin` and `destination` are dicts with `lat` and `lng` keys.
    """
    # unpack latitude/longitude
    lat1, lng1 = origin
    lat2, lng2 = destination

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    return math.sqrt(dlat**2 + dlng**2)


def distanceOfRadiansInKM(a, b):
    """Compute the Haversine distance in kilometers between two points represented as
    two-tuples of radians.

    Haversine formula stolen from https://github.com/mapado/haversine
    """
    y1, x1 = a
    y2, x2 = b
    y = y2 - y1
    x = x2 - x1
    d = math.sin(y * 0.5) ** 2 + math.cos(y1) * math.cos(y2) * math.sin(x * 0.5) ** 2

    return 2 * AVG_EARTH_RADIUS_KM * math.asin(math.sqrt(d))


def distanceInKM(origin, destination):
    """Haversine formula stolen from https://github.com/mapado/haversine

    `origin` and `destination` are (lat, lng) tuples.
    """
    # unpack latitude/longitude
    lat1, lng1 = origin
    lat2, lng2 = destination

    # convert all latitudes/longitudes from decimal degrees to radians
    lat1 = math.radians(lat1)
    lng1 = math.radians(lng1)
    lat2 = math.radians(lat2)
    lng2 = math.radians(lng2)

    # calculate haversine
    return distanceOfRadiansInKM((lat1, lng1), (lat2, lng2))


_marker = object()


@implementer(ISortIndex)
class ProximityIndex(UnIndex):
    """Index for sorting by geographic proximity"""

    meta_type = "ProximityIndex"
    manage_options = (dict(label="Settings", action="manage_main"),)
    manage = manage_main = DTMLFile("dtml/manageProximityIndex", globals())
    manage_main._setName("manage_main")
    query_options = ("center",)

    def insertForwardIndexEntry(self, entry, documentId):
        # don't use the forward index
        pass

    def removeForwardIndexEntry(self, entry, documentId):
        # don't use the forward index
        pass

    def __len__(self):
        # Borrowed from:
        # https://github.com/plone/plone.folder/blob/master/src/plone/folder/nogopip.py
        #
        # with python 2.4 returning `sys.maxint` gives:
        # OverflowError: __len__() should return 0 <= outcome < 2**31
        # so...
        return 2**31 - 1

    def _convert(self, value, default=None):
        # convert from degrees to radians because TODO why?
        try:
            return (math.radians(value.latitude), math.radians(value.longitude))
        except AttributeError:
            return _marker

    def _index_object(self, documentId, obj, threshold=None, attr=""):
        """index and object 'obj' with integer id 'documentId'"""
        returnStatus = 0

        # First we need to see if there's anything interesting to look at
        datum = self._get_object_datum(obj, attr)
        if datum is None:
            # Remove previous index if it exists
            oldDatum = self._unindex.get(documentId, _marker)
            if oldDatum:
                self.removeForwardIndexEntry(oldDatum, documentId)
                del self._unindex[documentId]
            return 0

        datum = self._convert(datum, default=_marker)

        # We don't want to do anything that we don't have to here, so we'll
        # check to see if the new and existing information is the same.
        oldDatum = self._unindex.get(documentId, _marker)
        if datum != oldDatum:
            if oldDatum is not _marker:
                self.removeForwardIndexEntry(oldDatum, documentId)
                if datum is _marker:
                    try:
                        del self._unindex[documentId]
                    except ConflictError:
                        raise

            if datum is not _marker:
                self.insertForwardIndexEntry(datum, documentId)
                self._unindex[documentId] = datum

            returnStatus = 1

        return returnStatus

    def documentToKeyMap(self):
        # get mapping from doc id to calculated proximity
        zope_request = getRequest()
        if not hasattr(zope_request, "_proximity_center"):
            raise ValueError(
                "Can't sort by {} unless a center point is provided in the query.".format(
                    self.id
                )
            )
        center = zope_request._proximity_center
        center_as_radians = (math.radians(center[0]), math.radians(center[1]))
        return DistanceKeyMap(center_as_radians, self._unindex)


class DistanceKeyMap:
    """Calculates the sort key using a Haversine distance formula.

    `center` and `unindex` are (lat, lng) tuples expressed as radians
    """

    def __init__(self, center, unindex):
        self.center = center
        self.unindex = unindex

    def __getitem__(self, doc):
        dist = distanceOfRadiansInKM(self.center, self.unindex[doc])
        return dist


manage_addProximityIndexForm = DTMLFile("dtml/addProximityIndex", globals())


def manage_addProximityIndex(
    self, identifier, extra=None, REQUEST=None, RESPONSE=None, URL3=None
):
    """add a geo proximity index"""
    return self.manage_addIndex(
        identifier,
        "ProximityIndex",
        extra=extra,
        REQUEST=REQUEST,
        RESPONSE=RESPONSE,
        URL1=URL3,
    )
