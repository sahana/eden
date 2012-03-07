
class InsertChunksWithoutCheckingForExistingReadings(object):
    """Insert chunks of 1000 records at a time, bypassing web2py's OR/M.
    
    This is much faster but not as safe, depending on the constraint 
    checking of the database.
    
    * should take names of fields
    """
    def __init__(self, sample_table):
        self.chunk = []
        self.sample_table = sample_table
    
    def write_chunk(self):
        #self.sample_table.insert_values(self.chunk)
        print "\n".join(self.chunk)
        self.chunk = []
    
    def __call__(
        self,
        time_period,
        place_id,
        value
    ):
#        self.chunk.append("".join((
#            "(",
#                str(time_period),",",
#                str(place_id),",",
#                str(value),
#            ")"
#        )))
        self.chunk.append(
            "%i,%i,%f" % (place_id, time_period, value)
        )
        if len(self.chunk) >= 1000:
            self.write_chunk()
            
    def done(self):
        if len(self.chunk) > 0:    
            self.write_chunk()
