<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:c="http://countries.data" version="1.0">

    <!-- Country templates

         include into other stylesheets with:
             <xsl:include href="../xml/countries.xsl"/>

         Copyright (c) 2011 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    -->

    <!-- ****************************************************************** -->

    <xsl:variable name="countries-top" select="document('')/*/c:countries"/>

    <!-- Convert country names to ISO 3166-1 country codes -->
    <xsl:key name="country2iso-lookup" match="c:country" use="c:name"/>

    <xsl:template name="countryname2iso">
        <xsl:param name="country"/>
        <xsl:apply-templates select="$countries-top">
            <xsl:with-param name="country" select="$country"/>
        </xsl:apply-templates>
    </xsl:template>

    <!-- Convert ISO 3166-1 country codes to names -->
    <xsl:key name="iso2country-lookup" match="c:country" use="c:code"/>

    <xsl:template name="iso2countryname">
        <xsl:param name="country"/>
        <xsl:apply-templates select="$countries-top">
            <xsl:with-param name="country" select="$country"/>
        </xsl:apply-templates>
    </xsl:template>

    <xsl:template match="c:countries">
        <xsl:param name="country"/>
        <xsl:choose>
            <xsl:when test="string-length($country)!=2">
                <xsl:value-of select="key('country2iso-lookup', $country)/c:code"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="key('iso2country-lookup', $country)/c:name"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <c:countries>
        <c:country><c:code>AF</c:code><c:name>Afghanistan</c:name></c:country>
        <c:country><c:code>AX</c:code><c:name>Åland Islands</c:name></c:country>
        <c:country><c:code>AL</c:code><c:name>Albania</c:name></c:country>
        <c:country><c:code>DZ</c:code><c:name>Algeria</c:name></c:country>
        <c:country><c:code>AS</c:code><c:name>American Samoa</c:name></c:country>
        <c:country><c:code>AD</c:code><c:name>Andorra</c:name></c:country>
        <c:country><c:code>AO</c:code><c:name>Angola</c:name></c:country>
        <c:country><c:code>AI</c:code><c:name>Anguilla</c:name></c:country>
        <c:country><c:code>AQ</c:code><c:name>Antarctica</c:name></c:country>
        <c:country><c:code>AG</c:code><c:name>Antigua and Barbuda</c:name></c:country>
        <c:country><c:code>AR</c:code><c:name>Argentina</c:name></c:country>
        <c:country><c:code>AM</c:code><c:name>Armenia</c:name></c:country>
        <c:country><c:code>AW</c:code><c:name>Aruba</c:name></c:country>
        <c:country><c:code>AU</c:code><c:name>Australia</c:name></c:country>
        <c:country><c:code>AT</c:code><c:name>Austria</c:name></c:country>
        <c:country><c:code>AZ</c:code><c:name>Azerbaijan</c:name></c:country>
        <c:country><c:code>BS</c:code><c:name>Bahamas</c:name></c:country>
        <c:country><c:code>BH</c:code><c:name>Bahrain</c:name></c:country>
        <c:country><c:code>BD</c:code><c:name>Bangladesh</c:name></c:country>
        <c:country><c:code>BB</c:code><c:name>Barbados</c:name></c:country>
        <c:country><c:code>BY</c:code><c:name>Belarus</c:name></c:country>
        <c:country><c:code>BE</c:code><c:name>Belgium</c:name></c:country>
        <c:country><c:code>BZ</c:code><c:name>Belize</c:name></c:country>
        <c:country><c:code>BJ</c:code><c:name>Benin</c:name></c:country>
        <c:country><c:code>BM</c:code><c:name>Bermuda</c:name></c:country>
        <c:country><c:code>BT</c:code><c:name>Bhutan</c:name></c:country>
        <c:country><c:code>BO</c:code><c:name>Bolivia</c:name></c:country>
        <c:country><c:code>BA</c:code><c:name>Bosnia and Herzegovina</c:name></c:country>
        <c:country><c:code>BW</c:code><c:name>Botswana</c:name></c:country>
        <c:country><c:code>BV</c:code><c:name>Bouvet Island</c:name></c:country>
        <c:country><c:code>BR</c:code><c:name>Brazil</c:name></c:country>
        <c:country><c:code>IO</c:code><c:name>British Indian Ocean Territory</c:name></c:country>
        <c:country><c:code>VG</c:code><c:name>British Virgin Islands</c:name></c:country>
        <c:country><c:code>BN</c:code><c:name>Brunei Darussalam</c:name></c:country>
        <c:country><c:code>BG</c:code><c:name>Bulgaria</c:name></c:country>
        <c:country><c:code>BF</c:code><c:name>Burkina Faso</c:name></c:country>
        <c:country><c:code>MM</c:code><c:name>Burma</c:name></c:country>
        <c:country><c:code>BI</c:code><c:name>Burundi</c:name></c:country>
        <c:country><c:code>KH</c:code><c:name>Cambodia</c:name></c:country>
        <c:country><c:code>CM</c:code><c:name>Cameroon</c:name></c:country>
        <c:country><c:code>CA</c:code><c:name>Canada</c:name></c:country>
        <c:country><c:code>CV</c:code><c:name>Cape Verde</c:name></c:country>
        <c:country><c:code>KY</c:code><c:name>Cayman Islands</c:name></c:country>
        <c:country><c:code>CF</c:code><c:name>Central African Republic</c:name></c:country>
        <c:country><c:code>TD</c:code><c:name>Chad</c:name></c:country>
        <c:country><c:code>CL</c:code><c:name>Chile</c:name></c:country>
        <c:country><c:code>CN</c:code><c:name>China</c:name></c:country>
        <c:country><c:code>CX</c:code><c:name>Christmas Island</c:name></c:country>
        <c:country><c:code>CC</c:code><c:name>Cocos (Keeling) Islands</c:name></c:country>
        <c:country><c:code>CO</c:code><c:name>Colombia</c:name></c:country>
        <c:country><c:code>KM</c:code><c:name>Comoros</c:name></c:country>
        <c:country><c:code>CG</c:code><c:name>Congo</c:name></c:country>
        <c:country><c:code>CK</c:code><c:name>Cook Islands</c:name></c:country>
        <c:country><c:code>CR</c:code><c:name>Costa Rica</c:name></c:country>
        <c:country><c:code>CI</c:code><c:name>Cote d'Ivoire</c:name></c:country>
        <c:country><c:code>HR</c:code><c:name>Croatia</c:name></c:country>
        <c:country><c:code>CU</c:code><c:name>Cuba</c:name></c:country>
        <c:country><c:code>CY</c:code><c:name>Cyprus</c:name></c:country>
        <c:country><c:code>CZ</c:code><c:name>Czech Republic</c:name></c:country>
        <c:country><c:code>CD</c:code><c:name>Democratic Republic of the Congo</c:name></c:country>
        <c:country><c:code>DK</c:code><c:name>Denmark</c:name></c:country>
        <c:country><c:code>DJ</c:code><c:name>Djibouti</c:name></c:country>
        <c:country><c:code>DM</c:code><c:name>Dominica</c:name></c:country>
        <c:country><c:code>DO</c:code><c:name>Dominican Republic</c:name></c:country>
        <c:country><c:code>EC</c:code><c:name>Ecuador</c:name></c:country>
        <c:country><c:code>EG</c:code><c:name>Egypt</c:name></c:country>
        <c:country><c:code>SV</c:code><c:name>El Salvador</c:name></c:country>
        <c:country><c:code>GQ</c:code><c:name>Equatorial Guinea</c:name></c:country>
        <c:country><c:code>ER</c:code><c:name>Eritrea</c:name></c:country>
        <c:country><c:code>EE</c:code><c:name>Estonia</c:name></c:country>
        <c:country><c:code>ET</c:code><c:name>Ethiopia</c:name></c:country>
        <c:country><c:code>FK</c:code><c:name>Falkland Islands (Malvinas)</c:name></c:country>
        <c:country><c:code>FO</c:code><c:name>Faroe Islands</c:name></c:country>
        <c:country><c:code>FJ</c:code><c:name>Fiji</c:name></c:country>
        <c:country><c:code>FI</c:code><c:name>Finland</c:name></c:country>
        <c:country><c:code>FR</c:code><c:name>France</c:name></c:country>
        <c:country><c:code>GF</c:code><c:name>French Guiana</c:name></c:country>
        <c:country><c:code>PF</c:code><c:name>French Polynesia</c:name></c:country>
        <c:country><c:code>TF</c:code><c:name>French Southern and Antarctic Lands</c:name></c:country>
        <c:country><c:code>GA</c:code><c:name>Gabon</c:name></c:country>
        <c:country><c:code>GM</c:code><c:name>Gambia</c:name></c:country>
        <c:country><c:code>GE</c:code><c:name>Georgia</c:name></c:country>
        <c:country><c:code>DE</c:code><c:name>Germany</c:name></c:country>
        <c:country><c:code>GH</c:code><c:name>Ghana</c:name></c:country>
        <c:country><c:code>GI</c:code><c:name>Gibraltar</c:name></c:country>
        <c:country><c:code>GR</c:code><c:name>Greece</c:name></c:country>
        <c:country><c:code>GL</c:code><c:name>Greenland</c:name></c:country>
        <c:country><c:code>GD</c:code><c:name>Grenada</c:name></c:country>
        <c:country><c:code>GP</c:code><c:name>Guadeloupe</c:name></c:country>
        <c:country><c:code>GU</c:code><c:name>Guam</c:name></c:country>
        <c:country><c:code>GT</c:code><c:name>Guatemala</c:name></c:country>
        <c:country><c:code>GG</c:code><c:name>Guernsey</c:name></c:country>
        <c:country><c:code>GN</c:code><c:name>Guinea</c:name></c:country>
        <c:country><c:code>GW</c:code><c:name>Guinea-Bissau</c:name></c:country>
        <c:country><c:code>GY</c:code><c:name>Guyana</c:name></c:country>
        <c:country><c:code>HT</c:code><c:name>Haiti</c:name></c:country>
        <c:country><c:code>HM</c:code><c:name>Heard Island and McDonald Islands</c:name></c:country>
        <c:country><c:code>VA</c:code><c:name>Holy See (Vatican City)</c:name></c:country>
        <c:country><c:code>HN</c:code><c:name>Honduras</c:name></c:country>
        <c:country><c:code>HK</c:code><c:name>Hong Kong</c:name></c:country>
        <c:country><c:code>HU</c:code><c:name>Hungary</c:name></c:country>
        <c:country><c:code>IS</c:code><c:name>Iceland</c:name></c:country>
        <c:country><c:code>IN</c:code><c:name>India</c:name></c:country>
        <c:country><c:code>ID</c:code><c:name>Indonesia</c:name></c:country>
        <c:country><c:code>IR</c:code><c:name>Iran (Islamic Republic of)</c:name></c:country>
        <c:country><c:code>IQ</c:code><c:name>Iraq</c:name></c:country>
        <c:country><c:code>IE</c:code><c:name>Ireland</c:name></c:country>
        <c:country><c:code>IM</c:code><c:name>Isle of Man</c:name></c:country>
        <c:country><c:code>IL</c:code><c:name>Israel</c:name></c:country>
        <c:country><c:code>IT</c:code><c:name>Italy</c:name></c:country>
        <c:country><c:code>JM</c:code><c:name>Jamaica</c:name></c:country>
        <c:country><c:code>JP</c:code><c:name>Japan</c:name></c:country>
        <c:country><c:code>JE</c:code><c:name>Jersey</c:name></c:country>
        <c:country><c:code>JO</c:code><c:name>Jordan</c:name></c:country>
        <c:country><c:code>KZ</c:code><c:name>Kazakhstan</c:name></c:country>
        <c:country><c:code>KE</c:code><c:name>Kenya</c:name></c:country>
        <c:country><c:code>KI</c:code><c:name>Kiribati</c:name></c:country>
        <c:country><c:code>KP</c:code><c:name>Korea, Democratic People's Republic of</c:name></c:country>
        <c:country><c:code>KR</c:code><c:name>Korea, Republic of</c:name></c:country>
        <c:country><c:code>KW</c:code><c:name>Kuwait</c:name></c:country>
        <c:country><c:code>KG</c:code><c:name>Kyrgyzstan</c:name></c:country>
        <c:country><c:code>LA</c:code><c:name>Lao People's Democratic Republic</c:name></c:country>
        <c:country><c:code>LV</c:code><c:name>Latvia</c:name></c:country>
        <c:country><c:code>LB</c:code><c:name>Lebanon</c:name></c:country>
        <c:country><c:code>LS</c:code><c:name>Lesotho</c:name></c:country>
        <c:country><c:code>LR</c:code><c:name>Liberia</c:name></c:country>
        <c:country><c:code>LY</c:code><c:name>Libyan Arab Jamahiriya</c:name></c:country>
        <c:country><c:code>LI</c:code><c:name>Liechtenstein</c:name></c:country>
        <c:country><c:code>LT</c:code><c:name>Lithuania</c:name></c:country>
        <c:country><c:code>LU</c:code><c:name>Luxembourg</c:name></c:country>
        <c:country><c:code>MO</c:code><c:name>Macau</c:name></c:country>
        <c:country><c:code>MG</c:code><c:name>Madagascar</c:name></c:country>
        <c:country><c:code>MW</c:code><c:name>Malawi</c:name></c:country>
        <c:country><c:code>MY</c:code><c:name>Malaysia</c:name></c:country>
        <c:country><c:code>MV</c:code><c:name>Maldives</c:name></c:country>
        <c:country><c:code>ML</c:code><c:name>Mali</c:name></c:country>
        <c:country><c:code>MT</c:code><c:name>Malta</c:name></c:country>
        <c:country><c:code>MH</c:code><c:name>Marshall Islands</c:name></c:country>
        <c:country><c:code>MQ</c:code><c:name>Martinique</c:name></c:country>
        <c:country><c:code>MR</c:code><c:name>Mauritania</c:name></c:country>
        <c:country><c:code>MU</c:code><c:name>Mauritius</c:name></c:country>
        <c:country><c:code>YT</c:code><c:name>Mayotte</c:name></c:country>
        <c:country><c:code>MX</c:code><c:name>Mexico</c:name></c:country>
        <c:country><c:code>FM</c:code><c:name>Micronesia, Federated States of</c:name></c:country>
        <c:country><c:code>MC</c:code><c:name>Monaco</c:name></c:country>
        <c:country><c:code>MN</c:code><c:name>Mongolia</c:name></c:country>
        <c:country><c:code>ME</c:code><c:name>Montenegro</c:name></c:country>
        <c:country><c:code>MS</c:code><c:name>Montserrat</c:name></c:country>
        <c:country><c:code>MA</c:code><c:name>Morocco</c:name></c:country>
        <c:country><c:code>MZ</c:code><c:name>Mozambique</c:name></c:country>
        <c:country><c:code>NA</c:code><c:name>Namibia</c:name></c:country>
        <c:country><c:code>NR</c:code><c:name>Nauru</c:name></c:country>
        <c:country><c:code>NP</c:code><c:name>Nepal</c:name></c:country>
        <c:country><c:code>NL</c:code><c:name>Netherlands</c:name></c:country>
        <c:country><c:code>AN</c:code><c:name>Netherlands Antilles</c:name></c:country>
        <c:country><c:code>NC</c:code><c:name>New Caledonia</c:name></c:country>
        <c:country><c:code>NZ</c:code><c:name>New Zealand</c:name></c:country>
        <c:country><c:code>NI</c:code><c:name>Nicaragua</c:name></c:country>
        <c:country><c:code>NE</c:code><c:name>Niger</c:name></c:country>
        <c:country><c:code>NG</c:code><c:name>Nigeria</c:name></c:country>
        <c:country><c:code>NU</c:code><c:name>Niue</c:name></c:country>
        <c:country><c:code>NF</c:code><c:name>Norfolk Island</c:name></c:country>
        <c:country><c:code>MP</c:code><c:name>Northern Mariana Islands</c:name></c:country>
        <c:country><c:code>NO</c:code><c:name>Norway</c:name></c:country>
        <c:country><c:code>OM</c:code><c:name>Oman</c:name></c:country>
        <c:country><c:code>PK</c:code><c:name>Pakistan</c:name></c:country>
        <c:country><c:code>PW</c:code><c:name>Palau</c:name></c:country>
        <c:country><c:code>PS</c:code><c:name>Palestine</c:name></c:country>
        <c:country><c:code>PA</c:code><c:name>Panama</c:name></c:country>
        <c:country><c:code>PG</c:code><c:name>Papua New Guinea</c:name></c:country>
        <c:country><c:code>PY</c:code><c:name>Paraguay</c:name></c:country>
        <c:country><c:code>PE</c:code><c:name>Peru</c:name></c:country>
        <c:country><c:code>PH</c:code><c:name>Philippines</c:name></c:country>
        <c:country><c:code>PN</c:code><c:name>Pitcairn Islands</c:name></c:country>
        <c:country><c:code>PL</c:code><c:name>Poland</c:name></c:country>
        <c:country><c:code>PT</c:code><c:name>Portugal</c:name></c:country>
        <c:country><c:code>PR</c:code><c:name>Puerto Rico</c:name></c:country>
        <c:country><c:code>QA</c:code><c:name>Qatar</c:name></c:country>
        <c:country><c:code>MD</c:code><c:name>Republic of Moldova</c:name></c:country>
        <c:country><c:code>RE</c:code><c:name>Reunion</c:name></c:country>
        <c:country><c:code>RO</c:code><c:name>Romania</c:name></c:country>
        <c:country><c:code>RU</c:code><c:name>Russia</c:name></c:country>
        <c:country><c:code>RW</c:code><c:name>Rwanda</c:name></c:country>
        <c:country><c:code>BL</c:code><c:name>Saint Barthelemy</c:name></c:country>
        <c:country><c:code>SH</c:code><c:name>Saint Helena</c:name></c:country>
        <c:country><c:code>KN</c:code><c:name>Saint Kitts and Nevis</c:name></c:country>
        <c:country><c:code>LC</c:code><c:name>Saint Lucia</c:name></c:country>
        <c:country><c:code>MF</c:code><c:name>Saint Martin</c:name></c:country>
        <c:country><c:code>PM</c:code><c:name>Saint Pierre and Miquelon</c:name></c:country>
        <c:country><c:code>VC</c:code><c:name>Saint Vincent and the Grenadines</c:name></c:country>
        <c:country><c:code>WS</c:code><c:name>Samoa</c:name></c:country>
        <c:country><c:code>SM</c:code><c:name>San Marino</c:name></c:country>
        <c:country><c:code>ST</c:code><c:name>Sao Tome and Principe</c:name></c:country>
        <c:country><c:code>SA</c:code><c:name>Saudi Arabia</c:name></c:country>
        <c:country><c:code>SN</c:code><c:name>Senegal</c:name></c:country>
        <c:country><c:code>RS</c:code><c:name>Serbia</c:name></c:country>
        <c:country><c:code>SC</c:code><c:name>Seychelles</c:name></c:country>
        <c:country><c:code>SL</c:code><c:name>Sierra Leone</c:name></c:country>
        <c:country><c:code>SG</c:code><c:name>Singapore</c:name></c:country>
        <c:country><c:code>SK</c:code><c:name>Slovakia</c:name></c:country>
        <c:country><c:code>SI</c:code><c:name>Slovenia</c:name></c:country>
        <c:country><c:code>SB</c:code><c:name>Solomon Islands</c:name></c:country>
        <c:country><c:code>SO</c:code><c:name>Somalia</c:name></c:country>
        <c:country><c:code>ZA</c:code><c:name>South Africa</c:name></c:country>
        <c:country><c:code>GS</c:code><c:name>South Georgia South Sandwich Islands</c:name></c:country>
        <c:country><c:code>ES</c:code><c:name>Spain</c:name></c:country>
        <c:country><c:code>LK</c:code><c:name>Sri Lanka</c:name></c:country>
        <c:country><c:code>SD</c:code><c:name>Sudan</c:name></c:country>
        <c:country><c:code>SR</c:code><c:name>Suriname</c:name></c:country>
        <c:country><c:code>SJ</c:code><c:name>Svalbard</c:name></c:country>
        <c:country><c:code>SZ</c:code><c:name>Swaziland</c:name></c:country>
        <c:country><c:code>SE</c:code><c:name>Sweden</c:name></c:country>
        <c:country><c:code>CH</c:code><c:name>Switzerland</c:name></c:country>
        <c:country><c:code>SY</c:code><c:name>Syrian Arab Republic</c:name></c:country>
        <c:country><c:code>TW</c:code><c:name>Taiwan</c:name></c:country>
        <c:country><c:code>TJ</c:code><c:name>Tajikistan</c:name></c:country>
        <c:country><c:code>TH</c:code><c:name>Thailand</c:name></c:country>
        <c:country><c:code>MK</c:code><c:name>The former Yugoslav Republic of Macedonia</c:name></c:country>
        <c:country><c:code>TL</c:code><c:name>Timor-Leste</c:name></c:country>
        <c:country><c:code>TG</c:code><c:name>Togo</c:name></c:country>
        <c:country><c:code>TK</c:code><c:name>Tokelau</c:name></c:country>
        <c:country><c:code>TO</c:code><c:name>Tonga</c:name></c:country>
        <c:country><c:code>TT</c:code><c:name>Trinidad and Tobago</c:name></c:country>
        <c:country><c:code>TN</c:code><c:name>Tunisia</c:name></c:country>
        <c:country><c:code>TR</c:code><c:name>Turkey</c:name></c:country>
        <c:country><c:code>TM</c:code><c:name>Turkmenistan</c:name></c:country>
        <c:country><c:code>TC</c:code><c:name>Turks and Caicos Islands</c:name></c:country>
        <c:country><c:code>TV</c:code><c:name>Tuvalu</c:name></c:country>
        <c:country><c:code>UG</c:code><c:name>Uganda</c:name></c:country>
        <c:country><c:code>UA</c:code><c:name>Ukraine</c:name></c:country>
        <c:country><c:code>AE</c:code><c:name>United Arab Emirates</c:name></c:country>
        <c:country><c:code>GB</c:code><c:name>United Kingdom</c:name></c:country>
        <c:country><c:code>TZ</c:code><c:name>United Republic of Tanzania</c:name></c:country>
        <c:country><c:code>US</c:code><c:name>United States</c:name></c:country>
        <c:country><c:code>UM</c:code><c:name>United States Minor Outlying Islands</c:name></c:country>
        <c:country><c:code>VI</c:code><c:name>United States Virgin Islands</c:name></c:country>
        <c:country><c:code>UY</c:code><c:name>Uruguay</c:name></c:country>
        <c:country><c:code>UZ</c:code><c:name>Uzbekistan</c:name></c:country>
        <c:country><c:code>VU</c:code><c:name>Vanuatu</c:name></c:country>
        <c:country><c:code>VE</c:code><c:name>Venezuela</c:name></c:country>
        <c:country><c:code>VN</c:code><c:name>Viet Nam</c:name></c:country>
        <c:country><c:code>WF</c:code><c:name>Wallis and Futuna Islands</c:name></c:country>
        <c:country><c:code>EH</c:code><c:name>Western Sahara</c:name></c:country>
        <c:country><c:code>YE</c:code><c:name>Yemen</c:name></c:country>
        <c:country><c:code>ZM</c:code><c:name>Zambia</c:name></c:country>
        <c:country><c:code>ZW</c:code><c:name>Zimbabwe</c:name></c:country>
    </c:countries>

<!-- ****************************************************************** -->
</xsl:stylesheet>