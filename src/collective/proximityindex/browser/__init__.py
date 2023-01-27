from ..index import ProximityIndex


class ProximityIndexAddView:
    def __call__(self, id='', submit_add=''):

        if submit_add and id:
            obj = ProximityIndex(id, extra={"indexed_attrs": "getGeolocation"})
            zcatalog = self.context.context
            zcatalog.addIndex(id, obj)

            # zcatalog._p_jar.add(obj)

            self.request.response.redirect(
                zcatalog.absolute_url()
                + "/manage_catalogIndexes?manage_tabs_message=Index%20Added"
            )

        # Note the unfortunate homonym "index": self.index() renders the add
        # form, which submits to this method to add a catalog index.
        return self.index()
