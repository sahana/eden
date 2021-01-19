from functools import partial

from s3compat import urlencode

try:
    from geopy.geocoders import GeoNames
    from geopy.geocoders.base import DEFAULT_SENTINEL
    from geopy.util import logger

    class rlp_GeoNames(GeoNames):

        enable = True

        geocode_path = '/mapbender/geoportal/gaz_geom_mobile.php?q=fall%2010&outputFormat=json&resultTarget=web&searchEPSG=4326&forcePoint=true&forceGeonames=true&bundesland=Rheinland-Pfalz'

        def __init__(
                self,
                *,
                timeout=DEFAULT_SENTINEL,
                proxies=DEFAULT_SENTINEL,
                user_agent=None,
                ssl_context=DEFAULT_SENTINEL,
                adapter_factory=None,
                scheme='https'
        ):
            """
                RLP's GeoNames-compatible GeoCoder service
            """
            super().__init__(
                username="dummy",
                scheme=scheme,
                timeout=timeout,
                proxies=proxies,
                user_agent=user_agent,
                ssl_context=ssl_context,
                adapter_factory=adapter_factory,
            )

            domain = 'www.geoportal.rlp.de'
            self.api = (
                "%s://%s%s" % (self.scheme, domain, self.geocode_path)
            )

        def geocode(
                self,
                query,
                *,
                exactly_one=True,
                timeout=DEFAULT_SENTINEL,
                country=None,
                country_bias=None
        ):
            """
            Return a location point by address.

            :param str query: The address or query you wish to geocode.

            :param bool exactly_one: Return one result or a list of results, if
                available.

            :param int timeout: Time, in seconds, to wait for the geocoding service
                to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
                exception. Set this only if you wish to override, on this call
                only, the value set during the geocoder's initialization.

            :param country: Limit records to the specified countries.
                Two letter country code ISO-3166 (e.g. ``FR``). Might be
                a single string or a list of strings.
            :type country: str or list

            :param str country_bias: Records from the country_bias are listed first.
                Two letter country code ISO-3166.

            :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
                ``exactly_one=False``.
            """
            params = [
                ('name_startsWith', query),
            ]

            #if country_bias:
            #    params.append(('countryBias', country_bias))

            #if not country:
            #    country = []
            #if isinstance(country, str):
            #    country = [country]
            #for country_item in country:
            #    params.append(('country', country_item))

            if exactly_one:
                params.append(('maxRows', 1))
            url = "&".join((self.api, urlencode(params)))
            logger.debug("%s.geocode: %s", self.__class__.__name__, url)
            callback = partial(self._parse_json, exactly_one=exactly_one)
            return self._call_geocoder(url, callback, timeout=timeout)

except ImportError:

    # Geopy not installed
    class rlp_GeoNames(object):
        enable = False
