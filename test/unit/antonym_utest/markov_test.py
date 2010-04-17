from unittest import TestCase, main

from antonym.core import DataException
from antonym.text.markov import Markov2Speaker

from katapult.log import config as logging_config


class Markov2Test(TestCase):
    
    def __log(self, msg):
        print msg
        
    def _test_short_ingest(self):
        speaker = self.__new_speaker()
        self.assertRaises(DataException, self.__ingest_and_speak, speaker, "hi", 0, 130)
    
    def _test_moderate_ingest(self):
        speaker = self.__new_speaker()
        source = """Operation Tractable was the final offensive conducted by Canadian Army and Polish Army troops as part of the Battle of Normandy. The goal of this operation was to capture the strategically important
French town of Falaise, and following that, the smaller towns of Trun and Chambois. This operation was undertaken by the Polish 1st Armoured Division and the First Canadian Army against the
Wehrmacht's Army Group B, and it was a part of the largest encirclement on the German Western Front during World War II. Despite a slow start to the offensive that was marked by limited gains north of
Falaise, innovative tactics by Polish 1st Armoured Division, under the command of Stanislaw Maczek during the drive for Chambois enabled the Falaise Gap to be partially closed by August 19, 1944,
trapping about 150,000 German soldiers in the Falaise Pocket."""
        self.__ingest_and_speak(speaker, source, 0, 130)
        
    def __new_speaker(self):
        return Markov2Speaker()
        
    def __ingest_and_speak(self, speaker, ingest, min_length, max_length):
        self.__log("ingesting %s" % ingest)
        speaker.ingest(ingest)
        speaker.compile()
        result = speaker.speak(min_length, max_length)
        self.__log("speak(%d,%d): %s" % (min_length, max_length, result))
        return result
        
if __name__ == "__main__":
    logging_config()
    main()