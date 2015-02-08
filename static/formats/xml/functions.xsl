<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

	<!-- Template to loop through a list calling the resource template for each element in the list -->
	<xsl:template name="splitList">
	  <xsl:param name="list"/>
	  <xsl:param name="splitsep"/>
	  <xsl:if test="$list!=''">
	      <xsl:choose>
		     <xsl:when test="contains($list,$splitsep)">
              <!-- When we have a list pop the first value off the list and pass this to
                   the resource template that will format the value as desired. The rest of
                   the list is then sent (recursively) to this function for further processing -->
        		   <xsl:call-template name="resource">
				     <xsl:with-param name="value" select="normalize-space(substring-before($list,$splitsep))"/>
			       </xsl:call-template>
                   <xsl:variable name="end" select="normalize-space(substring-after($list,$splitsep))"/>

                   <!-- recursive call -->
         	       <xsl:if test="$end!=''">
			           <xsl:call-template name="splitList">
			             <xsl:with-param name="list" select="$end"/>
			             <xsl:with-param name="splitsep" select="$splitsep"/>
			           </xsl:call-template>
			       </xsl:if>
		     </xsl:when>

		     <xsl:otherwise>
               <!-- This is not a list so it must be the last (or only) element pass this to
                    the resource template that will format the value as desired. -->
		       <xsl:call-template name="resource">
			      <xsl:with-param name="value" select="normalize-space($list)"/>
		       </xsl:call-template>
		     </xsl:otherwise>
	      </xsl:choose>
	   </xsl:if>
	</xsl:template>


	<!-- Template to loop through a list and quote each element -->
	<xsl:template name="quoteList">
	  <xsl:param name="list"/>
	  <xsl:param name="splitsep"/>
	  <xsl:param name="joinsep"/>
	  <xsl:if test="$list!=''">
         <xsl:choose>
		     <xsl:when test="contains($list,$splitsep)">
                <!-- When we have a list pop the first value off the list and and store in first.
                    The rest of the list is then sent to this function for further processing -->
                <xsl:variable name="front" select="substring-before($list,$splitsep)"/>
                <xsl:variable name="end" select="substring-after($list,$splitsep)"/>

                <!-- recursive call -->
        	    <xsl:if test="$end!=''">
			        <xsl:variable name="quotedList">
			          <xsl:call-template name="quoteList">
			            <xsl:with-param name="list" select="$end"/>
			             <xsl:with-param name="splitsep" select="$splitsep"/>
			          </xsl:call-template>
			        </xsl:variable>
			        <xsl:value-of select="concat('&quot;', $front,'&quot;',$joinsep,$quotedList)"/>
 	            </xsl:if>
		     </xsl:when>

		     <xsl:otherwise>
                <!-- This is not a list so it must be the last (or only) element pass this to
                    the resource template that will format the value as desired. -->
			    <xsl:value-of select="concat('&quot;', $list,'&quot;')"/>
		     </xsl:otherwise>
	      </xsl:choose>
	   </xsl:if>
	</xsl:template>

</xsl:stylesheet>
