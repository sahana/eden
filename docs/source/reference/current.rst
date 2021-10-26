The *current* Object
====================

The *current* object holds thread-local global variables. It can be imported into any context:

.. code-block:: python

   from gluon import current

.. table:: Objects accessible through current
   :widths: auto

   ===================================  =================  ============================================
   Attribute                            Type               Explanation
   ===================================  =================  ============================================
   current.db                           DAL                the database
   :doc:`current.s3db <services/s3db>`  DataModel          the model loader
   current.deployment_settings          S3Config           deployment settings
   :doc:`current.auth <services/auth>`  AuthS3             global authentication/authorisation service
   :doc:`current.gis <services/gis>`    GIS                global GIS service
   :doc:`current.msg <services/msg>`    S3Msg              global messaging service
   :doc:`current.xml <services/xml>`    S3XML              global XML decoder/encoder service
   current.request                      Request            web2py's global request object
   current.response                     Response           web2py's global response object
   current.T                            TranslatorFactory  String Translator (for i18n)
   current.messages                     Messages           Common labels (internationalised)
   current.ERROR                        Messages           Common error messages (internationalised)
   ===================================  =================  ============================================

