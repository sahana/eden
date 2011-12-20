
class InsertChunksWithoutCheckingForExistingReadings(object):
    """Insert chunks of 1000 records at a time, bypassing web2py's OR/M.
    
    This is much faster but not as safe.
    """
    def __init__(self, sample_table):
        self.chunk = []
        self.sample_table = sample_table
    
    def write_chunk(self, chunk):
        self.sample_table.insert_values(self.chunk)
        self.chunk = []
    
    def __call__(
        self,
        time_period,
        place_id,
        value
    ):
        self.chunk.append("".join((
            "(",
                time_period.__str__(),",",
                place_id.__str__(),",",
                value.__str__(),
            ")"
        )))
        if len(self.chunk) >= 1000:
            self.write_chunk()
            
    def done(self):
        if len(self.chunk) > 0:    
            self.write_chunk()
